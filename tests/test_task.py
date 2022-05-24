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
from exchangelib import Message
from exchangelib.ewsdatetime import EWSDateTime, EWSTimeZone
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


def test_convert_task_to_workplace_search_document():
    """Test method to convert task to Workplace Search document"""
    attachments_response = [
        {
            "type": "Tasks Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        }
    ]
    expected_task = {
        "Id": "123456789",
        "DisplayName": "Demo Task",
        "Description": "Due Date: 2022-04-11T02:13:00Z\n Status: NotStarted\n Owner: abc@xyz.com\n\
Start Date: 2022-04-12T02:13:00Z\n Complete Date: 2022-04-16T02:13:00Z\nBody: Sample Text Body\n \
Companies: Demo companies\nCategories: Yellow\n Importance: Normal",
        "Created": "2022-04-11T02:13:00Z",
    }
    expected_attachments = [
        {
            "type": "Tasks Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        }
    ]
    ms_outlook_task_obj = create_task_obj()
    ms_outlook_task_obj.time_zone = EWSTimeZone("Asia/Calcutta")
    tasks_obj = Task(
        last_modified_time=EWSDateTime(2022, 4, 11, 2, 13, 00),
        id="123456789",
        subject="Demo Task",
        due_date=EWSDateTime(2022, 4, 11, 2, 13, 00),
        status="NotStarted",
        owner="abc@xyz.com",
        start_date=EWSDateTime(2022, 4, 12, 2, 13, 00),
        complete_date=EWSDateTime(2022, 4, 16, 2, 13, 00),
        text_body="Sample Text Body",
        companies=["Demo companies"],
        categories=["Yellow"],
        importance="Normal",
        has_attachments=True,
    )
    ms_outlook_task_obj.get_task_attachments = Mock(return_value=attachments_response)
    (
        source_task,
        source_task_attachments,
    ) = ms_outlook_task_obj.convert_tasks_to_workplace_search_documents(
        tasks_obj,
        [],
        "abc@xyz.com",
        tasks_obj.start_date,
        EWSDateTime(2022, 4, 16, 2, 13, 00),
    )
    print(source_task)
    assert expected_task == source_task
    assert expected_attachments == source_task_attachments


def test_get_task_attachments():
    """Test method to get task attachments"""
    expected_attachments = [
        {
            "type": "Tasks Attachments",
            "id": "123456789",
            "title": "Demo.txt",
            "created": "2022-04-12T02:13:00Z",
            "_allow_permissions": ["abc@xyz.com"],
            "body": "\n\n\n\n\n\n\n\nDemo Body\n",
        }
    ]
    task_attachments_obj = Message(
        last_modified_time=EWSDateTime(2022, 4, 12, 2, 13, 00),
        id="123456789",
    )
    task_attachments_obj.attachments = [Mock()]
    task_attachments_obj.attachments[0].attachment_id.id = "123456789"
    task_attachments_obj.attachments[0].name = "Demo.txt"
    task_attachments_obj.attachments[0].content = "Demo Body"
    task_attachments_obj.attachments[0].last_modified_time = EWSDateTime(
        2022, 4, 12, 2, 13, 00
    )
    microsoft_outlook_task_obj = create_task_obj()
    microsoft_outlook_task_obj.time_zone = EWSTimeZone("Asia/Calcutta")
    source_attachments = microsoft_outlook_task_obj.get_task_attachments(
        [],
        task_attachments_obj,
        "abc@xyz.com",
        EWSDateTime(2022, 4, 11, 2, 13, 00),
        EWSDateTime(2022, 4, 13, 2, 13, 00),
    )
    assert expected_attachments == source_attachments
