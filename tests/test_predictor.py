from __future__ import annotations

import unittest
from datetime import date

from app.models import Entry, Race
from app.predictor import PredictionEngine
from app.scoring import RaceScorer


class PredictionEngineTest(unittest.TestCase):
    def test_generates_wide_bets_within_1000_yen(self) -> None:
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
                Entry("h1", "A", horse_number=12, win_odds=2.1, place_odds_min=1.1, place_odds_max=1.5),
                Entry("h2", "B", horse_number=7, win_odds=4.5, place_odds_min=1.4, place_odds_max=2.1),
                Entry("h3", "C", horse_number=3, win_odds=8.0, place_odds_min=2.0, place_odds_max=3.0),
            ),
        )
        race_score = RaceScorer().score(race)
        prediction = PredictionEngine().predict(race, race_score)
        self.assertIsNotNone(prediction)
        assert prediction is not None
        self.assertLessEqual(sum(bet.amount for bet in prediction.bets), 1000)
        self.assertLessEqual(len(prediction.bets), 2)


if __name__ == "__main__":
    unittest.main()
