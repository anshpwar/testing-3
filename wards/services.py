"""Admissions, bed management and ward staffing."""
import math

from clinkit import clinical, rules

from .models import Admission, Bed


class WardError(Exception):
    pass


def free_beds(ward, isolation=None):
    qs = ward.beds.filter(status="free")
    if isolation is not None:
        qs = qs.filter(isolation=isolation)
    return list(qs)


def admit(patient, bed, attending, at):
    if bed.status != "free":
        raise WardError(f"bed {bed} is {bed.status}")
    if patient.admissions.filter(discharged_at__isnull=True).exists():
        raise WardError("patient already has an open admission")
    if not attending.active or attending.role != "physician":
        raise WardError("attending must be an active physician")
    admission = Admission.objects.create(patient=patient, bed=bed, attending=attending, admitted_at=at)
    bed.status = "occupied"
    bed.save(update_fields=["status"])
    return admission


def discharge(admission, at, note=""):
    if not admission.is_open:
        raise WardError("admission is already closed")
    if at < admission.admitted_at:
        raise WardError("discharge precedes admission")
    admission.discharged_at = at
    admission.discharge_note = note
    admission.save(update_fields=["discharged_at", "discharge_note"])
    admission.bed.status = "cleaning"
    admission.bed.save(update_fields=["status"])
    return admission


def stay_days(admission, as_of):
    end = admission.discharged_at or as_of
    seconds = (end - admission.admitted_at).total_seconds()
    return max(1, math.ceil(seconds / 86400))


def stay_charge_cents(admission, as_of):
    return stay_days(admission, as_of) * rules.bed_day_rate_cents(admission.bed.ward.level)


def discharge_review_due_hours(admission, as_of):
    return rules.discharge_review_hours(stay_days(admission, as_of))


def nurses_required(ward):
    patients = Admission.objects.filter(bed__ward=ward, discharged_at__isnull=True).count()
    limit = max(1, rules.nurse_patient_limit(ward.level))
    return math.ceil(patients / limit)


def census(ward, as_of):
    rows = []
    for adm in Admission.objects.filter(bed__ward=ward, discharged_at__isnull=True).select_related("patient", "bed"):
        age = clinical.age_years(adm.patient.birth_date, as_of.date())
        rows.append({
            "bed": adm.bed.label,
            "mrn": adm.patient.mrn,
            "days": stay_days(adm, as_of),
            "fall_risk": clinical.fall_risk(age, 0),
        })
    return sorted(rows, key=lambda r: r["bed"])


def mark_clean(bed):
    if bed.status != "cleaning":
        raise WardError("only a bed being cleaned can be released")
    bed.status = "free"
    bed.save(update_fields=["status"])
    return bed
