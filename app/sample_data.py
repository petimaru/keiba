from __future__ import annotations

from datetime import date

from app.models import Entry, Race


def build_sample_races(target_date: date) -> tuple[Race, ...]:
    return (
        Race(
            race_id=f"{target_date.isoformat()}-FUKUSHIMA-11",
            date=target_date,
            venue="福島",
            race_number=11,
            race_name="サンプル堅実特別",
            distance=1800,
            surface="芝",
            weather="晴",
            track_condition="良",
            start_time="15:45",
            entries=(
                Entry("h001", "サンプルスター", 6, 12, win_odds=2.1, place_odds_min=1.2, place_odds_max=1.5, popularity=1, recent_finishes=(1, 2, 2, 1, 3)),
                Entry("h002", "サンプルロード", 4, 7, win_odds=4.8, place_odds_min=1.5, place_odds_max=2.0, popularity=2, recent_finishes=(2, 3, 1, 4, 2)),
                Entry("h003", "サンプルミライ", 2, 3, win_odds=7.2, place_odds_min=2.0, place_odds_max=2.8, popularity=3, recent_finishes=(3, 2, 5, 2, 1)),
                Entry("h004", "サンプルノヴァ", 1, 1, win_odds=18.5, place_odds_min=4.1, place_odds_max=6.2, popularity=8, recent_finishes=(8, 6, 4, 5, 7)),
            ),
        ),
        Race(
            race_id=f"{target_date.isoformat()}-HAKODATE-11",
            date=target_date,
            venue="函館",
            race_number=11,
            race_name="サンプル混戦ステークス",
            distance=1200,
            surface="ダート",
            weather="曇",
            track_condition="稍重",
            start_time="15:25",
            entries=(
                Entry("h101", "ミックスワン", 1, 1, win_odds=4.6, place_odds_min=1.8, place_odds_max=2.5, popularity=1),
                Entry("h102", "ミックスツー", 2, 2, win_odds=5.1, place_odds_min=1.9, place_odds_max=2.7, popularity=2),
                Entry("h103", "ミックススリー", 3, 3, win_odds=5.8, place_odds_min=2.1, place_odds_max=3.0, popularity=3),
            ),
        ),
        Race(
            race_id=f"{target_date.isoformat()}-TOKYO-05",
            date=target_date,
            venue="東京",
            race_number=5,
            race_name="メイクデビューサンプル",
            distance=1600,
            surface="芝",
            weather="晴",
            track_condition="良",
            start_time="12:30",
            entries=(
                Entry("h201", "デビューワン", 3, 5, win_odds=2.8, popularity=1),
                Entry("h202", "デビューツー", 4, 6, win_odds=4.2, popularity=2),
            ),
        ),
    )
