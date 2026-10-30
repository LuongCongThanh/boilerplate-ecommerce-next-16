"""Sự kiện qua outbox (07 mục 1, ADR 0007)."""

from shared.events.base import DomainEvent
from shared.events.publisher import publish
from shared.events.registry import handles

__all__ = ["DomainEvent", "handles", "publish"]
