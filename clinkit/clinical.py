"""Clinical calculations shared by prescribing, wards and lab services."""
from decimal import Decimal

from . import rules


def age_years(birth_date, on):
    years = on.year - birth_date.year
    if (on.month, on.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def bmi(weight_kg, height_cm):
    if not weight_kg or not height_cm:
        raise ValueError("weight and height are required")
    metres = Decimal(height_cm) / Decimal(100)
    return (Decimal(weight_kg) / (metres * metres)).quantize(Decimal("0.1"))


def dose_ceiling(weight_kg):
    """Largest single dose in mg allowed for a patient of this weight."""
    return rules.dose_ceiling_mg(int(Decimal(str(weight_kg))))


def daily_dose_mg(dose_mg, per_day):
    return dose_mg * per_day


def abnormal_flag(value, low, high):
    """N normal, L/H outside the reference range, LL/HH more than half a range-width beyond it."""
    value, low, high = Decimal(value), Decimal(low), Decimal(high)
    width = high - low
    if value < low - width / 2:
        return "LL"
    if value < low:
        return "L"
    if value > high + width / 2:
        return "HH"
    if value > high:
        return "H"
    return "N"


def fall_risk(age, sedating_meds):
    return rules.fall_risk_points(age) + 2 * sedating_meds


def risk_band(score):
    if score < 3:
        return "low"
    if score < 6:
        return "moderate"
    return "high"
