"""WebSocket API for the CardWallet Deluxe integration.

The frontend already holds an authenticated WebSocket connection, so this is
both cheaper and safer than the REST API: the user is known from the
connection, and clients can subscribe to changes instead of polling.

Every command is namespaced with the domain, so this integration can be
installed next to the original CardWallet without the two colliding.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_CARDS_UPDATED
from .controllers.helpers import get_store, notify_cards_changed, sharing_enabled
from .services.payload import PayloadError, apply_update, build_card


@callback
def async_register(hass: HomeAssistant) -> None:
    """Register all WebSocket commands."""
    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_add)
    websocket_api.async_register_command(hass, ws_update)
    websocket_api.async_register_command(hass, ws_delete)
    websocket_api.async_register_command(hass, ws_subscribe)


def _require_store(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
):
    store = get_store(hass)
    if store is None:
        connection.send_error(msg["id"], "not_ready", "CardWallet Deluxe is not set up")
        return None
    return store


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list"})
@websocket_api.async_response
async def ws_list(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return every card the connected user may see."""
    store = _require_store(hass, connection, msg)
    if store is None:
        return

    cards = store.visible_to(connection.user.id, include_shared=sharing_enabled(hass))
    connection.send_result(msg["id"], {"cards": [card.to_dict() for card in cards]})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/add",
        vol.Required("name"): str,
        vol.Required("code"): str,
        vol.Optional("format"): vol.Any(str, None),
        vol.Optional("color"): vol.Any(str, None),
        vol.Optional("shared"): bool,
        vol.Optional("notes"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_add(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create a card owned by the connected user."""
    store = _require_store(hass, connection, msg)
    if store is None:
        return

    payload = {key: value for key, value in msg.items() if key not in ("id", "type")}

    try:
        card = build_card(connection.user.id, connection.user.name or "", payload)
        saved = await store.async_add(card)
    except PayloadError as err:
        connection.send_error(msg["id"], "invalid_card", str(err))
        return
    except ValueError as err:
        connection.send_error(msg["id"], "limit_reached", str(err))
        return

    notify_cards_changed(hass)
    connection.send_result(msg["id"], saved.to_dict())


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/update",
        vol.Required("card_id"): str,
        vol.Optional("name"): str,
        vol.Optional("code"): str,
        vol.Optional("format"): vol.Any(str, None),
        vol.Optional("color"): vol.Any(str, None),
        vol.Optional("shared"): bool,
        vol.Optional("notes"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_update(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Update a card the connected user owns."""
    store = _require_store(hass, connection, msg)
    if store is None:
        return

    card = store.get(msg["card_id"])
    if card is None or card.user_id != connection.user.id:
        connection.send_error(msg["id"], "not_found", "Card not found")
        return

    payload = {key: value for key, value in msg.items() if key not in ("id", "type", "card_id")}

    try:
        updated = apply_update(card, payload)
    except PayloadError as err:
        connection.send_error(msg["id"], "invalid_card", str(err))
        return

    await store.async_replace(updated)
    notify_cards_changed(hass)
    connection.send_result(msg["id"], updated.to_dict())


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete",
        vol.Required("card_id"): str,
    }
)
@websocket_api.async_response
async def ws_delete(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete a card the connected user owns."""
    store = _require_store(hass, connection, msg)
    if store is None:
        return

    card = store.get(msg["card_id"])
    if card is None or card.user_id != connection.user.id:
        connection.send_error(msg["id"], "not_found", "Card not found")
        return

    await store.async_delete(card.card_id)
    notify_cards_changed(hass)
    connection.send_result(msg["id"], {"card_id": card.card_id})


@callback
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe"})
def ws_subscribe(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Notify the client whenever any card changes.

    Keeps a second phone or a second tab from showing a stale list.
    """

    @callback
    def _forward() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], {"changed": True}))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_CARDS_UPDATED, _forward
    )
    connection.send_result(msg["id"])
