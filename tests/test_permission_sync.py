#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import logging
import os
import sys
from unittest.mock import Mock

from tests.support import get_args

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_microsoft_outlook.configuration import Configuration  # noqa
from ees_microsoft_outlook.permission_sync_command import \
    PermissionSyncCommand  # noqa

CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "microsoft_outlook_connector.yml",
)


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(file_name=CONFIG_FILE)

    logger = logging.getLogger("unit_test_permission")
    return configuration, logger


def create_permission_sync_obj():
    """This function create permission object for test."""
    args = get_args("PermissionSyncCommand")
    return PermissionSyncCommand(args)


def test_remove_all_permissions():
    """Test method for removing all the permissions from Workplace Search"""
    configs, _ = settings()
    permission_sync_obj = create_permission_sync_obj()
    mocked_respose = {"results": [{"user": "user1", "permissions": ["permission1"]}]}
    permission_sync_obj.workplace_search_client.list_permissions = Mock(
        return_value=mocked_respose
    )
    permission_sync_obj.workplace_search_client.remove_user_permissions = Mock(
        return_value=True
    )
    permission_sync_obj.remove_all_permissions()
    enterprise_search_host = configs.get_value("enterprise_search.api_key")
    enterprise_search_source = configs.get_value("enterprise_search.source_id")
    permission_sync_obj.workplace_search_client.list_permissions.assert_called_with(
        http_auth=enterprise_search_host, content_source_id=enterprise_search_source
    )
    permission_sync_obj.workplace_search_client.remove_user_permissions.assert_called_with(
        http_auth=enterprise_search_host,
        content_source_id=enterprise_search_host,
        user="user1",
        body={"permissions": ["permission1"]},
    )
