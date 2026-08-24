"""REST controllers for the CardWallet integration."""

from .item_view import CardWalletItemView
from .list_view import CardWalletListView

# Pre-2.0 names, kept so external imports do not break.
CardWalletListAPI = CardWalletListView
CardWalletItemAPI = CardWalletItemView

__all__ = [
    "CardWalletItemAPI",
    "CardWalletItemView",
    "CardWalletListAPI",
    "CardWalletListView",
]
