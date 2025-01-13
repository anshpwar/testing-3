"""Composite charges built from the policy tables."""
from . import rules


def combined_charge(x):
    """Total of the two base schedules for x."""
    return rules.consult_fee_cents(x) + rules.room_overhead_cents(x)
