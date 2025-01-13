"""Identifier schemes: medical record numbers with a check digit, order and invoice numbers."""


def luhn_check_digit(digits):
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)


def make_mrn(seq, prefix="MRN"):
    if seq < 0 or seq > 9999999:
        raise ValueError("sequence out of range")
    body = f"{seq:07d}"
    return f"{prefix}{body}{luhn_check_digit(body)}"


def valid_mrn(mrn, prefix="MRN"):
    if not mrn.startswith(prefix):
        return False
    rest = mrn[len(prefix):]
    return len(rest) == 8 and rest.isdigit() and luhn_check_digit(rest[:7]) == rest[7]


def order_number(seq, priority):
    return f"LO{priority}-{seq:06d}"


def invoice_number(year, seq):
    return f"INV-{year:04d}-{seq:05d}"


def normalise_phone(raw):
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("expected a ten digit phone number")
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
