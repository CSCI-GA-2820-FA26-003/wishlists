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
Wishlist Steps

Steps file for wishlists.feature

The Background step uses the REST API to reset and load test data, the
same way lab-flask-bdd does. Every other step drives the web page with
Selenium, so the scenarios only ever interact with the user interface.
"""
import requests
from compare3 import expect
from behave import given, when  # pylint: disable=no-name-in-module
from selenium.webdriver.common.by import By

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204

WAIT_TIMEOUT = 60


@given("the following wishlists")
def load_wishlists(context):
    """Delete all Wishlists and load new ones"""

    # Get a list of all the wishlists
    rest_endpoint = f"{context.base_url}/wishlists"
    context.resp = requests.get(rest_endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_200_OK)
    # and delete them one by one (their items are deleted with them)
    for wishlist in context.resp.json():
        context.resp = requests.delete(f"{rest_endpoint}/{wishlist['id']}", timeout=WAIT_TIMEOUT)
        expect(context.resp.status_code).equal_to(HTTP_204_NO_CONTENT)

    # load the database with new wishlists and remember their ids by name
    context.wishlist_ids = {}
    for row in context.table:
        payload = {
            "name": row["name"],
            "customer_id": int(row["customer_id"]),
        }
        context.resp = requests.post(rest_endpoint, json=payload, timeout=WAIT_TIMEOUT)
        expect(context.resp.status_code).equal_to(HTTP_201_CREATED)
        context.wishlist_ids[row["name"]] = context.resp.json()["id"]


@when('I set the "Id" to the id of the "{name}" wishlist')
def set_id_of_wishlist(context, name):
    """Type the id of a wishlist loaded by the Background into the Id field"""
    element = context.driver.find_element(By.ID, "wishlist_id")
    element.clear()
    element.send_keys(str(context.wishlist_ids[name]))


@given("the following items")
def load_items(context):
    """Load items into the wishlists created by the Background."""
    for row in context.table:
        wishlist_id = context.wishlist_ids[row["wishlist"]]
        payload = {"product_id": int(row["product_id"]), "note": row["note"]}
        response = requests.post(
            f"{context.base_url}/wishlists/{wishlist_id}/items",
            json=payload,
            timeout=WAIT_TIMEOUT,
        )
        expect(response.status_code).equal_to(HTTP_201_CREATED)
