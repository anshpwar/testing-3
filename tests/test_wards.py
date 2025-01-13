import datetime as dt

from django.test import TestCase

from clinkit import clinical, rules
from wards import services
from wards.models import Admission

from . import factories as f

NOW = f.DAY


class AdmissionTests(TestCase):
    def setUp(self):
        self.doc = f.clinician()
        self.ward = f.ward("W1", level=2)
        self.beds = list(self.ward.beds.all())

    def test_admit_occupies_the_bed(self):
        adm = services.admit(f.patient(1), self.beds[0], self.doc, NOW)
        self.beds[0].refresh_from_db()
        self.assertEqual(self.beds[0].status, "occupied")
        self.assertTrue(adm.is_open)
        self.assertNotIn(self.beds[0], services.free_beds(self.ward))

    def test_occupied_bed_and_duplicate_admission_rejected(self):
        pat = f.patient(1)
        services.admit(pat, self.beds[0], self.doc, NOW)
        with self.assertRaises(services.WardError):
            services.admit(f.patient(2), self.beds[0], self.doc, NOW)
        with self.assertRaises(services.WardError):
            services.admit(pat, self.beds[1], self.doc, NOW)

    def test_attending_must_be_a_physician(self):
        nurse = f.clinician("E201", role="nurse", family="Lindqvist")
        with self.assertRaises(services.WardError):
            services.admit(f.patient(1), self.beds[0], nurse, NOW)

    def test_discharge_frees_into_cleaning_then_free(self):
        adm = services.admit(f.patient(1), self.beds[0], self.doc, NOW)
        services.discharge(adm, NOW + dt.timedelta(days=2), "home")
        self.beds[0].refresh_from_db()
        self.assertEqual(self.beds[0].status, "cleaning")
        self.assertEqual(adm.discharge_note, "home")
        services.mark_clean(self.beds[0])
        self.assertEqual(self.beds[0].status, "free")
        with self.assertRaises(services.WardError):
            services.mark_clean(self.beds[0])

    def test_discharge_checks(self):
        adm = services.admit(f.patient(1), self.beds[0], self.doc, NOW)
        with self.assertRaises(services.WardError):
            services.discharge(adm, NOW - dt.timedelta(hours=1))
        services.discharge(adm, NOW + dt.timedelta(hours=5))
        with self.assertRaises(services.WardError):
            services.discharge(adm, NOW + dt.timedelta(hours=6))

    def test_isolation_filter(self):
        self.beds[2].isolation = True
        self.beds[2].save()
        self.assertEqual(services.free_beds(self.ward, isolation=True), [self.beds[2]])
        self.assertEqual(len(services.free_beds(self.ward, isolation=False)), 2)


class ChargeAndStaffingTests(TestCase):
    def setUp(self):
        self.doc = f.clinician()
        self.ward = f.ward("W2", level=3, beds=("B1", "B2", "B3", "B4", "B5", "B6", "B7"))
        self.beds = list(self.ward.beds.all())

    def test_stay_is_charged_per_started_day(self):
        adm = services.admit(f.patient(1), self.beds[0], self.doc, NOW)
        self.assertEqual(services.stay_days(adm, NOW + dt.timedelta(hours=1)), 1)
        self.assertEqual(services.stay_days(adm, NOW + dt.timedelta(hours=25)), 2)
        self.assertEqual(services.stay_charge_cents(adm, NOW + dt.timedelta(hours=25)), 2 * rules.bed_day_rate_cents(3))

    def test_closed_stay_ignores_as_of(self):
        adm = services.admit(f.patient(1), self.beds[0], self.doc, NOW)
        services.discharge(adm, NOW + dt.timedelta(days=3))
        self.assertEqual(services.stay_days(adm, NOW + dt.timedelta(days=30)), 3)

    def test_review_deadline_uses_stay_length(self):
        adm = services.admit(f.patient(1), self.beds[0], self.doc, NOW)
        self.assertEqual(services.discharge_review_due_hours(adm, NOW + dt.timedelta(days=8)), rules.discharge_review_hours(8))

    def test_nurses_required(self):
        for i in range(7):
            services.admit(f.patient(i + 1), self.beds[i], self.doc, NOW)
        limit = max(1, rules.nurse_patient_limit(3))
        self.assertEqual(services.nurses_required(self.ward), -(-7 // limit))

    def test_census_rows_are_sorted_and_scored(self):
        old = f.patient(1, birth=dt.date(1940, 1, 1))
        young = f.patient(2, birth=dt.date(2000, 1, 1))
        services.admit(young, self.beds[1], self.doc, NOW)
        services.admit(old, self.beds[0], self.doc, NOW)
        rows = services.census(self.ward, NOW)
        self.assertEqual([r["bed"] for r in rows], ["B1", "B2"])
        self.assertEqual(rows[0]["fall_risk"], clinical.fall_risk(clinical.age_years(old.birth_date, NOW.date()), 0))
        self.assertEqual(Admission.objects.filter(discharged_at__isnull=True).count(), 2)
