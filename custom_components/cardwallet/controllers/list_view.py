"""REST view for the card collection."""

from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from ..services.payload import PayloadError, build_card
from .helpers import get_store, sharing_enabled, user_from_request

_LOGGER = logging.getLogger(__name__)


class CardWalletListView(HomeAssistantView):
    """``/api/cardwallet`` — list and create cards."""

    url = "/api/cardwallet"
    name = "api:cardwallet:list"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        """Keep a reference to hass; the store is looked up per request."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return the cards this user may see."""
        store = get_store(self.hass)
        if store is None:
            return self.json({"error": "cardwallet is not set up"}, status_code=503)

        user = user_from_request(request)
        cards = store.visible_to(user.id, include_shared=sharing_enabled(self.hass))
        return self.json([card.to_dict() for card in cards])

    async def post(self, request: web.Request) -> web.Response:
        """Create a card owned by the authenticated user."""
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

        try:
            card = build_card(user.id, user.name or "", data)
            saved = await store.async_add(card)
        except PayloadError as err:
            return self.json({"error": str(err)}, status_code=400)
        except ValueError as err:
            return self.json({"error": str(err)}, status_code=409)

        return self.json(saved.to_dict())
