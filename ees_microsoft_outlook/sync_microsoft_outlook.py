#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import csv
import os

from . import constant


class SyncMicrosoftOutlook:
    """This class is responsible for fetching the Microsoft Outlook objects and it's
    permissions from the Workplace Search."""

    def __init__(
        self,
        config,
        logger,
        workplace_search_custom_client,
        queue,
    ):
        self.logger = logger
        self.config = config
        self.workplace_search_custom_client = workplace_search_custom_client
        self.objects = config.get_value("objects")
        self.permission = config.get_value("enable_document_permission")
        self.microsoft_outlook_thread_count = config.get_value(
            "source_sync_thread_count"
        )
        self.ws_auth = config.get_value("enterprise_search.api_key")
        self.ws_source = config.get_value("enterprise_search.source_id")
        self.queue = queue

    def workplace_add_permission(self, user_name, permissions):
        """Indexes the user permissions into Workplace Search
        :param user_name: A string value denoting the username of the user
        :param permissions: Permissions that needs to be provided to the user
        """
        self.workplace_search_custom_client.add_permissions(
            user_name,
            permissions,
        )

    def map_ms_outlook_user_to_ws_user(self, user, permissions):
        """This method is used to map the Microsoft Outlook user to Workplace Search
        user and responsible to call the user permissions indexer method
        :param user: User for indexing the permissions
        :param permissions: User permissions
        """
        rows = {}
        mapping_sheet_path = self.config.get_value("connector.user_mapping")
        if mapping_sheet_path and os.path.exists(mapping_sheet_path) and os.path.getsize(mapping_sheet_path) > 0:
            with open(mapping_sheet_path, encoding="UTF-8") as file:
                csvreader = csv.reader(file)
                for row in csvreader:
                    rows[row[0]] = row[1]
        user_name = rows.get(user, user)
        self.workplace_add_permission(user_name, permissions)

    def fetch_mails(self, ids_list, users_account, mail_object, start_time, end_time):
        """This method is used to fetch mails from Microsoft Outlook
        :ids_list: List of ids of documents
        :param users_account: List of user accounts
        :param mail_object: Object of mails
        :param start_time: Start time for fetching the mails
        :param end_time: End time for fetching the mails
        """
        self.logger.info("Fetching Mails from Microsoft Outlook")
        try:
            documents = mail_object.get_mails(
                ids_list, users_account, start_time, end_time
            )
        except Exception as exception:
            self.logger.exception(f"Error while fetching Mails. Error: {exception}")
        self.logger.info("Successfully fetched Mails from Microsoft Outlook")
        self.queue.append_to_queue(constant.MAILS_OBJECT.lower(), documents)

    def fetch_calendar(
        self, ids_list, users_account, calendar_object, start_time, end_time
    ):
        """This method is used to fetch calendar from Microsoft Outlook
        :ids_list: List of ids of documents
        :param users_accounts: List of user account
        :param calendar_object: Object of calendar
        :param start_time: Start time for fetching the calendar
        :param end_time: End time for fetching the calendar
        """
        self.logger.info("Fetching Calendars from Microsoft Outlook")
        try:
            documents = calendar_object.get_calendar(
                ids_list, users_account, start_time, end_time
            )
        except Exception as exception:
            self.logger.exception(f"Error while fetching Calendar. Error: {exception}")
        self.logger.info("Successfully fetched Calendars from Microsoft Outlook")
        self.queue.append_to_queue(constant.CALENDARS_OBJECT.lower(), documents)

    def fetch_contacts(
        self, ids_list, users_account, contact_object, start_time, end_time
    ):
        """This method is used to fetch contacts from Microsoft Outlook
        :ids_list: List of ids of documents
        :param users_account: List of user account
        :param contact_object: Object of contacts
        :param start_time: Start time for fetching the contacts
        :param end_time: End time for fetching the contacts
        """
        self.logger.info("Fetching Contacts from Microsoft Outlook")
        try:
            documents = contact_object.get_contacts(
                ids_list, users_account, start_time, end_time
            )
        except Exception as exception:
            self.logger.exception(f"Error while fetching Contacts. Error: {exception}")
        self.logger.info("Successfully fetched Contacts from Microsoft Outlook")
        self.queue.append_to_queue(constant.CONTACTS_OBJECT.lower(), documents)

    def fetch_tasks(self, ids_list, users_account, task_object, start_time, end_time):
        """This method is used to fetch tasks from Microsoft Outlook
        :ids_list: List of ids of documents
        :param users_account: List of user accounts
        :param task_object: Object of task
        :param start_time: Start time for fetching the tasks
        :param end_time: End time for fetching the tasks
        """
        self.logger.info("Fetching Tasks from Microsoft Outlook")
        try:
            documents = task_object.get_tasks(
                ids_list, users_account, start_time, end_time
            )
        except Exception as exception:
            self.logger.exception(f"Error while fetching Tasks. Error: {exception}")
        self.logger.info("Successfully fetched Tasks from Microsoft Outlook")
        self.queue.append_to_queue(constant.TASKS_OBJECT.lower(), documents)
