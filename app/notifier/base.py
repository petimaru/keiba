from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationMessage:
    title: str
    body: str = ""


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, title: str, body: str = "") -> None:
        raise NotImplementedError

    def send_message(self, message: NotificationMessage) -> None:
        self.send(message.title, message.body)


Notifier = NotificationProvider
