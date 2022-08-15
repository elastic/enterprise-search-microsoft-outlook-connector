#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run a full sync against the source.
It will attempt to sync absolutely all documents that are available in the
third-party system and ingest them into Enterprise Search instance.
"""

from .base_indexing_command import BaseIndexingCommand
from .connector_queue import ConnectorQueue
from .constant import CURRENT_TIME
from .sync_microsoft_outlook import SyncMicrosoftOutlook

FULL_SYNC_INDEXING = "full"


class FullSyncCommand(BaseIndexingCommand):
    """This class start execution of fullsync feature."""

    def start_producer(self, queue):
        """This method starts async calls for the Producer which is responsible for fetching documents from
        the Microsoft Outlook and pushing them in the shared queue
        :param queue: Shared queue to fetch the stored documents
        """
        thread_count = self.config.get_value("microsoft_outlook_sync_thread_count")

        users_accounts = self.get_accounts()
        sync_microsoft_outlook = SyncMicrosoftOutlook(
            self.config,
            self.logger,
            self.workplace_search_custom_client,
            queue,
        )

        start_time, end_time = (
            self.config.get_value("start_time"),
            CURRENT_TIME,
        )
        # Logic to fetch mails, calendars, contacts and task from Microsoft Outlook by using multithreading approach
        time_range_list = self.get_datetime_iterable_list(start_time, end_time)
        self.create_jobs_for_mails(
            FULL_SYNC_INDEXING,
            sync_microsoft_outlook,
            thread_count,
            users_accounts,
            time_range_list,
            end_time,
            queue,
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
        self.create_jobs_for_contacts(
            FULL_SYNC_INDEXING,
            sync_microsoft_outlook,
            thread_count,
            users_accounts,
            time_range_list,
            end_time,
            queue,
        )
        self.create_jobs_for_tasks(
            FULL_SYNC_INDEXING,
            sync_microsoft_outlook,
            thread_count,
            users_accounts,
            time_range_list,
            end_time,
            queue,
        )
        self.pass_end_signal(queue)

    def execute(self):
        """This function execute the start function."""

        queue = ConnectorQueue(self.logger)
        self.local_storage.create_local_storage_directory()
        self.start_producer(queue)
        self.start_consumer(queue)
