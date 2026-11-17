"""Shared helpers for the REST views."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from ..const import (
    CONF_ALLOW_SHARING,
    DATA_ENTRY,
    DATA_STORE,
    DEFAULT_ALLOW_SHARING,
    DOMAIN,
    SIGNAL_CARDS_UPDATED,
)
from ..services.storage import CardStorage


def get_store(hass: HomeAssistant) -> CardStorage | None:
    """Return the loaded card store, or ``None`` while the entry is not set up."""
    return hass.data.get(DOMAIN, {}).get(DATA_STORE)


def sharing_enabled(hass: HomeAssistant) -> bool:
    """Return whether cards may be shared with other Home Assistant users."""
    entry = hass.data.get(DOMAIN, {}).get(DATA_ENTRY)
    if entry is None:
        return DEFAULT_ALLOW_SHARING
    return bool(entry.options.get(CONF_ALLOW_SHARING, DEFAULT_ALLOW_SHARING))


def user_from_request(request: Any) -> Any:
    """Return the authenticated Home Assistant user behind a request."""
    return request.get("hass_user")


@callback
def notify_cards_changed(hass: HomeAssistant) -> None:
    """Tell subscribed WebSocket clients that the card list changed.

    Called after every write, whether it came in over REST or WebSocket, so a
    second device never shows a stale list.
    """
    async_dispatcher_send(hass, SIGNAL_CARDS_UPDATED)
