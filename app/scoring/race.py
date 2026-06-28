from __future__ import annotations

from math import sqrt

from app.models import Race, RaceScore


class RaceScorer:
    def score(self, race: Race) -> RaceScore:
        reasons: list[str] = []
        risk_flags: list[str] = []
        exclusions = self._exclusion_reasons(race)
        if exclusions:
            return RaceScore(race.race_id, 0, False, tuple(exclusions), 0, ())

        score = 50
        entries = sorted(
            [entry for entry in race.entries if entry.win_odds is not None],
            key=lambda entry: entry.win_odds or 999.0,
        )
        favorite = entries[0] if entries else None

        if favorite is None:
            reasons.append("単勝オッズ不足")
            score -= 25
        elif favorite.win_odds <= 1.6:
            reasons.append("1人気がかなり抜けている")
            score += 18
        elif favorite.win_odds <= 1.9:
            reasons.append("1人気が抜けている")
            score += 15
        elif favorite.win_odds <= 2.2:
            reasons.append("1人気は安定寄り")
            score += 10
            risk_flags.append("1人気2倍前後で過信禁止")
        elif favorite.win_odds <= 2.5:
            reasons.append("1人気はやや安定")
            score += 6
            risk_flags.append("1人気2倍台で過信禁止")
        elif favorite.win_odds <= 3.5:
            reasons.append("1人気が比較的安定")
            score += 2
            risk_flags.append("1人気が抜け切らない")
        elif favorite.win_odds <= 4.5:
            reasons.append("1人気の信頼度は普通")
            score -= 5
            risk_flags.append("混戦寄り")
        else:
            reasons.append("1人気が高配当寄りで混戦")
            score -= 20

        if len(entries) >= 3:
            spread = (entries[2].win_odds or 999.0) - (entries[0].win_odds or 999.0)
            if spread >= 4.0:
                reasons.append("上位人気に差がある")
                score += 10
            elif spread <= 1.5:
                reasons.append("上位人気が団子")
                score -= 12

        field_size = len(race.entries)
        if field_size <= 10:
            reasons.append("少頭数")
            score += 10
        elif field_size <= 14:
            reasons.append("標準的な頭数")
            score += 5
        elif field_size >= 16:
            reasons.append("多頭数")
            score -= 10

        if race.track_condition == "稍重":
            reasons.append("馬場が少し重い")
            score -= 5
        elif race.track_condition == "重":
            reasons.append("重馬場")
            score -= 15

        if race.distance is not None and race.distance <= 1200:
            reasons.append("短距離で展開リスク")
            risk_flags.append("短距離で展開リスク")
            score -= 8

        if race.surface == "ダート" and race.distance is not None and race.distance <= 1400:
            reasons.append("ダート短距離")
            risk_flags.append("ダート短距離")
            score -= 4

        if "ハンデ" in race.race_name:
            reasons.append("ハンデ戦")
            risk_flags.append("ハンデ戦")
            score -= 12

        if "ハンデ" in race.race_name and race.distance is not None and race.distance <= 1200:
            reasons.append("短距離ハンデは上限調整")
            score = min(score, 82)

        if favorite is not None and favorite.win_odds is not None and favorite.win_odds >= 2.0:
            score = min(score, 90)

        estimated_wide_payout = self._estimate_wide_payout(entries)
        value_score, value_reasons = self._value_score(entries, race, estimated_wide_payout)
        reasons.extend(value_reasons)
        if score >= 75 and value_score < 50:
            reasons.append("堅いが妙味不足")

        score = max(0, min(100, score))
        value_score = max(0, min(100, value_score))
        eligible = score >= 75 and value_score >= 50
        return RaceScore(
            race.race_id,
            score,
            eligible,
            tuple(reasons),
            value_score,
            tuple(dict.fromkeys(risk_flags)),
            estimated_wide_payout,
        )

    def _value_score(
        self, entries: list, race: Race, estimated_wide_payout: float | None
    ) -> tuple[int, tuple[str, ...]]:
        reasons: list[str] = []
        if not entries:
            return 0, ("妙味評価に必要なオッズ不足",)

        value = 50
        favorite = entries[0]
        favorite_odds = favorite.win_odds or 999.0
        third_odds = entries[2].win_odds if len(entries) >= 3 else None

        if favorite_odds <= 1.5:
            reasons.append("1人気が安すぎる")
            value -= 25
        elif favorite_odds <= 1.8:
            reasons.append("1人気の配当妙味は薄め")
            value -= 15
        elif favorite_odds <= 2.1:
            reasons.append("1人気の妙味は控えめ")
            value -= 8

        if len(entries) >= 3 and third_odds is not None:
            popularities = tuple(entry.popularity for entry in entries[:3])
            if (
                len(race.entries) <= 10
                and popularities == (1, 2, 3)
                and favorite_odds <= 2.1
                and (entries[1].win_odds or 999.0) <= 6.5
                and third_odds <= 7.0
            ):
                reasons.append("人気順通りで配当妙味が薄い")
                value -= 12
            elif 6.0 <= third_odds <= 12.0:
                reasons.append("3番手に少し妙味あり")
                value += 10

        if "ハンデ" in race.race_name:
            reasons.append("ハンデ戦で期待値を下げる")
            value -= 8

        if race.distance is not None and race.distance <= 1200:
            reasons.append("短距離で妙味評価を下げる")
            value -= 6

        if estimated_wide_payout is not None:
            reasons.append(f"推定ワイド倍率 {estimated_wide_payout:.1f}倍")
            if estimated_wide_payout < 1.8:
                reasons.append("推定ワイド配当が低い")
                value -= 35
            elif estimated_wide_payout < 2.0:
                reasons.append("推定ワイド配当は控えめ")
                value -= 10
            elif estimated_wide_payout <= 3.5:
                reasons.append("ワイド配当に最低限の妙味")
                value += 8

        return value, tuple(reasons)

    def _estimate_wide_payout(self, entries: list) -> float | None:
        if len(entries) < 2:
            return None

        first = self._estimate_pair_wide(entries[0], entries[1])
        if first is None:
            return None
        if len(entries) < 3:
            return first

        second = self._estimate_pair_wide(entries[0], entries[2])
        if second is None:
            return first
        return round(first * 0.7 + second * 0.3, 1)

    def _estimate_pair_wide(self, left, right) -> float | None:
        left_place = self._place_mid(left)
        right_place = self._place_mid(right)
        if left_place is not None and right_place is not None:
            return round(max(1.1, min(8.0, ((left_place + right_place) / 2) * 1.15)), 1)

        if left.win_odds is None or right.win_odds is None:
            return None
        return round(max(1.1, min(8.0, sqrt(left.win_odds * right.win_odds) * 0.55)), 1)

    def _place_mid(self, entry) -> float | None:
        if entry.place_odds_min is None or entry.place_odds_max is None:
            return None
        return (entry.place_odds_min + entry.place_odds_max) / 2

    def _exclusion_reasons(self, race: Race) -> list[str]:
        reasons: list[str] = []
        if "新馬" in race.race_name or "メイクデビュー" in race.race_name:
            reasons.append("新馬戦は除外")
        if "未勝利" in race.race_name:
            reasons.append("未勝利戦は除外")
        if "障害" in race.race_name:
            reasons.append("障害戦は除外")
        if race.track_condition == "不良":
            reasons.append("不良馬場は除外")
        if len(race.entries) >= 16 and race.distance is not None and race.distance <= 1400:
            reasons.append("フルゲート短距離は除外")
        return reasons
