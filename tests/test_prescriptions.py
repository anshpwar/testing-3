import datetime as dt

from django.test import TestCase

from clinkit import clinical, rules
from patients import services as patient_services
from prescriptions import services
from prescriptions.models import Prescription

from . import factories as f

TODAY = dt.date(2025, 3, 3)


class PrescribeTests(TestCase):
    def setUp(self):
        self.doc = f.clinician()
        self.pat = f.patient(1, weight="70.0")
        self.med = f.medication()

    def test_dose_at_the_ceiling_is_accepted(self):
        ceiling = clinical.dose_ceiling(self.pat.weight_kg)
        rx = services.prescribe(self.pat, self.doc, self.med, ceiling, 2, 5, TODAY)
        self.assertEqual((rx.dose_mg, rx.status), (ceiling, "active"))

    def test_dose_above_the_ceiling_is_rejected(self):
        with self.assertRaises(services.PrescribingError):
            services.prescribe(self.pat, self.doc, self.med, clinical.dose_ceiling(self.pat.weight_kg) + 1, 1, 5, TODAY)

    def test_lighter_patients_get_lower_ceilings_by_policy(self):
        child = f.patient(2, weight="9.0")
        ceiling = clinical.dose_ceiling(child.weight_kg)
        self.assertEqual(ceiling, rules.dose_ceiling_mg(9))
        with self.assertRaises(services.PrescribingError):
            services.prescribe(child, self.doc, self.med, ceiling + 1, 1, 5, TODAY)

    def test_supply_limit_comes_from_the_schedule_table(self):
        controlled = f.medication("OXY5", "Oxycodone", 5, schedule=2)
        limit = services.max_days(controlled)
        services.prescribe(self.pat, self.doc, controlled, 5, 2, limit, TODAY)
        with self.assertRaises(services.PrescribingError):
            services.prescribe(self.pat, self.doc, controlled, 5, 2, limit + 1, TODAY)

    def test_refills_are_capped_by_days_of_supply(self):
        rx = services.prescribe(self.pat, self.doc, self.med, 100, 1, 30, TODAY, refills=99)
        self.assertEqual(rx.refills, rules.max_refills(30))

    def test_only_active_physicians_prescribe(self):
        nurse = f.clinician("E201", role="nurse", family="Lindqvist")
        with self.assertRaises(services.PrescribingError):
            services.prescribe(self.pat, nurse, self.med, 100, 1, 5, TODAY)
        self.doc.active = False
        self.doc.save()
        with self.assertRaises(services.PrescribingError):
            services.prescribe(self.pat, self.doc, self.med, 100, 1, 5, TODAY)

    def test_allergy_blocks_matching_medication(self):
        patient_services.record_allergy(self.pat, "Amoxicillin", "severe", TODAY)
        with self.assertRaises(services.PrescribingError):
            services.prescribe(self.pat, self.doc, self.med, 100, 1, 5, TODAY)

    def test_missing_weight_blocks_dosing(self):
        pat = f.patient(3, weight=None)
        with self.assertRaises(services.PrescribingError):
            services.prescribe(pat, self.doc, self.med, 100, 1, 5, TODAY)


class ActiveListTests(TestCase):
    def setUp(self):
        self.doc, self.pat = f.clinician(), f.patient(1)
        self.a = services.prescribe(self.pat, self.doc, f.medication(), 100, 3, 5, TODAY)
        self.b = services.prescribe(self.pat, self.doc, f.medication("ZOL10", "Zolpidem", 10, sedating=True), 10, 1, 5, TODAY)

    def test_totals_and_sedating_count(self):
        self.assertEqual(services.total_daily_mg(self.pat), 310)
        self.assertEqual(services.sedating_count(self.pat), 1)

    def test_stop_removes_from_active(self):
        services.stop(self.a)
        self.assertEqual([p.id for p in services.active_for(self.pat)], [self.b.id])
        with self.assertRaises(services.PrescribingError):
            services.stop(self.a)
        self.assertEqual(Prescription.objects.filter(status="stopped").count(), 1)
