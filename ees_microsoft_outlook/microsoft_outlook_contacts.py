#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This class fetches all contacts of all users from Microsoft Outlook
"""
import exchangelib
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


class MicrosoftOutlookContacts:
    """This class fetches contacts for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.time_zone = constant.DEFAULT_TIME_ZONE
        self.retry_count = self.config.get_value("retry_count")

    def convert_contacts_to_workplace_search_documents(self, contact_obj):
        """Method is used to convert contact data into Workplace Search document
        :param contact_obj: Object of contact
        Returns:
            contact_document: Dictionary of contact
        """

        # Logic for contact email address
        contact_emails = ""
        if contact_obj.email_addresses:
            contact_emails_list = []
            for email in contact_obj.email_addresses:
                contact_emails_list.append(email.email)
            contact_emails = ", ".join(contact_emails_list)

        # Logic for contact phone number
        contact_numbers = ""
        if contact_obj.phone_numbers:
            contact_numbers_list = []
            for number in contact_obj.phone_numbers:
                contact_numbers_list.append(number.phone_number)
            contact_numbers = ", ".join(contact_numbers_list)

        # Logic for contact last modified time
        contact_created = ""
        if contact_obj.last_modified_time:
            contact_created = change_datetime_format(
                contact_obj.last_modified_time, self.time_zone
            )

        # Logic to remove year from birthdate if birth year is kept empty by the user
        if contact_obj.birthday:
            if 1604 == contact_obj.birthday.year:
                contact_obj.birthday = contact_obj.birthday.strftime("%m-%d")

        # Logic to create document body
        contact_document = {
            "Id": contact_obj.id,
            "DisplayName": contact_obj.display_name,
            "Description": f"Email Addresses: {contact_emails}\nCompany Name: {contact_obj.company_name}\n"
            f"Contact Numbers: {contact_numbers}\nDate of Birth: {contact_obj.birthday}",
            "Created": contact_created,
        }
        return contact_document

    @retry(exception_list=(requests.exceptions.RequestException,))
    def get_contacts(self, ids_list_contacts, accounts, start_time, end_time):
        """This method is used to fetches contacts from the Microsoft Outlook
        :param ids_list_contacts: List of documents which is already fetched
        :param accounts: List of user accounts
        :param start_time: Start time for fetching the contacts
        :param end_time: End time for fetching the contacts
        Returns:
            documents: List of contact documents
        """
        documents = []
        start_time = convert_datetime_to_ews_format(start_time)
        end_time = convert_datetime_to_ews_format(end_time)
        contact_schema = get_schema_fields(
            constant.CONTACTS_OBJECT.lower(), self.config.get_value("objects")
        )
        for account in accounts:

            # Logic to set time zone according to user account
            self.time_zone = account.default_timezone

            try:
                # Logic to fetch contacts
                folder = account.root / "Top of Information Store" / "Contacts"
                for contact in (
                    folder.all()
                    .filter(
                        last_modified_time__gt=start_time,
                        last_modified_time__lt=end_time,
                    )
                    .only(
                        "email_addresses",
                        "phone_numbers",
                        "last_modified_time",
                        "display_name",
                        "company_name",
                        "birthday",
                    )
                ):
                    if isinstance(contact, exchangelib.items.contact.Contact):

                        # Logic to insert contact into global_keys object
                        insert_document_into_doc_id_storage(
                            ids_list_contacts,
                            contact.id,
                            "",
                            constant.CONTACTS_OBJECT.lower(),
                            self.config.get_value("connector_platform_type"),
                        )
                        contact_obj = (
                            self.convert_contacts_to_workplace_search_documents(contact)
                        )
                        contact_map = {}
                        contact_map["_allow_permissions"] = []
                        if self.config.get_value("enable_document_permission"):
                            contact_map["_allow_permissions"] = [
                                account.primary_smtp_address
                            ]
                        contact_map["type"] = constant.CONTACTS_OBJECT
                        for ws_field, ms_field in contact_schema.items():
                            contact_map[ws_field] = contact_obj[ms_field]
                        documents.append(contact_map)
            except requests.exceptions.RequestException as request_error:
                raise requests.exceptions.RequestException(
                    f"Error while fetching contacts data for {account.primary_smtp_address}. Error: {request_error}"
                )
            except Exception as exception:
                self.logger.info(
                    f"Error while fetching contacts data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass
        return list(unique_everseen(documents))
