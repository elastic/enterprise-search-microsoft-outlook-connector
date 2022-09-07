#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to remove recently deleted documents from Elastic Enterprise Search.

    Documents that were deleted in source will still be available in
    Elastic Enterprise Search until a full sync happens, or until this module is used.
"""
from . import constant
from .base_command import BaseCommand
from .connector_queue import ConnectorQueue
from .microsoft_exchange_server_user import MicrosoftExchangeServerUser
from .office365_user import Office365User
from .sync_enterprise_search import SyncEnterpriseSearch


class DeletionSyncCommand(BaseCommand):
    """This class start executions of deletion feature."""

    def remove_deleted_documents_from_global_keys(
        self,
        live_documents,
        list_ids_documents,
        deleted_documents,
        global_keys_documents,
    ):
        """Updates the local storage with removing the keys that were deleted from Microsoft Outlook
        :param live_documents: Documents present in Microsoft Outlook
        :param list_ids_documents: Documents present in respective doc_ids.json files
        :param deleted_documents: Document list that were deleted from Microsoft Outlook
        :param global_keys_documents: Document list that are present in doc_ids.json
        :param parent_id: Parent id of the document
        """
        for item in list_ids_documents:
            item_id = item["id"]
            platform = item["platform"]
            items_exists = list(
                filter(
                    lambda seq: seq["id"] == item_id,
                    live_documents,
                )
            )
            if len(items_exists) == 0 and self.config.get_value("connector_platform_type") in platform:
                deleted_documents.append(item_id)
                if item in global_keys_documents:
                    global_keys_documents.remove(item)

    def create_jobs_for_mails_deletion(
        self,
        thread_count,
        users_accounts,
        time_range_list,
        queue,
    ):
        """Creates jobs for deleting the mails
        :param thread_count: Thread count to make partitions
        :param users_accounts: User accounts
        :param time_range_list: Time range split
        :param queue: Shared queue for storing the data
        """
        if constant.MAILS_OBJECT.lower() not in self.config.get_value("objects"):
            return
        self.logger.debug("Started deletion of mails...")
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.MAIL_DELETION_PATH
        )
        mails_documents = self.create_jobs(
            thread_count,
            self.microsoft_outlook_mail_object.get_mails,
            (
                [],
                users_accounts,
            ),
            time_range_list,
        )
        delete_keys_documents = storage_with_collection.get("delete_keys") or []
        global_keys_documents = storage_with_collection.get("global_keys") or []
        deleted_documents = []
        self.remove_deleted_documents_from_global_keys(
            mails_documents,
            delete_keys_documents,
            deleted_documents,
            global_keys_documents,
        )
        queue.append_to_queue("deletion", list(deleted_documents))
        storage_with_collection["global_keys"] = list(global_keys_documents)
        storage_with_collection["delete_keys"] = []
        self.local_storage.update_storage(
            storage_with_collection, constant.MAIL_DELETION_PATH
        )
        self.logger.info("Completed deletion of mails")

    def create_jobs_for_calendar_deletion(
        self,
        thread_count,
        users_accounts,
        time_range_list,
        queue,
    ):
        """Creates jobs for deleting the calendar
        :param thread_count: Thread count to make partitions
        :param users_accounts: User accounts
        :param time_range_list: Time range split
        :param queue: Shared queue for storing the data
        """
        if constant.CALENDARS_OBJECT.lower() not in self.config.get_value("objects"):
            return
        self.logger.debug("Started deletion of calendar...")
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.CALENDAR_DELETION_PATH
        )
        calendar_documents = self.create_jobs(
            thread_count,
            self.microsoft_outlook_calendar_object.get_calendar,
            ([], users_accounts,),
            time_range_list,
        )
        delete_keys_documents = storage_with_collection.get("delete_keys") or []
        global_keys_documents = storage_with_collection.get("global_keys") or []
        deleted_documents = []
        self.remove_deleted_documents_from_global_keys(
            calendar_documents,
            delete_keys_documents,
            deleted_documents,
            global_keys_documents,
        )
        queue.append_to_queue("deletion", list(deleted_documents))
        storage_with_collection["global_keys"] = list(global_keys_documents)
        storage_with_collection["delete_keys"] = []
        self.local_storage.update_storage(
            storage_with_collection, constant.CALENDAR_DELETION_PATH
        )
        self.logger.info("Completed deletion of calendar")

    def create_jobs_for_contacts_deletion(
        self,
        thread_count,
        users_accounts,
        time_range_list,
        queue,
    ):
        """Creates jobs for deleting the contacts
        :param thread_count: Thread count to make partitions
        :param users_accounts: User accounts
        :param time_range_list: Time range split
        :param queue: Shared queue for storing the data
        """
        if constant.CONTACTS_OBJECT.lower() not in self.config.get_value("objects"):
            return
        self.logger.debug("Started deletion of contacts...")
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.CONTACT_DELETION_PATH
        )
        contacts_documents = self.create_jobs(
            thread_count,
            self.microsoft_outlook_contact_object.get_contacts,
            (
                [],
                users_accounts,
            ),
            time_range_list,
        )
        delete_keys_documents = storage_with_collection.get("delete_keys") or []
        global_keys_documents = storage_with_collection.get("global_keys") or []
        deleted_documents = []
        self.remove_deleted_documents_from_global_keys(
            contacts_documents,
            delete_keys_documents,
            deleted_documents,
            global_keys_documents,
        )
        queue.append_to_queue("deletion", list(deleted_documents))
        storage_with_collection["global_keys"] = list(global_keys_documents)
        storage_with_collection["delete_keys"] = []
        self.local_storage.update_storage(
            storage_with_collection, constant.CONTACT_DELETION_PATH
        )
        self.logger.info("Completed deletion of contacts")

    def create_jobs_for_tasks_deletion(
        self,
        thread_count,
        users_accounts,
        time_range_list,
        queue,
    ):
        """Creates jobs for deleting the tasks
        :param thread_count: Thread count to make partitions
        :param users_accounts: User accounts
        :param time_range_list: Time range split
        :param queue: Shared queue for storing the data
        """
        if constant.TASKS_OBJECT.lower() not in self.config.get_value("objects"):
            return
        self.logger.debug("Started deletion of tasks...")
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.TASK_DELETION_PATH
        )
        tasks_documents = self.create_jobs(
            thread_count,
            self.microsoft_outlook_task_object.get_tasks,
            ([], users_accounts,),
            time_range_list,
        )
        delete_keys_documents = storage_with_collection.get("delete_keys") or []
        global_keys_documents = storage_with_collection.get("global_keys") or []
        deleted_documents = []
        self.remove_deleted_documents_from_global_keys(
            tasks_documents,
            delete_keys_documents,
            deleted_documents,
            global_keys_documents,
        )
        queue.append_to_queue("deletion", list(deleted_documents))
        storage_with_collection["global_keys"] = list(global_keys_documents)
        storage_with_collection["delete_keys"] = []
        self.local_storage.update_storage(
            storage_with_collection, constant.TASK_DELETION_PATH
        )
        self.logger.info("Completed deletion of tasks")

    def start_producer(self, queue):
        """This method starts async calls for the producer which is responsible
        for fetching documents from the Microsoft Outlook and pushing them in the shared queue
        :param queue: Shared queue to store the fetched documents
        """
        thread_count = self.config.get_value("microsoft_outlook_sync_thread_count")
        product_type = self.config.get_value("connector_platform_type")
        self.logger.debug(f"Starting producer for fetching objects from {product_type}")

        # Logic to fetch users from Microsoft Exchange or Office365
        if constant.CONNECTOR_TYPE_OFFICE365 in self.config.get_value(
            "connector_platform_type"
        ):
            office365_connection = Office365User(self.config)
            users = office365_connection.get_users()
            users_accounts = office365_connection.get_users_accounts(users)
        elif constant.CONNECTOR_TYPE_MICROSOFT_EXCHANGE in self.config.get_value(
            "connector_platform_type"
        ):
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

        start_time, end_time = (
            self.config.get_value("start_time"),
            constant.CURRENT_TIME,
        )
        # Logic to fetch mails, calendars, contacts and task from Microsoft Outlook by using multithreading approach
        time_range_list = self.get_datetime_iterable_list(start_time, end_time)
        self.create_jobs_for_mails_deletion(
            thread_count,
            users_accounts,
            time_range_list,
            queue,
        )
        self.create_jobs_for_calendar_deletion(
            thread_count,
            users_accounts,
            time_range_list,
            queue,
        )
        self.create_jobs_for_contacts_deletion(
            thread_count,
            users_accounts,
            time_range_list,
            queue,
        )
        self.create_jobs_for_tasks_deletion(
            thread_count,
            users_accounts,
            time_range_list,
            queue,
        )
        for _ in range(self.config.get_value("enterprise_search_sync_thread_count")):
            queue.end_signal()

    def start_consumer(self, queue):
        """This method starts async calls for the consumer which is responsible for indexing documents to the
        Enterprise Search
        :param queue: Shared queue to fetch the stored documents
        """
        self.logger.debug("Starting consumer for deleting objects to Workplace Search")

        thread_count = self.config.get_value("enterprise_search_sync_thread_count")
        sync_es = SyncEnterpriseSearch(
            self.config, self.logger, self.workplace_search_custom_client, queue
        )

        self.create_jobs(thread_count, sync_es.perform_sync, (), [])
        self.logger.info("Completed deletion of the Microsoft Outlook objects")

    def execute(self):
        """This function execute the start function."""
        queue = ConnectorQueue(self.logger)

        self.start_producer(queue)
        self.start_consumer(queue)
        self.logger.info("Completed Deletion sync")
