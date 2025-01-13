"""Inbound HL7 result messages: parse, validate, match the order and store the result."""
import datetime as dt
from decimal import Decimal

from clinkit.hl7 import Hl7Error, Message
from clinkit.hl7_build import build_ack
from clinkit.hl7_validate import parse_timestamp, validate

from . import services
from .models import LabOrder

EPOCH = dt.datetime(2025, 1, 13, 9, 0, 0, tzinfo=dt.timezone.utc)


def ingest_oru(text, received_at=EPOCH):
    """Process an ORU^R01 message and return (ack_message, stored_results)."""
    try:
        message = Message.parse(text)
    except Hl7Error as exc:
        return None, str(exc)
    issues = validate(message)
    if issues:
        return build_ack(message, "AR", "; ".join(sorted({i.code for i in issues})), received_at), []
    if message.message_type != "ORU^R01":
        return build_ack(message, "AR", "unsupported-type", received_at), []
    obr = message.first("OBR")
    try:
        order = LabOrder.objects.select_related("test").get(placer_no=obr.value(2))
    except LabOrder.DoesNotExist:
        return build_ack(message, "AE", "unknown-order", received_at), []
    if order.patient.mrn != message.first("PID").value(3):
        return build_ack(message, "AE", "patient-mismatch", received_at), []
    stored = []
    for obx in message.all("OBX"):
        if obx.value(3, 1) != order.test.code:
            continue
        reported = parse_timestamp(obx.value(14) or message.msh.value(7)).replace(tzinfo=dt.timezone.utc)
        try:
            stored.append(services.record_result(order, Decimal(obx.value(5)), reported, message.control_id))
        except services.LabError as exc:
            return build_ack(message, "AE", str(exc), received_at), stored
    if not stored:
        return build_ack(message, "AE", "no-matching-observation", received_at), []
    return build_ack(message, "AA", "stored", received_at), stored
