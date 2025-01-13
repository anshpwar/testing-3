"""Construction of outbound HL7 messages and acknowledgements."""
from .hl7 import DEFAULT_DELIMITERS, Message, Segment, escape_text


def format_timestamp(value):
    return value.strftime("%Y%m%d%H%M%S")


def _seg(name, values):
    d = DEFAULT_DELIMITERS
    fields = [d.component.join(escape_text(c, d) for c in v) if isinstance(v, (list, tuple)) else escape_text(str(v), d) for v in values]
    return Segment(name, fields, d)


def header(message_type, trigger, control_id, sent_at, sender=("CLINKIT", "MAIN"), receiver=("LIS", "MAIN"), version="2.5"):
    d = DEFAULT_DELIMITERS
    values = [sender[0], sender[1], receiver[0], receiver[1], format_timestamp(sent_at), "",
              [message_type, trigger], control_id, "P", version]
    seg = _seg("MSH", values)
    seg.fields = [d.field, d.encoding_chars] + seg.fields
    return seg


def build_oru(patient, observations, control_id, sent_at, placer_no, test_code, test_name):
    """ORU^R01 result message. `observations` is a list of (value, unit, low, high, flag)."""
    segs = [
        header("ORU", "R01", control_id, sent_at),
        _seg("PID", ["1", "", patient["mrn"], "", [patient["family_name"], patient["given_name"]], "", patient["birth"], patient["sex"]]),
        _seg("OBR", ["1", placer_no, "", [test_code, test_name]]),
    ]
    for i, (value, unit, low, high, flag) in enumerate(observations, start=1):
        segs.append(_seg("OBX", [str(i), "NM", [test_code, test_name], "", value, unit, f"{low}-{high}", flag]))
    return Message(segs)


def build_adt(trigger, patient, control_id, sent_at, location=""):
    segs = [
        header("ADT", trigger, control_id, sent_at),
        _seg("EVN", [trigger, format_timestamp(sent_at)]),
        _seg("PID", ["1", "", patient["mrn"], "", [patient["family_name"], patient["given_name"]], "", patient["birth"], patient["sex"]]),
        _seg("PV1", ["1", "I", location]),
    ]
    return Message(segs)


def build_ack(message, code, text, sent_at):
    """ACK for a received message; code is AA (accepted), AE (error) or AR (rejected)."""
    segs = [
        header("ACK", message.msh.value(9, 2), "ACK" + message.control_id, sent_at,
               sender=(message.msh.value(5), message.msh.value(6)), receiver=(message.msh.value(3), message.msh.value(4))),
        _seg("MSA", [code, message.control_id, text]),
    ]
    return Message(segs)
