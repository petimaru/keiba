from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.models import Prediction, Race


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def init_schema(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS races (
                    race_id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    race_number INTEGER NOT NULL,
                    race_name TEXT NOT NULL,
                    distance INTEGER,
                    surface TEXT,
                    weather TEXT,
                    track_condition TEXT,
                    start_time TEXT
                );

                CREATE TABLE IF NOT EXISTS horses (
                    horse_id TEXT PRIMARY KEY,
                    horse_name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS entries (
                    race_id TEXT NOT NULL,
                    horse_id TEXT NOT NULL,
                    gate INTEGER,
                    horse_number INTEGER,
                    sex_age TEXT,
                    weight_carried REAL,
                    jockey TEXT,
                    trainer TEXT,
                    PRIMARY KEY (race_id, horse_id)
                );

                CREATE TABLE IF NOT EXISTS odds (
                    race_id TEXT NOT NULL,
                    horse_id TEXT NOT NULL,
                    win_odds REAL,
                    place_odds_min REAL,
                    place_odds_max REAL,
                    popularity INTEGER,
                    PRIMARY KEY (race_id, horse_id)
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    race_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    race_score INTEGER NOT NULL,
                    confidence INTEGER NOT NULL,
                    marks_json TEXT NOT NULL,
                    bets_json TEXT NOT NULL,
                    reasons_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bet_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    race TEXT NOT NULL,
                    bet TEXT NOT NULL,
                    investment INTEGER NOT NULL,
                    payout INTEGER NOT NULL,
                    profit INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS results (
                    race_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def save_race(self, race: Race) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO races
                (race_id, date, venue, race_number, race_name, distance, surface, weather, track_condition, start_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    race.race_id,
                    race.date.isoformat(),
                    race.venue,
                    race.race_number,
                    race.race_name,
                    race.distance,
                    race.surface,
                    race.weather,
                    race.track_condition,
                    race.start_time,
                ),
            )
            for entry in race.entries:
                conn.execute(
                    "INSERT OR REPLACE INTO horses (horse_id, horse_name) VALUES (?, ?)",
                    (entry.horse_id, entry.horse_name),
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO entries
                    (race_id, horse_id, gate, horse_number, sex_age, weight_carried, jockey, trainer)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        race.race_id,
                        entry.horse_id,
                        entry.gate,
                        entry.horse_number,
                        entry.sex_age,
                        entry.weight_carried,
                        entry.jockey,
                        entry.trainer,
                    ),
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO odds
                    (race_id, horse_id, win_odds, place_odds_min, place_odds_max, popularity)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        race.race_id,
                        entry.horse_id,
                        entry.win_odds,
                        entry.place_odds_min,
                        entry.place_odds_max,
                        entry.popularity,
                    ),
                )

    def save_prediction(self, prediction: Prediction) -> None:
        self.save_race(prediction.race)
        marks = {
            mark: {
                "horse_id": entry.horse_id,
                "horse_number": entry.horse_number,
                "horse_name": entry.horse_name,
            }
            for mark, entry in prediction.marks.items()
        }
        bets = [
            {"kind": bet.kind, "numbers": bet.numbers, "amount": bet.amount}
            for bet in prediction.bets
        ]
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO predictions
                (race_id, race_score, confidence, marks_json, bets_json, reasons_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction.race.race_id,
                    prediction.race_score.score,
                    prediction.confidence,
                    json.dumps(marks, ensure_ascii=False),
                    json.dumps(bets, ensure_ascii=False),
                    json.dumps(prediction.reasons, ensure_ascii=False),
                ),
            )
