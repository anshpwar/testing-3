import datetime as dt

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from clinkit import identifiers
from clinkit.httpjson import error, read_json

from . import services
from .models import Patient


@require_GET
def detail(request, mrn):
    try:
        patient = Patient.objects.get(mrn=mrn)
    except Patient.DoesNotExist:
        raise Http404
    on = dt.date.fromisoformat(request.GET["on"]) if "on" in request.GET else dt.date(2025, 1, 13)
    return JsonResponse(services.profile(patient, on))


@require_GET
def page(request, mrn):
    try:
        patient = Patient.objects.get(mrn=mrn)
    except Patient.DoesNotExist:
        raise Http404
    context = {"patient": patient, "allergies": patient.allergies.order_by("substance"),
               "contact": services.primary_contact(patient)}
    return render(request, "patients/patient_page.html", context)


@csrf_exempt
@require_POST
def register(request):
    body = read_json(request)
    needed = ("family_name", "given_name", "birth_date")
    if not body or any(k not in body for k in needed):
        return error("bad_request")
    try:
        birth = dt.date.fromisoformat(body["birth_date"])
        patient = services.register(body["family_name"], body["given_name"], birth, body.get("sex", "U"),
                                    body.get("phone", ""))
    except ValueError as exc:
        return error("invalid", detail=str(exc))
    return JsonResponse({"mrn": patient.mrn, "valid": identifiers.valid_mrn(patient.mrn)}, status=201)
