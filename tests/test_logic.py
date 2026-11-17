"""Offline tests for the pure logic (no Home Assistant runtime needed).

Home Assistant cannot be installed on every Python version, so a minimal stub
for the helpers we import from it is injected before loading the modules under
test.
"""

import importlib
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

# --- stub out the bits of homeassistant that the pure modules touch ---------
ha = types.ModuleType("homeassistant")
ha_util = types.ModuleType("homeassistant.util")
ha_dt = types.ModuleType("homeassistant.util.dt")
ha_dt.utcnow = lambda: datetime.now(timezone.utc)
ha_util.dt = ha_dt
ha.util = ha_util
sys.modules.setdefault("homeassistant", ha)
sys.modules.setdefault("homeassistant.util", ha_util)
sys.modules.setdefault("homeassistant.util.dt", ha_dt)

# --- mount the subpackages without running the package __init__ -------------
# The package __init__ pulls in the whole Home Assistant runtime; the modules
# under test do not.
BASE = Path(__file__).resolve().parents[1] / "custom_components" / "cardwallet_deluxe"

for name, path in (
    ("cw", BASE),
    ("cw.models", BASE / "models"),
    ("cw.services", BASE / "services"),
):
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module

_card = importlib.import_module("cw.models.card")
Card = _card.Card
cards_from_dicts = _card.cards_from_dicts
_formats = importlib.import_module("cw.services.formats")
CodeValidationError = _formats.CodeValidationError
gtin_check_digit = _formats.gtin_check_digit
normalize_format = _formats.normalize_format
validate_code = _formats.validate_code
_payload = importlib.import_module("cw.services.payload")
PayloadError = _payload.PayloadError
apply_update = _payload.apply_update
build_card = _payload.build_card

failures = []


def check(label, condition):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


def raises(label, func, exc=PayloadError):
    try:
        func()
    except exc:
        print(f"  ok   {label}")
    except Exception as err:  # noqa: BLE001
        print(f"  FAIL {label} (raised {type(err).__name__}: {err})")
        failures.append(label)
    else:
        print(f"  FAIL {label} (no error raised)")
        failures.append(label)


print("format normalisation")
check("scanner name ean_13 -> EAN13", normalize_format("ean_13") == "EAN13")
check("qr_code -> QR", normalize_format("qr_code") == "QR")
check("code_128 -> CODE128", normalize_format("code_128") == "CODE128")
check("upc_a -> UPC", normalize_format("upc_a") == "UPC")
check("CODE128C survives", normalize_format("CODE128C") == "CODE128C")
check("already-clean EAN13 survives", normalize_format("EAN13") == "EAN13")
check("unknown falls back", normalize_format("wat") == "CODE128")
check("None falls back", normalize_format(None) == "CODE128")
check("code_93 -> CODE128, not CODE39", normalize_format("code_93") == "CODE128")
check("upc_ean_extension is not EAN13", normalize_format("upc_ean_extension") != "EAN13")

print("\ncheck digits")
check("EAN13 4006381333931", validate_code("4006381333931", "EAN13") == "4006381333931")
check("EAN8 96385074", validate_code("96385074", "EAN8") == "96385074")
check("UPC-A 036000291452", validate_code("036000291452", "UPC") == "036000291452")
check("check digit of 400638133393 is 1", gtin_check_digit("400638133393") == 1)
raises("EAN13 with bad check digit", lambda: validate_code("4006381333932", "EAN13"), CodeValidationError)
raises("EAN13 too short", lambda: validate_code("400638133393", "EAN13"), CodeValidationError)
raises("EAN13 with letters", lambda: validate_code("40063813339X", "EAN13"), CodeValidationError)
check("CODE128 takes anything printable", validate_code("ABC-123", "CODE128") == "ABC-123")
check("QR takes a URL", validate_code("https://example.org/x", "QR") == "https://example.org/x")
check("spaces stripped for numeric formats", validate_code("4006 3813 33931", "EAN13") == "4006381333931")

print("\nbuilding cards")
card = build_card("user-a", "Anna", {"name": "  DM   PAYBACK ", "code": "4006381333931", "format": "ean_13"})
check("name collapsed", card.name == "DM PAYBACK")
check("owner recorded", card.owner == "Anna")
check("user id from caller", card.user_id == "user-a")
check("card id generated", len(card.card_id) == 32)
check("not shared by default", card.shared is False)
check("timestamps set", card.created_at == card.updated_at and card.created_at)
qr = build_card("user-a", "Anna", {"name": "Bonus", "code": "https://example.org/42", "format": "qr_code"})
check("scanned QR is stored as QR", qr.format == "QR")
raises("empty name rejected", lambda: build_card("u", "", {"name": "  ", "code": "123"}))
raises("bad colour rejected", lambda: build_card("u", "", {"name": "X", "code": "1", "color": "red"}))
check("hex colour kept", build_card("u", "", {"name": "X", "code": "1", "color": "#E30613"}).color == "#e30613")

print("\nupdating cards")
updated = apply_update(card, {"name": "DM"})
check("name changed", updated.name == "DM")
check("code untouched", updated.code == card.code)
check("owner untouched", updated.user_id == "user-a")
check("updated_at moved", updated.updated_at >= card.updated_at)
check("original untouched", card.name == "DM PAYBACK")

sneaky = apply_update(card, {"user_id": "user-b", "card_id": "hijack", "name": "X"})
check("user_id cannot be set from payload", sneaky.user_id == "user-a")
check("card_id cannot be set from payload", sneaky.card_id == card.card_id)

raises("changing format re-validates the stored code", lambda: apply_update(card, {"format": "EAN8"}))
check("no changes -> same object", apply_update(card, {}) is card)
check("switching a card to QR works", apply_update(card, {"format": "QR"}).format == "QR")

print("\nshared and notes")
raises("string 'false' is not a boolean", lambda: build_card("u", "", {"name": "X", "code": "1", "shared": "false"}))
raises("update with string shared rejected", lambda: apply_update(card, {"shared": "false"}))
check("shared true accepted", apply_update(card, {"shared": True}).shared is True)
check("shared null means not shared", build_card("u", "", {"name": "X", "code": "1", "shared": None}).shared is False)
check("notes truncated", len(build_card("u", "", {"name": "X", "code": "1", "notes": "n" * 900}).notes) == 500)
check("notes null -> empty", apply_update(card, {"notes": None}).notes == "")
raises("non-string notes rejected", lambda: build_card("u", "", {"name": "X", "code": "1", "notes": 42}))

print("\nlegacy data")
legacy = Card.from_dict(
    {"card_id": "1", "name": "Alt", "code": "123", "owner": "John", "user_id": "u", "unknown_key": "x"}
)
check("unknown keys ignored", legacy.name == "Alt")
check("format defaulted", legacy.format == "CODE128")
check("shared defaulted", legacy.shared is False)
check("round trip", Card.from_dict(legacy.to_dict()) == legacy)
mixed = cards_from_dicts(
    [
        {"card_id": "1", "name": "Ok", "code": "1", "user_id": "u"},
        {"card_id": "2", "name": "No code", "user_id": "u"},
        "not a dict",
        {"card_id": "3", "name": "Also ok", "code": "3", "user_id": "u"},
    ],
    "test",
)
check("broken entries skipped, good ones kept", [c.card_id for c in mixed] == ["1", "3"])

print()
if failures:
    print(f"{len(failures)} FAILING: {failures}")
    sys.exit(1)
print("all checks passed")
