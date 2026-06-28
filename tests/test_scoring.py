from __future__ import annotations

import unittest
from datetime import date

from app.models import Entry, Race
from app.scoring import RaceScorer


class RaceScorerTest(unittest.TestCase):
    def test_scores_stable_race_as_eligible(self) -> None:
        race = Race(
            "r1",
            date(2026, 6, 27),
            "福島",
            11,
            "テスト特別",
            1800,
            "芝",
            track_condition="良",
            entries=(
                Entry("h1", "A", horse_number=1, win_odds=2.1),
                Entry("h2", "B", horse_number=2, win_odds=5.4),
                Entry("h3", "C", horse_number=3, win_odds=8.2),
            ),
        )
        score = RaceScorer().score(race)
        self.assertTrue(score.eligible)
        self.assertGreaterEqual(score.score, 75)
        self.assertGreaterEqual(score.value_score, 50)

    def test_skips_stable_but_low_value_race(self) -> None:
        race = Race(
            "r3",
            date(2026, 6, 28),
            "函館",
            9,
            "臥牛山特別",
            1800,
            "芝",
            track_condition="良",
            entries=(
                Entry("h1", "A", horse_number=1, win_odds=2.0, popularity=1),
                Entry("h2", "B", horse_number=4, win_odds=6.3, popularity=2),
                Entry("h3", "C", horse_number=3, win_odds=6.8, popularity=3),
                Entry("h4", "D", horse_number=7, win_odds=15.0, popularity=4),
                Entry("h5", "E", horse_number=8, win_odds=18.0, popularity=5),
            ),
        )
        score = RaceScorer().score(race)
        self.assertGreaterEqual(score.score, 75)
        self.assertLess(score.value_score, 50)
        self.assertFalse(score.eligible)
        self.assertIn("堅いが妙味不足", score.reasons)

    def test_penalizes_short_handicap_race(self) -> None:
        race = Race(
            "r4",
            date(2026, 6, 28),
            "小倉",
            11,
            "紫川ステークス ハンデ",
            1200,
            "芝",
            track_condition="良",
            entries=(
                Entry("h1", "A", horse_number=6, win_odds=1.9, popularity=1),
                Entry("h2", "B", horse_number=8, win_odds=3.8, popularity=2),
                Entry("h3", "C", horse_number=3, win_odds=9.7, popularity=3),
                Entry("h4", "D", horse_number=5, win_odds=12.0, popularity=4),
            ),
        )
        score = RaceScorer().score(race)
        self.assertFalse(score.eligible)
        self.assertIn("短距離で展開リスク", score.risk_flags)
        self.assertIn("ハンデ戦", score.risk_flags)

    def test_excludes_debut_race(self) -> None:
        race = Race(
            "r2",
            date(2026, 6, 27),
            "東京",
            5,
            "メイクデビュー東京",
            1600,
            "芝",
            track_condition="良",
            entries=(Entry("h1", "A", horse_number=1, win_odds=2.1),),
        )
        score = RaceScorer().score(race)
        self.assertFalse(score.eligible)
        self.assertIn("新馬戦は除外", score.reasons)


if __name__ == "__main__":
    unittest.main()
