#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to fetch tasks from Microsoft Outlook.
"""

from iteration_utilities import unique_everseen

from . import constant
from .utils import (change_datetime_ews_format, change_datetime_format,
                    extract, get_schema_fields,
                    insert_document_into_doc_id_storage)


class MicrosoftOutlookTasks:
    """This class fetches tasks for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.time_zone = constant.DEFAULT_TIME_ZONE

    def get_task_attachments(
        self, ids_list_tasks, task_obj, user_email_address, start_time, end_time
    ):
        """Method is used to fetch attachment from task object store in dictionary
        :param ids_list_tasks: Documents ids of tasks
        :param mail_obj: Object of account
        :param user_email_address: Email address of user
        :param start_time: Start time for fetching the tasks
        :param end_time: End time for fetching the tasks
        Returns:
            task_attachments: Dictionary of attachment
        """
        task_attachments = []
        for attachment in task_obj.attachments:

            # Logic for task last modified time
            attachment_created = ""
            if attachment.last_modified_time:
                attachment_created = change_datetime_format(
                    attachment.last_modified_time, self.time_zone
                )

            # Logic to fetch task attachments
            if attachment.last_modified_time >= start_time and attachment.last_modified_time < end_time:
                attachments = {
                    "type": constant.TASKS_ATTACHMENTS_OBJECT,
                    "id": attachment.attachment_id.id,
                    "title": attachment.name,
                    "created": attachment_created,
                }
                attachments["_allow_permissions"] = []
                if self.config.get_value("enable_document_permission"):
                    attachments["_allow_permissions"] = [user_email_address]

                # Logic to insert task attachment into global_keys object
                insert_document_into_doc_id_storage(
                    ids_list_tasks,
                    attachment.attachment_id.id,
                    task_obj.id,
                    constant.TASKS_ATTACHMENTS_OBJECT.lower(),
                    self.config.get_value("connector_platform_type"),
                )
                if hasattr(attachment, "content"):
                    attachments["body"] = extract(attachment.content)
                task_attachments.append(attachments)

        return task_attachments

    def convert_tasks_to_workplace_search_documents(
        self, task_obj, ids_list_tasks, user_email_address, start_time, end_time
    ):
        """Method is used to convert task data into Workplace Search document
        :param task_obj: Object of task
        :param ids_list_tasks: List of ids of documents
        :param user_email_address: Email address of user
        :param start_time: Start time for fetching the tasks
        :param end_time: End time for fetching the tasks
        Returns:
            task_document: Dictionary of task
            task_attachments_documents: Dictionary of attachment
        """

        # Logic for task last modified time
        task_created = ""
        if task_obj.last_modified_time:
            task_created = change_datetime_format(
                task_obj.last_modified_time, self.time_zone
            )

        # Logic for task start date
        task_start = ""
        if task_obj.start_date:
            task_start = change_datetime_format(task_obj.start_date, self.time_zone)

        # Logic for task due date
        task_due = ""
        if task_obj.due_date:
            task_due = change_datetime_format(task_obj.due_date, self.time_zone)

        # Logic for task complete date
        task_complete = ""
        if task_obj.complete_date:
            task_complete = (
                change_datetime_format(task_obj.complete_date, self.time_zone)
            ).split("T", 1)[0]

        # Logic for task categories
        task_categories = ""
        if task_obj.categories:
            task_categories_list = []
            for categories in task_obj.categories:
                task_categories_list.append(categories)
            task_categories = ", ".join(task_categories_list)

        # Logic for task companies
        task_companies = ""
        if task_obj.companies:
            task_companies = task_obj.companies[0]

        # Logic to create document body
        task_document = {
            "Id": task_obj.id,
            "DisplayName": task_obj.subject,
            "Description": f"Due Date: {task_due}\n Status: {task_obj.status}\n Owner: {task_obj.owner}\n"
            f"Start Date: {task_start}\n Complete Date: {task_complete}\n"
            f"Body: {task_obj.text_body}\n Companies: {task_companies}\n"
            f"Categories: {task_categories}\n Importance: {task_obj.importance}",
            "Created": task_created,
        }

        # Logic to fetches attachments
        task_attachments_documents = []
        if task_obj.has_attachments:
            task_attachments_documents = self.get_task_attachments(
                ids_list_tasks, task_obj, user_email_address, start_time, end_time
            )

        return task_document, task_attachments_documents

    def get_tasks(self, ids_list_tasks, start_time, end_time, accounts):
        """This method is used to fetch tasks from Microsoft Outlook
        :param ids_list_tasks: List of ids of documents
        :param start_time: Start time for fetching the tasks
        :param end_time: End time for fetching the tasks
        :param accounts: List of user accounts
        Returns:
            documents: List of documents
        """
        documents = []
        start_time = change_datetime_ews_format(start_time)
        end_time = change_datetime_ews_format(end_time)
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
                    (
                        task_obj,
                        task_attachment,
                    ) = self.convert_tasks_to_workplace_search_documents(
                        task,
                        ids_list_tasks,
                        account.primary_smtp_address,
                        start_time,
                        end_time,
                    )
                    task_map = {}
                    task_map["_allow_permissions"] = []
                    if self.config.get_value("enable_document_permission"):
                        task_map["_allow_permissions"] = [account.primary_smtp_address]
                    task_map["type"] = constant.TASKS_OBJECT
                    for ws_field, ms_field in task_schema.items():
                        task_map[ws_field] = task_obj[ms_field]
                    documents.append(task_map)
                    if task_attachment:
                        documents.extend(task_attachment)
            except Exception as exception:
                self.logger.info(
                    f"Error while fetching tasks data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass

        return list(unique_everseen(documents))
