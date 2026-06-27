from __future__ import annotations

from app.models import Race, RaceScore


class RaceScorer:
    def score(self, race: Race) -> RaceScore:
        reasons: list[str] = []
        exclusions = self._exclusion_reasons(race)
        if exclusions:
            return RaceScore(race.race_id, 0, False, tuple(exclusions))

        score = 50
        entries = sorted(
            [entry for entry in race.entries if entry.win_odds is not None],
            key=lambda entry: entry.win_odds or 999.0,
        )
        favorite = entries[0] if entries else None

        if favorite is None:
            reasons.append("単勝オッズ不足")
            score -= 25
        elif favorite.win_odds <= 2.5:
            reasons.append("1人気が抜けている")
            score += 25
        elif favorite.win_odds <= 3.5:
            reasons.append("1人気が比較的安定")
            score += 15
        elif favorite.win_odds <= 4.5:
            reasons.append("1人気の信頼度は普通")
            score += 5
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

        if race.surface == "ダート" and race.distance is not None and race.distance <= 1400:
            reasons.append("ダート短距離")
            score -= 8

        if "ハンデ" in race.race_name:
            reasons.append("ハンデ戦")
            score -= 10

        score = max(0, min(100, score))
        return RaceScore(race.race_id, score, score >= 65, tuple(reasons))

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
