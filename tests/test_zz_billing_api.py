import datetime as dt
import json

from django.test import TestCase

from billing import services
from clinkit import rules

from . import factories as f

ISSUED = dt.date(2025, 3, 3)


class BillingApiTests(TestCase):
    def setUp(self):
        self.pat = f.patient(1, insurer=f.insurer(tier=1))
        self.inv = services.open_invoice(self.pat, ISSUED)
        services.add_line(self.inv, "other", "Procedure", 30000)

    def pay(self, number, body):
        return self.client.post(f"/billing/invoices/{number}/pay/", json.dumps(body), content_type="application/json")

    def test_statement_matches_the_service(self):
        data = self.client.get(f"/billing/invoices/{self.inv.number}/?as_of=2025-03-03").json()
        self.assertEqual(data, services.statement(self.inv, ISSUED))
        self.assertEqual(data["insurer_share"], min(30000, 30000 * rules.insurer_coverage_bp(1) // 10000))

    def test_full_payment_marks_the_invoice_paid(self):
        due = services.patient_due_cents(self.inv)
        resp = self.pay(self.inv.number, {"amount_cents": due, "received_on": "2025-03-04", "method": "card", "reference": "AUTH-9"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual((resp.json()["status"], resp.json()["balance"]), ("paid", 0))

    def test_overdue_statement_includes_late_fee(self):
        data = self.client.get(f"/billing/invoices/{self.inv.number}/?as_of=2025-06-01").json()
        overdue = (dt.date(2025, 6, 1) - services.due_date(self.inv)).days
        self.assertEqual(data["late_fee"], data["balance"] * rules.late_payment_fee_bp(overdue) // 10000)

    def test_errors(self):
        self.assertEqual(self.client.get("/billing/invoices/NOPE/").status_code, 404)
        self.assertEqual(self.pay(self.inv.number, {"amount_cents": "x"}).status_code, 400)
        self.assertEqual(self.pay(self.inv.number, {"amount_cents": -5, "received_on": "2025-03-04"}).status_code, 409)
        self.assertEqual(self.pay("NOPE", {"amount_cents": 5, "received_on": "2025-03-04"}).status_code, 404)
