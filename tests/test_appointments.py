import datetime as dt

from django.test import TestCase

from appointments import services
from appointments.models import Appointment
from clinkit import rules

from . import factories as f


class BookingTests(TestCase):
    def setUp(self):
        self.doc = f.clinician()
        self.pat = f.patient(1)

    def test_book_stores_the_slot(self):
        appt = services.book(self.pat, self.doc, f.DAY, 30, "check-up")
        self.assertEqual((appt.status, appt.duration_min, appt.reason), ("booked", 30, "check-up"))

    def test_overlap_is_rejected(self):
        services.book(self.pat, self.doc, f.DAY, 30)
        with self.assertRaises(services.SchedulingError):
            services.book(f.patient(2), self.doc, f.DAY + dt.timedelta(minutes=10), 30)

    def test_buffer_is_enforced_from_the_policy_table(self):
        services.book(self.pat, self.doc, f.DAY, 30)
        buf = rules.appointment_buffer_minutes(30)
        other = f.patient(2)
        if buf:
            with self.assertRaises(services.SchedulingError):
                services.book(other, self.doc, f.DAY + dt.timedelta(minutes=30 + buf - 1), 30)
        ok = services.book(other, self.doc, f.DAY + dt.timedelta(minutes=30 + buf), 30)
        self.assertEqual(ok.status, "booked")

    def test_other_clinicians_are_independent(self):
        services.book(self.pat, self.doc, f.DAY, 30)
        nurse = f.clinician("E200", role="nurse", family="Lindqvist")
        self.assertEqual(services.book(f.patient(2), nurse, f.DAY, 30).clinician, nurse)

    def test_inactive_patient_or_wrong_role_rejected(self):
        self.pat.active = False
        self.pat.save()
        with self.assertRaises(services.SchedulingError):
            services.book(self.pat, self.doc, f.DAY)
        tech = f.clinician("E300", role="technician", family="Abara")
        with self.assertRaises(services.SchedulingError):
            services.book(f.patient(2), tech, f.DAY)

    def test_next_free_skips_booked_time(self):
        services.book(self.pat, self.doc, f.DAY, 30)
        slot = services.next_free(self.doc, f.DAY, f.DAY + dt.timedelta(hours=4), 30)
        earliest = 30 + rules.appointment_buffer_minutes(30)
        self.assertEqual(slot, f.DAY + dt.timedelta(minutes=-(-earliest // 5) * 5))


class CancellationTests(TestCase):
    def setUp(self):
        self.doc = f.clinician()
        self.appt = services.book(f.patient(1), self.doc, f.DAY + dt.timedelta(days=3), 20, "follow-up")

    def test_fee_depends_on_notice(self):
        fee = services.cancel(self.appt, f.DAY, "travel")
        self.assertEqual(fee, rules.no_show_fee_cents(72))
        self.appt.refresh_from_db()
        self.assertEqual((self.appt.status, self.appt.cancel_reason), ("cancelled", "travel"))

    def test_short_notice_fee(self):
        fee = services.cancel(self.appt, self.appt.starts_at - dt.timedelta(hours=1, minutes=30))
        self.assertEqual(fee, rules.no_show_fee_cents(1))

    def test_cancelled_slot_can_be_rebooked(self):
        services.cancel(self.appt, f.DAY)
        again = services.book(f.patient(2), self.doc, self.appt.starts_at, 20)
        self.assertEqual(again.status, "booked")

    def test_double_cancel_rejected(self):
        services.cancel(self.appt, f.DAY)
        with self.assertRaises(services.SchedulingError):
            services.cancel(self.appt, f.DAY)

    def test_no_show_and_complete(self):
        self.assertEqual(services.mark_no_show(self.appt), rules.no_show_fee_cents(0))
        with self.assertRaises(services.SchedulingError):
            services.complete(self.appt)


class ChargeTests(TestCase):
    def test_charge_is_fee_plus_overhead(self):
        doc, pat = f.clinician(), f.patient(1)
        for minutes in (10, 30, 45, 90):
            appt = Appointment.objects.create(patient=pat, clinician=doc, starts_at=f.DAY, duration_min=minutes)
            self.assertEqual(services.charge_cents(appt), rules.consult_fee_cents(minutes) + rules.room_overhead_cents(minutes))

    def test_day_schedule_excludes_cancelled(self):
        doc = f.clinician()
        a = services.book(f.patient(1), doc, f.DAY, 20)
        b = services.book(f.patient(2), doc, f.DAY + dt.timedelta(hours=2), 20)
        services.cancel(b, f.DAY - dt.timedelta(days=1))
        self.assertEqual(services.day_schedule(doc, f.DAY.date()), [a])
