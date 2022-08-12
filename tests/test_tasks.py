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
from exchangelib.ewsdatetime import EWSDate, EWSTimeZone
from exchangelib.items.task import Task


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
    expected_tasks = [
        {
            "_allow_permissions": ["abc@xyz.com"],
            "type": "Tasks",
            "id": "123456789",
            "title": "Demo Task",
            "body": "Due Date: 2022-04-23\n Status: NotStarted\n Owner: Sample User\n Start Date: None\n \
Complete Date: None\n Body: demo task for test\r\n\n Companies: None\n Categories: None\n Importance: Normal",
            "created_at": "2022-04-22T12:12:04Z",
        }
    ]
    account = Mock()
    account.tasks = MagicMock()
    account.primary_smtp_address = "abc@xyz.com"
    account_list = [account]
    ms_outlook_task_obj = create_task_obj()
    ms_outlook_task_obj.tasks_to_docs = Mock(
        return_value=task_response
    )
    start_date = "2022-04-21T12:10:00Z"
    end_date = "2022-04-21T12:13:00Z"
    account.tasks.all().filter().only = Mock(return_value=[Mock()])
    source_tasks = ms_outlook_task_obj.get_tasks([], account_list, start_date, end_date)
    assert expected_tasks == source_tasks


def test_tasks_to_docs():
    """Test method to convert task to Workplace Search document"""
    expected_task = {
        "type": "Tasks",
        "Id": "123456789",
        "DisplayName": "Demo Task",
        "Description": """
                Due Date: 2022-04-11
                Status: NotStarted
                Owner: abc@xyz.com
                Start Date: 2022-04-12
                Complete Date: 2022-04-16
                Body: Sample Text Body
                Companies: Demo companies
                Categories: Yellow
                Importance: Normal""",
        "Created": "2022-04-11",
    }
    ms_outlook_task_obj = create_task_obj()
    ms_outlook_task_obj.time_zone = EWSTimeZone("Asia/Calcutta")
    tasks_obj = Task(
        last_modified_time=EWSDate(2022, 4, 11),
        id="123456789",
        subject="Demo Task",
        due_date=EWSDate(2022, 4, 11),
        status="NotStarted",
        owner="abc@xyz.com",
        start_date=EWSDate(2022, 4, 12),
        complete_date=EWSDate(2022, 4, 16),
        text_body="Sample Text Body",
        companies=["Demo companies"],
        categories=["Yellow"],
        importance="Normal",
        has_attachments=True,
    )
    source_task = ms_outlook_task_obj.tasks_to_docs(tasks_obj)
    assert expected_task == source_task
