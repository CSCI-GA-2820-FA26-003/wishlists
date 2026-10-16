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
TestYourResourceModel API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Wishlist
from .factories import WishlistFactory, ItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Wishlist).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # read a wishlist

    def test_get_wishlist(self):
        """It should Read a single Wishlist with its Items"""
        wishlist = WishlistFactory()
        item = ItemFactory(wishlist=wishlist)
        wishlist.create()
        resp = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], wishlist.id)
        self.assertEqual(data["name"], wishlist.name)
        self.assertEqual(data["customer_id"], wishlist.customer_id)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["product_id"], item.product_id)

    def test_get_wishlist_not_found(self):
        """It should not Read a Wishlist that does not exist"""
        resp = self.client.get("/wishlists/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("was not found", data["message"])

    # update a wishlist

    def test_update_wishlist(self):
        """It should Update an existing Wishlist"""
        wishlist = WishlistFactory(name="Birthdays")
        wishlist.create()
        new_data = {"name": "2026 Birthday Wishlist", "customer_id": 123}
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=new_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], wishlist.id)
        self.assertEqual(data["name"], "2026 Birthday Wishlist")
        self.assertEqual(data["customer_id"], 123)
        resp = self.client.get(f"/wishlists/{wishlist.id}")
        self.assertEqual(resp.get_json()["name"], "2026 Birthday Wishlist")

    def test_update_wishlist_keeps_url_id(self):
        """It should ignore an id in the body when Updating a Wishlist"""
        wishlist = WishlistFactory()
        wishlist.create()
        new_data = {"id": wishlist.id + 1000, "name": "renamed", "customer_id": 1}
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=new_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["id"], wishlist.id)

    def test_update_wishlist_does_not_duplicate_items(self):
        """It should not add Items again when Updating a Wishlist"""
        wishlist = WishlistFactory()
        ItemFactory(wishlist=wishlist)
        wishlist.create()
        new_data = wishlist.serialize()
        new_data["name"] = "renamed"
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=new_data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], "renamed")
        self.assertEqual(len(data["items"]), 1)

    def test_update_wishlist_not_found(self):
        """It should not Update a Wishlist that does not exist"""
        new_data = {"name": "nothing", "customer_id": 1}
        resp = self.client.put("/wishlists/0", json=new_data)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_wishlist_missing_name(self):
        """It should not Update a Wishlist without a name"""
        wishlist = WishlistFactory()
        wishlist.create()
        resp = self.client.put(f"/wishlists/{wishlist.id}", json={"customer_id": 1})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_wishlist_bad_customer_id(self):
        """It should not Update a Wishlist with a bad customer_id"""
        wishlist = WishlistFactory()
        wishlist.create()
        new_data = {"name": "renamed", "customer_id": "abc"}
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=new_data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_wishlist_not_a_dict(self):
        """It should not Update a Wishlist when the body is not an object"""
        wishlist = WishlistFactory()
        wishlist.create()
        resp = self.client.put(f"/wishlists/{wishlist.id}", json=["renamed", 1])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_wishlist_unsupported_media_type(self):
        """It should not Update a Wishlist with the wrong Content-Type"""
        wishlist = WishlistFactory()
        wishlist.create()
        resp = self.client.put(
            f"/wishlists/{wishlist.id}", data="hello", content_type="text/plain"
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
