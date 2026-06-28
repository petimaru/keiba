from __future__ import annotations

from app.models import Prediction
from app.notifier.base import NotificationMessage


def build_prediction_notification(predictions: tuple[Prediction, ...]) -> NotificationMessage:
    if not predictions:
        return build_skip_notification("今日は見送り推奨", ("堅いレースなし",))

    title = f"本日の狙い目 {len(predictions)}レース"
    lines: list[str] = []
    for index, prediction in enumerate(predictions, start=1):
        race = prediction.race
        if lines:
            lines.append("")
        lines.append(f"{index}位 {race.venue}{race.race_number}R {race.race_name}")
        if race.start_time:
            lines.append(f"発走 {race.start_time}")
        lines.append(f"堅実度 {prediction.race_score.score}")
        lines.append(f"妙味 {prediction.race_score.value_score}")
        lines.append(f"推奨信頼度 {prediction.confidence}%")
        if prediction.race_score.risk_flags:
            lines.append(f"注意 {', '.join(prediction.race_score.risk_flags[:2])}")
        for mark, entry in prediction.marks.items():
            number = entry.horse_number if entry.horse_number is not None else "-"
            lines.append(f"{mark} {number} {entry.horse_name}")
        if prediction.bets:
            lines.append("買い目:")
            for bet in prediction.bets:
                left, right = bet.numbers
                lines.append(f"{bet.kind} {left}-{right} {bet.amount}円")
        lines.append("理由:")
        for reason in prediction.race_score.reasons[:4]:
            lines.append(f"・{reason}")
    return NotificationMessage(title=title, body="\n".join(lines))


def build_prediction_message(predictions: tuple[Prediction, ...]) -> str:
    return _format_message(build_prediction_notification(predictions))


def build_skip_notification(title: str, reasons: tuple[str, ...]) -> NotificationMessage:
    lines: list[str] = []
    if reasons:
        lines.append("理由:")
        for reason in reasons:
            lines.append(f"・{reason}")
    return NotificationMessage(title=title, body="\n".join(lines))


def build_skip_message(title: str, reasons: tuple[str, ...]) -> str:
    return _format_message(build_skip_notification(title, reasons))


def _format_message(message: NotificationMessage) -> str:
    return f"{message.title}\n{message.body}" if message.body else message.title
