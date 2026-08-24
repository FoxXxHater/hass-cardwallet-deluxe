"""Shared helpers for the REST views."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from ..const import CONF_ALLOW_SHARING, DATA_ENTRY, DATA_STORE, DEFAULT_ALLOW_SHARING, DOMAIN
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
