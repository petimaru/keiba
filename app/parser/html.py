from __future__ import annotations

import json
import re
from datetime import date
from html.parser import HTMLParser
from typing import Any

from app.models import Entry, Race


class ParserError(RuntimeError):
    pass


class _ScriptJsonParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_target = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "script" and attr_map.get("id") == "knotify-race-data":
            self.in_target = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_target:
            self.in_target = False

    def handle_data(self, data: str) -> None:
        if self.in_target:
            self.parts.append(data)


class JraHtmlParser:
    """Parser for saved HTML.

    The stable test path is a small JSON script tag. Real JRA pages can be
    mapped into the same model incrementally as their HTML is inspected.
    """

    def parse_race(self, html: str, fallback_date: date) -> Race:
        data = self._extract_embedded_json(html)
        if data is None:
            return self._parse_jra_race_card(html, fallback_date)
        return self._race_from_dict(data, fallback_date)

    def _extract_embedded_json(self, html: str) -> dict[str, Any] | None:
        parser = _ScriptJsonParser()
        parser.feed(html)
        raw = "".join(parser.parts).strip()
        if raw:
            return json.loads(raw)

        match = re.search(
            r'<script[^>]+id=["\']knotify-race-data["\'][^>]*>(.*?)</script>',
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if match:
            return json.loads(match.group(1))
        return None

    def _race_from_dict(self, data: dict[str, Any], fallback_date: date) -> Race:
        entries = tuple(
            Entry(
                horse_id=str(entry.get("horse_id") or entry.get("horse_number")),
                horse_name=str(entry["horse_name"]),
                gate=_optional_int(entry.get("gate")),
                horse_number=_optional_int(entry.get("horse_number")),
                sex_age=str(entry.get("sex_age") or ""),
                weight_carried=_optional_float(entry.get("weight_carried")),
                jockey=str(entry.get("jockey") or ""),
                trainer=str(entry.get("trainer") or ""),
                win_odds=_optional_float(entry.get("win_odds")),
                place_odds_min=_optional_float(entry.get("place_odds_min")),
                place_odds_max=_optional_float(entry.get("place_odds_max")),
                popularity=_optional_int(entry.get("popularity")),
                body_weight=_optional_int(entry.get("body_weight")),
                weight_change=_optional_int(entry.get("weight_change")),
                recent_finishes=tuple(int(value) for value in entry.get("recent_finishes", ())),
            )
            for entry in data.get("entries", ())
        )
        race_date = date.fromisoformat(data["date"]) if data.get("date") else fallback_date
        return Race(
            race_id=str(data["race_id"]),
            date=race_date,
            venue=str(data["venue"]),
            race_number=int(data["race_number"]),
            race_name=str(data["race_name"]),
            distance=_optional_int(data.get("distance")),
            surface=str(data.get("surface") or ""),
            weather=str(data.get("weather") or ""),
            track_condition=str(data.get("track_condition") or ""),
            start_time=str(data.get("start_time") or ""),
            entries=entries,
        )

    def _parse_jra_race_card(self, html: str, fallback_date: date) -> Race:
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise ParserError("beautifulsoup4 が未インストールです") from exc

        soup = BeautifulSoup(html, "html.parser")
        if soup.select_one("#syutsuba") is None:
            raise ParserError("JRA出馬表ページではありません")

        date_text = _text(soup.select_one(".date_line .date"))
        race_date = _parse_jra_date(date_text) or fallback_date
        venue = _parse_venue(date_text)
        race_number = _parse_first_int(_text(soup.select_one(".race_number img"), attr="alt"))
        race_name = _text(soup.select_one(".race_name"))
        time_text = _text(soup.select_one(".date_line .time strong"))
        start_time = _parse_start_time(time_text)
        course_text = _text(soup.select_one(".type .course"))
        distance = _parse_distance(course_text)
        surface = _parse_surface(course_text)
        track_condition = _parse_track_condition(html)

        if not venue or race_number is None or not race_name:
            raise ParserError("JRA出馬表の基本情報を取得できません")

        entries: list[Entry] = []
        for row in soup.select("#syutsuba tbody tr"):
            horse_cell = row.select_one("td.horse")
            if horse_cell is None:
                continue
            horse_link = horse_cell.select_one(".name a")
            horse_name = _text(horse_link)
            if not horse_name:
                continue
            horse_id = _extract_cname(_text(horse_link, attr="href")) or horse_name
            gate = _parse_first_int(_text(row.select_one("td.waku img"), attr="alt"))
            horse_number = _parse_first_int(_text(row.select_one("td.num")))
            odds_text = _text(horse_cell.select_one(".odds .num strong"))
            popularity_text = _text(horse_cell.select_one(".pop_rank"))
            jockey_cell = row.select_one("td.jockey")
            sex_age = _text(jockey_cell.select_one(".age")) if jockey_cell else ""
            weight_carried = _optional_float_from_text(
                _text(jockey_cell.select_one(".weight")) if jockey_cell else ""
            )
            jockey = _text(jockey_cell.select_one(".jockey a")) if jockey_cell else ""
            trainer = _text(horse_cell.select_one(".trainer a"))
            body_weight_text = _text(horse_cell.select_one(".weight"))

            entries.append(
                Entry(
                    horse_id=horse_id,
                    horse_name=horse_name,
                    gate=gate,
                    horse_number=horse_number,
                    sex_age=sex_age,
                    weight_carried=weight_carried,
                    jockey=jockey,
                    trainer=trainer,
                    win_odds=_optional_float_from_text(odds_text),
                    popularity=_parse_first_int(popularity_text),
                    body_weight=_parse_body_weight(body_weight_text)[0],
                    weight_change=_parse_body_weight(body_weight_text)[1],
                )
            )

        if not entries:
            raise ParserError("JRA出馬表の出走馬を取得できません")

        return Race(
            race_id=f"{race_date.isoformat()}-{venue}-{race_number:02d}",
            date=race_date,
            venue=venue,
            race_number=race_number,
            race_name=race_name,
            distance=distance,
            surface=surface,
            track_condition=track_condition,
            start_time=start_time,
            entries=tuple(entries),
        )


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _text(node: Any, attr: str | None = None) -> str:
    if node is None:
        return ""
    if attr:
        return str(node.get(attr) or "").strip()
    return node.get_text(" ", strip=True)


def _parse_jra_date(value: str) -> date | None:
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", value)
    if not match:
        return None
    year, month, day = (int(part) for part in match.groups())
    return date(year, month, day)


def _parse_venue(value: str) -> str:
    match = re.search(r"\d+回([^0-9\s]+)\d+日", value)
    return match.group(1) if match else ""


def _parse_first_int(value: str) -> int | None:
    match = re.search(r"\d+", value.replace(",", ""))
    return int(match.group(0)) if match else None


def _parse_start_time(value: str) -> str:
    match = re.search(r"(\d{1,2})時(\d{1,2})分", value)
    if not match:
        return value
    return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"


def _parse_distance(value: str) -> int | None:
    match = re.search(r"([\d,]+)\s*メートル", value)
    return int(match.group(1).replace(",", "")) if match else None


def _parse_surface(value: str) -> str:
    if "芝" in value:
        return "芝"
    if "ダート" in value:
        return "ダート"
    return ""


def _parse_track_condition(html: str) -> str:
    for condition in ("不良", "重", "稍重", "良"):
        if f"馬場状態：{condition}" in html or f"馬場：{condition}" in html:
            return condition
    return ""


def _optional_float_from_text(value: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
    return float(match.group(0)) if match else None


def _parse_body_weight(value: str) -> tuple[int | None, int | None]:
    match = re.search(r"(\d{3})\s*\(([+-]?\d+)\)", value)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _extract_cname(value: str) -> str | None:
    match = re.search(r"CNAME=([^\"'>\s]+)", value)
    return match.group(1) if match else None
