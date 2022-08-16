#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from unittest.mock import Mock

import pytest
from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.connector_queue import ConnectorQueue
from ees_microsoft_outlook.sync_microsoft_outlook import SyncMicrosoftOutlook
from elastic_enterprise_search import WorkplaceSearch


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )
    logger = logging.getLogger("unit_test_sync_outlook")
    return configuration, logger


def create_object_of_sync_microsoft_outlook():
    """This function create object of Sync Microsoft Teams class."""
    configs, logger = settings()
    enterprise_search_host = configs.get_value("enterprise_search.host_url")
    workplace_search_client = WorkplaceSearch(
        enterprise_search_host,
        http_auth=configs.get_value("enterprise_search.api_key"),
    )
    queue = ConnectorQueue(logger)
    queue.end_signal()
    return SyncMicrosoftOutlook(configs, logger, workplace_search_client, queue)


@pytest.mark.parametrize(
    "mock_response",
    [({"user": "dummy_user", "permissions": ["permission1"]},)],
)
def test_workplace_add_permission(mock_response, caplog):
    """Test method to add permission into Workplace Search"""
    # Setup
    caplog.set_level("INFO")
    sync_outlook = create_object_of_sync_microsoft_outlook()
    sync_outlook.workplace_search_custom_client.add_permissions = Mock(
        return_value=mock_response
    )

    # Execute
    sync_outlook.workplace_add_permission("dummy_user", ["permission1"])

    # Assert
    sync_outlook.workplace_search_custom_client.add_permissions.assert_called_with("dummy_user", ["permission1"])
