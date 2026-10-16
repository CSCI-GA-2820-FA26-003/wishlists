"""
Test Factory to make fake objects for testing
"""

import factory
from service.models import Wishlist, Item


class WishlistFactory(factory.Factory):
    """Creates fake Wishlists"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Wishlist

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("word")
    customer_id = factory.Sequence(lambda n: n + 1)


class ItemFactory(factory.Factory):
    """Creates fake Items that belong to a Wishlist

    Pass the parent in with ItemFactory(wishlist=wishlist) so the Item is
    saved together with its Wishlist when wishlist.create() is called.
    The id is left to the database so it never collides with a generated one.
    """

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Item

    product_id = factory.Sequence(lambda n: n + 100)
    note = factory.Faker("sentence")
    wishlist = factory.SubFactory(WishlistFactory)
