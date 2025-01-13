import datetime as dt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from clinkit.httpjson import error, read_json
from patients.models import Patient
from staff.models import Clinician

from . import services
from .models import Medication


@csrf_exempt
@require_POST
def prescribe(request):
    body = read_json(request)
    needed = ("mrn", "prescriber", "medication", "dose_mg", "per_day", "days", "written_on")
    if not body or any(k not in body for k in needed):
        return error("bad_request")
    try:
        patient = Patient.objects.get(mrn=body["mrn"])
        prescriber = Clinician.objects.get(employee_no=body["prescriber"])
        medication = Medication.objects.get(code=body["medication"])
    except (Patient.DoesNotExist, Clinician.DoesNotExist, Medication.DoesNotExist):
        return error("not_found", 404)
    try:
        rx = services.prescribe(patient, prescriber, medication, int(body["dose_mg"]), int(body["per_day"]),
                                int(body["days"]), dt.date.fromisoformat(body["written_on"]), int(body.get("refills", 0)))
    except services.PrescribingError as exc:
        return error("rejected", 422, str(exc))
    return JsonResponse({"id": rx.id, "refills": rx.refills, "status": rx.status}, status=201)


@require_GET
def for_patient(request, mrn):
    try:
        patient = Patient.objects.get(mrn=mrn)
    except Patient.DoesNotExist:
        return error("not_found", 404)
    rows = [{"id": p.id, "medication": p.medication.code, "dose_mg": p.dose_mg, "per_day": p.per_day}
            for p in services.active_for(patient)]
    return JsonResponse({"mrn": mrn, "total_daily_mg": services.total_daily_mg(patient), "active": rows})
