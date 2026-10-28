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
Wishlist API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Wishlist, Item
from .factories import WishlistFactory, ItemFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestWishlistService(TestCase):
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
        db.session.query(Item).delete()
        db.session.query(Wishlist).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should return service information from the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.content_type, "application/json")
        data = resp.get_json()
        self.assertEqual(data["name"], "Wishlists Service")
        self.assertEqual(data["version"], app.config["VERSION"])
        self.assertEqual(data["list_url"], "/wishlists")

    def test_create_wishlist(self):
        """It should save a new empty wishlist."""
        data = {"name": "Birthday", "customer_id": 123}

        response = self.client.post("/wishlists", json=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.is_json)
        wishlist = response.get_json()
        self.assertIsInstance(wishlist["id"], int)
        self.assertEqual(wishlist["name"], data["name"])
        self.assertEqual(wishlist["customer_id"], data["customer_id"])
        self.assertEqual(wishlist["items"], [])
        self.assertEqual(
            response.headers["Location"],
            f"http://localhost/wishlists/{wishlist['id']}",
        )

        db.session.expire_all()
        saved = Wishlist.find(wishlist["id"])
        self.assertIsNotNone(saved)
        self.assertEqual(saved.name, data["name"])
        self.assertEqual(saved.customer_id, data["customer_id"])
        self.assertEqual(list(saved.items), [])
        self.assertEqual(len(Wishlist.all()), 1)

    def test_create_wishlist_with_empty_items(self):
        """It should accept an explicitly empty item list."""
        data = {"name": "Birthday", "customer_id": 123, "items": []}

        response = self.client.post("/wishlists", json=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.get_json()["items"], [])
        saved = Wishlist.find(response.get_json()["id"])
        self.assertEqual(list(saved.items), [])

    def test_create_wishlists_with_duplicate_names(self):
        """It should allow a customer to create wishlists with the same name."""
        data = {"name": "Birthday", "customer_id": 123}

        first = self.client.post("/wishlists", json=data)
        second = self.client.post("/wishlists", json=data)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first.get_json()["id"], second.get_json()["id"])
        self.assertEqual(len(Wishlist.all()), 2)

    def test_create_wishlist_ignores_submitted_id(self):
        """It should use a database-generated ID."""
        data = {"id": -1, "name": "Birthday", "customer_id": 123}

        response = self.client.post("/wishlists", json=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(response.get_json()["id"], 0)
        self.assertIsNotNone(Wishlist.find(response.get_json()["id"]))

    def test_create_wishlist_missing_name(self):
        """It should reject a wishlist without a name."""
        response = self.client.post("/wishlists", json={"customer_id": 123})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)
        self.assertTrue(response.get_json()["message"])
        self.assertEqual(len(Wishlist.all()), 0)

    def test_create_wishlist_invalid_name(self):
        """It should reject empty, whitespace-only, and non-string names."""
        for name in ("", " \t\n", 123, None):
            with self.subTest(name=name):
                response = self.client.post(
                    "/wishlists", json={"name": name, "customer_id": 123}
                )

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertTrue(response.is_json)
                self.assertTrue(response.get_json()["message"])
                self.assertEqual(len(Wishlist.all()), 0)

    def test_create_wishlist_name_length(self):
        """It should accept a 63 character name and reject a 64 character one."""
        response = self.client.post(
            "/wishlists", json={"name": "x" * 63, "customer_id": 123}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.get_json()["name"], "x" * 63)

        response = self.client.post(
            "/wishlists", json={"name": "x" * 64, "customer_id": 123}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)
        self.assertIn("63", response.get_json()["message"])
        self.assertEqual(len(Wishlist.all()), 1)

    def test_create_wishlist_missing_customer_id(self):
        """It should reject a wishlist without a customer ID."""
        response = self.client.post("/wishlists", json={"name": "Birthday"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)
        self.assertTrue(response.get_json()["message"])
        self.assertEqual(len(Wishlist.all()), 0)

    def test_create_wishlist_invalid_customer_id(self):
        """It should reject a customer ID that is not an integer."""
        response = self.client.post(
            "/wishlists", json={"name": "Birthday", "customer_id": "abc"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)
        self.assertTrue(response.get_json()["message"])
        self.assertEqual(len(Wishlist.all()), 0)

    def test_create_wishlist_unsupported_media_type(self):
        """It should reject plain text without saving a wishlist."""
        response = self.client.post(
            "/wishlists", data="not json", content_type="text/plain"
        )

        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertTrue(response.is_json)
        self.assertTrue(response.get_json()["message"])
        self.assertEqual(len(Wishlist.all()), 0)

    def test_create_wishlist_with_items(self):
        """It should reject items when creating a wishlist."""
        data = {"name": "Birthday", "customer_id": 123, "items": [{"product_id": 1}]}

        response = self.client.post("/wishlists", json=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)
        self.assertTrue(response.get_json()["message"])
        self.assertEqual(len(Wishlist.all()), 0)

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

    def test_update_wishlist_name_length(self):
        """It should accept a 63 character name and reject a 64 character one."""
        wishlist = WishlistFactory(name="Birthday")
        wishlist.create()
        url = f"/wishlists/{wishlist.id}"

        resp = self.client.put(url, json={"name": "x" * 64, "customer_id": 1})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(resp.is_json)
        self.assertEqual(self.client.get(url).get_json()["name"], "Birthday")

        resp = self.client.put(url, json={"name": "x" * 63, "customer_id": 1})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(url).get_json()["name"], "x" * 63)

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

    def test_delete_wishlist(self):
        """It should delete only the requested wishlist and return no content"""
        wishlist = WishlistFactory()
        wishlist.create()
        other = WishlistFactory()
        other.create()
        wishlist_id = wishlist.id
        other_id = other.id

        resp = self.client.delete(f"/wishlists/{wishlist_id}")

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp.data, b"")
        db.session.remove()
        self.assertIsNone(Wishlist.find(wishlist_id))
        self.assertIsNotNone(Wishlist.find(other_id))

    def test_delete_wishlist_not_found(self):
        """It should return no content when the wishlist does not exist"""
        self.assertIsNone(Wishlist.find(1))

        resp = self.client.delete("/wishlists/1")

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(resp.data, b"")

    def test_list_wishlists(self):
        """It should return all wishlists as a JSON array"""
        wishlists = WishlistFactory.create_batch(3)
        for wishlist in wishlists:
            wishlist.create()

        resp = self.client.get("/wishlists")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.mimetype, "application/json")
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertCountEqual(data, [wishlist.serialize() for wishlist in wishlists])

    def test_list_wishlists_empty(self):
        """It should return an empty JSON array when no wishlists exist"""
        resp = self.client.get("/wishlists")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.mimetype, "application/json")
        self.assertEqual(resp.get_json(), [])
