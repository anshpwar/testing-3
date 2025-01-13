import datetime as dt
import unittest

from clinkit import scheduling

T0 = dt.datetime(2025, 3, 3, 9, 0)


def at(minutes):
    return T0 + dt.timedelta(minutes=minutes)


class ConflictTests(unittest.TestCase):
    def test_overlap(self):
        self.assertTrue(scheduling.conflicts(at(0), 30, at(15), 30))

    def test_back_to_back_without_buffer(self):
        self.assertFalse(scheduling.conflicts(at(0), 30, at(30), 30))

    def test_buffer_pushes_the_next_slot(self):
        self.assertTrue(scheduling.conflicts(at(0), 30, at(34), 30, buffer_minutes=5))
        self.assertFalse(scheduling.conflicts(at(0), 30, at(35), 30, buffer_minutes=5))

    def test_conflict_is_symmetric(self):
        self.assertEqual(scheduling.conflicts(at(40), 20, at(0), 30, 15), scheduling.conflicts(at(0), 30, at(40), 20, 15))


class SlotSearchTests(unittest.TestCase):
    def test_first_free_slot_skips_busy_time(self):
        busy = [(at(0), 30), (at(40), 20)]
        slot = scheduling.first_free_slot(busy, at(0), at(240), 20, buffer_minutes=10)
        self.assertEqual(slot, at(70))

    def test_empty_day_starts_immediately(self):
        self.assertEqual(scheduling.first_free_slot([], at(0), at(60), 30), at(0))

    def test_no_room_returns_none(self):
        self.assertIsNone(scheduling.first_free_slot([(at(0), 60)], at(0), at(60), 30))

    def test_overlapping_pairs(self):
        slots = [(at(0), 30), (at(20), 30), (at(100), 15)]
        self.assertEqual(scheduling.overlapping(slots), [(0, 1)])
