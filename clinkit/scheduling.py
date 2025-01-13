"""Pure scheduling arithmetic used by the appointment service."""
import datetime as dt


def end_of(start, minutes):
    return start + dt.timedelta(minutes=minutes)


def conflicts(start_a, minutes_a, start_b, minutes_b, buffer_minutes=0):
    """True when two slots overlap once each is padded by the buffer on its trailing edge."""
    pad = dt.timedelta(minutes=buffer_minutes)
    return start_a < end_of(start_b, minutes_b) + pad and start_b < end_of(start_a, minutes_a) + pad


def first_free_slot(busy, day_start, day_end, duration, buffer_minutes=0, step=5):
    """Earliest start in [day_start, day_end) where a slot of `duration` fits. busy is [(start, minutes)]."""
    candidate = day_start
    step_delta = dt.timedelta(minutes=step)
    while end_of(candidate, duration) <= day_end:
        if not any(conflicts(candidate, duration, s, m, buffer_minutes) for s, m in busy):
            return candidate
        candidate += step_delta
    return None


def overlapping(slots, buffer_minutes=0):
    """Pairs of indexes in `slots` ([(start, minutes)]) that conflict."""
    pairs = []
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            if conflicts(slots[i][0], slots[i][1], slots[j][0], slots[j][1], buffer_minutes):
                pairs.append((i, j))
    return pairs
