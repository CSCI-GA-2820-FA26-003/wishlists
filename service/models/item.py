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
Item Model

An Item is a product saved in a Wishlist
"""

import logging
from .persistent_base import db, PersistentBase, DataValidationError

logger = logging.getLogger("flask.app")

# Longest note the database column can hold
NOTE_MAX_LENGTH = 255


######################################################################
#  I T E M   M O D E L
######################################################################
class Item(db.Model, PersistentBase):
    """
    Class that represents an Item in a Wishlist
    """

    # Table Schema
    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(
        db.Integer, db.ForeignKey("wishlist.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(NOTE_MAX_LENGTH), nullable=True)  # note is optional

    # purchased is read-only in request bodies, it only changes through the purchase action
    purchased = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Item product_id=[{self.product_id}] id=[{self.id}] wishlist[{self.wishlist_id}]>"

    def serialize(self) -> dict:
        """Converts an Item into a dictionary"""
        logger.info("Serializing %s", self)
        return {
            "id": self.id,
            "wishlist_id": self.wishlist_id,
            "product_id": self.product_id,
            "note": self.note,
            "purchased": self.purchased,
        }

    def deserialize(self, data: dict) -> None:
        """
        Populates an Item from a dictionary

        id and wishlist_id are never read from the data, they come from the URL.
        note is optional and may be null. purchased is never read from the data
        either: a new Item starts out not purchased and only the purchase
        action can change it.

        Args:
            data (dict): A dictionary containing the resource data
        """
        logger.info("Deserializing an Item")
        try:
            product_id = data["product_id"]
            note = data.get("note")
            if not isinstance(product_id, int) or isinstance(product_id, bool):
                raise DataValidationError("Invalid Item: product_id must be an integer")
            if note is not None and not isinstance(note, str):
                raise DataValidationError("Invalid Item: note must be a string")
            if note is not None and len(note) > NOTE_MAX_LENGTH:
                raise DataValidationError(
                    f"Invalid Item: note must be at most {NOTE_MAX_LENGTH} characters"
                )
            self.product_id = product_id
            self.note = note
        except KeyError as error:
            raise DataValidationError(
                "Invalid Item: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Item: body of request contained bad or no data " + str(error)
            ) from error
