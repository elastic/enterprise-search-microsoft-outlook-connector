#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run a full sync against the source.

It will attempt to sync absolutely all documents that are available in the
third-party system and ingest them into Enterprise Search instance.
"""

from . import constant
from .base_command import BaseCommand
from .checkpointing import Checkpoint
from .connector_queue import ConnectorQueue
from .microsoft_exchange_server_user import MicrosoftExchangeServerUser
from .office365_user import Office365User
from .sync_enterprise_search import SyncEnterpriseSearch
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
        product_type = self.config.get_value("connector_platform_type")
        self.logger.debug(f"Starting producer for fetching objects from {product_type}")

        # Logic to fetch users from Microsoft Exchange or Office365
        if constant.CONNECTOR_TYPE_OFFICE365 in product_type:
            office365_connection = Office365User(self.config)
            users = office365_connection.get_users()
            users_accounts = office365_connection.get_users_accounts(users)
        elif constant.CONNECTOR_TYPE_MICROSOFT_EXCHANGE in product_type:
            microsoft_exchange_server_connection = MicrosoftExchangeServerUser(
                self.config
            )
            users = microsoft_exchange_server_connection.get_users()
            users_accounts = microsoft_exchange_server_connection.get_users_accounts(
                users
            )

        if len(users_accounts) >= 0:
            self.logger.info(
                f"Successfully fetched users accounts from the {product_type}"
            )
        else:
            self.logger.info("Error while fetching users from the Active Directory")
            exit()

        sync_microsoft_outlook = SyncMicrosoftOutlook(
            self.config,
            self.logger,
            self.workplace_search_client,
            queue,
        )

        # Logic to fetch mails, calendars, contacts and task from Microsoft Outlook by using multithreading approach
        (
            end_time,
            time_range_list,
        ) = self.get_datetime_iterable_list_based_on_full_inc_sync(
            FULL_SYNC_INDEXING, ""
        )
        self.create_jobs_for_calendar(
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

    def start_consumer(self, queue):
        """This method starts async calls for the consumer which is responsible for indexing documents to the
        Enterprise Search
        :param queue: Shared queue to fetch the stored documents
        """
        checkpoint = Checkpoint(self.logger, self.config)
        thread_count = self.config.get_value("enterprise_search_sync_thread_count")
        sync_es = SyncEnterpriseSearch(
            self.config, self.logger, self.workplace_search_client, queue
        )
        try:
            self.create_jobs(thread_count, sync_es.perform_sync, (), [])
            for checkpoint_data in sync_es.checkpoint_list:
                checkpoint.set_checkpoint(
                    checkpoint_data["current_time"], checkpoint_data["index_type"], checkpoint_data["object_type"]
                )
        except Exception as exception:
            raise Exception(f"Error while running Full sync command. Error: {exception}")

    def execute(self):
        """This function execute the start function."""

        queue = ConnectorQueue(self.logger)
        self.local_storage.create_local_storage_directory()
        self.start_producer(queue)
        self.start_consumer(queue)
