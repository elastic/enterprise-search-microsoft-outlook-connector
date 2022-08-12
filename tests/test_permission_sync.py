#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import os
import sys
from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_microsoft_outlook.permission_sync_command import PermissionSyncCommand  # noqa

from tests.support import get_args

CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "microsoft_outlook_connector.yml",
)


def create_permission_sync_obj():
    """This function create permission object for test."""
    args = get_args("PermissionSyncCommand")
    return PermissionSyncCommand(args)


def test_remove_all_permissions():
    """Test method for removing all the permissions from Workplace Search"""

    class Users:
        """class to define users"""

        def __init__(self, name, primary_smtp_address):
            self.name = name
            self.primary_smtp_address = primary_smtp_address

    permission_sync_obj = create_permission_sync_obj()
    mocked_respose = {
        "results": [
            {"user": "user1", "permissions": ["user1@example.com"]},
            {"user": "user2", "permissions": ["user2@example.com"]},
        ]
    }
    permission_sync_obj.workplace_search_custom_client.list_permissions = Mock(
        return_value=mocked_respose
    )
    permission_sync_obj.workplace_search_custom_client.remove_permissions = Mock(
        return_value=True
    )
    permission_sync_obj.remove_all_permissions([Users("user1", "user1@example.com")])
    permission_sync_obj.workplace_search_custom_client.remove_permissions.assert_called_with(
        {"user": "user2", "permissions": ["user2@example.com"]}
    )
