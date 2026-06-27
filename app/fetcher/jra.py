from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import time
from urllib import parse
from urllib import request

from app.models import Race
from app.parser import JraHtmlParser, ParserError


@dataclass(frozen=True)
class FetchResult:
    races: tuple[Race, ...]
    errors: tuple[str, ...] = ()


class JRAFetcher:
    def __init__(self, parser: JraHtmlParser | None = None, sleep_seconds: float = 0.2) -> None:
        self.parser = parser or JraHtmlParser()
        self.sleep_seconds = sleep_seconds

    def fetch_from_source_dir(self, source_dir: Path, target_date: date) -> FetchResult:
        races: list[Race] = []
        errors: list[str] = []
        for path in sorted(source_dir.glob("*.html")):
            try:
                races.append(self.parser.parse_race(path.read_text(encoding="utf-8"), target_date))
            except (OSError, ParserError, ValueError, KeyError) as exc:
                errors.append(f"{path.name}: {exc}")
        return FetchResult(tuple(races), tuple(errors))

    def fetch_live(self, target_date: date) -> FetchResult:
        """Fetch current JRA race cards using the official CNAME form flow."""
        errors: list[str] = []
        try:
            select_html = self._post_cname("/JRADB/accessD.html", "pw01dli00/F3")
        except OSError as exc:
            return FetchResult((), (f"JRA公式ページ取得失敗: {exc}",))

        meeting_cnames = self._extract_cnames(select_html, "pw01drl", target_date)
        if not meeting_cnames:
            return FetchResult((), ("対象日の開催ページが見つかりません",))

        detail_cnames: list[str] = []
        for cname in meeting_cnames:
            try:
                meeting_html = self._post_cname("/JRADB/accessD.html", cname)
                detail_cnames.extend(self._extract_cnames(meeting_html, "pw01dde", target_date))
                time.sleep(self.sleep_seconds)
            except OSError as exc:
                errors.append(f"開催ページ取得失敗: {cname}: {exc}")

        detail_cnames = sorted(set(detail_cnames))
        if not detail_cnames:
            return FetchResult((), tuple(errors) or ("対象日のレース詳細が見つかりません",))

        races: list[Race] = []
        for cname in detail_cnames:
            try:
                html = self._get_cname("/JRADB/accessD.html", cname)
                races.append(self.parser.parse_race(html, target_date))
                time.sleep(self.sleep_seconds)
            except (OSError, ParserError, ValueError, KeyError) as exc:
                errors.append(f"レース詳細取得失敗: {cname}: {exc}")

        return FetchResult(tuple(races), tuple(errors))

    def _post_cname(self, path: str, cname: str) -> str:
        data = parse.urlencode({"cname": cname}).encode("ascii")
        req = request.Request(
            f"https://www.jra.go.jp{path}",
            data=data,
            headers={
                "User-Agent": "K-Notify-MVP/0.1",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        return self._open_text(req)

    def _get_cname(self, path: str, cname: str) -> str:
        query = parse.urlencode({"CNAME": cname})
        req = request.Request(
            f"https://www.jra.go.jp{path}?{query}",
            headers={"User-Agent": "K-Notify-MVP/0.1"},
        )
        return self._open_text(req)

    def _open_text(self, req: request.Request) -> str:
        with request.urlopen(req, timeout=20) as response:
            if response.status >= 300:
                raise OSError(f"HTTP {response.status}")
            return response.read().decode("shift_jis", errors="replace")

    def _extract_cnames(self, html: str, prefix: str, target_date: date) -> tuple[str, ...]:
        ymd = target_date.strftime("%Y%m%d")
        cnames = re.findall(r"['\"]((?:" + re.escape(prefix) + r")[A-Za-z0-9/]+)['\"]", html)
        cnames.extend(re.findall(r"CNAME=((?:" + re.escape(prefix) + r")[A-Za-z0-9/]+)", html))
        return tuple(sorted({cname for cname in cnames if ymd in cname}))
