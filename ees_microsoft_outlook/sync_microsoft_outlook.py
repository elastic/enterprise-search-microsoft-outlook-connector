#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import csv
import os

from . import constant
from .permission_sync_command import PermissionSyncCommand


class SyncMicrosoftOutlook:
    """This class is responsible for fetching the Microsoft Outlook objects and it's
    permissions from the Workplace Search."""

    def __init__(
        self,
        config,
        logger,
        workplace_search_client,
        queue,
    ):
        self.logger = logger
        self.config = config
        self.workplace_search_client = workplace_search_client
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
        try:
            self.workplace_search_client.add_user_permissions(
                http_auth=self.ws_auth,
                content_source_id=self.ws_source,
                user=user_name,
                body={"permissions": permissions},
            )
            self.logger.info(
                f"Successfully indexed the permissions for user {user_name} to the workplace"
            )
        except Exception as exception:
            self.logger.exception(
                f"Error while indexing the permissions for user:{user_name} to the workplace. "
                f"Error: {exception}"
            )
            self.is_error = True

    def map_ms_outlook_user_to_ws_user(self, user, permissions):
        """This method is used to map the Microsoft Outlook user to Workplace Search
        user and responsible to call the user permissions indexer method
        :param user: User for indexing the permissions
        :param permissions: User permissions
        """
        rows = {}
        mapping_sheet_path = self.config.get_value("connector.user_mapping")
        if (
            mapping_sheet_path
            and os.path.exists(mapping_sheet_path)
            and os.path.getsize(mapping_sheet_path) > 0
        ):
            with open(mapping_sheet_path, encoding="UTF-8") as file:
                csvreader = csv.reader(file)
                for row in csvreader:
                    rows[row[0]] = row[1]
        user_name = rows.get(user, user)
        self.workplace_add_permission(user_name, permissions)

    def fetch_tasks(
        self, ids_list, users_account, task_object, is_deletion, start_time, end_time
    ):
        """This method is used to fetch tasks from Microsoft Outlook
        :ids_list: List of ids of documents
        :param users_account: List of user accounts
        :param mail_object: Object of task
        :param is_deletion: Boolean to check method called by deletion or indexer
        :param start_time: Start time for fetching the tasks
        :param end_time: End time for fetching the tasks
        """
        self.logger.info("Fetching Tasks from Microsoft Outlook")
        try:
            documents = task_object.get_tasks(
                ids_list, start_time, end_time, users_account
            )
        except Exception as exception:
            self.logger.exception(f"Error while fetching Tasks. Error: {exception}")
        self.logger.info("Successfully fetched Tasks from Microsoft Outlook")
        if is_deletion:
            return documents
        self.queue.append_to_queue(constant.TASKS_OBJECT.lower(), documents)

    def remove_permissions(self, workplace_search_client):
        """Removes the permissions from Workplace Search"""
        if self.config.get_value("enable_document_permission"):
            PermissionSyncCommand(
                self.logger, self.config, workplace_search_client
            ).remove_all_permissions()
        else:
            self.logger.info("'enable_document_permission' is disabled, skipping permission removal")
