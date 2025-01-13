import datetime as dt
import json

from django.test import TestCase

from clinkit import clinical, rules
from patients import services as patient_services

from . import factories as f


class ClinicApiBase(TestCase):
    def post(self, url, body=None):
        return self.client.post(url, json.dumps(body or {}), content_type="application/json")


class PatientApiTests(ClinicApiBase):
    def test_registration_assigns_a_valid_mrn(self):
        resp = self.post("/patients/", {"family_name": " Marsh ", "given_name": "Dale", "birth_date": "1975-02-01", "phone": "(555) 010-0123"})
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertTrue(body["valid"])
        detail = self.client.get(f"/patients/{body['mrn']}/?on=2025-03-03").json()
        self.assertEqual((detail["name"], detail["age"]), ("Dale Marsh", 50))

    def test_validation(self):
        self.assertEqual(self.post("/patients/", {"family_name": "x"}).status_code, 400)
        bad = self.post("/patients/", {"family_name": "x", "given_name": "y", "birth_date": "1990-01-01", "phone": "12"})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.client.get("/patients/MRN0000000X/").status_code, 404)

    def test_profile_and_page(self):
        pat = f.patient(1, weight="70.0")
        patient_services.record_allergy(pat, "Penicillin", "severe", dt.date(2025, 1, 5))
        patient_services.add_contact(pat, "Sam Testson", "spouse", "555-010-0188", primary=True)
        detail = self.client.get(f"/patients/{pat.mrn}/?on=2025-03-03").json()
        self.assertEqual((detail["allergies"], detail["bmi"]), (["penicillin"], "24.2"))
        html = self.client.get(f"/patients/{pat.mrn}/page/").content.decode()
        self.assertIn("penicillin: severe", html)
        self.assertIn("Sam Testson (spouse) 555-010-0188", html)


class AppointmentApiTests(ClinicApiBase):
    def setUp(self):
        self.doc, self.pat = f.clinician(), f.patient(1)

    def test_book_fetch_and_cancel(self):
        resp = self.post("/appointments/", {"mrn": self.pat.mrn, "clinician": self.doc.employee_no,
                                            "starts_at": "2025-03-06T10:00:00", "duration_min": 30})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["charge_cents"], rules.consult_fee_cents(30) + rules.room_overhead_cents(30))
        self.assertEqual(self.client.get(f"/appointments/{data['id']}/").json()["status"], "booked")
        cancelled = self.post(f"/appointments/{data['id']}/cancel/", {"now": "2025-03-03T10:00:00"})
        self.assertEqual(cancelled.json(), {"status": "cancelled", "fee_cents": rules.no_show_fee_cents(72)})
        self.assertEqual(self.post(f"/appointments/{data['id']}/cancel/").status_code, 409)

    def test_conflicting_booking_is_409(self):
        body = {"mrn": self.pat.mrn, "clinician": self.doc.employee_no, "starts_at": "2025-03-06T10:00:00", "duration_min": 30}
        self.assertEqual(self.post("/appointments/", body).status_code, 201)
        self.assertEqual(self.post("/appointments/", dict(body, starts_at="2025-03-06T10:15:00")).status_code, 409)

    def test_unknown_references(self):
        resp = self.post("/appointments/", {"mrn": "nope", "clinician": "nope", "starts_at": "2025-03-06T10:00:00"})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self.client.get("/appointments/9999/").status_code, 404)


class PrescriptionApiTests(ClinicApiBase):
    def setUp(self):
        self.doc, self.pat, self.med = f.clinician(), f.patient(1), f.medication()

    def body(self, **over):
        data = {"mrn": self.pat.mrn, "prescriber": self.doc.employee_no, "medication": self.med.code,
                "dose_mg": 250, "per_day": 3, "days": 7, "written_on": "2025-03-03"}
        data.update(over)
        return data

    def test_prescribe_and_list(self):
        resp = self.post("/prescriptions/", self.body())
        self.assertEqual(resp.status_code, 201)
        listing = self.client.get(f"/prescriptions/patient/{self.pat.mrn}/").json()
        self.assertEqual((listing["total_daily_mg"], len(listing["active"])), (750, 1))

    def test_ceiling_violation_is_422(self):
        too_much = clinical.dose_ceiling(self.pat.weight_kg) + 1
        self.assertEqual(self.post("/prescriptions/", self.body(dose_mg=too_much)).status_code, 422)

    def test_bad_request(self):
        self.assertEqual(self.post("/prescriptions/", {"mrn": "x"}).status_code, 400)


class WardApiTests(ClinicApiBase):
    def test_admit_and_census(self):
        doc, pat = f.clinician(), f.patient(1)
        ward = f.ward("W1", level=2)
        resp = self.post("/wards/W1/admit/", {"mrn": pat.mrn, "bed": "A1", "attending": doc.employee_no, "at": "2025-03-03T09:00:00"})
        self.assertEqual(resp.status_code, 201)
        again = self.post("/wards/W1/admit/", {"mrn": pat.mrn, "bed": "A2", "attending": doc.employee_no, "at": "2025-03-03T09:00:00"})
        self.assertEqual(again.status_code, 409)
        census = self.client.get(f"/wards/{ward.code}/census/?as_of=2025-03-04T12:00:00").json()
        self.assertEqual(census["nurses_required"], 1)
        self.assertEqual([(r["bed"], r["days"]) for r in census["census"]], [("A1", 2)])
        self.assertEqual(self.client.get("/wards/NOPE/census/").status_code, 404)
