import datetime as dt

from django.test import TestCase

from appointments import services as appointment_services
from billing import services
from billing.models import Invoice
from clinkit import rules
from labs import services as lab_services
from wards import services as ward_services

from . import factories as f

ISSUED = dt.date(2025, 3, 3)


class InvoiceTests(TestCase):
    def setUp(self):
        self.doc = f.clinician()
        self.pat = f.patient(1)

    def invoice(self, patient=None):
        return services.open_invoice(patient or self.pat, ISSUED)

    def test_numbers_are_sequential_per_year(self):
        a, b = self.invoice(), self.invoice()
        self.assertEqual((a.number, b.number), ("INV-2025-00001", "INV-2025-00002"))
        c = services.open_invoice(self.pat, dt.date(2026, 1, 2))
        self.assertEqual(c.number, "INV-2026-00001")

    def test_totals(self):
        inv = self.invoice()
        services.add_line(inv, "other", "Dressing", 1250, qty=2)
        services.add_line(inv, "other", "Gloves", 300)
        self.assertEqual(services.total_cents(inv), 2800)

    def test_negative_amounts_and_closed_invoices_rejected(self):
        inv = self.invoice()
        with self.assertRaises(services.BillingError):
            services.add_line(inv, "other", "Bad", -1)
        inv.status = "void"
        inv.save()
        with self.assertRaises(services.BillingError):
            services.add_line(inv, "other", "Late", 1)

    def test_appointment_stay_and_lab_lines(self):
        inv = self.invoice()
        appt = appointment_services.book(self.pat, self.doc, f.DAY, 30, "review")
        line = services.charge_appointment(inv, appt)
        self.assertEqual(line.unit_cents, appointment_services.charge_cents(appt))
        self.assertEqual(line.appointment, appt)
        ward = f.ward("W1", level=2)
        adm = ward_services.admit(self.pat, ward.beds.first(), self.doc, f.DAY)
        stay = services.charge_stay(inv, adm, f.DAY + dt.timedelta(hours=30))
        self.assertEqual(stay.unit_cents, 2 * rules.bed_day_rate_cents(2))
        order = lab_services.place_order(self.pat, self.doc, f.lab_test(), 3, f.DAY)
        services.charge_lab(inv, order, 1800)
        self.assertEqual(sorted(inv.lines.values_list("kind", flat=True)), ["bed", "consult", "lab"])
        self.assertEqual(services.total_cents(inv), line.unit_cents + stay.unit_cents + 1800)


class CoverageTests(TestCase):
    def setUp(self):
        self.insurer = f.insurer(tier=2)
        self.pat = f.patient(1, insurer=self.insurer)
        self.inv = services.open_invoice(self.pat, ISSUED)
        services.add_line(self.inv, "other", "Procedure", 40000)

    def test_insurer_share_uses_the_plan_tier(self):
        expected = min(40000, 40000 * rules.insurer_coverage_bp(2) // 10000)
        self.assertEqual(services.insurer_share_cents(self.inv), expected)

    def test_uninsured_patient_owes_everything(self):
        pat = f.patient(2)
        inv = services.open_invoice(pat, ISSUED)
        services.add_line(inv, "other", "Procedure", 40000)
        self.assertEqual((services.insurer_share_cents(inv), services.patient_due_cents(inv)), (0, 40000))

    def test_patient_due_is_at_least_the_copay_but_never_above_total(self):
        total = services.total_cents(self.inv)
        uncovered = total - services.insurer_share_cents(self.inv)
        self.assertEqual(services.patient_due_cents(self.inv), min(total, max(uncovered, rules.copay_cents(total))))
        self.assertLessEqual(services.patient_due_cents(self.inv), total)

    def test_payments_settle_the_invoice(self):
        due = services.patient_due_cents(self.inv)
        if due > 1:
            services.record_payment(self.inv, 1, ISSUED, "cash")
            self.assertEqual(services.balance_cents(self.inv), due - 1)
            self.assertNotEqual(Invoice.objects.get(pk=self.inv.pk).status, "paid")
        services.record_payment(self.inv, services.balance_cents(self.inv) or 1, ISSUED, "card", "AUTH-1")
        self.assertEqual(Invoice.objects.get(pk=self.inv.pk).status, "paid")

    def test_invalid_payments(self):
        with self.assertRaises(services.BillingError):
            services.record_payment(self.inv, 0, ISSUED)
        self.inv.status = "void"
        self.inv.save()
        with self.assertRaises(services.BillingError):
            services.record_payment(self.inv, 100, ISSUED)


class LateFeeTests(TestCase):
    def setUp(self):
        self.pat = f.patient(1)
        self.inv = services.open_invoice(self.pat, ISSUED)
        services.add_line(self.inv, "other", "Procedure", 20000)

    def test_due_date_uses_due_days(self):
        self.assertEqual(services.due_date(self.inv), ISSUED + dt.timedelta(days=30))

    def test_no_fee_before_due_or_when_paid(self):
        self.assertEqual(services.late_fee_cents(self.inv, ISSUED + dt.timedelta(days=30)), 0)
        services.record_payment(self.inv, 20000, ISSUED)
        self.assertEqual(services.late_fee_cents(self.inv, ISSUED + dt.timedelta(days=200)), 0)

    def test_fee_scales_with_days_overdue(self):
        for overdue in (10, 45, 80, 120):
            as_of = services.due_date(self.inv) + dt.timedelta(days=overdue)
            self.assertEqual(services.late_fee_cents(self.inv, as_of), 20000 * rules.late_payment_fee_bp(overdue) // 10000)

    def test_statement_collects_the_figures(self):
        stmt = services.statement(self.inv, ISSUED)
        self.assertEqual((stmt["number"], stmt["total"], stmt["paid"], stmt["due_on"]), ("INV-2025-00001", 20000, 0, "2025-04-02"))
        self.assertEqual(stmt["balance"], stmt["patient_due"])
