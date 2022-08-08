#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from unittest.mock import Mock, patch

from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.connector_queue import ConnectorQueue
from ees_microsoft_outlook.full_sync_command import FullSyncCommand
from ees_microsoft_outlook.microsoft_exchange_server_user import \
    MicrosoftExchangeServerUser
from tests.support import get_args


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""

    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )
    logger = logging.getLogger("unit_test_full_sync")
    return configuration, logger


@patch.object(MicrosoftExchangeServerUser, "get_users_accounts")
@patch.object(MicrosoftExchangeServerUser, "get_users")
def test_start_producer(
    mock_get_users, mock_get_users_accounts
):
    """Test method of start producer to fetching data from microsoft outlook for full sync"""
    # Setup
    config, logger = settings()
    args = get_args("FullSyncCommand")
    full = FullSyncCommand(args)
    queue = ConnectorQueue(logger)
    mock_get_users.return_value = [Mock()]
    mock_get_users_accounts.return_value = [Mock()]
    full.create_jobs_for_mails = Mock()
    full.create_jobs_for_calendar = Mock()
    full.create_jobs_for_contacts = Mock()

    # Execute
    full.start_producer(queue)

    # Assert
    assert queue.qsize() == config.get_value("enterprise_search_sync_thread_count")
