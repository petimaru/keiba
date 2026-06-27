#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_settings
from app.notifier.discord import DiscordWebhookNotifier


def main() -> int:
    settings = load_settings()
    if not settings.discord_webhook_url:
        print("DISCORD_WEBHOOK_URL が未設定です。")
        print("例: export DISCORD_WEBHOOK_URL='DiscordのWebhook URL'")
        return 2

    now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S JST")
    message = f"K-Notify 接続テスト\n送信時刻: {now}"
    try:
        DiscordWebhookNotifier(settings.discord_webhook_url).send(message)
    except RuntimeError as exc:
        print(exc)
        return 1
    print("Discordへ接続テストを送信しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
