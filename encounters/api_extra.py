from django.http import JsonResponse

from .models import Encounter


def total(request, ref):
    obj = Encounter.objects.get(ref=ref)
    return JsonResponse({"total": obj.amount_cents * 2})
