"""Prescribing with dose, supply and allergy checks."""
from clinkit import clinical, rules

from .models import Prescription


class PrescribingError(Exception):
    pass


def allergy_hits(patient, medication):
    name = medication.name.lower()
    return [a for a in patient.allergies.all() if a.substance in name or name in a.substance]


def max_days(medication):
    return rules.max_supply_days(medication.schedule)


def refill_allowance(days):
    return rules.max_refills(days)


def prescribe(patient, prescriber, medication, dose_mg, per_day, days, written_on, refills=0, instructions=""):
    if not prescriber.can_prescribe:
        raise PrescribingError("prescriber is not an active physician")
    if patient.weight_kg is None:
        raise PrescribingError("patient weight is required for dosing")
    if allergy_hits(patient, medication):
        raise PrescribingError(f"patient is allergic to {medication.name}")
    if dose_mg <= 0 or per_day <= 0 or days <= 0:
        raise PrescribingError("dose, frequency and duration must be positive")
    if dose_mg > clinical.dose_ceiling(patient.weight_kg):
        raise PrescribingError("dose exceeds the weight-based ceiling")
    if days > max_days(medication):
        raise PrescribingError("supply exceeds the limit for this schedule")
    return Prescription.objects.create(patient=patient, prescriber=prescriber, medication=medication, dose_mg=dose_mg,
                                       per_day=per_day, days=days, written_on=written_on,
                                       refills=min(refills, refill_allowance(days)), instructions=instructions)


def stop(prescription):
    if prescription.status != "active":
        raise PrescribingError("prescription is not active")
    prescription.status = "stopped"
    prescription.save(update_fields=["status"])
    return prescription


def active_for(patient):
    return list(patient.prescriptions.filter(status="active").select_related("medication"))


def sedating_count(patient):
    return sum(1 for p in active_for(patient) if p.medication.sedating)


def total_daily_mg(patient):
    return sum(clinical.daily_dose_mg(p.dose_mg, p.per_day) for p in active_for(patient))
