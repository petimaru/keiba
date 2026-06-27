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
        self.assertGreaterEqual(score.score, 65)

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
