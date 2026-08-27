<p align="center">
  <img src="assets/logo.png" alt="CardWallet Deluxe" width="320">
</p>

<h1 align="center">CardWallet Deluxe</h1>

<p align="center">
  Loyalty and membership cards in Home Assistant — stored per user, shown as a
  scannable barcode or QR code.
</p>

---

Backend for the
[CardWallet card](https://github.com/<user>/lovelace-cardwallet-deluxe).
The integration keeps the cards; the card draws them.

## 📦 Installation

### HACS

- HACS → Integrations → ⋮ → Custom repositories
- `https://github.com/<user>/hass-cardwallet-deluxe`, category **Integration**
- Install and restart Home Assistant.

### Manual

Copy `custom_components/cardwallet` into `config/custom_components` and restart.

## ⚙️ Setup

**Settings → Devices & Services → Add Integration → CardWallet.**

No YAML. The single option, *allow sharing*, decides whether cards marked as
shared are visible to the other users of this instance; it can be changed later
under **Configure**.

Installations that still use a `cardwallet:` block in `configuration.yaml` are
imported into the UI on the next restart — the block can then be deleted.

## 🔐 Ownership

A card belongs to the Home Assistant user who created it. The owner is taken
from the authenticated request and can never be set by the client. Cards are
readable by their owner, plus by everyone if the card is marked `shared` and
sharing is enabled. Only the owner can change or delete a card.

## 🔌 WebSocket API

Preferred for frontend cards: the connection is already authenticated, and
clients can subscribe to changes instead of polling.

| Command | Payload | Returns |
| --- | --- | --- |
| `cardwallet/list` | – | `{ "cards": [...] }` |
| `cardwallet/add` | `name`, `code`, `format?`, `color?`, `shared?`, `notes?` | the created card |
| `cardwallet/update` | `card_id`, plus any field above | the updated card |
| `cardwallet/delete` | `card_id` | `{ "card_id": "…" }` |
| `cardwallet/subscribe` | – | an event whenever any card changes |

## 📚 REST API

- `GET /api/cardwallet` – cards visible to the authenticated user
- `POST /api/cardwallet` – create a card
- `PUT /api/cardwallet/{card_id}` – update an owned card
- `DELETE /api/cardwallet/{card_id}` – delete an owned card

`user_id` in a request body is ignored; the authenticated user always wins.

## 🏷️ Card format

`format` follows JsBarcode naming (`CODE128`, `EAN13`, `EAN8`, `UPC`, `ITF14`,
`QR`, …). Scanner names such as `ean_13` or `qr_code` are normalised on the way
in, so a value straight from `BarcodeDetector` or ZXing can be passed through
unchanged.

Codes are validated when they are stored, not when they are rendered: `EAN13`,
`EAN8`, `UPC` and `ITF14` must carry a correct mod-10 check digit. A card that
would be rejected at the till is rejected here instead.

## 💾 Storage

Cards live in Home Assistant's own storage (`.storage/cardwallet.cards`,
written atomically with restrictive permissions) and are therefore part of a
normal backup. A pre-2.0 `cardwallet_cards.json` in the config directory is
imported once on first start and renamed to `.migrated`.

> Card numbers are stored in plain text, as is every other integration's data.
> That is fine for loyalty cards; do not put anything with a payment function
> in here.

## 🎨 Branding

The icon shown in Home Assistant comes from the
[home-assistant/brands](https://github.com/home-assistant/brands) repository —
see `brands/HOWTO.md` in this repo for the files and the submission steps.

---

Fork of [rozgonyiadam/hass-cardwallet](https://github.com/rozgonyiadam/hass-cardwallet).
