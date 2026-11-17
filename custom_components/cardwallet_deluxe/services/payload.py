"""Turning untrusted request payloads into valid cards.

Both the REST views and the WebSocket commands funnel through here, so the
rules only exist once. Two things are deliberately *not* taken from the
payload: ``card_id`` and ``user_id``. The first is assigned by us, the second
comes from the authenticated connection.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any
from uuid import uuid4

from homeassistant.util import dt as dt_util

from ..const import MAX_CODE_LENGTH, MAX_NAME_LENGTH, MAX_NOTES_LENGTH
from ..models.card import Card
from .formats import CodeValidationError, normalize_format, validate_code

_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


class PayloadError(ValueError):
    """Raised when a payload cannot be turned into a valid card."""


def _clean_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PayloadError("name must not be empty")
    name = " ".join(value.split())
    if len(name) > MAX_NAME_LENGTH:
        raise PayloadError(f"name must be at most {MAX_NAME_LENGTH} characters")
    return name


def _clean_color(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str) or not _COLOR_PATTERN.match(value.strip()):
        raise PayloadError("color must be a hex value like #E30613")
    return value.strip().lower()


def _clean_shared(value: Any) -> bool:
    # Only a real JSON boolean counts: bool("false") would be True and would
    # silently share a card the user meant to keep private.
    if value is None:
        return False
    if not isinstance(value, bool):
        raise PayloadError("shared must be true or false")
    return value


def _clean_notes(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise PayloadError("notes must be a string")
    return value[:MAX_NOTES_LENGTH]


def _clean_code(value: Any, barcode_format: str) -> str:
    if isinstance(value, str) and len(value) > MAX_CODE_LENGTH:
        raise PayloadError(f"code must be at most {MAX_CODE_LENGTH} characters")
    try:
        return validate_code(value, barcode_format)
    except CodeValidationError as err:
        raise PayloadError(str(err)) from err


def build_card(user_id: str, owner_name: str, data: dict[str, Any]) -> Card:
    """Create a new card from a payload."""
    barcode_format = normalize_format(data.get("format"))
    now = dt_util.utcnow().isoformat()

    return Card(
        card_id=uuid4().hex,
        user_id=user_id,
        name=_clean_name(data.get("name")),
        code=_clean_code(data.get("code"), barcode_format),
        format=barcode_format,
        owner=owner_name,
        shared=_clean_shared(data.get("shared")),
        color=_clean_color(data.get("color")),
        created_at=now,
        updated_at=now,
        notes=_clean_notes(data.get("notes")),
    )


def apply_update(card: Card, data: dict[str, Any]) -> Card:
    """Return a copy of ``card`` with the payload's changes applied.

    Only the fields present in the payload are touched; identity fields are
    never taken from it.
    """
    changes: dict[str, Any] = {}

    if "name" in data:
        changes["name"] = _clean_name(data["name"])

    barcode_format = card.format
    if "format" in data:
        barcode_format = normalize_format(data["format"])
        changes["format"] = barcode_format

    if "code" in data:
        changes["code"] = _clean_code(data["code"], barcode_format)
    elif "format" in data:
        # The format changed but the code did not — re-validate the stored code
        # so we never end up with an EAN13 card holding a nine-digit number.
        changes["code"] = _clean_code(card.code, barcode_format)

    if "color" in data:
        changes["color"] = _clean_color(data["color"])

    if "shared" in data:
        changes["shared"] = _clean_shared(data["shared"])

    if "notes" in data:
        changes["notes"] = _clean_notes(data["notes"])

    if not changes:
        return card

    changes["updated_at"] = dt_util.utcnow().isoformat()
    return replace(card, **changes)
