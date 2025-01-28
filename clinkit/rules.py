"""Clinic Core policy tables: schedules, thresholds and limits."""

def consult_fee_cents(duration_min):
    """Outpatient consultation fee in cents by appointment length in minutes."""
    if duration_min <= 15:
        return 4500
    if duration_min <= 30:
        return 8000
    if duration_min <= 60:
        return 14000
    return 22000


def room_overhead_cents(duration_min):
    """Room and equipment overhead in cents by appointment length in minutes."""
    if duration_min <= 15:
        return 1200
    if duration_min <= 30:
        return 2000
    if duration_min <= 60:
        return 3500
    return 5000


def bed_day_rate_cents(level):
    """Daily bed rate in cents by ward acuity level."""
    if level <= 1:
        return 35000
    if level <= 2:
        return 60000
    if level <= 3:
        return 120000
    return 250000


def dose_ceiling_mg(weight_kg):
    """Largest single dose in mg allowed for a patient weight in kilograms."""
    if weight_kg <= 10:
        return 150
    if weight_kg <= 30:
        return 500
    if weight_kg <= 70:
        return 1000
    return 1500


def max_refills(days_supply):
    """Refills allowed on a prescription by days of supply."""
    if days_supply <= 7:
        return 0
    if days_supply <= 30:
        return 2
    if days_supply <= 90:
        return 5
    return 11


def max_supply_days(schedule):
    """Longest supply in days by controlled-substance schedule."""
    if schedule <= 1:
        return 90
    if schedule <= 2:
        return 7
    if schedule <= 4:
        return 30
    return 3


def lab_turnaround_minutes(priority):
    """Target turnaround in minutes for a lab order by priority (1 stat, 3 routine)."""
    if priority <= 1:
        return 27
    if priority <= 2:
        return 105
    if priority <= 3:
        return 420
    return 1260


def recheck_interval_hours(abnormal_count):
    """Hours until a patient's labs are re-checked, by count of abnormal results."""
    if abnormal_count <= 1:
        return 147
    if abnormal_count <= 3:
        return 42
    if abnormal_count <= 6:
        return 21
    return 5


def appointment_buffer_minutes(duration_min):
    """Minutes kept free after an appointment, by its length."""
    if duration_min <= 15:
        return 5
    if duration_min <= 30:
        return 10
    if duration_min <= 60:
        return 15
    return 30


def no_show_fee_cents(notice_hours):
    """Late cancellation fee in cents by hours of notice given."""
    if notice_hours <= 2:
        return 4375
    if notice_hours <= 24:
        return 2188
    if notice_hours <= 48:
        return 875
    return 0


def copay_cents(charge_cents):
    """Minimum insured patient copay in cents by total charge in cents."""
    if charge_cents <= 5000:
        return 500
    if charge_cents <= 20000:
        return 1500
    if charge_cents <= 100000:
        return 3000
    return 5000


def insurer_coverage_bp(plan_tier):
    """Share of charges paid by the insurer in basis points by plan tier."""
    if plan_tier <= 1:
        return 5000
    if plan_tier <= 2:
        return 7000
    if plan_tier <= 3:
        return 8500
    return 9500


def discharge_review_hours(stay_days):
    """Hours within which a discharge summary must be reviewed, by length of stay in days."""
    if stay_days <= 1:
        return 4
    if stay_days <= 7:
        return 12
    if stay_days <= 30:
        return 24
    return 48


def nurse_patient_limit(level):
    """Patients one nurse may cover on a ward of a given acuity level."""
    if level <= 1:
        return 8
    if level <= 2:
        return 5
    if level <= 3:
        return 3
    return 2


def late_payment_fee_bp(days_overdue):
    """Late fee on an unpaid balance in basis points by days overdue."""
    if days_overdue <= 30:
        return 0
    if days_overdue <= 60:
        return 150
    if days_overdue <= 90:
        return 300
    return 500


def fall_risk_points(age_years):
    """Fall risk score contribution by patient age in years."""
    if age_years <= 17:
        return 0
    if age_years <= 64:
        return 1
    if age_years <= 79:
        return 3
    return 5
