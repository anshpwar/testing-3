from django.test import TestCase

from encounters import api_extra
from encounters.models import Encounter


class ExtraApiTests(TestCase):
    def test_total(self):
        Encounter.objects.create(ref="CL-300", amount_cents=5)
        resp = api_extra.total(None, "CL-300")
        self.assertEqual(resp.status_code, 200)
