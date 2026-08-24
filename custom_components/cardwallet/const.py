"""Constants for the CardWallet integration."""

DOMAIN = "cardwallet"

# Storage
STORAGE_KEY = f"{DOMAIN}.cards"
STORAGE_VERSION = 2
LEGACY_FILENAME = "cardwallet_cards.json"

# hass.data keys
DATA_STORE = "store"
DATA_ENTRY = "entry"
DATA_REGISTERED = "registered"

# Options
CONF_ALLOW_SHARING = "allow_sharing"
DEFAULT_ALLOW_SHARING = True

# Limits
MAX_NAME_LENGTH = 80
MAX_CODE_LENGTH = 512
MAX_CARDS_PER_USER = 200
