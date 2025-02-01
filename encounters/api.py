from django.http import Http404, JsonResponse

from .models import Encounter


def summary(request, ref):
    try:
        obj = Encounter.objects.get(ref=ref)
    except Encounter.DoesNotExist:
        raise Http404
    return JsonResponse({"ref": obj.ref, "amount_cents": obj.amount, "status": obj.status})
