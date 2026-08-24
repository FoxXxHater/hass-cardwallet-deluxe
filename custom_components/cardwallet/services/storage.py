"""Persistence for wallet cards.

Cards are kept in Home Assistant's own storage (``.storage/cardwallet.cards``)
instead of a hand-rolled JSON file. That removes the ``aiofiles`` dependency,
gives us atomic writes, restrictive file permissions and a versioned migration
path — and it means the data is part of a normal HA backup.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..const import MAX_CARDS_PER_USER, STORAGE_KEY, STORAGE_VERSION
from ..models.card import Card
from .path_utils import get_legacy_storage_path

_LOGGER = logging.getLogger(__name__)


class CardWalletStore(Store):
    """Store with a migration path from the first storage layout."""

    async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, Any],
    ) -> dict[str, Any]:
        if old_major_version < 2:
            cards = old_data.get("cards", []) if isinstance(old_data, dict) else []
            old_data = {"cards": [Card.from_dict(card).to_dict() for card in cards]}
        return old_data


class CardStorage:
    """In-memory list of cards, backed by a Home Assistant store."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise the store for this Home Assistant instance."""
        self.hass = hass
        self._store = CardWalletStore(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
            private=True,
            atomic_writes=True,
        )
        self._cards: list[Card] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # loading
    # ------------------------------------------------------------------

    async def async_load(self) -> None:
        """Load cards from disk, importing the legacy file once if needed."""
        data = await self._store.async_load()

        if data is None:
            imported = await self._async_import_legacy()
            self._cards = imported
            if imported:
                await self._async_save()
        else:
            self._cards = [Card.from_dict(card) for card in data.get("cards", [])]

        self._loaded = True
        _LOGGER.debug("Loaded %s card(s)", len(self._cards))

    async def _async_import_legacy(self) -> list[Card]:
        """Read the pre-2.0 JSON file, if one is lying around."""
        path = get_legacy_storage_path(self.hass)

        def _read() -> list[dict[str, Any]]:
            if not os.path.exists(path):
                return []
            try:
                with open(path, encoding="utf-8") as handle:
                    content = json.load(handle)
            except (OSError, json.JSONDecodeError):
                _LOGGER.warning("Could not read legacy card file at %s", path)
                return []
            return content if isinstance(content, list) else []

        raw = await self.hass.async_add_executor_job(_read)
        if not raw:
            return []

        _LOGGER.info("Importing %s card(s) from %s", len(raw), path)

        def _rename() -> None:
            try:
                os.rename(path, f"{path}.migrated")
            except OSError:
                _LOGGER.warning("Imported cards but could not rename %s", path)

        await self.hass.async_add_executor_job(_rename)
        return [Card.from_dict(card) for card in raw]

    async def _async_save(self) -> None:
        await self._store.async_save({"cards": [card.to_dict() for card in self._cards]})

    # ------------------------------------------------------------------
    # reading
    # ------------------------------------------------------------------

    def visible_to(self, user_id: str, include_shared: bool = True) -> list[Card]:
        """Return the user's own cards plus, optionally, shared ones."""
        return [
            card
            for card in self._cards
            if card.user_id == user_id or (include_shared and card.shared)
        ]

    def owned_by(self, user_id: str) -> list[Card]:
        """Return only the cards this user owns."""
        return [card for card in self._cards if card.user_id == user_id]

    def get(self, card_id: str) -> Card | None:
        """Return a card by id, regardless of owner."""
        return next((card for card in self._cards if card.card_id == card_id), None)

    def count_for_user(self, user_id: str) -> int:
        """Return how many cards this user owns."""
        return sum(1 for card in self._cards if card.user_id == user_id)

    # ------------------------------------------------------------------
    # writing
    # ------------------------------------------------------------------

    async def async_add(self, card: Card) -> Card:
        """Append a card and persist."""
        if self.count_for_user(card.user_id) >= MAX_CARDS_PER_USER:
            raise ValueError(f"a user may hold at most {MAX_CARDS_PER_USER} cards")
        self._cards.append(card)
        await self._async_save()
        return card

    async def async_replace(self, card: Card) -> Card:
        """Replace an existing card (matched by id) and persist."""
        for index, existing in enumerate(self._cards):
            if existing.card_id == card.card_id:
                self._cards[index] = card
                await self._async_save()
                return card
        raise KeyError(card.card_id)

    async def async_delete(self, card_id: str) -> bool:
        """Remove a card by id. Ownership is checked by the caller."""
        remaining = [card for card in self._cards if card.card_id != card_id]
        if len(remaining) == len(self._cards):
            return False
        self._cards = remaining
        await self._async_save()
        return True
