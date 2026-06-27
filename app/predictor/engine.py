from __future__ import annotations

from statistics import mean

from app.models import Bet, Entry, HorseScore, Prediction, Race, RaceScore


class PredictionEngine:
    def predict(self, race: Race, race_score: RaceScore) -> Prediction | None:
        if not race_score.eligible:
            return None

        horse_scores = tuple(
            sorted(
                (self._score_entry(entry) for entry in race.entries),
                key=lambda item: item.score,
                reverse=True,
            )
        )
        if len(horse_scores) < 2:
            return None

        top = horse_scores[0]
        second = horse_scores[1]
        third = horse_scores[2] if len(horse_scores) >= 3 else None

        gap_bonus = min(20, max(0, int((top.score - second.score) * 2)))
        confidence = max(0, min(100, int(race_score.score * 0.75 + gap_bonus)))

        marks = {"◎": top.entry, "○": second.entry}
        if third is not None:
            marks["△"] = third.entry

        bets: list[Bet] = []
        if top.entry.horse_number is not None and second.entry.horse_number is not None:
            bets.append(Bet("ワイド", (top.entry.horse_number, second.entry.horse_number), 700))
        if third is not None and top.entry.horse_number is not None and third.entry.horse_number is not None:
            bets.append(Bet("ワイド", (top.entry.horse_number, third.entry.horse_number), 300))

        reasons = (
            f"堅実度 {race_score.score}",
            "上位馬のオッズと安定度を重視",
            "馬体重未発表は中立評価",
        )
        return Prediction(race, race_score, horse_scores, confidence, marks, tuple(bets[:2]), reasons)

    def _score_entry(self, entry: Entry) -> HorseScore:
        score = 50.0
        reasons: list[str] = []

        if entry.win_odds is None:
            reasons.append("単勝オッズなし")
            score -= 10
        elif entry.win_odds <= 2.5:
            reasons.append("単勝人気が高い")
            score += 25
        elif entry.win_odds <= 5.0:
            reasons.append("上位人気")
            score += 15
        elif entry.win_odds <= 10.0:
            reasons.append("中穴")
            score += 5
        else:
            reasons.append("人気薄")
            score -= 10

        if entry.place_odds_min is not None and entry.place_odds_max is not None:
            place_mid = (entry.place_odds_min + entry.place_odds_max) / 2
            if place_mid <= 1.8:
                reasons.append("複勝圏が安定")
                score += 15
            elif place_mid <= 3.0:
                reasons.append("複勝圏は普通")
                score += 5

        if entry.recent_finishes:
            avg_finish = mean(entry.recent_finishes)
            if avg_finish <= 2.5:
                reasons.append("近走安定")
                score += 15
            elif avg_finish >= 6:
                reasons.append("近走不安")
                score -= 10

        if entry.weight_change is not None:
            if abs(entry.weight_change) <= 8:
                reasons.append("馬体重変化が許容範囲")
                score += 5
            elif abs(entry.weight_change) >= 16:
                reasons.append("馬体重変化が大きい")
                score -= 10

        return HorseScore(entry, max(0.0, min(100.0, score)), tuple(reasons))
