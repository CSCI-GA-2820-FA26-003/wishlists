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
Wishlist Service

This service implements a REST API that allows you to Create, Read, Update
and Delete wishlists
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Wishlist, Item
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            name="Wishlists Service",
            version=app.config["VERSION"],
            list_url="/wishlists",
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.mimetype == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@app.route("/wishlists", methods=["POST"])
def create_wishlist():
    """Create an empty wishlist."""
    app.logger.info("Request to create a wishlist")
    if not request.is_json:
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Content-Type must be application/json",
        )

    data = request.get_json()
    # Items are added separately after the wishlist is created.
    if isinstance(data, dict) and data.get("items"):
        abort(status.HTTP_400_BAD_REQUEST, "Add items after creating the wishlist")

    wishlist = Wishlist()
    wishlist.deserialize(data)
    wishlist.create()

    location = f"{url_for('create_wishlist', _external=True)}/{wishlist.id}"
    app.logger.info("Created wishlist with ID %s", wishlist.id)
    return (
        jsonify(wishlist.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location},
    )


######################################################################
# READ A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["GET"])
def get_wishlist(wishlist_id):
    """
    Retrieve a single Wishlist

    This endpoint will return a Wishlist, with its Items, based on its id
    """
    app.logger.info("Request to Retrieve a Wishlist with id [%s]", wishlist_id)

    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    app.logger.info("Returning Wishlist: %s", wishlist.name)
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE AN EXISTING WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["PUT"])
def update_wishlist(wishlist_id):
    """
    Update a Wishlist

    This endpoint will update the name and customer_id of a Wishlist.
    Items are managed through their own endpoints, so any items in the
    body are ignored.
    """
    app.logger.info("Request to Update a Wishlist with id [%s]", wishlist_id)
    if not request.is_json:
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Content-Type must be application/json",
        )

    wishlist = Wishlist.find(wishlist_id)
    if not wishlist:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Wishlist with id '{wishlist_id}' was not found.",
        )

    data = request.get_json()
    if isinstance(data, dict):
        # deserialize() appends items, which would duplicate the existing ones
        data.pop("items", None)
    wishlist.deserialize(data)
    wishlist.update()

    app.logger.info("Wishlist with id [%s] updated.", wishlist.id)
    return jsonify(wishlist.serialize()), status.HTTP_200_OK


######################################################################
# DELETE A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>", methods=["DELETE"])
def delete_wishlist(wishlist_id):
    """Deletes a wishlist if it exists"""
    app.logger.info("Request to delete wishlist with id: %s", wishlist_id)
    wishlist = Wishlist.find(wishlist_id)
    if wishlist is not None:
        wishlist.delete()
    return "", status.HTTP_204_NO_CONTENT


# LIST ALL WISHLISTS
######################################################################
@app.route("/wishlists", methods=["GET"])
def list_wishlists():
    """Returns all wishlists"""
    app.logger.info("Request to list all wishlists")
    wishlists = Wishlist.all()
    return jsonify([wishlist.serialize() for wishlist in wishlists]), status.HTTP_200_OK


######################################################################
# CREATE AN ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["POST"])
def create_item(wishlist_id):
    """Add an item to an existing wishlist."""
    app.logger.info("Request to create an item in wishlist %s", wishlist_id)
    check_content_type("application/json")
    wishlist = Wishlist.find(wishlist_id)
    if wishlist is None:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' was not found.")

    item = Item()
    item.deserialize(request.get_json())
    item.wishlist_id = wishlist.id
    item.create()
    location = f"{url_for('create_item', wishlist_id=wishlist_id, _external=True)}/{item.id}"
    return jsonify(item.serialize()), status.HTTP_201_CREATED, {"Location": location}


######################################################################
# READ AN ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["GET"])
def get_item(wishlist_id, item_id):
    """Read an item only from its own wishlist."""
    app.logger.info("Request to read item %s in wishlist %s", item_id, wishlist_id)
    if Wishlist.find(wishlist_id) is None:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' was not found.")
    item = Item.find(item_id)
    if item is None or item.wishlist_id != wishlist_id:
        abort(status.HTTP_404_NOT_FOUND, f"Item with id '{item_id}' was not found in this wishlist.")
    return jsonify(item.serialize()), status.HTTP_200_OK


######################################################################
# LIST ITEMS IN A WISHLIST
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items", methods=["GET"])
def list_items(wishlist_id):
    """List the items belonging to one wishlist."""
    app.logger.info("Request to list items in wishlist %s", wishlist_id)
    wishlist = Wishlist.find(wishlist_id)
    if wishlist is None:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' was not found.")
    return jsonify([item.serialize() for item in wishlist.items]), status.HTTP_200_OK


######################################################################
# UPDATE AN ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["PUT"])
def update_item(wishlist_id, item_id):
    """Replace an item's product_id and optional note."""
    app.logger.info("Request to update item %s in wishlist %s", item_id, wishlist_id)
    check_content_type("application/json")
    if Wishlist.find(wishlist_id) is None:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' was not found.")
    item = Item.find(item_id)
    if item is None or item.wishlist_id != wishlist_id:
        abort(status.HTTP_404_NOT_FOUND, f"Item with id '{item_id}' was not found in this wishlist.")
    item.deserialize(request.get_json())
    item.update()
    return jsonify(item.serialize()), status.HTTP_200_OK


######################################################################
# DELETE AN ITEM
######################################################################
@app.route("/wishlists/<int:wishlist_id>/items/<int:item_id>", methods=["DELETE"])
def delete_item(wishlist_id, item_id):
    """Delete an item without removing its wishlist."""
    app.logger.info("Request to delete item %s in wishlist %s", item_id, wishlist_id)
    if Wishlist.find(wishlist_id) is None:
        abort(status.HTTP_404_NOT_FOUND, f"Wishlist with id '{wishlist_id}' was not found.")
    item = Item.find(item_id)
    if item is None:
        return "", status.HTTP_204_NO_CONTENT
    if item.wishlist_id != wishlist_id:
        abort(status.HTTP_404_NOT_FOUND, f"Item with id '{item_id}' was not found in this wishlist.")
    item.delete()
    return "", status.HTTP_204_NO_CONTENT
