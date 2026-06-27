from __future__ import annotations

from app.notifier.base import Notifier


class DryRunNotifier(Notifier):
    def send(self, title: str, body: str = "") -> None:
        print(title)
        if body:
            print(body)
