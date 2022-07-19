#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run a full sync against the source.
It will attempt to sync absolutely all documents that are available in the
third-party system and ingest them into Enterprise Search instance.
"""

from .base_command import BaseCommand
from .connector_queue import ConnectorQueue
from .microsoft_exchange_server_user import MicrosoftExchangeServerUser
from .sync_microsoft_outlook import SyncMicrosoftOutlook

FULL_SYNC_INDEXING = "full"


class FullSyncCommand(BaseCommand):
    """This class start execution of fullsync feature."""

    def start_producer(self, queue):
        """This method starts async calls for the Producer which is responsible for fetching documents from
        the Microsoft Outlook and pushing them in the shared queue
        :param queue: Shared queue to fetch the stored documents
        """
        thread_count = self.config.get_value("source_sync_thread_count")
        self.logger.debug("Starting producer for fetching objects from Microsoft Exchange")

        # Logic to fetch users from Microsoft Exchange
        microsoft_exchange_server_connection = MicrosoftExchangeServerUser(
            self.config
        )
        users = microsoft_exchange_server_connection.get_users()
        users_accounts = microsoft_exchange_server_connection.get_users_accounts(
            users
        )

        if len(users_accounts) >= 0:
            self.logger.info(
                "Successfully fetched users accounts from the Microsoft Exchange"
            )
        else:
            self.logger.info("Error while fetching users from the Active Directory")
            exit()

        sync_microsoft_outlook = SyncMicrosoftOutlook(
            self.config,
            self.logger,
            self.workplace_search_custom_client,
            queue,
        )

        # Logic to fetch mails, calendars, contacts and task from Microsoft Outlook by using multithreading approach
        (
            end_time,
            time_range_list,
        ) = self.get_datetime_iterable_list_based_on_full_inc_sync(
            FULL_SYNC_INDEXING, ""
        )
        self.create_jobs_for_mails(
            FULL_SYNC_INDEXING,
            sync_microsoft_outlook,
            thread_count,
            users_accounts,
            time_range_list,
            end_time,
            queue,
        )

        enterprise_thread_count = self.config.get_value(
            "enterprise_search_sync_thread_count"
        )
        for _ in range(enterprise_thread_count):
            queue.end_signal()

    def execute(self):
        """This function execute the start function."""

        queue = ConnectorQueue(self.logger)
        self.local_storage.create_local_storage_directory()
        self.start_producer(queue)
