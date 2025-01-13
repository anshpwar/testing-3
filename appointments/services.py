"""Booking, cancellation and charging of outpatient appointments."""
import datetime as dt

from clinkit import rules, scheduling

from .models import Appointment


class SchedulingError(Exception):
    pass


def _active_slots(clinician, exclude=None):
    qs = Appointment.objects.filter(clinician=clinician, status="booked")
    if exclude is not None:
        qs = qs.exclude(pk=exclude.pk)
    return [(a.starts_at, a.duration_min) for a in qs]


def buffer_for(duration_min):
    return rules.appointment_buffer_minutes(duration_min)


def book(patient, clinician, starts_at, duration_min=20, reason="", room=""):
    if not patient.active:
        raise SchedulingError("patient record is inactive")
    if not clinician.active or clinician.role not in ("physician", "nurse"):
        raise SchedulingError("clinician cannot take appointments")
    if duration_min <= 0:
        raise SchedulingError("duration must be positive")
    buf = buffer_for(duration_min)
    for start, minutes in _active_slots(clinician):
        if scheduling.conflicts(starts_at, duration_min, start, minutes, buf):
            raise SchedulingError("clinician is not free at that time")
    return Appointment.objects.create(patient=patient, clinician=clinician, starts_at=starts_at,
                                      duration_min=duration_min, reason=reason, room=room)


def next_free(clinician, day_start, day_end, duration_min=20):
    return scheduling.first_free_slot(_active_slots(clinician), day_start, day_end, duration_min, buffer_for(duration_min))


def cancel(appointment, now, reason=""):
    """Cancel and return the late-cancellation fee in cents (zero with enough notice)."""
    if appointment.status != "booked":
        raise SchedulingError(f"appointment is {appointment.status}")
    notice_hours = max(0, int((appointment.starts_at - now).total_seconds() // 3600))
    appointment.status = "cancelled"
    appointment.cancel_reason = reason
    appointment.save(update_fields=["status", "cancel_reason"])
    return rules.no_show_fee_cents(notice_hours)


def complete(appointment):
    if appointment.status != "booked":
        raise SchedulingError(f"appointment is {appointment.status}")
    appointment.status = "completed"
    appointment.save(update_fields=["status"])
    return appointment


def mark_no_show(appointment):
    if appointment.status != "booked":
        raise SchedulingError(f"appointment is {appointment.status}")
    appointment.status = "no_show"
    appointment.save(update_fields=["status"])
    return rules.no_show_fee_cents(0)


def charge_cents(appointment):
    minutes = appointment.duration_min
    return rules.consult_fee_cents(minutes) + rules.room_overhead_cents(minutes)


def day_schedule(clinician, day):
    start = dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(days=1)
    return list(Appointment.objects.filter(clinician=clinician, starts_at__gte=start, starts_at__lt=end)
                .exclude(status="cancelled").select_related("patient"))
