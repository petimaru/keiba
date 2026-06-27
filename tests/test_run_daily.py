from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import Race
from scripts.run_daily import filter_future_races


class RunDailyTest(unittest.TestCase):
    def test_filters_started_races_only_for_today(self) -> None:
        now = datetime(2026, 6, 27, 14, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
        races = (
            Race("past", now.date(), "函館", 7, "過去レース", start_time="13:10"),
            Race("future", now.date(), "福島", 11, "未来レース", start_time="15:45"),
        )

        kept, reasons = filter_future_races(races, now.date(), now)

        self.assertEqual([race.race_id for race in kept], ["future"])
        self.assertEqual(reasons, ("発走済みレースを除外: 1件",))

    def test_does_not_filter_when_checking_other_date(self) -> None:
        now = datetime(2026, 6, 27, 14, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
        target_date = now.date().replace(day=28)
        races = (Race("other-day", target_date, "福島", 11, "別日レース", start_time="13:10"),)

        kept, reasons = filter_future_races(races, target_date, now)

        self.assertEqual(kept, races)
        self.assertEqual(reasons, ())


if __name__ == "__main__":
    unittest.main()
