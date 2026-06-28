from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Entry:
    horse_id: str
    horse_name: str
    gate: Optional[int] = None
    horse_number: Optional[int] = None
    sex_age: str = ""
    weight_carried: Optional[float] = None
    jockey: str = ""
    trainer: str = ""
    win_odds: Optional[float] = None
    place_odds_min: Optional[float] = None
    place_odds_max: Optional[float] = None
    popularity: Optional[int] = None
    body_weight: Optional[int] = None
    weight_change: Optional[int] = None
    recent_finishes: tuple[int, ...] = ()


@dataclass(frozen=True)
class Race:
    race_id: str
    date: date
    venue: str
    race_number: int
    race_name: str
    distance: Optional[int] = None
    surface: str = ""
    weather: str = ""
    track_condition: str = ""
    start_time: str = ""
    entries: tuple[Entry, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RaceScore:
    race_id: str
    score: int
    eligible: bool
    reasons: tuple[str, ...]
    value_score: int = 0
    risk_flags: tuple[str, ...] = ()
    estimated_wide_payout: float | None = None


@dataclass(frozen=True)
class HorseScore:
    entry: Entry
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Bet:
    kind: str
    numbers: tuple[int, int]
    amount: int


@dataclass(frozen=True)
class Prediction:
    race: Race
    race_score: RaceScore
    horse_scores: tuple[HorseScore, ...]
    confidence: int
    marks: dict[str, Entry]
    bets: tuple[Bet, ...]
    reasons: tuple[str, ...]
