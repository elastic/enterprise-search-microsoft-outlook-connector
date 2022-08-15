#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to run an incremental sync against the source.

    It will attempt to sync documents that have changed or have been added in the
    third-party system recently and ingest them into Enterprise Search instance.

    Recency is determined by the time when the last successful incremental or full job
    was ran.
"""
from . import constant
from .base_indexing_command import BaseIndexingCommand
from .checkpointing import Checkpoint
from .connector_queue import ConnectorQueue
from .sync_microsoft_outlook import SyncMicrosoftOutlook

INCREMENTAL_SYNC_INDEXING = "incremental"


class IncrementalSyncCommand(BaseIndexingCommand):
    """This class start executions of incremental sync feature."""

    def start_producer(self, queue):
        """This method starts async calls for the Producer which is responsible for fetching documents from
        the Microsoft Outlook and pushing them in the shared queue
        :param queue: Shared queue to fetch the stored documents
        """
        thread_count = self.config.get_value("microsoft_outlook_sync_thread_count")
        checkpoint = Checkpoint(self.logger, self.config)

        users_accounts = self.get_accounts()
        sync_microsoft_outlook = SyncMicrosoftOutlook(
            self.config,
            self.logger,
            self.workplace_search_custom_client,
            queue,
        )

        # Logic to fetch mails from Microsoft Outlook by using multithreading approach based on saved checkpoint
        start_time, end_time = checkpoint.get_checkpoint(
            constant.CURRENT_TIME, constant.MAILS_OBJECT.lower()
        )
        time_range_list = self.get_datetime_iterable_list(start_time, end_time)
        self.create_jobs_for_mails(
            INCREMENTAL_SYNC_INDEXING,
            sync_microsoft_outlook,
            thread_count,
            users_accounts,
            time_range_list,
            end_time,
            queue,
        )

        # Logic to fetch calendars from Microsoft Outlook by using multithreading approach based on saved checkpoint
        start_time, end_time = checkpoint.get_checkpoint(
            constant.CURRENT_TIME, constant.CALENDARS_OBJECT.lower()
        )
        time_range_list = self.get_datetime_iterable_list(start_time, end_time)
        self.create_jobs_for_calendar(
            INCREMENTAL_SYNC_INDEXING,
            sync_microsoft_outlook,
            thread_count,
            users_accounts,
            time_range_list,
            end_time,
            queue,
        )

        # Logic to fetch contacts from Microsoft Outlook by using multithreading approach based on saved checkpoint
        start_time, end_time = checkpoint.get_checkpoint(
            constant.CURRENT_TIME, constant.CONTACTS_OBJECT.lower()
        )
        time_range_list = self.get_datetime_iterable_list(start_time, end_time)
        self.create_jobs_for_contacts(
            INCREMENTAL_SYNC_INDEXING,
            sync_microsoft_outlook,
            thread_count,
            users_accounts,
            time_range_list,
            end_time,
            queue,
        )

        # Logic to fetch tasks from Microsoft Outlook by using multithreading approach based on saved checkpoint
        start_time, end_time = checkpoint.get_checkpoint(
            constant.CURRENT_TIME, constant.TASKS_OBJECT.lower()
        )
        time_range_list = self.get_datetime_iterable_list(start_time, end_time)
        self.create_jobs_for_tasks(
            INCREMENTAL_SYNC_INDEXING,
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
