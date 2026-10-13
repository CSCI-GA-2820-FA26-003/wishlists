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
Wishlist Model

A Wishlist belongs to a customer and holds a collection of Items
"""

import logging
from .persistent_base import db, PersistentBase, DataValidationError
from .item import Item

logger = logging.getLogger("flask.app")


#  wishlist model
class Wishlist(db.Model, PersistentBase):
    """
    Class that represents a Wishlist
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    # delete-orphan: deleting a Wishlist (or removing an Item from .items) deletes the Item
    items = db.relationship(
        "Item", backref="wishlist", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self):
        return f"<Wishlist {self.name} id=[{self.id}]>"

    def serialize(self) -> dict:
        """Converts a Wishlist into a dictionary"""
        logger.info("Serializing %s", self)
        wishlist = {
            "id": self.id,
            "name": self.name,
            "customer_id": self.customer_id,
            "items": [],
        }
        for item in self.items:
            wishlist["items"].append(item.serialize())
        return wishlist

    def deserialize(self, data: dict) -> None:
        """
        Populates a Wishlist from a dictionary

        id is never read from the data, it comes from the database or the URL.
        items is optional; when present, each one is deserialized and APPENDED
        to self.items. Callers updating an existing Wishlist must remove "items"
        from the data first, or the existing items will be duplicated.

        Args:
            data (dict): A dictionary containing the resource data
        """
        logger.info("Deserializing a Wishlist")
        try:
            name = data["name"]
            customer_id = data["customer_id"]
            if not isinstance(name, str) or not name.strip():
                raise DataValidationError(
                    "Invalid Wishlist: name must be a non-empty string"
                )
            if not isinstance(customer_id, int) or isinstance(customer_id, bool):
                raise DataValidationError(
                    "Invalid Wishlist: customer_id must be an integer"
                )
            self.name = name
            self.customer_id = customer_id
            item_list = data.get("items") or []
            if not isinstance(item_list, list):
                raise DataValidationError("Invalid Wishlist: items must be a list")
            for json_item in item_list:
                item = Item()
                item.deserialize(json_item)
                self.items.append(item)
        except KeyError as error:
            raise DataValidationError(
                "Invalid Wishlist: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Wishlist: body of request contained bad or no data "
                + str(error)
            ) from error
