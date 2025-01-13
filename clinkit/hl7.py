"""HL7 v2 style message parsing: segments, fields, repetitions, components and escape sequences.

Field numbering follows the HL7 convention: for MSH, field 1 is the field separator itself and
field 2 the encoding characters; for every other segment field 1 is the first value after the
segment name.
"""
SEGMENT_SEP = "\r"


class Hl7Error(ValueError):
    """Raised when text cannot be parsed as a message."""


class Delimiters:
    def __init__(self, field="|", component="^", repeat="~", escape="\\", sub="&"):
        chars = [field, component, repeat, escape, sub]
        if any(len(c) != 1 for c in chars) or len(set(chars)) != 5:
            raise Hl7Error("delimiters must be five distinct single characters")
        self.field, self.component, self.repeat, self.escape, self.sub = chars

    @classmethod
    def from_msh(cls, line):
        if not line.startswith("MSH") or len(line) < 8:
            raise Hl7Error("message must start with an MSH segment")
        return cls(field=line[3], component=line[4], repeat=line[5], escape=line[6], sub=line[7])

    @property
    def encoding_chars(self):
        return self.component + self.repeat + self.escape + self.sub


DEFAULT_DELIMITERS = Delimiters()


def escape_text(text, d=DEFAULT_DELIMITERS):
    """Encode delimiter characters inside a data value."""
    out = []
    for ch in text:
        if ch == d.escape:
            out.append(d.escape + "E" + d.escape)
        elif ch == d.field:
            out.append(d.escape + "F" + d.escape)
        elif ch == d.component:
            out.append(d.escape + "S" + d.escape)
        elif ch == d.sub:
            out.append(d.escape + "T" + d.escape)
        elif ch == d.repeat:
            out.append(d.escape + "R" + d.escape)
        elif ch == "\n":
            out.append(d.escape + ".br" + d.escape)
        else:
            out.append(ch)
    return "".join(out)


def unescape_text(text, d=DEFAULT_DELIMITERS):
    """Decode escape sequences. Unknown formatting sequences are dropped, malformed ones raise."""
    if d.escape not in text:
        return text
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch != d.escape:
            out.append(ch)
            i += 1
            continue
        end = text.find(d.escape, i + 1)
        if end == -1:
            raise Hl7Error("unterminated escape sequence")
        code = text[i + 1:end]
        table = {"F": d.field, "S": d.component, "T": d.sub, "R": d.repeat, "E": d.escape, ".br": "\n"}
        if code in table:
            out.append(table[code])
        elif code.startswith("X") and len(code) > 1 and len(code) % 2 == 1:
            try:
                out.append(bytes.fromhex(code[1:]).decode("latin-1"))
            except ValueError:
                raise Hl7Error(f"bad hex escape {code!r}")
        # other sequences (highlighting such as H and N) carry no data
        i = end + 1
    return "".join(out)


class Segment:
    def __init__(self, name, fields, delimiters=DEFAULT_DELIMITERS):
        self.name = name
        self.fields = list(fields)
        self.d = delimiters

    @classmethod
    def parse(cls, line, delimiters=DEFAULT_DELIMITERS):
        if len(line) < 3:
            raise Hl7Error(f"segment too short: {line!r}")
        name = line[:3]
        if not (name.isalnum() and name[0].isalpha() and name == name.upper()):
            raise Hl7Error(f"bad segment name {name!r}")
        parts = line.split(delimiters.field)
        if name == "MSH":
            return cls(name, [delimiters.field] + parts[1:], delimiters)
        return cls(name, parts[1:], delimiters)

    def raw(self, number):
        if number < 1 or number > len(self.fields):
            return ""
        return self.fields[number - 1]

    def repetitions(self, number):
        raw = self.raw(number)
        return raw.split(self.d.repeat) if raw else []

    def components(self, number, rep=1):
        reps = self.repetitions(number)
        if rep < 1 or rep > len(reps):
            return []
        return [unescape_text(c, self.d) for c in reps[rep - 1].split(self.d.component)]

    def value(self, number, comp=1, rep=1, sub=None):
        if self.name == "MSH" and number == 2:
            return self.d.encoding_chars if comp == 1 else ""
        if self.name == "MSH" and number == 1:
            return self.d.field
        reps = self.repetitions(number)
        if rep < 1 or rep > len(reps):
            return ""
        comps = reps[rep - 1].split(self.d.component)
        if comp < 1 or comp > len(comps):
            return ""
        piece = comps[comp - 1]
        if sub is not None:
            subs = piece.split(self.d.sub)
            piece = subs[sub - 1] if 1 <= sub <= len(subs) else ""
        return unescape_text(piece, self.d)

    def encode(self):
        if self.name == "MSH":
            return self.d.field.join([self.name] + self.fields[1:])
        return self.d.field.join([self.name] + self.fields)

    def __repr__(self):
        return f"<Segment {self.name} fields={len(self.fields)}>"


class Message:
    def __init__(self, segments, delimiters=DEFAULT_DELIMITERS):
        self.segments = list(segments)
        self.d = delimiters

    @classmethod
    def parse(cls, text):
        if not text or not text.strip():
            raise Hl7Error("empty message")
        normalised = text.replace("\r\n", SEGMENT_SEP).replace("\n", SEGMENT_SEP).strip(SEGMENT_SEP + " ")
        lines = [ln for ln in normalised.split(SEGMENT_SEP) if ln]
        if not lines[0].startswith("MSH"):
            raise Hl7Error("message must start with an MSH segment")
        d = Delimiters.from_msh(lines[0])
        return cls([Segment.parse(ln, d) for ln in lines], d)

    def all(self, name):
        return [s for s in self.segments if s.name == name]

    def first(self, name):
        found = self.all(name)
        return found[0] if found else None

    @property
    def msh(self):
        return self.segments[0]

    @property
    def message_type(self):
        trigger = self.msh.value(9, 2)
        base = self.msh.value(9, 1)
        return f"{base}^{trigger}" if trigger else base

    @property
    def control_id(self):
        return self.msh.value(10)

    @property
    def version(self):
        return self.msh.value(12)

    def encode(self):
        return SEGMENT_SEP.join(s.encode() for s in self.segments) + SEGMENT_SEP
