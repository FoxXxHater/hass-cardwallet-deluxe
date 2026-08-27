"""Filesystem helpers.

Cards live in Home Assistant's own storage. The only path this module still
resolves is the plain JSON file written by CardWallet 1.x, so that existing
installations can be migrated once and then forgotten.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..const import LEGACY_FILENAME


def get_legacy_storage_path(hass: HomeAssistant) -> str:
    """Return the path of the 1.x ``cardwallet_cards.json`` file."""
    return hass.config.path(LEGACY_FILENAME)
