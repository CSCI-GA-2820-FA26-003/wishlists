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
YourResourceModel Service

This service implements a REST API that allows you to Create, Read, Update
and Delete YourResourceModel
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Wishlist
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


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
