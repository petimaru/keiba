from __future__ import annotations

import unittest
from datetime import date

from app.models import Entry, Race
from app.notifier import build_prediction_message
from app.predictor import PredictionEngine
from app.scoring import RaceScorer


class MessageTest(unittest.TestCase):
    def test_message_uses_confidence_label(self) -> None:
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
                Entry("h2", "B", horse_number=7, win_odds=4.5, place_odds_min=1.7, place_odds_max=2.4),
                Entry("h3", "C", horse_number=3, win_odds=8.0, place_odds_min=2.4, place_odds_max=3.4),
            ),
        )
        race_score = RaceScorer().score(race)
        prediction = PredictionEngine().predict(race, race_score)
        assert prediction is not None
        message = build_prediction_message((prediction,))
        self.assertIn("推奨信頼度", message)
        self.assertIn("妙味", message)
        self.assertNotIn("推奨確率", message)


if __name__ == "__main__":
    unittest.main()
