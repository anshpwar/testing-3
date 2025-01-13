import datetime as dt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from clinkit.httpjson import error, read_json
from patients.models import Patient
from staff.models import Clinician

from . import services
from .models import Appointment


def _when(text):
    return dt.datetime.fromisoformat(text).replace(tzinfo=dt.timezone.utc)


def _row(a):
    return {"id": a.id, "mrn": a.patient.mrn, "clinician": a.clinician.employee_no, "starts_at": a.starts_at.isoformat(),
            "duration_min": a.duration_min, "status": a.status, "charge_cents": services.charge_cents(a)}


@csrf_exempt
@require_POST
def book(request):
    body = read_json(request)
    if not body or any(k not in body for k in ("mrn", "clinician", "starts_at")):
        return error("bad_request")
    try:
        patient = Patient.objects.get(mrn=body["mrn"])
        clinician = Clinician.objects.get(employee_no=body["clinician"])
    except (Patient.DoesNotExist, Clinician.DoesNotExist):
        return error("not_found", 404)
    try:
        appt = services.book(patient, clinician, _when(body["starts_at"]), int(body.get("duration_min", 20)),
                             body.get("reason", ""))
    except services.SchedulingError as exc:
        return error("rejected", 409, str(exc))
    return JsonResponse(_row(appt), status=201)


@require_GET
def detail(request, pk):
    try:
        return JsonResponse(_row(Appointment.objects.select_related("patient", "clinician").get(pk=pk)))
    except Appointment.DoesNotExist:
        return error("not_found", 404)


@csrf_exempt
@require_POST
def cancel(request, pk):
    body = read_json(request) or {}
    try:
        appt = Appointment.objects.get(pk=pk)
    except Appointment.DoesNotExist:
        return error("not_found", 404)
    now = _when(body.get("now", "2025-01-13T09:00:00"))
    try:
        fee = services.cancel(appt, now, body.get("reason", ""))
    except services.SchedulingError as exc:
        return error("rejected", 409, str(exc))
    return JsonResponse({"status": "cancelled", "fee_cents": fee})
