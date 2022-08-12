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
from exchangelib.ewsdatetime import EWSDate, EWSTimeZone
from exchangelib.items.calendar_item import CalendarItem


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
    calendar_obj.calendar_to_docs = Mock(
        return_value=(calendar_response, calendar_attachments_response)
    )
    start_date = "2022-04-21T12:10:00Z"
    end_date = "2022-04-21T12:13:00Z"
    account.calendar.filter().only = Mock(return_value=[Mock()])
    source_calendar_events = calendar_obj.get_calendar(
        [], account_list, start_date, end_date
    )
    assert expected_calendar_events == source_calendar_events


def test_calendar_to_docs():
    """Test method to convert calendar event to Workplace Search document"""
    attachment_response = [
        {
            "type": "Calendar Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        }
    ]
    expected_calendar_document = {
        "type": "Calendar",
        "Id": "123465789",
        "DisplayName": "Demo Event",
        "Description": """
                Start Date: 2022-04-12
                End Date: 2022-04-13
                Location: Demo Location
                Organizer: abc@xyz.com
                Meeting Type: Recurring ('Every One Week',)
                Attendee List: abc@xyz.com
                Description: Demo Body""",
        "Created": "2022-04-11",
    }
    expected_attachments_documents = [
        {
            "type": "Calendar Attachments",
            "id": "987654321",
            "title": "demo_attachment.txt",
            "created": "2022-04-22T10:11:38Z",
            "_allow_permissions": [],
            "body": "\n\n\n\n\n\n\n\ndemo body\n",
        }
    ]
    microsoft_outlook_cal_obj = create_calendar_obj()
    microsoft_outlook_cal_obj.time_zone = EWSTimeZone("Asia/Calcutta")
    calendar_obj = CalendarItem(
        required_attendees=[Mock()],
        type="RecurringMaster",
        recurrence=Mock(),
        last_modified_time=EWSDate(2022, 4, 11),
        id="123465789",
        subject="Demo Event",
        start=EWSDate(2022, 4, 12),
        end=EWSDate(2022, 4, 13),
        location="Demo Location",
        organizer=Mock(),
        body="Demo Body",
        has_attachments=True,
    )
    calendar_obj.required_attendees[0].mailbox.email_address = "abc@xyz.com"
    calendar_obj.recurrence.pattern = ("Every One Week",)
    calendar_obj.organizer.email_address = "abc@xyz.com"
    microsoft_outlook_cal_obj.get_calendar_attachments = Mock(
        return_value=attachment_response
    )
    (
        source_calendar,
        source_calendar_attachments,
    ) = microsoft_outlook_cal_obj.calendar_to_docs(
        [], calendar_obj, "abc@xyz.com", calendar_obj.start, calendar_obj.end, ""
    )
    assert expected_calendar_document == source_calendar
    assert expected_attachments_documents == source_calendar_attachments
