"""The card model."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, fields
from typing import Any

from ..services.formats import DEFAULT_FORMAT

_LOGGER = logging.getLogger(__name__)


@dataclass
class Card:
    """A single wallet card.

    ``user_id`` is the owner and is always taken from the authenticated
    request — never from the request body.
    """

    card_id: str
    user_id: str
    name: str
    code: str
    format: str = DEFAULT_FORMAT
    owner: str = ""
    shared: bool = False
    color: str | None = None
    created_at: str = ""
    updated_at: str = ""
    notes: str = field(default="")

    def to_dict(self) -> dict[str, Any]:
        """Return the card as a JSON-serialisable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Card:
        """Build a card from stored or legacy data, ignoring unknown keys.

        Old files carry keys this model no longer knows (and miss keys it does),
        so anything unexpected is dropped instead of raising ``TypeError``.
        """
        known = {f.name for f in fields(cls)}
        payload = {key: value for key, value in data.items() if key in known}
        payload.setdefault("format", DEFAULT_FORMAT)
        payload.setdefault("owner", "")
        payload["shared"] = bool(payload.get("shared", False))
        return cls(**payload)


def cards_from_dicts(raw: Iterable[Any], source: str) -> list[Card]:
    """Build cards from stored or imported data, skipping broken entries.

    A single damaged entry (missing ``code``, not a dict, …) must not keep the
    whole integration from starting, so it is logged and dropped instead.
    """
    cards: list[Card] = []
    for index, entry in enumerate(raw):
        try:
            if not isinstance(entry, dict):
                raise TypeError(f"expected an object, got {type(entry).__name__}")
            cards.append(Card.from_dict(entry))
        except (TypeError, ValueError) as err:
            _LOGGER.warning("Skipping unreadable card #%s from %s: %s", index, source, err)
    return cards
