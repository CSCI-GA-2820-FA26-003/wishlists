"""
Models for the Wishlists service

All of the models are stored in this package
"""

from .persistent_base import db, DataValidationError
from .item import Item
from .wishlist import Wishlist
