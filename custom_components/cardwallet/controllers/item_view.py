"""REST view for a single card."""

from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from ..services.payload import PayloadError, apply_update
from .helpers import get_store, user_from_request

_LOGGER = logging.getLogger(__name__)


class CardWalletItemView(HomeAssistantView):
    """``/api/cardwallet/{card_id}`` — update and delete a card."""

    url = "/api/cardwallet/{card_id}"
    name = "api:cardwallet:item"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Keep a reference to hass; the store is looked up per request."""
        self.hass = hass

    async def put(self, request: web.Request, card_id: str) -> web.Response:
        """Update a card the authenticated user owns."""
        store = get_store(self.hass)
        if store is None:
            return self.json({"error": "cardwallet is not set up"}, status_code=503)

        try:
            data = await request.json()
        except ValueError:
            return self.json({"error": "invalid JSON body"}, status_code=400)

        if not isinstance(data, dict):
            return self.json({"error": "expected a JSON object"}, status_code=400)

        user = user_from_request(request)
        card = store.get(card_id)

        if card is None:
            return self.json({"error": "card not found"}, status_code=404)
        if card.user_id != user.id:
            # Same answer as a missing card: not being the owner should not
            # confirm that the id exists.
            return self.json({"error": "card not found"}, status_code=404)

        try:
            updated = apply_update(card, data)
        except PayloadError as err:
            return self.json({"error": str(err)}, status_code=400)

        await store.async_replace(updated)
        return self.json(updated.to_dict())

    async def delete(self, request: web.Request, card_id: str) -> web.Response:
        """Delete a card the authenticated user owns."""
        store = get_store(self.hass)
        if store is None:
            return self.json({"error": "cardwallet is not set up"}, status_code=503)

        user = user_from_request(request)
        card = store.get(card_id)

        if card is None or card.user_id != user.id:
            return self.json({"error": "card not found"}, status_code=404)

        await store.async_delete(card_id)
        return self.json({"status": "deleted", "card_id": card_id})
