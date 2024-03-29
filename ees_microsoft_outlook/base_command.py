#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Module contains a base command interface.
Connector can run multiple commands such as full-sync, incremental-sync,
etc. This module provides convenience interface defining the shared
objects and methods that will can be used by commands."""
import logging

# For Python>=3.8 cached_property should be imported from functools,
# and for the prior versions it should be imported from cached_property
try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property

from concurrent.futures import ThreadPoolExecutor, as_completed

from . import constant
from .configuration import Configuration
from .enterprise_search_wrapper import EnterpriseSearchWrapper
from .local_storage import LocalStorage
from .microsoft_outlook_calendar import MicrosoftOutlookCalendar
from .microsoft_outlook_contacts import MicrosoftOutlookContacts
from .microsoft_outlook_mails import MicrosoftOutlookMails
from .microsoft_outlook_tasks import MicrosoftOutlookTasks
from .utils import split_date_range_into_chunks


class BaseCommand:
    """Base interface for all module commands.
    Inherit from it and implement 'execute' method, then add
    code to cli.py to register this command."""

    def __init__(self, args):
        self.args = args

    def execute(self):
        """Run the command.
        This method is overridden by actual commands with logic
        that is specific to each command implementing it."""
        raise NotImplementedError

    @cached_property
    def logger(self):
        """Get the logger instance for the running command.
        log level will be determined by the configuration
        setting log_level.
        """
        log_level = self.config.get_value("log_level")
        logger = logging.getLogger(__name__)
        logger.propagate = True
        logger.setLevel(log_level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s Thread[%(thread)s]: %(message)s"
        )
        handler.setFormatter(formatter)
        # Uncomment the following lines to output logs in ECS-compatible format
        # formatter = ecs_logging.StdlibFormatter()
        # handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)

        return logger

    @cached_property
    def workplace_search_custom_client(self):
        """Get the Workplace Search custom client instance for the running command."""
        return EnterpriseSearchWrapper(self.logger, self.config, self.args)

    @cached_property
    def config(self):
        """Get the configuration for the connector for the running command."""
        file_name = self.args.config_file
        return Configuration(file_name)

    @cached_property
    def local_storage(self):
        """Get the object for local storage to fetch and update ids stored locally"""
        return LocalStorage(self.logger)

    @cached_property
    def microsoft_outlook_mail_object(self):
        """Get the object for fetching the mails related data"""
        return MicrosoftOutlookMails(self.logger, self.config)

    @cached_property
    def microsoft_outlook_calendar_object(self):
        """Get the object for fetching the calendars related data"""
        return MicrosoftOutlookCalendar(self.logger, self.config)

    @cached_property
    def microsoft_outlook_contact_object(self):
        """Get the object for fetching the contacts related data"""
        return MicrosoftOutlookContacts(self.logger, self.config)

    @cached_property
    def microsoft_outlook_task_object(self):
        """Get the object for fetching the tasks related data"""
        return MicrosoftOutlookTasks(self.logger, self.config)

    def create_jobs(self, thread_count, func, args, iterable_list):
        """Creates a thread pool of given number of thread count
        :param thread_count: Total number of threads to be spawned
        :param func: The target function on which the async calls would be made
        :param args: Arguments for the targeted function
        :param iterable_list: list to iterate over and create thread
        """
        # If iterable_list is present, then iterate over the list and pass each list element
        # as an argument to the async function, else iterate over number of threads configured
        if iterable_list:
            documents = []
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                future_to_path = {
                    executor.submit(func, *args, *list_element): list_element
                    for list_element in iterable_list
                }
                for future in as_completed(future_to_path):
                    try:
                        if future.result():
                            documents.extend(future.result())
                    except Exception as exception:
                        self.logger.exception(
                            f"Error while fetching the data from Microsoft Outlook. Error {exception}"
                        )
            return documents
        else:
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                for _ in range(thread_count):
                    executor.submit(func)

    def create_jobs_for_mails(
        self,
        indexing_type,
        sync_microsoft_outlook,
        thread_count,
        users_accounts,
        time_range_list,
        end_time,
        queue,
    ):
        """Create job for fetching the mails
        :param indexing_type: The type of the indexing i.e. Full or Incremental
        :param sync_microsoft_outlook: Object of SyncMicrosoftOutlook
        :param thread_count: Thread count to make partitions
        :param users_accounts: List of users account
        :param time_range_list: List of time range for fetching the data
        :param end_time: End time for setting checkpoint
        :param queue: Shared queue for storing the data
        """
        if constant.MAILS_OBJECT.lower() not in self.config.get_value("objects"):
            self.logger.info(
                "Mails are not getting indexed because user has excluded from configuration file"
            )
            return
        self.logger.debug("Started fetching the mails")
        ids_list = []
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.MAIL_DELETION_PATH
        )
        ids_list = storage_with_collection.get("global_keys")
        self.create_jobs(
            thread_count,
            sync_microsoft_outlook.fetch_mails,
            (ids_list, users_accounts, self.microsoft_outlook_mail_object),
            time_range_list,
        )
        storage_with_collection["global_keys"] = list(ids_list)
        self.local_storage.update_storage(
            storage_with_collection, constant.MAIL_DELETION_PATH
        )
        queue.put_checkpoint(constant.MAILS_OBJECT.lower(), end_time, indexing_type)

    def create_jobs_for_calendar(
        self,
        indexing_type,
        sync_microsoft_outlook,
        thread_count,
        users_accounts,
        time_range_list,
        end_time,
        queue,
    ):
        """Create job for fetching the calendars
        :param indexing_type: The type of the indexing i.e. Full or Incremental
        :param sync_microsoft_outlook: Object of SyncMicrosoftOutlook
        :param thread_count: Thread count to make partitions
        :param users_accounts: List of users account
        :param time_range_list: List of time range for fetching the data
        :param end_time: End time for setting checkpoint
        :param queue: Shared queue for storing the data
        """
        if constant.CALENDARS_OBJECT.lower() not in self.config.get_value("objects"):
            self.logger.info(
                "Calendar events are not getting indexed because user has excluded from configuration file"
            )
            return
        self.logger.debug("Started fetching the calendar")
        ids_list = []
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.CALENDAR_DELETION_PATH
        )
        ids_list = storage_with_collection.get("global_keys")
        self.create_jobs(
            thread_count,
            sync_microsoft_outlook.fetch_calendar,
            (ids_list, users_accounts, self.microsoft_outlook_calendar_object),
            time_range_list,
        )
        storage_with_collection["global_keys"] = list(ids_list)
        self.local_storage.update_storage(
            storage_with_collection, constant.CALENDAR_DELETION_PATH
        )
        queue.put_checkpoint(constant.CALENDARS_OBJECT.lower(), end_time, indexing_type)

    def create_jobs_for_contacts(
        self,
        indexing_type,
        sync_microsoft_outlook,
        thread_count,
        users_accounts,
        time_range_list,
        end_time,
        queue,
    ):
        """Create job for fetching the contacts
        :param indexing_type: The type of the indexing i.e. Full or Incremental
        :param sync_microsoft_outlook: Object of SyncMicrosoftOutlook
        :param thread_count: Thread count to make partitions
        :param users_accounts: List of users account
        :param time_range_list: List of time range for fetching the data
        :param end_time: End time for setting checkpoint
        :param queue: Shared queue for storing the data
        """
        if constant.CONTACTS_OBJECT.lower() not in self.config.get_value("objects"):
            self.logger.info(
                "Contacts are not getting indexed because user has excluded from configuration file"
            )
            return
        self.logger.debug("Started fetching the contacts")
        ids_list = []
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.CONTACT_DELETION_PATH
        )
        ids_list = storage_with_collection.get("global_keys")
        self.create_jobs(
            thread_count,
            sync_microsoft_outlook.fetch_contacts,
            (ids_list, users_accounts, self.microsoft_outlook_contact_object),
            time_range_list,
        )
        storage_with_collection["global_keys"] = list(ids_list)
        self.local_storage.update_storage(
            storage_with_collection, constant.CONTACT_DELETION_PATH
        )
        queue.put_checkpoint(constant.CONTACTS_OBJECT.lower(), end_time, indexing_type)

    def create_jobs_for_tasks(
        self,
        indexing_type,
        sync_microsoft_outlook,
        thread_count,
        users_accounts,
        time_range_list,
        end_time,
        queue,
    ):
        """Create job for fetching the tasks
        :param indexing_type: The type of the indexing i.e. Full or Incremental
        :param sync_microsoft_outlook: Object of SyncMicrosoftOutlook
        :param thread_count: Thread count to make partitions
        :param users_accounts: List of users account
        :param time_range_list: List of time range for fetching the data
        :param end_time: End time for setting checkpoint
        :param queue: Shared queue for storing the data
        """
        if constant.TASKS_OBJECT.lower() not in self.config.get_value("objects"):
            self.logger.info(
                "Tasks are not getting indexed because user has excluded from configuration file"
            )
            return
        self.logger.debug("Started fetching the tasks")
        ids_list = []
        storage_with_collection = self.local_storage.get_storage_with_collection(
            self.local_storage, constant.TASK_DELETION_PATH
        )
        ids_list = storage_with_collection.get("global_keys")
        self.create_jobs(
            thread_count,
            sync_microsoft_outlook.fetch_tasks,
            (ids_list, users_accounts, self.microsoft_outlook_task_object),
            time_range_list,
        )
        storage_with_collection["global_keys"] = list(ids_list)
        self.local_storage.update_storage(
            storage_with_collection, constant.TASK_DELETION_PATH
        )
        queue.put_checkpoint(constant.TASKS_OBJECT.lower(), end_time, indexing_type)

    def get_datetime_iterable_list(self, start_time, end_time):
        """Get time range partition based on time duration and thread count
        :param start_time: Start time for fetching data
        :param end_time: End time for fetching data
        """
        thread_count = self.config.get_value("source_sync_thread_count")
        datelist_mails = split_date_range_into_chunks(
            start_time,
            end_time,
            thread_count,
        )
        time_range_list = []
        for num in range(0, thread_count):
            time_range_list.append((datelist_mails[num], datelist_mails[num + 1]))
        return time_range_list
