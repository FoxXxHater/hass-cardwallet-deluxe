"""Config flow — this is what puts CardWallet Deluxe into the Add-Integration dialog."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

from .const import CONF_ALLOW_SHARING, DEFAULT_ALLOW_SHARING, DOMAIN

TITLE = "CardWallet Deluxe"


class CardWalletDeluxeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI setup.

    There is nothing to connect to and nothing to authenticate against, so the
    flow is a single confirmation step. Its only real job is to create the
    config entry that ``async_setup_entry`` hangs off.
    """

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the step started from the UI."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_ALLOW_SHARING, default=DEFAULT_ALLOW_SHARING
                        ): bool,
                    }
                ),
            )

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=TITLE,
            data={},
            options={CONF_ALLOW_SHARING: user_input[CONF_ALLOW_SHARING]},
        )

    async def async_step_import(self, import_data: dict[str, Any] | None = None):
        """Take over installations that were configured via configuration.yaml."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=TITLE,
            data={},
            options={CONF_ALLOW_SHARING: DEFAULT_ALLOW_SHARING},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> CardWalletDeluxeOptionsFlow:
        """Return the options flow."""
        return CardWalletDeluxeOptionsFlow(config_entry)


class CardWalletDeluxeOptionsFlow(OptionsFlow):
    """Let the user toggle sharing after the fact."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Remember the entry under our own attribute name.

        ``self.config_entry`` is managed by Home Assistant and must not be
        assigned to by integrations.
        """
        self._entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Show and store the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._entry.options.get(CONF_ALLOW_SHARING, DEFAULT_ALLOW_SHARING)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Required(CONF_ALLOW_SHARING, default=current): bool}
            ),
        )
