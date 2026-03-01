from collections import deque
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional


class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class LogMessage:
    level: LogLevel
    body: str
    tags: set[str] = field(default_factory=set)


class Logger:
    def __init__(self, max_size: int = 1000):
        self._messages: deque[LogMessage] = deque(maxlen=max_size)

    def log(self, level: LogLevel, body: str, tags: Optional[set[str]] = None):
        print(f"[{level.name}] {body}")
        self._messages.append(LogMessage(level=level, body=body, tags=tags or set()))

    def debug(self, body: str, tags: Optional[set[str]] = None):
        self.log(LogLevel.DEBUG, body, tags)

    def info(self, body: str, tags: Optional[set[str]] = None):
        self.log(LogLevel.INFO, body, tags)

    def warning(self, body: str, tags: Optional[set[str]] = None):
        self.log(LogLevel.WARNING, body, tags)

    def error(self, body: str, tags: Optional[set[str]] = None):
        self.log(LogLevel.ERROR, body, tags)

    def critical(self, body: str, tags: Optional[set[str]] = None):
        self.log(LogLevel.CRITICAL, body, tags)

    def get(
        self,
        levels: Optional[set[LogLevel]] = None,
        tags: Optional[set[str]] = None,
        limit: Optional[int] = None,
    ) -> list[LogMessage]:
        result = list(self._messages)
        if levels:
            result = [m for m in result if m.level in levels]
        if tags:
            result = [m for m in result if m.tags & tags]
        if limit is not None:
            result = result[-limit:]
        return result

    def clear(self):
        self._messages.clear()

logger = Logger(max_size=50)