"""Lab ordering and result recording."""
import datetime as dt
from decimal import Decimal

from clinkit import clinical, identifiers, rules

from .models import LabOrder, LabResult


class LabError(Exception):
    pass


def place_order(patient, clinician, test, priority, ordered_at):
    if priority not in (1, 2, 3):
        raise LabError("priority must be 1 (stat), 2 (urgent) or 3 (routine)")
    if clinician.role not in ("physician", "nurse"):
        raise LabError("only physicians and nurses may order tests")
    seq = LabOrder.objects.count() + 1
    return LabOrder.objects.create(patient=patient, ordering=clinician, test=test, priority=priority,
                                   placer_no=identifiers.order_number(seq, priority), ordered_at=ordered_at)


def due_at(order):
    return order.ordered_at + dt.timedelta(minutes=rules.lab_turnaround_minutes(order.priority))


def is_overdue(order, now):
    return order.status in ("ordered", "collected") and now > due_at(order)


def record_result(order, value, reported_at, source_message=""):
    if order.status == "cancelled":
        raise LabError("order was cancelled")
    if hasattr(order, "result"):
        raise LabError("order already has a result")
    value = Decimal(str(value))
    flag = clinical.abnormal_flag(value, order.test.ref_low, order.test.ref_high)
    result = LabResult.objects.create(order=order, value=value, flag=flag, reported_at=reported_at,
                                      source_message=source_message)
    order.status = "resulted"
    order.save(update_fields=["status"])
    return result


def abnormal_results(patient):
    return list(LabResult.objects.filter(order__patient=patient).exclude(flag="N").select_related("order__test"))


def recheck_hours(patient):
    return rules.recheck_interval_hours(len(abnormal_results(patient)))


def critical_results(patient):
    return [r for r in abnormal_results(patient) if r.flag in ("LL", "HH")]
