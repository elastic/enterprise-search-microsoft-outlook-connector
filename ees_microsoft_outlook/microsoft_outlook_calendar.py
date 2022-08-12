#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to fetch calendar events from Microsoft Outlook.
"""
import requests

from . import constant
from .utils import (convert_datetime_to_ews_format, change_datetime_format, get_schema_fields, html_to_text,
                    insert_document_into_doc_id_storage, retry)


class MicrosoftOutlookCalendar:
    """This class fetches Calendar Events for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.time_zone = constant.DEFAULT_TIME_ZONE
        self.retry_count = self.config.get_value("retry_count")

    def calendar_to_docs(
        self,
        calendar_obj,
        child_calendar,
    ):
        """Fetches data from outlook and store in dictionary
        :param calendar_obj: Object of account
        :param child_calendar: Type of child calendar
        Returns:
            calendar_document: Dictionary of calendar events
        """

        # Logic for attendees list
        if calendar_obj.required_attendees:
            attendees_list = []
            for attendee in calendar_obj.required_attendees:
                if attendee.mailbox.email_address:
                    attendees_list.append(attendee.mailbox.email_address)
            attendees = ", ".join(attendees_list)
        else:
            attendees = ""

        # Logic for meeting type
        if calendar_obj.type == "Single":
            event_type = "Normal"
        else:
            event_type = f"Recurring {calendar_obj.recurrence.pattern}"

        # Logic for calendar last modified time
        if calendar_obj.last_modified_time:
            calendar_created = change_datetime_format(
                calendar_obj.last_modified_time, self.time_zone
            )
        else:
            calendar_created = ""

        # Logic to create document body
        calendar_document = {
            "type": constant.CALENDARS_OBJECT,
            "Id": calendar_obj.id,
            "DisplayName": calendar_obj.subject,
            "Created": calendar_created,
        }

        # Logic for Birthday Calendar Events
        if child_calendar in ["Folder (Birthdays)", "Birthdays (Birthdays)"]:
            calendar_document["Description"] = f"""
                Date: {(change_datetime_format(calendar_obj.start, self.time_zone)).split('T', 1)[0]}
                Organizer: {calendar_obj.organizer.email_address}\n Meeting Type: {event_type}\n"""

        # Logic for Other Calendar Events
        else:
            calendar_document["Description"] = f"""
                Start Date: {change_datetime_format(calendar_obj.start, self.time_zone)}
                End Date: {change_datetime_format(calendar_obj.end, self.time_zone)}
                Location: {calendar_obj.location}
                Organizer: {calendar_obj.organizer.email_address}
                Meeting Type: {event_type}
                Attendee List: {attendees}
                Description: {html_to_text(calendar_obj.body)}"""

        return calendar_document

    @retry(exception_list=(requests.exceptions.RequestException,))
    def get_calendar(self, ids_list_calendars, accounts, start_time, end_time):
        """This method is used to get documents of calendar and mapped with Workplace Search fields
        :param ids_list_calendars: List of ids of documents
        param accounts: List of user accounts
        :param start_time: Start time for fetching the calendar events
        :param end_time: End time for fetching the calendar events
        Returns:
            documents: Documents with all calendar events
        """
        documents = []
        start_time = convert_datetime_to_ews_format(start_time)
        end_time = convert_datetime_to_ews_format(end_time)
        calendar_schema = get_schema_fields(
            constant.CALENDARS_OBJECT.lower(), self.config.get_value("objects")
        )
        for account in accounts:

            # Logic to set time zone according to user account
            self.time_zone = account.default_timezone

            try:
                # Logic to fetch Calendar Events
                for calendar in account.calendar.filter(
                    last_modified_time__gt=start_time,
                    last_modified_time__lt=end_time,
                ).only(
                    "required_attendees",
                    "type",
                    "recurrence",
                    "last_modified_time",
                    "subject",
                    "start",
                    "end",
                    "location",
                    "organizer",
                    "body",
                    "has_attachments",
                    "attachments",
                ):

                    # Logic to insert calendar into global_keys object
                    insert_document_into_doc_id_storage(
                        ids_list_calendars,
                        calendar.id,
                        "",
                        constant.CALENDARS_OBJECT.lower(),
                        self.config.get_value("connector_platform_type"),
                    )
                    calendar_obj = self.calendar_to_docs(
                        calendar,
                        str(calendar),
                    )
                    calendar_map = {}
                    calendar_map["_allow_permissions"] = []
                    if self.config.get_value("enable_document_permission"):
                        calendar_map["_allow_permissions"] = [
                            account.primary_smtp_address
                        ]
                    calendar_map["type"] = calendar_obj["type"]
                    for ws_field, ms_fields in calendar_schema.items():
                        calendar_map[ws_field] = calendar_obj[ms_fields]
                    documents.append(calendar_map)
            except requests.exceptions.RequestException as request_error:
                raise requests.exceptions.RequestException(
                    f"Error while fetching calendar data for {account.primary_smtp_address}. Error: {request_error}"
                )
            except Exception as exception:
                self.logger.info(
                    f"Error while fetching calendar data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass

        return documents
