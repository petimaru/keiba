from __future__ import annotations

from app.models import Prediction


def build_prediction_message(predictions: tuple[Prediction, ...]) -> str:
    if not predictions:
        return build_skip_message("今日は見送り推奨", ("堅いレースなし",))

    lines = [f"本日の狙い目 {len(predictions)}レース"]
    for index, prediction in enumerate(predictions, start=1):
        race = prediction.race
        lines.append("")
        lines.append(f"{index}位 {race.venue}{race.race_number}R {race.race_name}")
        if race.start_time:
            lines.append(f"発走 {race.start_time}")
        lines.append(f"堅実度 {prediction.race_score.score}")
        lines.append(f"推奨信頼度 {prediction.confidence}%")
        for mark, entry in prediction.marks.items():
            number = entry.horse_number if entry.horse_number is not None else "-"
            lines.append(f"{mark} {number} {entry.horse_name}")
        if prediction.bets:
            lines.append("買い目:")
            for bet in prediction.bets:
                left, right = bet.numbers
                lines.append(f"{bet.kind} {left}-{right} {bet.amount}円")
        lines.append("理由:")
        for reason in prediction.race_score.reasons[:3]:
            lines.append(f"・{reason}")
    return "\n".join(lines)


def build_skip_message(title: str, reasons: tuple[str, ...]) -> str:
    lines = [title]
    if reasons:
        lines.append("理由:")
        for reason in reasons:
            lines.append(f"・{reason}")
    return "\n".join(lines)
