import datetime as dt
from decimal import Decimal

from django.test import TestCase

from clinkit import rules
from clinkit.hl7 import Message
from clinkit.hl7_build import build_oru
from labs import ingest, services

from . import factories as f

WHEN = dt.datetime(2025, 3, 3, 9, 30, 0)


class OrderTests(TestCase):
    def setUp(self):
        self.doc, self.pat, self.test = f.clinician(), f.patient(1), f.lab_test()

    def test_placer_numbers_encode_priority_and_sequence(self):
        a = services.place_order(self.pat, self.doc, self.test, 1, f.DAY)
        b = services.place_order(self.pat, self.doc, self.test, 3, f.DAY)
        self.assertEqual((a.placer_no, b.placer_no), ("LO1-000001", "LO3-000002"))

    def test_turnaround_follows_priority_table(self):
        for priority in (1, 2, 3):
            order = services.place_order(self.pat, self.doc, self.test, priority, f.DAY)
            self.assertEqual(services.due_at(order), f.DAY + dt.timedelta(minutes=rules.lab_turnaround_minutes(priority)))

    def test_overdue_only_while_open(self):
        order = services.place_order(self.pat, self.doc, self.test, 1, f.DAY)
        late = services.due_at(order) + dt.timedelta(minutes=1)
        self.assertFalse(services.is_overdue(order, services.due_at(order)))
        self.assertTrue(services.is_overdue(order, late))
        services.record_result(order, "4.0", late)
        self.assertFalse(services.is_overdue(order, late))

    def test_invalid_orders(self):
        with self.assertRaises(services.LabError):
            services.place_order(self.pat, self.doc, self.test, 9, f.DAY)
        tech = f.clinician("E300", role="technician", family="Abara")
        with self.assertRaises(services.LabError):
            services.place_order(self.pat, tech, self.test, 3, f.DAY)


class ResultTests(TestCase):
    def setUp(self):
        self.doc, self.pat, self.test = f.clinician(), f.patient(1), f.lab_test()

    def order(self, priority=3):
        return services.place_order(self.pat, self.doc, self.test, priority, f.DAY)

    def test_flags_follow_the_reference_range(self):
        for value, flag in (("4.2", "N"), ("3.0", "L"), ("5.5", "H"), ("2.0", "LL"), ("8.0", "HH")):
            result = services.record_result(self.order(), value, f.DAY, "M1")
            self.assertEqual(result.flag, flag)
            self.assertEqual(result.order.status, "resulted")

    def test_second_result_rejected(self):
        order = self.order()
        services.record_result(order, "4.2", f.DAY)
        with self.assertRaises(services.LabError):
            services.record_result(order, "4.3", f.DAY)

    def test_cancelled_order_rejects_results(self):
        order = self.order()
        order.status = "cancelled"
        order.save()
        with self.assertRaises(services.LabError):
            services.record_result(order, "4.2", f.DAY)

    def test_recheck_interval_counts_abnormal_results(self):
        self.assertEqual(services.recheck_hours(self.pat), rules.recheck_interval_hours(0))
        services.record_result(self.order(), "5.5", f.DAY)
        services.record_result(self.order(), "2.0", f.DAY)
        services.record_result(self.order(), "4.2", f.DAY)
        self.assertEqual(len(services.abnormal_results(self.pat)), 2)
        self.assertEqual([r.flag for r in services.critical_results(self.pat)], ["LL"])
        self.assertEqual(services.recheck_hours(self.pat), rules.recheck_interval_hours(2))


class IngestTests(TestCase):
    def setUp(self):
        self.doc, self.pat, self.test = f.clinician(), f.patient(1), f.lab_test()
        self.order = services.place_order(self.pat, self.doc, self.test, 2, f.DAY)

    def message(self, value="4.2", placer=None, mrn=None, code="K", control="C500"):
        patient = {"mrn": mrn or self.pat.mrn, "family_name": "Testson1", "given_name": "Pat", "birth": "19800615", "sex": "F"}
        msg = build_oru(patient, [(value, "mmol/L", "3.5", "5.1", "N")], control, WHEN, placer or self.order.placer_no, code, "Potassium")
        return msg.encode()

    def test_result_is_stored_and_acknowledged(self):
        ack, stored = ingest.ingest_oru(self.message("5.4"))
        self.assertEqual(ack.first("MSA").value(1), "AA")
        self.assertEqual(len(stored), 1)
        self.assertEqual((stored[0].value, stored[0].flag, stored[0].source_message), (Decimal("5.400"), "H", "C500"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "resulted")

    def test_reported_time_comes_from_the_message(self):
        _, stored = ingest.ingest_oru(self.message())
        self.assertEqual(stored[0].reported_at, dt.datetime(2025, 3, 3, 9, 30, tzinfo=dt.timezone.utc))

    def test_unknown_order_is_an_application_error(self):
        ack, stored = ingest.ingest_oru(self.message(placer="LO9-999999"))
        self.assertEqual((ack.first("MSA").value(1), ack.first("MSA").value(3), stored), ("AE", "unknown-order", []))

    def test_patient_mismatch(self):
        ack, _ = ingest.ingest_oru(self.message(mrn="MRN00000000"))
        self.assertEqual(ack.first("MSA").value(3), "patient-mismatch")

    def test_invalid_message_is_rejected_with_codes(self):
        ack, _ = ingest.ingest_oru(self.message(value="high"))
        self.assertEqual((ack.first("MSA").value(1), ack.first("MSA").value(3)), ("AR", "non-numeric-result"))

    def test_wrong_test_code_stores_nothing(self):
        ack, stored = ingest.ingest_oru(self.message(code="NA"))
        self.assertEqual((ack.first("MSA").value(3), stored), ("no-matching-observation", []))

    def test_duplicate_delivery_is_reported(self):
        ingest.ingest_oru(self.message())
        ack, _ = ingest.ingest_oru(self.message(control="C501"))
        self.assertEqual((ack.first("MSA").value(1), ack.first("MSA").value(3)), ("AE", "order already has a result"))

    def test_garbage_text(self):
        ack, reason = ingest.ingest_oru("not hl7")
        self.assertIsNone(ack)
        self.assertIn("MSH", reason)

    def test_other_message_types_are_not_processed(self):
        text = Message.parse(self.message()).encode().replace("ORU^R01", "ORM^O01")
        ack, stored = ingest.ingest_oru(text)
        self.assertEqual(ack.first("MSA").value(1), "AR")
        self.assertEqual(stored, [])
