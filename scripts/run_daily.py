#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_settings
from app.dependencies import missing_runtime_dependencies
from app.fetcher import JRAFetcher
from app.notifier import build_prediction_message, build_skip_message
from app.notifier.discord import DiscordWebhookNotifier
from app.notifier.dry_run import DryRunNotifier
from app.predictor import PredictionEngine
from app.sample_data import build_sample_races
from app.scoring import RaceScorer
from app.storage import SQLiteStore


def main() -> int:
    args = parse_args()
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    target_date = args.date or now.date()
    settings = load_settings()

    if args.sample:
        races = build_sample_races(target_date)
        fetch_errors: tuple[str, ...] = ()
    else:
        missing = missing_runtime_dependencies()
        if missing:
            message = build_skip_message(
                "実データ取得の準備不足",
                (
                    f"未インストール: {', '.join(missing)}",
                    "先に pip install -r requirements.txt を実行してください",
                ),
            )
            DryRunNotifier().send(message)
            return 1

        fetcher = JRAFetcher()
        if args.source_dir:
            result = fetcher.fetch_from_source_dir(args.source_dir, target_date)
        else:
            result = fetcher.fetch_live(target_date)
        races = result.races
        fetch_errors = result.errors

    if args.sample:
        time_skip_reasons: tuple[str, ...] = ()
    else:
        races, time_skip_reasons = filter_future_races(races, target_date, now)

    scorer = RaceScorer()
    predictor = PredictionEngine()
    predictions = []
    skipped_reasons: list[str] = list(time_skip_reasons)

    for race in races:
        race_score = scorer.score(race)
        prediction = predictor.predict(race, race_score)
        if prediction is None:
            skipped_reasons.extend(race_score.reasons)
            continue
        predictions.append(prediction)

    predictions = sorted(
        predictions,
        key=lambda prediction: (prediction.race_score.score, prediction.confidence),
        reverse=True,
    )[:3]

    store = SQLiteStore(settings.database_path)
    store.init_schema()
    for prediction in predictions:
        store.save_prediction(prediction)

    if fetch_errors and not predictions:
        message = build_skip_message("JRAデータ取得失敗", tuple(fetch_errors))
    elif not races and time_skip_reasons:
        message = build_skip_message("今日は見送り推奨", time_skip_reasons)
    elif not races:
        message = build_skip_message("必要データ不足", ("対象レースを取得できませんでした",))
    elif not predictions:
        reasons = tuple(dict.fromkeys(skipped_reasons)) or ("堅いレースなし",)
        message = build_skip_message("今日は見送り推奨", reasons)
    else:
        message = build_prediction_message(tuple(predictions))

    notifier = DryRunNotifier()
    if settings.discord_webhook_url and not args.dry_run:
        notifier = DiscordWebhookNotifier(settings.discord_webhook_url)
    notifier.send(message)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="K-Notify daily prediction runner")
    parser.add_argument("--date", type=lambda value: datetime.strptime(value, "%Y-%m-%d").date())
    parser.add_argument("--sample", action="store_true", help="サンプルデータで実行")
    parser.add_argument("--dry-run", action="store_true", help="Discordへ送らず標準出力に表示")
    parser.add_argument("--source-dir", type=Path, help="保存済みHTMLディレクトリを読み込む")
    return parser.parse_args()


def filter_future_races(
    races: tuple, target_date: date, now: datetime
) -> tuple[tuple, tuple[str, ...]]:
    if target_date != now.date():
        return races, ()

    kept = []
    skipped_count = 0
    for race in races:
        race_time = parse_start_time(race.start_time)
        if race_time is not None and race_time <= now.time():
            skipped_count += 1
            continue
        kept.append(race)

    if skipped_count == 0:
        return tuple(kept), ()
    return tuple(kept), (f"発走済みレースを除外: {skipped_count}件",)


def parse_start_time(value: str) -> time | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
