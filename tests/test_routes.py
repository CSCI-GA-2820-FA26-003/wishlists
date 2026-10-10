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
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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
