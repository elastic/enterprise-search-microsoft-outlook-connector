#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Module contains a base indexing command interface.
Connector can run multiple commands such as full-sync and incremental-sync.
This module provides convenience interface defining the shared
objects and methods that will can be used by commands."""

from .base_command import BaseCommand
from .checkpointing import Checkpoint
from .constant import (CONNECTOR_TYPE_MICROSOFT_EXCHANGE,
                       CONNECTOR_TYPE_OFFICE365)
from .microsoft_exchange_server_user import MicrosoftExchangeServerUser
from .office365_user import Office365User
from .sync_enterprise_search import SyncEnterpriseSearch


class BaseIndexingCommand(BaseCommand):
    """This class contain common methods for full-sync and incremental-sync commands."""

    def get_accounts(self):
        """This method gets Outlook account of active directory users
        Returns:
            users_accounts: List of all user accounts
        """
        platform_type = self.config.get_value("connector_platform_type")
        self.logger.debug(
            f"Starting producer for fetching objects from {platform_type}"
        )
        self.logger.info(f"Fetching users account from the {platform_type}")
        # Logic to fetch users from Microsoft Exchange or Office365
        if CONNECTOR_TYPE_OFFICE365 in platform_type:
            office365_connection = Office365User(self.config)
            users = office365_connection.get_users()
            users_accounts = office365_connection.get_users_accounts(users)
        elif CONNECTOR_TYPE_MICROSOFT_EXCHANGE in platform_type:
            microsoft_exchange_server_connection = MicrosoftExchangeServerUser(
                self.config
            )
            users = microsoft_exchange_server_connection.get_users()
            users_accounts = microsoft_exchange_server_connection.get_users_accounts(
                users
            )

        if len(users_accounts) >= 0:
            self.logger.info(
                f"Successfully fetched users accounts from the {platform_type}"
            )
        else:
            self.logger.info("Error while fetching users from the Active Directory")
            exit()
        return users_accounts

    def pass_end_signal(self, queue):
        """This method pass end signal into queue
        :param queue: Shared queue to pass end signal
        """
        enterprise_thread_count = self.config.get_value(
            "enterprise_search_sync_thread_count"
        )
        for _ in range(enterprise_thread_count):
            queue.end_signal()

    def start_consumer(self, queue):
        """This method starts async calls for the consumer which is responsible for indexing documents to the
        Enterprise Search
        :param queue: Shared queue to fetch the stored documents
        """
        checkpoint = Checkpoint(self.logger, self.config)
        thread_count = self.config.get_value("enterprise_search_sync_thread_count")
        sync_es = SyncEnterpriseSearch(
            self.config, self.logger, self.workplace_search_custom_client, queue
        )
        self.create_jobs(thread_count, sync_es.perform_sync, (), [])
        for checkpoint_data in sync_es.checkpoint_list:
            checkpoint.set_checkpoint(
                checkpoint_data["current_time"],
                checkpoint_data["index_type"],
                checkpoint_data["object_type"],
            )
