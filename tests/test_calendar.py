#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from unittest.mock import Mock

from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.microsoft_outlook_calendar import MicrosoftOutlookCalendar
from exchangelib import Message
from exchangelib.ewsdatetime import EWSDateTime, EWSTimeZone
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


def test_convert_calendar_to_workplace_search_document():
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
        "Description": "Start Date: 2022-04-12T02:13:00Z\nEnd Date: 2022-04-13T02:13:00Z\nLocation: Demo Location\n \
Organizer: abc@xyz.com\nMeeting Type: Recurring ('Every One Week',)\n Attendee List: abc@xyz.com\n\
Description: Demo Body",
        "Created": "2022-04-11T02:13:00Z",
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
        last_modified_time=EWSDateTime(2022, 4, 11, 2, 13, 00),
        id="123465789",
        subject="Demo Event",
        start=EWSDateTime(2022, 4, 12, 2, 13, 00),
        end=EWSDateTime(2022, 4, 13, 2, 13, 00),
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
    ) = microsoft_outlook_cal_obj.convert_calendars_to_workplace_search_documents(
        [], calendar_obj, "abc@xyz.com", calendar_obj.start, calendar_obj.end
    )
    assert expected_calendar_document == source_calendar
    assert expected_attachments_documents == source_calendar_attachments


def test_get_calendar_attachments():
    """Test method to get calendar attachments"""
    expected_attachments = [
        {
            "type": "Calendar Attachments",
            "id": "123456789",
            "title": "Demo.txt",
            "created": "2022-04-12T03:13:00Z",
            "_allow_permissions": ["abc@xyz.com"],
            "body": "\n\n\n\n\n\n\n\nDemo Body\n",
        }
    ]
    calendar_attachments_obj = Message(
        last_modified_time=EWSDateTime(2022, 4, 12, 3, 13, 00),
        id="123456789",
    )
    calendar_attachments_obj.attachments = [Mock()]
    calendar_attachments_obj.attachments[0].attachment_id.id = "123456789"
    calendar_attachments_obj.attachments[0].name = "Demo.txt"
    calendar_attachments_obj.attachments[0].content = "Demo Body"
    calendar_attachments_obj.attachments[0].last_modified_time = EWSDateTime(
        2022, 4, 12, 3, 13, 00
    )
    microsoft_outlook_calendar_obj = create_calendar_obj()
    microsoft_outlook_calendar_obj.time_zone = EWSTimeZone("Asia/Calcutta")
    source_attachments = microsoft_outlook_calendar_obj.get_calendar_attachments(
        [],
        calendar_attachments_obj,
        "abc@xyz.com",
        EWSDateTime(2022, 4, 12, 2, 13, 00),
        EWSDateTime(2022, 4, 13, 2, 13, 00),
    )
    assert expected_attachments == source_attachments
