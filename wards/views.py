import datetime as dt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from clinkit.httpjson import error, read_json
from patients.models import Patient
from staff.models import Clinician

from . import services
from .models import Bed, Ward


def _when(text):
    return dt.datetime.fromisoformat(text).replace(tzinfo=dt.timezone.utc)


@require_GET
def census(request, code):
    try:
        ward = Ward.objects.get(code=code)
    except Ward.DoesNotExist:
        return error("ward_not_found", 404)
    as_of = _when(request.GET.get("as_of", "2025-01-13T09:00:00"))
    return JsonResponse({"ward": ward.code, "nurses_required": services.nurses_required(ward),
                         "census": services.census(ward, as_of)})


@csrf_exempt
@require_POST
def admit(request, code):
    body = read_json(request)
    if not body or any(k not in body for k in ("mrn", "bed", "attending", "at")):
        return error("bad_request")
    try:
        bed = Bed.objects.get(ward__code=code, label=body["bed"])
        patient = Patient.objects.get(mrn=body["mrn"])
        attending = Clinician.objects.get(employee_no=body["attending"])
    except (Bed.DoesNotExist, Patient.DoesNotExist, Clinician.DoesNotExist):
        return error("not_found", 404)
    try:
        adm = services.admit(patient, bed, attending, _when(body["at"]))
    except services.WardError as exc:
        return error("rejected", 409, str(exc))
    return JsonResponse({"admission": adm.id, "bed": str(bed)}, status=201)
