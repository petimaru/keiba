from __future__ import annotations

import unittest
from datetime import date

from app.parser import JraHtmlParser


class ParserTest(unittest.TestCase):
    def test_parses_embedded_json_fixture(self) -> None:
        html = """
        <html><body>
        <script type="application/json" id="knotify-race-data">
        {
          "race_id": "r1",
          "date": "2026-06-27",
          "venue": "福島",
          "race_number": 11,
          "race_name": "テスト特別",
          "distance": 1800,
          "surface": "芝",
          "track_condition": "良",
          "entries": [
            {"horse_id": "h1", "horse_name": "A", "horse_number": 12, "win_odds": 2.1}
          ]
        }
        </script>
        </body></html>
        """
        race = JraHtmlParser().parse_race(html, date(2026, 6, 27))
        self.assertEqual(race.venue, "福島")
        self.assertEqual(race.entries[0].horse_number, 12)


if __name__ == "__main__":
    unittest.main()
