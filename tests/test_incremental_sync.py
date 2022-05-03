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
from ees_microsoft_outlook.incremental_sync_command import \
    IncrementalSyncCommand
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
    logger = logging.getLogger("unit_test_incremental_sync")
    return configuration, logger


@patch.object(MicrosoftExchangeServerUser, "get_users_accounts")
@patch.object(MicrosoftExchangeServerUser, "get_users")
def test_start_producer(mock_get_users_accounts, mock_get_users):
    """Test method of start producer to fetching data from microsoft outlook for incremental sync"""
    config, logger = settings()
    args = get_args("FullSyncCommand")
    incremental_sync = IncrementalSyncCommand(args)
    queue = ConnectorQueue(logger)
    mock_get_users_accounts.return_value = [Mock()]
    mock_get_users.return_value = [Mock()]
    incremental_sync.create_jobs_for_mails = Mock()
    incremental_sync.start_producer(queue)
    assert queue.qsize() == config.get_value("enterprise_search_sync_thread_count")
