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
JSON Error Handler Test Suite
"""

import logging
from unittest import TestCase
from unittest.mock import patch
from flask import request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
from wsgi import app
from service.common import status
from service.models import DataValidationError
from service.routes import check_content_type


######################################################################
#  E R R O R   H A N D L E R   T E S T   C A S E S
######################################################################
class TestErrorHandlers(TestCase):
    """Tests that every error is returned as consistent JSON"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.logger.setLevel(logging.CRITICAL)

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()

    def assert_json_error(self, resp, code, error):
        """Asserts that resp is a JSON error with the expected status and title"""
        self.assertEqual(resp.status_code, code)
        self.assertEqual(resp.content_type, "application/json")
        data = resp.get_json()
        self.assertEqual(data["status"], code)
        self.assertEqual(data["error"], error)
        self.assertIn("message", data)
        return data

    @staticmethod
    def handle(exception):
        """Runs an exception through the registered error handlers"""
        return app.make_response(app.handle_user_exception(exception))

    ######################################################################
    #  4 0 0   B A D   R E Q U E S T
    ######################################################################

    def test_bad_request_invalid_json(self):
        """It should return a JSON 400 when the body is not valid JSON"""
        with app.test_request_context(
            "/", method="POST", data="{not valid json", content_type="application/json"
        ):
            with self.assertRaises(BadRequest) as context:
                request.get_json()
            resp = self.handle(context.exception)
        self.assert_json_error(resp, status.HTTP_400_BAD_REQUEST, "Bad Request")

    def test_data_validation_error(self):
        """It should return a JSON 400 for a DataValidationError"""
        with app.test_request_context("/"):
            resp = self.handle(DataValidationError("Invalid Wishlist: missing name"))
        data = self.assert_json_error(resp, status.HTTP_400_BAD_REQUEST, "Bad Request")
        self.assertIn("missing name", data["message"])

    ######################################################################
    #  4 0 4   N O T   F O U N D
    ######################################################################

    def test_not_found(self):
        """It should return a JSON 404 for an unknown URL"""
        resp = self.client.get("/no-such-resource")
        self.assert_json_error(resp, status.HTTP_404_NOT_FOUND, "Not Found")

    ######################################################################
    #  4 0 5   M E T H O D   N O T   A L L O W E D
    ######################################################################

    def test_method_not_allowed(self):
        """It should return a JSON 405 with an Allow header"""
        resp = self.client.post("/")
        self.assert_json_error(
            resp, status.HTTP_405_METHOD_NOT_ALLOWED, "Method not Allowed"
        )
        self.assertIn("GET", resp.headers["Allow"])

    ######################################################################
    #  4 1 5   U N S U P P O R T E D   M E D I A   T Y P E
    ######################################################################

    def test_wrong_content_type(self):
        """It should return a JSON 415 when Content-Type is not application/json"""
        with app.test_request_context(
            "/", method="POST", data="hello", content_type="text/plain"
        ):
            with self.assertRaises(UnsupportedMediaType) as context:
                check_content_type("application/json")
            resp = self.handle(context.exception)
        data = self.assert_json_error(
            resp, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported media type"
        )
        self.assertIn("Content-Type must be application/json", data["message"])

    def test_missing_content_type(self):
        """It should return a JSON 415 when there is no Content-Type"""
        with app.test_request_context("/", method="POST"):
            with self.assertRaises(UnsupportedMediaType) as context:
                check_content_type("application/json")
            resp = self.handle(context.exception)
        self.assert_json_error(
            resp, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported media type"
        )

    def test_correct_content_type(self):
        """It should accept application/json, including a charset parameter"""
        for content_type in ["application/json", "application/json; charset=utf-8"]:
            with app.test_request_context(
                "/", method="POST", data="{}", content_type=content_type
            ):
                self.assertIsNone(check_content_type("application/json"))

    ######################################################################
    #  5 0 0   I N T E R N A L   S E R V E R   E R R O R
    ######################################################################

    def test_internal_server_error(self):
        """It should return a JSON 500 without leaking internal details"""
        with patch.dict(app.config, {"PROPAGATE_EXCEPTIONS": False}):
            with patch(
                "service.routes.jsonify",
                side_effect=RuntimeError("secret database password"),
            ):
                resp = self.client.get("/")
        data = self.assert_json_error(
            resp, status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error"
        )
        self.assertEqual(data["message"], "Something went wrong")
        body = resp.get_data(as_text=True)
        self.assertNotIn("secret", body)
        self.assertNotIn("Traceback", body)
        self.assertNotIn("RuntimeError", body)
