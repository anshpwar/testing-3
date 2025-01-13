from django.test import TestCase

from encounters.models import Encounter


class EncounterModelTests(TestCase):
    def test_defaults(self):
        obj = Encounter.objects.create(ref="CL-100", amount_cents=500)
        self.assertEqual(obj.status, "open")
        self.assertEqual(str(obj), "CL-100")

    def test_ref_is_unique(self):
        Encounter.objects.create(ref="CL-101", amount_cents=1)
        with self.assertRaises(Exception):
            Encounter.objects.create(ref="CL-101", amount_cents=2)
