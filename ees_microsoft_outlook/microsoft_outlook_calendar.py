#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to fetch calendar events from Microsoft Outlook.
"""


from . import constant
from .utils import (change_date_format, change_datetime_format, extract,
                    get_schema_fields, html_to_text,
                    insert_document_into_doc_id_storage)


class MicrosoftOutlookCalendar:
    """This class fetches Calendar Events for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config

    def get_calendar_attachments(
        self, ids_list_calendars, calendar_obj, user_email_address
    ):
        """Method is used to fetches attachments from calendar object
        :param ids_list_calendars: Documents ids of calendar
        :param calendar_obj: Object of account
        :param user_email_address: Email address of user
        Returns:
            calendar_attachments: Dictionary of calendar attachments
        """
        calendar_attachments = []

        # Logic for calendar last modified time
        calendar_created = ""
        if calendar_obj.last_modified_time:
            calendar_created = change_datetime_format(calendar_obj.last_modified_time)

        for attachment in calendar_obj.attachments:
            attachments = {
                "type": constant.CALENDAR_ATTACHMENTS_OBJECT,
                "id": attachment.attachment_id.id,
                "title": attachment.name,
                "created": calendar_created,
            }
            attachments["_allow_permissions"] = []
            if self.config.get_value("enable_document_permission"):
                attachments["_allow_permissions"] = [user_email_address]

            # Logic to insert calendar attachment into global_keys object
            insert_document_into_doc_id_storage(
                ids_list_calendars,
                attachment.attachment_id.id,
                calendar_obj.id,
                constant.CALENDAR_ATTACHMENTS_OBJECT.lower(),
                self.config.get_value("connector_platform_type"),
            )
            if hasattr(attachment, "content"):
                attachments["body"] = extract(attachment.content)
            calendar_attachments.append(attachments)
        return calendar_attachments

    def convert_calendars_to_workplace_search_documents(
        self, ids_list_calendars, calendar_obj, user_email_address
    ):
        """Fetches data from outlook and store in dictionary
        :param ids_list_calendars: Documents ids of calendar
        :param calendar_obj: Object of account
        :param user_email_address: Email address of user
        Returns:
            calendar_document: Dictionary of calendar events
            calendar_attachments_documents: Dictionary of calendar attachments
        """

        # Logic for attendees list
        attendees = ""
        if calendar_obj.required_attendees:
            for attendee in calendar_obj.required_attendees:
                if attendee.mailbox.email_address:
                    attendees = attendees + ", " + attendee.mailbox.email_address

        # Logic for meeting type
        if calendar_obj.type == "Single":
            event_type = "Normal"
        else:
            event_type = f"Recurring {calendar_obj.recurrence.pattern}"

        # Logic for calendar last modified time
        calendar_created = ""
        if calendar_obj.last_modified_time:
            calendar_created = change_datetime_format(calendar_obj.last_modified_time)

        # Logic to create document body
        calendar_document = {
            "type": constant.CALENDARS_OBJECT,
            "Id": calendar_obj.id,
            "DisplayName": calendar_obj.subject,
            "Description": f"Start Time: {calendar_obj.start}\n End Time: {calendar_obj.end}\n"
            f"Location: {calendar_obj.location}\n Organizer: {calendar_obj.organizer.email_address}\n"
            f"Meeting Type: {event_type}\n Attendee List: {attendees}\n"
            f"Descriptions: {html_to_text(calendar_obj.body)}",
            "Created": calendar_created,
        }

        # Logic to fetches attachments
        calendar_attachments_documents = []
        if calendar_obj.has_attachments:
            calendar_attachments_documents = self.get_calendar_attachments(
                ids_list_calendars, calendar_obj, user_email_address
            )

        return calendar_document, calendar_attachments_documents

    def get_calendar(self, ids_list_calendars, start_time, end_time, accounts):
        """This method is used to get documents of calendar and mapped with Workplace Search fields
        :param ids_list_calendars: List of ids of documents
        :param start_time: Start time for fetching the calendar events
        :param end_time: End time for fetching the calendar events
        param accounts: List of user accounts
        Returns:
            documents: Documents with all calendar events
        """
        documents = []
        start_time = change_date_format(start_time)
        end_time = change_date_format(end_time)
        calendar_schema = get_schema_fields(
            constant.CALENDARS_OBJECT.lower(), self.config.get_value("objects")
        )
        for account in accounts:

            try:
                # Logic to fetch Calendar Events
                for calendar in account.calendar.filter(
                    last_modified_time__gt=start_time,
                    last_modified_time__lt=end_time,
                ):

                    # Logic to insert calendar into global_keys object
                    insert_document_into_doc_id_storage(
                        ids_list_calendars,
                        calendar.id,
                        "",
                        constant.CALENDARS_OBJECT.lower(),
                        self.config.get_value("connector_platform_type"),
                    )
                    (
                        calendar_obj,
                        calendar_attachment,
                    ) = self.convert_calendars_to_workplace_search_documents(
                        ids_list_calendars, calendar, account.primary_smtp_address
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
                    if calendar_attachment:
                        documents.extend(calendar_attachment)
                # Logic to fetch Custom Calendar Events
                for child_calendar in account.calendar.children:
                    for calendar in child_calendar.filter(
                        last_modified_time__gt=start_time,
                        last_modified_time__lt=end_time,
                    ):
                        # Logic to insert calendar into global_keys object
                        insert_document_into_doc_id_storage(
                            ids_list_calendars,
                            calendar.id,
                            "",
                            constant.CALENDARS_OBJECT.lower(),
                            self.config.get_value("connector_platform_type"),
                        )
                        (
                            calendar_obj,
                            calendar_attachment,
                        ) = self.convert_calendars_to_workplace_search_documents(
                            ids_list_calendars, calendar, account.primary_smtp_address
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
                        if calendar_attachment:
                            documents.extend(calendar_attachment)

            except Exception as exception:
                self.logger.info(
                    f"Error while fetching calendar data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass

        return documents
