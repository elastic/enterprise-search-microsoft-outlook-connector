#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to fetch tasks from Microsoft Outlook.
"""
import requests
from iteration_utilities import unique_everseen

from . import constant
from .utils import (
    change_datetime_format,
    convert_datetime_to_ews_format,
    get_schema_fields,
    insert_document_into_doc_id_storage,
    retry,
)


class MicrosoftOutlookTasks:
    """This class fetches tasks for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.time_zone = constant.DEFAULT_TIME_ZONE
        self.retry_count = self.config.get_value("retry_count")

    def tasks_to_docs(self, task_obj):
        """Method is used to convert task data into Workplace Search document
        :param task_obj: Object of task
        Returns:
            task_document: Dictionary of task
        """

        # Logic for task last modified time
        if task_obj.last_modified_time:
            task_created = change_datetime_format(
                task_obj.last_modified_time, self.time_zone
            )
        else:
            task_created = ""

        # Logic for task start date
        if task_obj.start_date:
            task_start = change_datetime_format(task_obj.start_date, self.time_zone)
        else:
            task_start = ""

        # Logic for task due date
        if task_obj.due_date:
            task_due = change_datetime_format(task_obj.due_date, self.time_zone)
        else:
            task_due = ""

        # Logic for task complete date
        if task_obj.complete_date:
            task_complete = (
                change_datetime_format(task_obj.complete_date, self.time_zone)
            ).split("T", 1)[0]
        else:
            task_complete = ""

        # Logic for task categories
        if task_obj.categories:
            task_categories_list = []
            for categories in task_obj.categories:
                task_categories_list.append(categories)
            task_categories = ", ".join(task_categories_list)
        else:
            task_categories = ""

        # Logic for task companies
        if task_obj.companies:
            task_companies = task_obj.companies[0]
        else:
            task_companies = ""

        # Logic to create document body
        task_document = {
            "type": constant.TASKS_OBJECT,
            "Id": task_obj.id,
            "DisplayName": task_obj.subject,
            "Created": task_created,
        }

        # Logic to bifurcate connector platform document
        if constant.CONNECTOR_TYPE_MICROSOFT_EXCHANGE in self.config.get_value(
            "connector_platform_type"
        ):
            task_document[
                "Description"
            ] = f"""
                Due Date: {task_due}
                Status: {task_obj.status}
                Owner: {task_obj.owner}
                Start Date: {task_start}
                Complete Date: {task_complete}
                Body: {task_obj.text_body}
                Companies: {task_companies}
                Categories: {task_categories}
                Importance: {task_obj.importance}"""

        elif constant.CONNECTOR_TYPE_OFFICE365 in self.config.get_value(
            "connector_platform_type"
        ):
            task_document[
                "Description"
            ] = f"""
                Due Date: {task_due}
                Status: {task_obj.status}
                Owner: {task_obj.owner}
                Complete Date: {task_complete}
                Body: {task_obj.text_body}
                Categories: {task_categories}
                Importance: {task_obj.importance}"""

        return task_document

    @retry(exception_list=(requests.exceptions.RequestException,))
    def get_tasks(self, ids_list_tasks, accounts, start_time, end_time):
        """This method is used to fetch tasks from Microsoft Outlook
        :param ids_list_tasks: List of ids of documents
        :param accounts: List of user accounts
        :param start_time: Start time for fetching the tasks
        :param end_time: End time for fetching the tasks
        Returns:
            documents: List of documents
        """
        documents = []
        start_time = convert_datetime_to_ews_format(start_time)
        end_time = convert_datetime_to_ews_format(end_time)
        task_schema = get_schema_fields(
            constant.TASKS_OBJECT.lower(), self.config.get_value("objects")
        )

        for account in accounts:

            # Logic to set time zone according to user account
            self.time_zone = account.default_timezone

            try:
                # Logic to fetch tasks
                for task in (
                    account.tasks.all()
                    .filter(
                        last_modified_time__gt=start_time,
                        last_modified_time__lt=end_time,
                    )
                    .only(
                        "last_modified_time",
                        "due_date",
                        "complete_date",
                        "subject",
                        "status",
                        "owner",
                        "start_date",
                        "text_body",
                        "companies",
                        "categories",
                        "importance",
                        "has_attachments",
                        "attachments",
                    )
                ):

                    # Logic to insert task into global_keys object
                    insert_document_into_doc_id_storage(
                        ids_list_tasks,
                        task.id,
                        "",
                        constant.TASKS_OBJECT.lower(),
                        self.config.get_value("connector_platform_type"),
                    )
                    task_obj = self.tasks_to_docs(task)
                    task_map = {}
                    task_map["_allow_permissions"] = []
                    if self.config.get_value("enable_document_permission"):
                        task_map["_allow_permissions"] = [account.primary_smtp_address]
                    task_map["type"] = constant.TASKS_OBJECT
                    for ws_field, ms_field in task_schema.items():
                        task_map[ws_field] = task_obj[ms_field]
                    documents.append(task_map)
            except requests.exceptions.RequestException as request_error:
                raise requests.exceptions.RequestException(
                    f"Error while fetching tasks data for {account.primary_smtp_address}. Error: {request_error}"
                )
            except Exception as exception:
                self.logger.info(
                    f"Error while fetching tasks data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass

        return list(unique_everseen(documents))
