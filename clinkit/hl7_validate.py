"""Structural and content validation of parsed HL7 messages."""
import datetime as dt

SUPPORTED_VERSIONS = ("2.3", "2.3.1", "2.4", "2.5")
REQUIRED_SEGMENTS = {
    "ADT^A01": ("MSH", "EVN", "PID", "PV1"),
    "ADT^A03": ("MSH", "EVN", "PID", "PV1"),
    "ADT^A04": ("MSH", "EVN", "PID", "PV1"),
    "ORM^O01": ("MSH", "PID", "ORC", "OBR"),
    "ORU^R01": ("MSH", "PID", "OBR", "OBX"),
}
VALUE_TYPES = ("NM", "ST", "TX", "CE", "DT", "TS")


class Issue:
    def __init__(self, code, segment, text):
        self.code = code
        self.segment = segment
        self.text = text

    def __eq__(self, other):
        return isinstance(other, Issue) and (self.code, self.segment) == (other.code, other.segment)

    def __repr__(self):
        return f"Issue({self.code}, {self.segment})"


def parse_timestamp(text):
    """Parse YYYY[MM[DD[HH[MM[SS]]]]] into a naive datetime; raises ValueError."""
    if not text or not text.isdigit() or len(text) not in (4, 6, 8, 10, 12, 14):
        raise ValueError(f"bad HL7 timestamp {text!r}")
    padded = text + "0101000000"[len(text) - 4:] if len(text) < 8 else text
    year, month, day = int(padded[0:4]), int(padded[4:6]) or 1, int(padded[6:8]) or 1
    hour = int(padded[8:10]) if len(padded) >= 10 else 0
    minute = int(padded[10:12]) if len(padded) >= 12 else 0
    second = int(padded[12:14]) if len(padded) >= 14 else 0
    return dt.datetime(year, month, day, hour, minute, second)


def is_number(text):
    try:
        float(text)
    except ValueError:
        return False
    return True


def validate(message):
    """Return a list of Issue objects; an empty list means the message is acceptable."""
    issues = []
    msh = message.msh
    if not message.control_id:
        issues.append(Issue("missing-control-id", "MSH", "MSH-10 is required"))
    if message.version and message.version not in SUPPORTED_VERSIONS:
        issues.append(Issue("unsupported-version", "MSH", f"version {message.version} is not supported"))
    required = REQUIRED_SEGMENTS.get(message.message_type)
    if required is None:
        issues.append(Issue("unknown-type", "MSH", f"unsupported message type {message.message_type!r}"))
        required = ("MSH",)
    present = {s.name for s in message.segments}
    for name in required:
        if name not in present:
            issues.append(Issue("missing-segment", name, f"{name} segment is required for {message.message_type}"))
    try:
        parse_timestamp(msh.value(7))
    except ValueError:
        issues.append(Issue("bad-timestamp", "MSH", "MSH-7 is not a valid timestamp"))
    pid = message.first("PID")
    if pid is not None:
        if not pid.value(3):
            issues.append(Issue("missing-patient-id", "PID", "PID-3 is required"))
        if pid.value(7):
            try:
                parse_timestamp(pid.value(7))
            except ValueError:
                issues.append(Issue("bad-birth-date", "PID", "PID-7 is not a valid date"))
        if pid.value(8) and pid.value(8) not in ("M", "F", "O", "U"):
            issues.append(Issue("bad-sex", "PID", "PID-8 must be M, F, O or U"))
    for obx in message.all("OBX"):
        vtype = obx.value(2)
        if vtype not in VALUE_TYPES:
            issues.append(Issue("bad-value-type", "OBX", f"OBX-2 {vtype!r} is not recognised"))
        elif vtype == "NM" and not is_number(obx.value(5)):
            issues.append(Issue("non-numeric-result", "OBX", "OBX-5 must be numeric for NM"))
    return issues
