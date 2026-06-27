from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib import request

from app.notifier.base import Notifier


class DiscordWebhookNotifier(Notifier):
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send(self, message: str) -> None:
        payload = json.dumps({"content": message}, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self.webhook_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "K-Notify-MVP/0.1",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as response:
                if response.status >= 300:
                    raise RuntimeError(f"Discord通知失敗: HTTP {response.status}")
        except HTTPError as exc:
            detail = _read_error_detail(exc)
            if exc.code in (401, 403, 404):
                raise RuntimeError(
                    f"Discord通知失敗: Webhook URLが無効、削除済み、または権限不足です{detail}"
                ) from exc
            raise RuntimeError(f"Discord通知失敗: HTTP {exc.code}{detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Discord通知失敗: ネットワーク接続エラー: {exc.reason}") from exc


def _read_error_detail(exc: HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace").strip()
    except OSError:
        return ""
    if not body:
        return ""
    return f" / Discord応答: {body[:300]}"
