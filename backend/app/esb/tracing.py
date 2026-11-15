from collections import deque
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID

from pydantic import Field

from app.core.models import StrictModel


class MessageTrace(StrictModel):
    message_id: UUID
    correlation_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    destination: str
    operation: str
    status: str
    status_code: int
    duration_ms: float = Field(ge=0)


class TraceStore:
    def __init__(self, capacity: int = 200) -> None:
        self._entries: deque[MessageTrace] = deque(maxlen=capacity)
        self._lock = Lock()

    def record(self, trace: MessageTrace) -> None:
        with self._lock:
            self._entries.appendleft(trace)

    def recent(self, limit: int) -> list[MessageTrace]:
        with self._lock:
            return list(self._entries)[:limit]
