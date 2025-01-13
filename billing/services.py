"""Invoicing: charges from visits, stays and lab work; insurer share, copay, payments and late fees."""
import datetime as dt

from appointments.services import charge_cents as appointment_charge_cents
from clinkit import identifiers, rules
from wards.services import stay_charge_cents

from .models import Invoice, InvoiceLine, Payment


class BillingError(Exception):
    pass


def open_invoice(patient, issued_on):
    seq = Invoice.objects.filter(issued_on__year=issued_on.year).count() + 1
    return Invoice.objects.create(patient=patient, number=identifiers.invoice_number(issued_on.year, seq),
                                  issued_on=issued_on, status="draft")


def add_line(invoice, kind, description, unit_cents, qty=1, **links):
    if invoice.status not in ("draft", "issued"):
        raise BillingError(f"invoice {invoice.number} is {invoice.status}")
    if unit_cents < 0 or qty < 1:
        raise BillingError("negative amounts are not allowed")
    return InvoiceLine.objects.create(invoice=invoice, kind=kind, description=description, unit_cents=unit_cents, qty=qty, **links)


def charge_appointment(invoice, appointment):
    return add_line(invoice, "consult", f"Consultation: {appointment.reason}", appointment_charge_cents(appointment),
                    appointment=appointment)


def charge_stay(invoice, admission, as_of):
    return add_line(invoice, "bed", f"Ward stay {admission.bed.ward.code}", stay_charge_cents(admission, as_of), admission=admission)


def charge_lab(invoice, lab_order, unit_cents):
    return add_line(invoice, "lab", f"Lab {lab_order.test.code}", unit_cents, lab_order=lab_order)


def total_cents(invoice):
    return sum(line.total_cents for line in invoice.lines.all())


def insurer_share_cents(invoice):
    insurer = invoice.patient.insurer
    if insurer is None:
        return 0
    total = total_cents(invoice)
    return min(total, total * rules.insurer_coverage_bp(insurer.plan_tier) // 10000)


def patient_due_cents(invoice):
    """What the patient owes: the uncovered part, but never less than the policy copay (capped at the total)."""
    total = total_cents(invoice)
    uncovered = total - insurer_share_cents(invoice)
    if invoice.patient.insurer is None:
        return uncovered
    return min(total, max(uncovered, rules.copay_cents(total)))


def paid_cents(invoice):
    return sum(p.amount_cents for p in invoice.payments.all())


def balance_cents(invoice):
    return patient_due_cents(invoice) - paid_cents(invoice)


def record_payment(invoice, amount_cents, received_on, method="card", reference=""):
    if amount_cents <= 0:
        raise BillingError("payment must be positive")
    if invoice.status == "void":
        raise BillingError("invoice is void")
    pay = Payment.objects.create(invoice=invoice, amount_cents=amount_cents, received_on=received_on, method=method,
                                 reference=reference)
    if balance_cents(invoice) <= 0:
        invoice.status = "paid"
        invoice.save(update_fields=["status"])
    return pay


def due_date(invoice):
    return invoice.issued_on + dt.timedelta(days=invoice.due_days)


def late_fee_cents(invoice, as_of):
    balance = balance_cents(invoice)
    overdue = (as_of - due_date(invoice)).days
    if balance <= 0 or overdue <= 0:
        return 0
    return balance * rules.late_payment_fee_bp(overdue) // 10000


def statement(invoice, as_of):
    return {
        "number": invoice.number,
        "status": invoice.status,
        "total": total_cents(invoice),
        "insurer_share": insurer_share_cents(invoice),
        "patient_due": patient_due_cents(invoice),
        "paid": paid_cents(invoice),
        "balance": balance_cents(invoice),
        "late_fee": late_fee_cents(invoice, as_of),
        "due_on": due_date(invoice).isoformat(),
    }
