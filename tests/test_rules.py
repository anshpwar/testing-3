import unittest

from clinkit import rules


class RuleTests(unittest.TestCase):
    def test_consult_fee_cents(self):
        self.assertEqual(rules.consult_fee_cents(0), 4500)
        self.assertEqual(rules.consult_fee_cents(1), 4500)
        self.assertEqual(rules.consult_fee_cents(15), 4500)
        self.assertEqual(rules.consult_fee_cents(16), 8000)
        self.assertEqual(rules.consult_fee_cents(30), 8000)
        self.assertEqual(rules.consult_fee_cents(31), 14000)
        self.assertEqual(rules.consult_fee_cents(60), 14000)
        self.assertEqual(rules.consult_fee_cents(61), 22000)

    def test_room_overhead_cents(self):
        self.assertEqual(rules.room_overhead_cents(0), 1200)
        self.assertEqual(rules.room_overhead_cents(1), 1200)
        self.assertEqual(rules.room_overhead_cents(15), 1200)
        self.assertEqual(rules.room_overhead_cents(16), 2000)
        self.assertEqual(rules.room_overhead_cents(30), 2000)
        self.assertEqual(rules.room_overhead_cents(31), 3500)
        self.assertEqual(rules.room_overhead_cents(60), 3500)
        self.assertEqual(rules.room_overhead_cents(61), 5000)

    def test_bed_day_rate_cents(self):
        self.assertEqual(rules.bed_day_rate_cents(0), 35000)
        self.assertEqual(rules.bed_day_rate_cents(1), 35000)
        self.assertEqual(rules.bed_day_rate_cents(2), 60000)
        self.assertEqual(rules.bed_day_rate_cents(3), 120000)
        self.assertEqual(rules.bed_day_rate_cents(4), 250000)

    def test_dose_ceiling_mg(self):
        self.assertEqual(rules.dose_ceiling_mg(0), 150)
        self.assertEqual(rules.dose_ceiling_mg(1), 150)
        self.assertEqual(rules.dose_ceiling_mg(10), 150)
        self.assertEqual(rules.dose_ceiling_mg(11), 500)
        self.assertEqual(rules.dose_ceiling_mg(30), 500)
        self.assertEqual(rules.dose_ceiling_mg(31), 1000)
        self.assertEqual(rules.dose_ceiling_mg(70), 1000)
        self.assertEqual(rules.dose_ceiling_mg(71), 1500)

    def test_max_refills(self):
        self.assertEqual(rules.max_refills(0), 0)
        self.assertEqual(rules.max_refills(1), 0)
        self.assertEqual(rules.max_refills(7), 0)
        self.assertEqual(rules.max_refills(8), 2)
        self.assertEqual(rules.max_refills(30), 2)
        self.assertEqual(rules.max_refills(31), 5)
        self.assertEqual(rules.max_refills(90), 5)
        self.assertEqual(rules.max_refills(91), 11)

    def test_max_supply_days(self):
        self.assertEqual(rules.max_supply_days(0), 90)
        self.assertEqual(rules.max_supply_days(1), 90)
        self.assertEqual(rules.max_supply_days(2), 7)
        self.assertEqual(rules.max_supply_days(3), 30)
        self.assertEqual(rules.max_supply_days(4), 30)
        self.assertEqual(rules.max_supply_days(5), 3)

    def test_lab_turnaround_minutes(self):
        self.assertEqual(rules.lab_turnaround_minutes(0), 30)
        self.assertEqual(rules.lab_turnaround_minutes(1), 30)
        self.assertEqual(rules.lab_turnaround_minutes(2), 120)
        self.assertEqual(rules.lab_turnaround_minutes(3), 480)
        self.assertEqual(rules.lab_turnaround_minutes(4), 1440)

    def test_recheck_interval_hours(self):
        self.assertEqual(rules.recheck_interval_hours(0), 168)
        self.assertEqual(rules.recheck_interval_hours(1), 168)
        self.assertEqual(rules.recheck_interval_hours(2), 48)
        self.assertEqual(rules.recheck_interval_hours(3), 48)
        self.assertEqual(rules.recheck_interval_hours(4), 24)
        self.assertEqual(rules.recheck_interval_hours(6), 24)
        self.assertEqual(rules.recheck_interval_hours(7), 6)

    def test_appointment_buffer_minutes(self):
        self.assertEqual(rules.appointment_buffer_minutes(0), 5)
        self.assertEqual(rules.appointment_buffer_minutes(1), 5)
        self.assertEqual(rules.appointment_buffer_minutes(15), 5)
        self.assertEqual(rules.appointment_buffer_minutes(16), 10)
        self.assertEqual(rules.appointment_buffer_minutes(30), 10)
        self.assertEqual(rules.appointment_buffer_minutes(31), 15)
        self.assertEqual(rules.appointment_buffer_minutes(60), 15)
        self.assertEqual(rules.appointment_buffer_minutes(61), 30)

    def test_no_show_fee_cents(self):
        self.assertEqual(rules.no_show_fee_cents(0), 5000)
        self.assertEqual(rules.no_show_fee_cents(1), 5000)
        self.assertEqual(rules.no_show_fee_cents(2), 5000)
        self.assertEqual(rules.no_show_fee_cents(3), 2500)
        self.assertEqual(rules.no_show_fee_cents(24), 2500)
        self.assertEqual(rules.no_show_fee_cents(25), 1000)
        self.assertEqual(rules.no_show_fee_cents(48), 1000)
        self.assertEqual(rules.no_show_fee_cents(49), 0)

    def test_copay_cents(self):
        self.assertEqual(rules.copay_cents(0), 500)
        self.assertEqual(rules.copay_cents(1), 500)
        self.assertEqual(rules.copay_cents(5000), 500)
        self.assertEqual(rules.copay_cents(5001), 1500)
        self.assertEqual(rules.copay_cents(20000), 1500)
        self.assertEqual(rules.copay_cents(20001), 3000)
        self.assertEqual(rules.copay_cents(100000), 3000)
        self.assertEqual(rules.copay_cents(100001), 5000)

    def test_insurer_coverage_bp(self):
        self.assertEqual(rules.insurer_coverage_bp(0), 5000)
        self.assertEqual(rules.insurer_coverage_bp(1), 5000)
        self.assertEqual(rules.insurer_coverage_bp(2), 7000)
        self.assertEqual(rules.insurer_coverage_bp(3), 8500)
        self.assertEqual(rules.insurer_coverage_bp(4), 9500)

    def test_discharge_review_hours(self):
        self.assertEqual(rules.discharge_review_hours(0), 4)
        self.assertEqual(rules.discharge_review_hours(1), 4)
        self.assertEqual(rules.discharge_review_hours(2), 12)
        self.assertEqual(rules.discharge_review_hours(7), 12)
        self.assertEqual(rules.discharge_review_hours(8), 24)
        self.assertEqual(rules.discharge_review_hours(30), 24)
        self.assertEqual(rules.discharge_review_hours(31), 48)

    def test_nurse_patient_limit(self):
        self.assertEqual(rules.nurse_patient_limit(0), 8)
        self.assertEqual(rules.nurse_patient_limit(1), 8)
        self.assertEqual(rules.nurse_patient_limit(2), 5)
        self.assertEqual(rules.nurse_patient_limit(3), 3)
        self.assertEqual(rules.nurse_patient_limit(4), 2)

    def test_late_payment_fee_bp(self):
        self.assertEqual(rules.late_payment_fee_bp(0), 0)
        self.assertEqual(rules.late_payment_fee_bp(1), 0)
        self.assertEqual(rules.late_payment_fee_bp(30), 0)
        self.assertEqual(rules.late_payment_fee_bp(31), 150)
        self.assertEqual(rules.late_payment_fee_bp(60), 150)
        self.assertEqual(rules.late_payment_fee_bp(61), 300)
        self.assertEqual(rules.late_payment_fee_bp(90), 300)
        self.assertEqual(rules.late_payment_fee_bp(91), 500)

    def test_fall_risk_points(self):
        self.assertEqual(rules.fall_risk_points(0), 0)
        self.assertEqual(rules.fall_risk_points(1), 0)
        self.assertEqual(rules.fall_risk_points(17), 0)
        self.assertEqual(rules.fall_risk_points(18), 0)
        self.assertEqual(rules.fall_risk_points(64), 0)
        self.assertEqual(rules.fall_risk_points(65), 2)
        self.assertEqual(rules.fall_risk_points(79), 2)
        self.assertEqual(rules.fall_risk_points(80), 4)
