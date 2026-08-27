"""The CardWallet Deluxe integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DATA_ENTRY, DATA_REGISTERED, DATA_STORE, DOMAIN
from .controllers import CardWalletItemView, CardWalletListView
from .services.storage import CardStorage
from .websocket import async_register as async_register_websocket

_LOGGER = logging.getLogger(__name__)

# A bare "cardwallet_deluxe:" line in YAML parses to None, so both an empty
# mapping and None have to validate — otherwise such a setup fails to start.
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Any(vol.Schema({}), None)}, extra=vol.ALLOW_EXTRA
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Import a ``cardwallet_deluxe:`` block from configuration.yaml, if present.

    Kept only so that installations from before the config flow keep working;
    the YAML block can be deleted afterwards.
    """
    if DOMAIN in config:
        _LOGGER.warning(
            "Configuring CardWallet Deluxe via configuration.yaml is deprecated. "
            "The integration has been imported into the UI — you can remove "
            "the 'cardwallet_deluxe:' block"
        )
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data={}
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CardWallet Deluxe from a config entry."""
    store = CardStorage(hass)
    await store.async_load()

    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[DATA_STORE] = store
    domain_data[DATA_ENTRY] = entry

    # HTTP views and WebSocket commands are global and cannot be unregistered,
    # so they are registered exactly once per Home Assistant run. They read the
    # store from hass.data on every request, which keeps them correct across
    # reloads.
    if not domain_data.get(DATA_REGISTERED):
        hass.http.register_view(CardWalletListView(hass))
        hass.http.register_view(CardWalletItemView(hass))
        async_register_websocket(hass)
        domain_data[DATA_REGISTERED] = True

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    domain_data = hass.data.get(DOMAIN, {})
    domain_data.pop(DATA_STORE, None)
    domain_data.pop(DATA_ENTRY, None)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after its options changed."""
    await hass.config_entries.async_reload(entry.entry_id)
