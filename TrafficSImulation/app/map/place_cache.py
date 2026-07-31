"""In-process place resolution cache keyed by normalized query text."""

from __future__ import annotations

from app.map.types import ResolvedPlace


class PlaceResolutionCache:
    def __init__(self) -> None:
        self._entries: dict[str, ResolvedPlace] = {}

    def get(self, normalized_query: str) -> ResolvedPlace | None:
        return self._entries.get(normalized_query)

    def set(self, normalized_query: str, place: ResolvedPlace) -> None:
        self._entries[normalized_query] = place

    def clear(self) -> None:
        self._entries.clear()


__all__ = ["PlaceResolutionCache"]
