import datetime as dt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from clinkit.httpjson import error, read_json

from . import services
from .models import Invoice


@require_GET
def statement(request, number):
    try:
        invoice = Invoice.objects.get(number=number)
    except Invoice.DoesNotExist:
        return error("invoice_not_found", 404)
    as_of = dt.date.fromisoformat(request.GET.get("as_of", invoice.issued_on.isoformat()))
    return JsonResponse(services.statement(invoice, as_of))


@csrf_exempt
@require_POST
def pay(request, number):
    body = read_json(request)
    if not body or not isinstance(body.get("amount_cents"), int) or "received_on" not in body:
        return error("bad_request")
    try:
        invoice = Invoice.objects.get(number=number)
    except Invoice.DoesNotExist:
        return error("invoice_not_found", 404)
    try:
        payment = services.record_payment(invoice, body["amount_cents"], dt.date.fromisoformat(body["received_on"]),
                                          body.get("method", "card"), body.get("reference", ""))
    except services.BillingError as exc:
        return error("rejected", 409, str(exc))
    invoice.refresh_from_db()
    return JsonResponse({"payment": payment.id, "status": invoice.status, "balance": services.balance_cents(invoice)}, status=201)
