from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    discord_webhook_url: str | None
    database_path: Path


def load_settings() -> Settings:
    return Settings(
        discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL") or None,
        database_path=Path(os.getenv("K_NOTIFY_DB", "db/knotify.sqlite3")),
    )
