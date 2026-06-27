from __future__ import annotations

from app.notifier.base import Notifier


class DryRunNotifier(Notifier):
    def send(self, message: str) -> None:
        print(message)
