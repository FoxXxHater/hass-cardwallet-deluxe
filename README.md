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
[CardWallet Deluxe card](https://github.com/FoxXxHater/lovelace-cardwallet-deluxe).
The integration keeps the cards; the card draws them.

Domain: `cardwallet_deluxe`. It can be installed alongside the original
CardWallet — nothing is shared between the two.

## 📦 Installation

### HACS

- HACS → Integrations → ⋮ → Custom repositories
- `https://github.com/FoxXxHater/hass-cardwallet-deluxe`, category **Integration**
- Install and restart Home Assistant.

### Manual

Copy `custom_components/cardwallet_deluxe` into `config/custom_components` and
restart.

## ⚙️ Setup

**Settings → Devices & Services → Add Integration → CardWallet Deluxe.**

No YAML. The single option, *allow sharing*, decides whether cards marked as
shared are visible to the other users of this instance; it can be changed later
under **Configure**.

## 🔄 Coming from CardWallet 1.x or 2.0

On first start the integration looks for existing data and imports it once:

1. `.storage/cardwallet.cards` — CardWallet 2.0 under the old domain
2. `cardwallet_cards.json` in the config directory — CardWallet 1.x

Neither is deleted, so the old integration keeps working if it is still
installed. Remove it once the cards show up here, otherwise both are in the
config directory doing the same job.

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
| `cardwallet_deluxe/list` | – | `{ "cards": [...] }` |
| `cardwallet_deluxe/add` | `name`, `code`, `format?`, `color?`, `shared?`, `notes?` | the created card |
| `cardwallet_deluxe/update` | `card_id`, plus any field above | the updated card |
| `cardwallet_deluxe/delete` | `card_id` | `{ "card_id": "…" }` |
| `cardwallet_deluxe/subscribe` | – | an event whenever any card changes |

## 📚 REST API

- `GET /api/cardwallet_deluxe` – cards visible to the authenticated user
- `POST /api/cardwallet_deluxe` – create a card
- `PUT /api/cardwallet_deluxe/{card_id}` – update an owned card
- `DELETE /api/cardwallet_deluxe/{card_id}` – delete an owned card

`user_id` in a request body is ignored; the authenticated user always wins.

## 🏷️ Card format

`format` follows JsBarcode naming (`CODE128`, `EAN13`, `EAN8`, `UPC`, `ITF14`,
`QR`, …). Scanner names such as `ean_13` or `qr_code` are normalised on the way
in, so a value straight from `BarcodeDetector` can be passed through unchanged —
that is how the card decides barcode or QR when you scan one.

Codes are validated when they are stored, not when they are rendered: `EAN13`,
`EAN8`, `UPC` and `ITF14` must carry a correct mod-10 check digit. A card that
would be rejected at the till is rejected here instead.

## 💾 Storage

Cards live in `.storage/cardwallet_deluxe.cards`, written atomically with
restrictive permissions, and are therefore part of a normal backup.

> Card numbers are stored in plain text, as is every other integration's data.
> That is fine for loyalty cards; do not put anything with a payment function
> in here.

---

Fork of [rozgonyiadam/hass-cardwallet](https://github.com/rozgonyiadam/hass-cardwallet).
