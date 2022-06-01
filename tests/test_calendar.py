#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from unittest.mock import Mock

from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.microsoft_outlook_calendar import \
    MicrosoftOutlookCalendar


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""

    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )
    logger = logging.getLogger("unit_test_calendar")
    return configuration, logger


def create_calendar_obj():
    """This function create object of MicrosoftOutlookCalendar class for test"""
    config, logger = settings()
    return MicrosoftOutlookCalendar(logger, config)


def test_get_calendar():
    """Test method to get calendars from Microsoft Outlook"""
    calendar_response = {
        "_allow_permissions": [],
        "type": "Calendar",
        "Id": "123456789",
        "DisplayName": "demo_calendar",
        "Description": "Start Time: 2022-04-22 09:30:00+00:00 \n End Time: 2022-04-22 11:30:00+00:00 \n\
Location: demo\n Organizer: abc@xyz.com \n Meeting Type: Normal \n Attendee List: \n\
Descriptions: demo calendar event\n",
        "Created": "2022-04-22T10:11:38Z",
    }
    calendar_attachments_response = [
        {
            "type": "Calendar Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        }
    ]
    expected_calendar_events = [
        {
            "_allow_permissions": ["abc@xyz.com"],
            "type": "Calendar",
            "id": "123456789",
            "title": "demo_calendar",
            "body": "Start Time: 2022-04-22 09:30:00+00:00 \n End Time: 2022-04-22 11:30:00+00:00 \n\
Location: demo\n Organizer: abc@xyz.com \n Meeting Type: Normal \n Attendee List: \n\
Descriptions: demo calendar event\n",
            "created_at": "2022-04-22T10:11:38Z",
        },
        {
            "type": "Calendar Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        },
    ]
    account = Mock()
    account_list = [account]
    account.primary_smtp_address = "abc@xyz.com"
    calendar_obj = create_calendar_obj()
    calendar_obj.convert_calendars_to_workplace_search_documents = Mock(
        return_value=(calendar_response, calendar_attachments_response)
    )
    start_date = "2022-04-21T12:10:00Z"
    end_date = "2022-04-21T12:13:00Z"
    account.calendar.filter().only = Mock(return_value=[Mock()])
    source_calendar_events = calendar_obj.get_calendar(
        [], start_date, end_date, account_list
    )
    assert expected_calendar_events == source_calendar_events
