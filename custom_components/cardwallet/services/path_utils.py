"""Filesystem helpers.

Cards live in Home Assistant's own storage directory now. The only path this
module still resolves is the pre-2.0 plain JSON file, so that existing
installations can be migrated once and then forgotten.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..const import LEGACY_FILENAME


def get_legacy_storage_path(hass: HomeAssistant) -> str:
    """Return the path of the pre-2.0 ``cardwallet_cards.json`` file."""
    return hass.config.path(LEGACY_FILENAME)
