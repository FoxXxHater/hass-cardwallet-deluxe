"""Barcode format handling and validation.

Format names follow the JsBarcode / frontend naming (``EAN13``, ``CODE128``…)
because that is what the Lovelace card needs when it renders a card. Scanners
report their own names (``ean_13``, ``qr_code``…), so everything coming from the
outside is normalised here before it is stored.
"""

from __future__ import annotations

DEFAULT_FORMAT = "CODE128"

#: Formats the frontend is able to render.
SUPPORTED_FORMATS: frozenset[str] = frozenset(
    {
        "CODE128",
        "CODE39",
        "CODABAR",
        "EAN13",
        "EAN8",
        "UPC",
        "UPCE",
        "ITF",
        "ITF14",
        "MSI",
        "PHARMACODE",
        "QR",
        "DATAMATRIX",
        "PDF417",
        "AZTEC",
    }
)

#: Names reported by BarcodeDetector / ZXing mapped onto the names above.
_ALIASES: dict[str, str] = {
    "AZTEC": "AZTEC",
    "CODABAR": "CODABAR",
    "CODE_39": "CODE39",
    "CODE_93": "CODE39",
    "CODE_128": "CODE128",
    "DATA_MATRIX": "DATAMATRIX",
    "EAN_8": "EAN8",
    "EAN_13": "EAN13",
    "ITF": "ITF",
    "ITF_14": "ITF14",
    "PDF_417": "PDF417",
    "QR_CODE": "QR",
    "UPC_A": "UPC",
    "UPC_E": "UPCE",
    "UPC_EAN_EXTENSION": "EAN13",
}

#: Formats that carry a fixed number of digits including a trailing check digit.
_GTIN_LENGTHS: dict[str, int] = {
    "EAN8": 8,
    "EAN13": 13,
    "UPC": 12,
    "ITF14": 14,
}

#: Formats that may only contain digits.
_NUMERIC_ONLY: frozenset[str] = frozenset({"EAN8", "EAN13", "UPC", "UPCE", "ITF", "ITF14", "MSI"})


class CodeValidationError(ValueError):
    """Raised when a code does not fit the barcode format it claims to be."""


def normalize_format(value: str | None) -> str:
    """Return a supported format name for whatever the caller sent."""
    if not isinstance(value, str) or not value.strip():
        return DEFAULT_FORMAT

    candidate = value.strip().upper().replace("-", "_").replace(" ", "_")
    candidate = _ALIASES.get(candidate, candidate.replace("_", ""))

    if candidate in SUPPORTED_FORMATS:
        return candidate
    return DEFAULT_FORMAT


def gtin_check_digit(payload: str) -> int:
    """Return the mod-10 check digit for a GTIN payload (without check digit).

    Works for EAN-8, EAN-13, UPC-A and ITF-14 alike: weight the digits 3-1-3-1…
    starting from the right of the payload.
    """
    total = 0
    for index, char in enumerate(reversed(payload)):
        weight = 3 if index % 2 == 0 else 1
        total += int(char) * weight
    return (10 - total % 10) % 10


def validate_code(code: str, barcode_format: str) -> str:
    """Return the cleaned code, or raise :class:`CodeValidationError`.

    Validation happens on write rather than on render: a card with a broken
    check digit is rejected at the till, and finding that out while standing in
    the queue is the worst possible moment.
    """
    if not isinstance(code, str):
        raise CodeValidationError("code must be a string")

    cleaned = code.strip()
    if not cleaned:
        raise CodeValidationError("code must not be empty")

    if barcode_format in _NUMERIC_ONLY:
        cleaned = cleaned.replace(" ", "")
        if not cleaned.isdigit():
            raise CodeValidationError(f"{barcode_format} accepts digits only")

    expected_length = _GTIN_LENGTHS.get(barcode_format)
    if expected_length is not None:
        if len(cleaned) != expected_length:
            raise CodeValidationError(
                f"{barcode_format} needs exactly {expected_length} digits, got {len(cleaned)}"
            )
        if gtin_check_digit(cleaned[:-1]) != int(cleaned[-1]):
            raise CodeValidationError(f"{barcode_format} check digit does not match")

    if barcode_format == "ITF" and len(cleaned) % 2:
        raise CodeValidationError("ITF needs an even number of digits")

    return cleaned
