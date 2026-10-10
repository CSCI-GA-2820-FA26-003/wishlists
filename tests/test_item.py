######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Test cases for Item Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.models import Wishlist, Item, DataValidationError, db
from .factories import WishlistFactory, ItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  I T E M   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestItem(TestCase):
    """Test Cases for Item Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Item).delete()  # clean up the last tests
        db.session.query(Wishlist).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  H A P P Y   P A T H S
    ######################################################################

    def test_add_an_item_to_a_wishlist(self):
        """It should Create a Wishlist with an Item and add it to the database"""
        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.create()
        # Assert that both were assigned ids and the item points at the wishlist
        self.assertIsNotNone(wishlist.id)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.wishlist_id, wishlist.id)
        self.assertEqual(len(Item.all()), 1)

        found = Wishlist.find(wishlist.id)
        self.assertEqual(len(found.items), 1)
        self.assertEqual(found.items[0].product_id, item.product_id)
        self.assertEqual(found.items[0].note, item.note)

        # Add a second item through the relationship, the way a route would.
        # Note: only ItemFactory(wishlist=wishlist) is NOT enough once the
        # wishlist is saved, SQLAlchemy 2 does not cascade along a backref.
        item2 = ItemFactory(wishlist=None)
        wishlist.items.append(item2)
        wishlist.update()
        found = Wishlist.find(wishlist.id)
        self.assertEqual(len(found.items), 2)
        self.assertEqual({i.product_id for i in found.items}, {item.product_id, item2.product_id})

    def test_find_an_item(self):
        """It should Find an Item by its id"""
        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.create()
        found = Item.find(item.id)
        self.assertEqual(found.id, item.id)
        self.assertEqual(found.product_id, item.product_id)
        self.assertEqual(found.wishlist_id, wishlist.id)
        self.assertIsNone(Item.find(item.id + 1))

    def test_update_a_wishlist_item(self):
        """It should Update an Item in a Wishlist"""
        wishlist = WishlistFactory()
        ItemFactory(wishlist=wishlist)
        wishlist.create()
        # Fetch it back and change the note
        found = Wishlist.find(wishlist.id)
        old_item = found.items[0]
        old_item.note = "XX"
        found.update()
        # Fetch it back again
        found = Wishlist.find(wishlist.id)
        self.assertEqual(found.items[0].note, "XX")

    def test_delete_a_wishlist_item(self):
        """It should Delete an Item from a Wishlist"""
        wishlist = WishlistFactory()
        ItemFactory(wishlist=wishlist)
        wishlist.create()
        found = Wishlist.find(wishlist.id)
        self.assertEqual(len(found.items), 1)
        found.items[0].delete()
        # Fetch it back again
        found = Wishlist.find(wishlist.id)
        self.assertEqual(found.items, [])
        self.assertEqual(Item.all(), [])

    def test_serialize_an_item(self):
        """It should Serialize an Item"""
        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.create()
        data = item.serialize()
        self.assertEqual(data["id"], item.id)
        self.assertEqual(data["wishlist_id"], wishlist.id)
        self.assertEqual(data["product_id"], item.product_id)
        self.assertEqual(data["note"], item.note)
        self.assertIn("Item", repr(item))

    def test_deserialize_an_item(self):
        """It should Deserialize an Item"""
        item = ItemFactory()
        item.create()
        new_item = Item()
        new_item.deserialize(item.serialize())
        self.assertEqual(new_item.product_id, item.product_id)
        self.assertEqual(new_item.note, item.note)
        # id and wishlist_id are never read from the data
        self.assertIsNone(new_item.id)
        self.assertIsNone(new_item.wishlist_id)

    def test_deserialize_an_item_without_note(self):
        """It should Deserialize an Item with no note"""
        item = Item()
        item.deserialize({"product_id": 456})
        self.assertEqual(item.product_id, 456)
        self.assertIsNone(item.note)

    ######################################################################
    #  S A D   P A T H S
    ######################################################################

    def test_deserialize_missing_product_id(self):
        """It should not Deserialize an Item with no product_id"""
        item = Item()
        self.assertRaises(DataValidationError, item.deserialize, {"note": "no product"})

    def test_deserialize_bad_product_id(self):
        """It should not Deserialize an Item with a non-integer product_id"""
        item = Item()
        for bad_id in ["456", 4.5, True, None]:
            self.assertRaises(DataValidationError, item.deserialize, {"product_id": bad_id})

    def test_deserialize_bad_note(self):
        """It should not Deserialize an Item with a non-string note"""
        item = Item()
        self.assertRaises(DataValidationError, item.deserialize, {"product_id": 456, "note": 123})

    def test_deserialize_bad_data(self):
        """It should not Deserialize bad data"""
        item = Item()
        for bad_data in [None, [], "string", 42]:
            self.assertRaises(DataValidationError, item.deserialize, bad_data)

    def test_create_an_item_without_a_wishlist(self):
        """It should not Create an Item that has no Wishlist"""
        item = Item()
        item.deserialize({"product_id": 456})
        self.assertRaises(DataValidationError, item.create)
        self.assertEqual(Item.all(), [])
