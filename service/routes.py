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

@app.route("/wishlists", methods=["POST"])
def create_wishlist():
    """Create an empty wishlist."""
    app.logger.info("Request to create a wishlist")
    if not request.is_json:
        abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Content-Type must be application/json")

    data = request.get_json()
    # Items are added separately after the wishlist is created.
    if isinstance(data, dict) and data.get("items"):
        abort(status.HTTP_400_BAD_REQUEST, "Add items after creating the wishlist")

    wishlist = Wishlist()
    wishlist.deserialize(data)
    wishlist.create()

    location = f"{url_for('create_wishlist', _external=True)}/{wishlist.id}"
    app.logger.info("Created wishlist with ID %s", wishlist.id)
    return jsonify(wishlist.serialize()), status.HTTP_201_CREATED, {"Location": location}
