"""Tests for items inside a wishlist."""

import logging
from unittest import TestCase
from wsgi import app
from service.models import db, Wishlist, Item
from tests.factories import WishlistFactory


class TestItemRoutes(TestCase):
    """Check item responses and changes saved in the database."""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.logger.setLevel(logging.CRITICAL)
        cls.context = app.app_context()
        cls.context.push()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.context.pop()

    def setUp(self):
        self.client = app.test_client()
        db.session.query(Item).delete()
        db.session.query(Wishlist).delete()
        db.session.commit()
        self.wishlist = WishlistFactory()
        self.wishlist.create()
        self.url = f"/wishlists/{self.wishlist.id}/items"

    def tearDown(self):
        db.session.remove()

    def test_create_item(self):
        """It should create an item in the requested wishlist."""
        response = self.client.post(self.url, json={"product_id": 10, "note": "For later"})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data["wishlist_id"], self.wishlist.id)
        self.assertEqual(data["product_id"], 10)
        self.assertEqual(data["note"], "For later")
        self.assertEqual(response.headers["Location"], f"http://localhost{self.url}/{data['id']}")
        db.session.remove()
        self.assertEqual(Item.find(data["id"]).serialize(), data)

    def test_create_item_without_note(self):
        """It should allow an omitted or null note."""
        for data in ({"product_id": 10}, {"product_id": 11, "note": None}):
            with self.subTest(data=data):
                response = self.client.post(self.url, json=data)
                self.assertEqual(response.status_code, 201)
                self.assertIsNone(response.get_json()["note"])

    def test_create_item_ignores_body_ids(self):
        """It should use the URL parent and generate the item ID."""
        other = WishlistFactory()
        other.create()
        response = self.client.post(self.url, json={"id": -1, "wishlist_id": other.id, "product_id": 10})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertNotEqual(data["id"], -1)
        self.assertEqual(data["wishlist_id"], self.wishlist.id)
        db.session.expire_all()
        self.assertEqual(other.items, [])

    def test_create_item_missing_wishlist(self):
        """It should return JSON 404 when the parent does not exist."""
        response = self.client.post("/wishlists/0/items", json={"product_id": 10})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Wishlist", response.get_json()["message"])
        self.assertEqual(Item.all(), [])

    def test_create_item_bad_data(self):
        """It should reject invalid data without saving an item."""
        for data in ({}, [], "bad", {"product_id": True}, {"product_id": "10"},
                     {"product_id": None}, {"product_id": 1.5}, {"product_id": 10, "note": 123}):
            with self.subTest(data=data):
                response = self.client.post(self.url, json=data)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)
                self.assertEqual(Item.all(), [])

    def test_create_item_bad_json(self):
        """It should reject malformed or null JSON."""
        for body in ('{"product_id":', 'null'):
            with self.subTest(body=body):
                response = self.client.post(self.url, data=body, content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)

    def test_create_item_content_type(self):
        """It should require JSON and accept a charset parameter."""
        for content_type in (None, "text/plain"):
            with self.subTest(content_type=content_type):
                response = self.client.post(self.url, data='{"product_id":10}', content_type=content_type)
                self.assertEqual(response.status_code, 415)
                self.assertTrue(response.is_json)
        response = self.client.post(self.url, data='{"product_id":10}',
                                    content_type="application/json; charset=utf-8")
        self.assertEqual(response.status_code, 201)
