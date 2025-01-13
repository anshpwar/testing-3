import datetime as dt

from django.test import TestCase

from clinkit.hl7 import Message
from clinkit.hl7_build import build_oru
from labs import services

from . import factories as f


class Hl7EndpointTests(TestCase):
    def setUp(self):
        self.doc, self.pat, self.test = f.clinician(), f.patient(1), f.lab_test()
        self.order = services.place_order(self.pat, self.doc, self.test, 1, f.DAY)

    def oru(self, value="5.5", control="C900"):
        patient = {"mrn": self.pat.mrn, "family_name": "Testson1", "given_name": "Pat", "birth": "19800615", "sex": "F"}
        msg = build_oru(patient, [(value, "mmol/L", "3.5", "5.1", "N")], control, dt.datetime(2025, 3, 3, 10, 0, 0),
                        self.order.placer_no, "K", "Potassium")
        return msg.encode().replace("\r", "\n")

    def send(self, text):
        return self.client.post("/labs/hl7/", text, content_type="text/plain")

    def test_result_round_trip(self):
        resp = self.send(self.oru())
        self.assertEqual(resp.status_code, 200)
        ack = Message.parse(resp.content.decode())
        self.assertEqual((ack.first("MSA").value(1), ack.first("MSA").value(2)), ("AA", "C900"))
        detail = self.client.get(f"/labs/orders/{self.order.placer_no}/").json()
        self.assertEqual(detail["status"], "resulted")
        self.assertEqual(detail["result"], {"value": "5.500", "flag": "H"})

    def test_critical_value_is_flagged(self):
        self.send(self.oru("9.0"))
        self.assertEqual(self.client.get(f"/labs/orders/{self.order.placer_no}/").json()["result"]["flag"], "HH")
        self.assertEqual(len(services.critical_results(self.pat)), 1)

    def test_invalid_message_is_422_with_ack(self):
        resp = self.send(self.oru("n/a"))
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(Message.parse(resp.content.decode()).first("MSA").value(1), "AR")

    def test_unparseable_body_is_400(self):
        self.assertEqual(self.send("hello").status_code, 400)

    def test_order_detail_before_result(self):
        detail = self.client.get(f"/labs/orders/{self.order.placer_no}/").json()
        self.assertEqual(detail["status"], "ordered")
        self.assertNotIn("result", detail)
        self.assertEqual(self.client.get("/labs/orders/LO0-000000/").status_code, 404)
