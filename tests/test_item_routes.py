"""Tests for items inside a wishlist."""

import logging
from unittest import TestCase
from wsgi import app
from service.models import db, Wishlist, Item
from tests.factories import WishlistFactory, ItemFactory


class TestItemRoutes(TestCase):  # pylint: disable=too-many-public-methods
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
        response = self.client.post(
            self.url, json={"product_id": 10, "note": "For later"}
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data["wishlist_id"], self.wishlist.id)
        self.assertEqual(data["product_id"], 10)
        self.assertEqual(data["note"], "For later")
        self.assertEqual(
            response.headers["Location"], f"http://localhost{self.url}/{data['id']}"
        )
        db.session.remove()
        self.assertEqual(Item.find(data["id"]).serialize(), data)

    def test_read_item(self):
        """It should read an item through its parent wishlist."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        response = self.client.get(f"{self.url}/{item.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), item.serialize())

    def test_read_item_missing(self):
        """It should return JSON 404 for a missing item or parent."""
        for url in (f"{self.url}/0", "/wishlists/0/items/0"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertTrue(response.is_json)

    def test_read_item_wrong_wishlist(self):
        """It should not return another wishlist's item."""
        other = WishlistFactory()
        other.create()
        item = ItemFactory(wishlist=other)
        item.create()
        response = self.client.get(f"{self.url}/{item.id}")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)

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
        response = self.client.post(
            self.url, json={"id": -1, "wishlist_id": other.id, "product_id": 10}
        )
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
        for data in (
            {},
            [],
            "bad",
            {"product_id": True},
            {"product_id": "10"},
            {"product_id": None},
            {"product_id": 1.5},
            {"product_id": 10, "note": 123},
        ):
            with self.subTest(data=data):
                response = self.client.post(self.url, json=data)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)
                self.assertEqual(Item.all(), [])

    def test_create_item_bad_json(self):
        """It should reject malformed or null JSON."""
        for body in ('{"product_id":', "null"):
            with self.subTest(body=body):
                response = self.client.post(
                    self.url, data=body, content_type="application/json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)

    def test_create_item_content_type(self):
        """It should require JSON and accept a charset parameter."""
        for content_type in (None, "text/plain"):
            with self.subTest(content_type=content_type):
                response = self.client.post(
                    self.url, data='{"product_id":10}', content_type=content_type
                )
                self.assertEqual(response.status_code, 415)
                self.assertTrue(response.is_json)
        response = self.client.post(
            self.url,
            data='{"product_id":10}',
            content_type="application/json; charset=utf-8",
        )
        self.assertEqual(response.status_code, 201)

    def test_list_items(self):
        """It should list only the requested wishlist's items."""
        items = []
        for _ in range(2):
            item = ItemFactory(wishlist=self.wishlist)
            item.create()
            items.append(item)
        other = WishlistFactory()
        other.create()
        ItemFactory(wishlist=other).create()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.get_json(), [item.serialize() for item in items])

    def test_list_items_empty(self):
        """It should return an empty list for an empty wishlist."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_list_items_missing_wishlist(self):
        """It should distinguish a missing wishlist from an empty one."""
        response = self.client.get("/wishlists/0/items")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Wishlist", response.get_json()["message"])

    def test_update_item(self):
        """It should save product_id and note without changing either ID."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        item_id = item.id
        parent_id = self.wishlist.id
        response = self.client.put(
            f"{self.url}/{item_id}",
            json={
                "product_id": 50,
                "note": "Updated",
                "id": -1,
                "wishlist_id": -1,
            },
        )
        self.assertEqual(response.status_code, 200)
        expected = {
            "id": item_id,
            "wishlist_id": parent_id,
            "product_id": 50,
            "note": "Updated",
            "purchased": False,
        }
        self.assertEqual(response.get_json(), expected)
        db.session.remove()
        self.assertEqual(Item.find(item_id).serialize(), expected)
        self.assertEqual(len(Item.all()), 1)

    def test_create_item_ignores_purchased(self):
        """It should ignore purchased in the body and create an unpurchased item."""
        response = self.client.post(
            self.url, json={"product_id": 10, "purchased": True}
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertFalse(data["purchased"])
        db.session.remove()
        self.assertFalse(Item.find(data["id"]).purchased)

    def test_update_item_keeps_purchased(self):
        """It should keep purchased when an item is updated."""
        item = ItemFactory(wishlist=self.wishlist, purchased=True)
        item.create()
        body = {"product_id": 20, "note": "Updated", "purchased": False}
        response = self.client.put(f"{self.url}/{item.id}", json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["product_id"], 20)
        self.assertTrue(response.get_json()["purchased"])
        db.session.remove()
        self.assertTrue(Item.find(item.id).purchased)

    def test_update_item_without_note(self):
        """It should clear the optional note on a full replacement."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        response = self.client.put(f"{self.url}/{item.id}", json={"product_id": 20})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["note"])

    def test_update_item_missing(self):
        """It should return JSON 404 for a missing item or parent."""
        for url in (f"{self.url}/0", "/wishlists/0/items/0"):
            with self.subTest(url=url):
                response = self.client.put(url, json={"product_id": 20})
                self.assertEqual(response.status_code, 404)
                self.assertTrue(response.is_json)

    def test_update_item_wrong_wishlist(self):
        """It should leave another wishlist's item unchanged."""
        other = WishlistFactory()
        other.create()
        item = ItemFactory(wishlist=other)
        item.create()
        original = item.serialize()
        response = self.client.put(f"{self.url}/{item.id}", json={"product_id": 20})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)
        db.session.remove()
        self.assertEqual(Item.find(original["id"]).serialize(), original)

    def test_update_item_bad_data(self):
        """It should reject invalid replacements without changing stored data."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        original = item.serialize()
        for data in (
            {},
            [],
            "bad",
            {"product_id": True},
            {"product_id": "10"},
            {"product_id": None},
            {"product_id": 1.5},
            {"product_id": 10, "note": 123},
        ):
            with self.subTest(data=data):
                response = self.client.put(f"{self.url}/{original['id']}", json=data)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)
                db.session.remove()
                self.assertEqual(Item.find(original["id"]).serialize(), original)

    def test_update_item_bad_json(self):
        """It should reject malformed or null JSON."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        for body in ('{"product_id":', "null"):
            with self.subTest(body=body):
                response = self.client.put(
                    f"{self.url}/{item.id}", data=body, content_type="application/json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.is_json)

    def test_update_item_content_type(self):
        """It should require JSON for an update."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        for content_type in (None, "text/plain"):
            with self.subTest(content_type=content_type):
                response = self.client.put(
                    f"{self.url}/{item.id}",
                    data='{"product_id":10}',
                    content_type=content_type,
                )
                self.assertEqual(response.status_code, 415)
                self.assertTrue(response.is_json)

    def test_delete_item(self):
        """It should remove only the requested item and keep its parent."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        remaining = ItemFactory(wishlist=self.wishlist)
        remaining.create()
        item_id, remaining_id = item.id, remaining.id
        parent_id = self.wishlist.id
        response = self.client.delete(f"{self.url}/{item_id}")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        db.session.remove()
        self.assertIsNone(Item.find(item_id))
        self.assertIsNotNone(Item.find(remaining_id))
        self.assertIsNotNone(Wishlist.find(parent_id))
        self.assertEqual(self.client.get(f"{self.url}/{item_id}").status_code, 404)
        self.assertEqual(
            [item["id"] for item in self.client.get(self.url).get_json()],
            [remaining_id],
        )

    def test_delete_item_missing(self):
        """It should return 204 when the item is already absent."""
        response = self.client.delete(f"{self.url}/0")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")
        self.assertIsNotNone(Wishlist.find(self.wishlist.id))

    def test_delete_item_missing_wishlist(self):
        """It should still return JSON 404 for a missing parent."""
        response = self.client.delete("/wishlists/0/items/0")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)

    def test_delete_item_wrong_wishlist(self):
        """It should not delete another wishlist's item."""
        other = WishlistFactory()
        other.create()
        item = ItemFactory(wishlist=other)
        item.create()
        original = item.serialize()
        response = self.client.delete(f"{self.url}/{item.id}")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)
        db.session.remove()
        self.assertEqual(Item.find(original["id"]).serialize(), original)

    def test_delete_item_twice(self):
        """It should return 204 with no body on both delete requests."""
        item = ItemFactory(wishlist=self.wishlist)
        item.create()
        url = f"{self.url}/{item.id}"
        for _ in range(2):
            response = self.client.delete(url)
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response.data, b"")
