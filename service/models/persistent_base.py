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
Persistent Base class for database CRUD functions
"""

import logging
from abc import abstractmethod
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

db = SQLAlchemy()

# Range of a PostgreSQL INTEGER column, the type of every id in this service
MIN_INTEGER = -2147483648
MAX_INTEGER = 2147483647


def in_integer_range(value: int) -> bool:
    """Returns True when the value fits in a database INTEGER column"""
    return MIN_INTEGER <= value <= MAX_INTEGER


# What a client is told when the database refuses a record. The database's
# own error can name tables and constraints, so it only goes to the log.
NOT_SAVED = "The record could not be saved"
NOT_DELETED = "The record could not be deleted"


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


######################################################################
#  P E R S I S T E N T   B A S E   M O D E L
######################################################################
class PersistentBase:
    """Base class added persistent methods"""

    def __init__(self):
        self.id = None  # pylint: disable=invalid-name

    @abstractmethod
    def serialize(self) -> dict:
        """Convert an object into a dictionary"""

    @abstractmethod
    def deserialize(self, data: dict) -> None:
        """Convert a dictionary into an object"""

    def create(self) -> None:
        """
        Creates a Account to the database
        """
        logger.info("Creating %s", self)
        # id must be none to generate next primary key
        self.id = None
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record %s: %s", self, e)
            raise DataValidationError(NOT_SAVED) from e

    def update(self) -> None:
        """
        Updates a Account to the database
        """
        logger.info("Updating %s", self)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record %s: %s", self, e)
            raise DataValidationError(NOT_SAVED) from e

    def delete(self) -> None:
        """Removes a Account from the data store"""
        logger.info("Deleting %s", self)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record %s: %s", self, e)
            raise DataValidationError(NOT_DELETED) from e

    @classmethod
    def all(cls):
        """Returns all of the records in the database ordered by id"""
        logger.info("Processing all records")
        # pylint: disable=no-member
        return cls.query.order_by(cls.id).all()

    @classmethod
    def find(cls, by_id):
        """Finds a record by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        # No record can have an id the column cannot hold, and the database
        # raises an error instead of finding nothing when it is asked for one
        if not in_integer_range(by_id):
            return None
        # pylint: disable=no-member
        return cls.query.session.get(cls, by_id)
