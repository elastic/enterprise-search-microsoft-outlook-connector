#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from unittest.mock import MagicMock, Mock

from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.microsoft_outlook_tasks import MicrosoftOutlookTasks


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )
    logger = logging.getLogger("unit_test_tasks")
    return configuration, logger


def create_task_obj():
    """This function create object of MicrosoftOutlookTasks class for test"""
    config, logger = settings()
    return MicrosoftOutlookTasks(logger, config)


def test_get_tasks():
    """Test method to get tasks from Microsoft Outlook"""
    task_response = {
        "_allow_permissions": [],
        "type": "Tasks",
        "Id": "123456789",
        "DisplayName": "Demo Task",
        "Description": "Due Date: 2022-04-23\n Status: NotStarted\n Owner: Sample User\n Start Date: None\n \
Complete Date: None\n Body: demo task for test\r\n\n Companies: None\n Categories: None\n Importance: Normal",
        "Created": "2022-04-22T12:12:04Z",
    }
    task_attachments_response = [
        {
            "type": "Tasks Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        }
    ]
    expected_tasks = [
        {
            "_allow_permissions": ["abc@xyz.com"],
            "type": "Tasks",
            "id": "123456789",
            "title": "Demo Task",
            "body": "Due Date: 2022-04-23\n Status: NotStarted\n Owner: Sample User\n Start Date: None\n \
Complete Date: None\n Body: demo task for test\r\n\n Companies: None\n Categories: None\n Importance: Normal",
            "created_at": "2022-04-22T12:12:04Z",
        },
        {
            "type": "Tasks Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        },
    ]
    account = Mock()
    account.tasks = MagicMock()
    account.primary_smtp_address = "abc@xyz.com"
    account_list = [account]
    ms_outlook_task_obj = create_task_obj()
    ms_outlook_task_obj.convert_tasks_to_workplace_search_documents = Mock(
        return_value=(task_response, task_attachments_response)
    )
    start_date = "2022-04-21T12:10:00Z"
    end_date = "2022-04-21T12:13:00Z"
    account.tasks.all().filter().only = Mock(return_value=[Mock()])
    source_tasks = ms_outlook_task_obj.get_tasks([], start_date, end_date, account_list)
    assert expected_tasks == source_tasks
