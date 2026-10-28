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
Test cases for Wishlist Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.models import Wishlist, Item, DataValidationError, db
from .factories import WishlistFactory, ItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  W I S H L I S T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestWishlist(TestCase):
    """Test Cases for Wishlist Model"""

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

    def test_create_a_wishlist(self):
        """It should Create a Wishlist and add it to the database"""
        self.assertEqual(Wishlist.all(), [])
        wishlist = WishlistFactory()
        wishlist.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(wishlist.id)
        self.assertEqual(len(Wishlist.all()), 1)
        found = Wishlist.find(wishlist.id)
        self.assertEqual(found.name, wishlist.name)
        self.assertEqual(found.customer_id, wishlist.customer_id)
        self.assertEqual(found.items, [])
        self.assertEqual(repr(wishlist), f"<Wishlist {wishlist.name} id=[{wishlist.id}]>")

    def test_find_a_wishlist_not_found(self):
        """It should return None when a Wishlist id does not exist"""
        wishlist = WishlistFactory()
        wishlist.create()
        self.assertIsNone(Wishlist.find(wishlist.id + 1))

    def test_list_all_wishlists(self):
        """It should List all Wishlists in the database"""
        self.assertEqual(Wishlist.all(), [])
        for _ in range(5):
            WishlistFactory().create()
        self.assertEqual(len(Wishlist.all()), 5)

    def test_update_a_wishlist(self):
        """It should Update a Wishlist"""
        wishlist = WishlistFactory()
        wishlist.create()
        self.assertIsNotNone(wishlist.id)
        wishlist.name = "Updated name"
        wishlist.update()
        # Fetch it back and make sure the change stuck and nothing was duplicated
        found = Wishlist.find(wishlist.id)
        self.assertEqual(found.name, "Updated name")
        self.assertEqual(len(Wishlist.all()), 1)

    def test_delete_a_wishlist(self):
        """It should Delete a Wishlist"""
        wishlist = WishlistFactory()
        wishlist.create()
        self.assertEqual(len(Wishlist.all()), 1)
        wishlist.delete()
        self.assertEqual(Wishlist.all(), [])

    def test_delete_a_wishlist_deletes_its_items(self):
        """It should Delete the Items when their Wishlist is deleted"""
        wishlist = WishlistFactory()
        ItemFactory(wishlist=wishlist)
        ItemFactory(wishlist=wishlist)
        wishlist.create()
        self.assertEqual(len(Item.all()), 2)
        wishlist.delete()
        self.assertEqual(Wishlist.all(), [])
        self.assertEqual(Item.all(), [])

    def test_serialize_a_wishlist(self):
        """It should Serialize a Wishlist with its Items"""
        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.create()
        data = wishlist.serialize()
        self.assertEqual(data["id"], wishlist.id)
        self.assertEqual(data["name"], wishlist.name)
        self.assertEqual(data["customer_id"], wishlist.customer_id)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["id"], item.id)
        self.assertEqual(data["items"][0]["wishlist_id"], wishlist.id)
        self.assertEqual(data["items"][0]["product_id"], item.product_id)
        self.assertEqual(data["items"][0]["note"], item.note)

    def test_deserialize_a_wishlist(self):
        """It should Deserialize a Wishlist without items"""
        wishlist = Wishlist()
        wishlist.deserialize({"name": "Birthday", "customer_id": 123})
        self.assertEqual(wishlist.name, "Birthday")
        self.assertEqual(wishlist.customer_id, 123)
        self.assertEqual(wishlist.items, [])

    def test_deserialize_a_wishlist_with_items(self):
        """It should Deserialize a Wishlist with nested items"""
        data = {
            "name": "Birthday",
            "customer_id": 123,
            "items": [
                {"product_id": 456, "note": "red one"},
                {"product_id": 789},
            ],
        }
        wishlist = Wishlist()
        wishlist.deserialize(data)
        self.assertEqual(len(wishlist.items), 2)
        self.assertEqual(wishlist.items[0].product_id, 456)
        self.assertEqual(wishlist.items[0].note, "red one")
        self.assertEqual(wishlist.items[1].product_id, 789)
        self.assertIsNone(wishlist.items[1].note)

    def test_deserialize_ignores_id(self):
        """It should not read the id from the data"""
        wishlist = Wishlist()
        wishlist.deserialize({"id": 999, "name": "Birthday", "customer_id": 123})
        self.assertIsNone(wishlist.id)

    def test_find_by_customer(self):
        """It should Find Wishlists by customer_id ordered by id"""
        first = WishlistFactory(customer_id=1)
        first.create()
        other = WishlistFactory(customer_id=2)
        other.create()
        second = WishlistFactory(customer_id=1)
        second.create()
        found = Wishlist.find_by_customer(1)
        self.assertEqual([wishlist.id for wishlist in found], [first.id, second.id])
        for wishlist in found:
            self.assertEqual(wishlist.customer_id, 1)
        self.assertEqual([wishlist.id for wishlist in Wishlist.find_by_customer(2)], [other.id])

    def test_find_by_customer_not_found(self):
        """It should return an empty list when a customer has no Wishlists"""
        WishlistFactory(customer_id=1).create()
        self.assertEqual(Wishlist.find_by_customer(99), [])

    def test_find_by_name(self):
        """It should Find every Wishlist with a name, across customers"""
        first = WishlistFactory(name="Birthday", customer_id=1)
        first.create()
        WishlistFactory(name="Holiday", customer_id=1).create()
        second = WishlistFactory(name="Birthday", customer_id=2)
        second.create()
        found = Wishlist.find_by_name("Birthday")
        self.assertEqual([wishlist.id for wishlist in found], [first.id, second.id])
        for wishlist in found:
            self.assertEqual(wishlist.name, "Birthday")

    def test_find_by_name_not_found(self):
        """It should return an empty list when no Wishlist has that name"""
        WishlistFactory(name="Birthday").create()
        self.assertEqual(Wishlist.find_by_name("Nothing"), [])
        self.assertEqual(Wishlist.find_by_name("birthday"), [])

    ######################################################################
    #  S A D   P A T H S
    ######################################################################

    def test_deserialize_missing_name(self):
        """It should not Deserialize a Wishlist with no name"""
        wishlist = Wishlist()
        self.assertRaises(DataValidationError, wishlist.deserialize, {"customer_id": 123})

    def test_deserialize_missing_customer_id(self):
        """It should not Deserialize a Wishlist with no customer_id"""
        wishlist = Wishlist()
        self.assertRaises(DataValidationError, wishlist.deserialize, {"name": "Birthday"})

    def test_deserialize_bad_name(self):
        """It should not Deserialize a Wishlist with an empty or non-string name"""
        wishlist = Wishlist()
        for bad_name in [123, "", "   ", None]:
            data = {"name": bad_name, "customer_id": 123}
            self.assertRaises(DataValidationError, wishlist.deserialize, data)

    def test_deserialize_bad_customer_id(self):
        """It should not Deserialize a Wishlist with a non-integer customer_id"""
        wishlist = Wishlist()
        for bad_id in ["123", 12.5, True, None]:
            data = {"name": "Birthday", "customer_id": bad_id}
            self.assertRaises(DataValidationError, wishlist.deserialize, data)

    def test_deserialize_bad_items(self):
        """It should not Deserialize a Wishlist with bad items"""
        wishlist = Wishlist()
        data = {"name": "Birthday", "customer_id": 123, "items": "not a list"}
        self.assertRaises(DataValidationError, wishlist.deserialize, data)
        data = {"name": "Birthday", "customer_id": 123, "items": [{"note": "no product"}]}
        self.assertRaises(DataValidationError, wishlist.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not Deserialize bad data"""
        wishlist = Wishlist()
        for bad_data in [None, [], "string", 42]:
            self.assertRaises(DataValidationError, wishlist.deserialize, bad_data)

    def test_update_with_no_id(self):
        """It should not Update a Wishlist with no id"""
        wishlist = WishlistFactory()
        wishlist.id = None
        self.assertRaises(DataValidationError, wishlist.update)

    def test_create_database_error(self):
        """It should raise DataValidationError when the database fails on create"""
        wishlist = WishlistFactory()
        with patch.object(db.session, "commit", side_effect=Exception("db is down")):
            self.assertRaises(DataValidationError, wishlist.create)

    def test_update_database_error(self):
        """It should raise DataValidationError when the database fails on update"""
        wishlist = WishlistFactory()
        wishlist.create()
        with patch.object(db.session, "commit", side_effect=Exception("db is down")):
            self.assertRaises(DataValidationError, wishlist.update)

    def test_delete_database_error(self):
        """It should raise DataValidationError when the database fails on delete"""
        wishlist = WishlistFactory()
        wishlist.create()
        with patch.object(db.session, "commit", side_effect=Exception("db is down")):
            self.assertRaises(DataValidationError, wishlist.delete)
