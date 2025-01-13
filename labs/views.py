from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from clinkit.httpjson import error

from . import ingest, services
from .models import LabOrder


@csrf_exempt
@require_POST
def receive_hl7(request):
    ack, stored = ingest.ingest_oru(request.body.decode("utf-8", errors="replace"))
    if ack is None:
        return error("unparseable", 400, stored)
    code = ack.first("MSA").value(1)
    status = 200 if code == "AA" else 422
    return HttpResponse(ack.encode().replace("\r", "\n"), status=status, content_type="text/plain")


@require_GET
def order_detail(request, placer_no):
    try:
        order = LabOrder.objects.select_related("test", "patient").get(placer_no=placer_no)
    except LabOrder.DoesNotExist:
        return error("not_found", 404)
    data = {"placer_no": order.placer_no, "test": order.test.code, "status": order.status,
            "due_at": services.due_at(order).isoformat()}
    if hasattr(order, "result"):
        data["result"] = {"value": str(order.result.value), "flag": order.result.flag}
    return JsonResponse(data)
