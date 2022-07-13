#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ees_microsoft_outlook.local_storage import LocalStorage  # noqa

DIRECTORY_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "ees_microsoft_outlook",
    "doc_ids",
)

DOC_IDS_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "tests",
    "doc_ids.json",
)


def create_local_storage_obj():
    """This function create object of LocalStorage class for test"""
    logger = logging.getLogger("unit_test_local_storage")
    local_storage = LocalStorage(logger)
    return local_storage


def test_create_local_storage_directory():
    """This method test if directory is exits or not"""
    # Setup
    local_storage_obj = create_local_storage_obj()

    # Execute
    local_storage_obj.create_local_storage_directory()

    # Assert
    if os.path.exists(DIRECTORY_PATH):
        assert True
    else:
        assert False


def test_get_storage_with_collection():
    """This method test get_storage_with_collection"""
    # Setup
    local_storage_obj = create_local_storage_obj()
    expected_response = {
        "global_keys": [
            {
                "id": "abc123",
                "parent id": "xyz123",
                "type": "inbox mail",
                "platform": "Microsoft Exchange",
            }
        ],
        "delete_keys": [
            {
                "id": "abc123",
                "parent id": "xyz123",
                "type": "inbox mail",
                "platform": "Microsoft Exchange",
            }
        ],
    }

    # Execute
    actual_response = local_storage_obj.get_storage_with_collection(local_storage_obj, DOC_IDS_PATH)

    # Assert
    assert expected_response == actual_response
