#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from unittest.mock import MagicMock, Mock

import exchangelib
from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.microsoft_outlook_contacts import \
    MicrosoftOutlookContacts
from exchangelib.ewsdatetime import EWSDate, EWSTimeZone
from exchangelib.items.contact import Contact


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )
    logger = logging.getLogger("unit_test_contacts")
    return configuration, logger


def create_contact_obj():
    """This function create object of MicrosoftOutlookContacts class for test"""
    config, logger = settings()
    return MicrosoftOutlookContacts(logger, config)


def test_get_contacts():
    """Test method to get contacts from Microsoft Outlook"""
    contact_response = {
        "_allow_permissions": [],
        "type": "Contacts",
        "Id": "123456789",
        "DisplayName": "Demo User",
        "Description": "Email Addresses: , demo@abc.com\n Company Name: None\nContact Numbers: \n Date of Birth: None",
        "Created": "2022-04-22T11:54:34Z",
    }
    expected_contacts = [
        {
            "_allow_permissions": ["abc@xyz.com"],
            "type": "Contacts",
            "id": "123456789",
            "title": "Demo User",
            "body": "Email Addresses: , demo@abc.com\n Company Name: None\nContact Numbers: \n Date of Birth: None",
            "created_at": "2022-04-22T11:54:34Z",
        }
    ]
    account = Mock()
    account.root = MagicMock()
    account.primary_smtp_address = "abc@xyz.com"
    account_list = [account]
    microsoft_outlook_con_obj = create_contact_obj()
    microsoft_outlook_con_obj.convert_contacts_to_workplace_search_documents = Mock(
        return_value=(contact_response)
    )
    start_date = "2022-04-21T12:10:00Z"
    end_date = "2022-04-21T12:13:00Z"
    updated_account = account.root / "Top of Information Store" / "Contacts"
    updated_account.all().filter().only = Mock(
        return_value=[Mock(spec_set=exchangelib.items.contact.Contact)]
    )
    source_contacts = microsoft_outlook_con_obj.get_contacts(
        [], account_list, start_date, end_date
    )

    assert expected_contacts == source_contacts


def test_convert_contact_to_workplace_search_document():
    """Test method to convert contact to Workplace Search document"""
    expected_contact = {
        "Id": "123456789",
        "DisplayName": "Demo User",
        "Description": """Email Addresses: demo@abc.com
                            Company Name: demo_com
                            Contact Numbers: 123456789
                            Date of Birth: """,
        "Created": "2022-04-11"
    }
    microsoft_outlook_con_obj = create_contact_obj()
    microsoft_outlook_con_obj.time_zone = EWSTimeZone("Asia/Calcutta")
    contact_obj = Contact(
        email_addresses=[Mock()],
        phone_numbers=[Mock()],
        last_modified_time=EWSDate(2022, 4, 11),
        id="123456789",
        display_name="Demo User",
        company_name="demo_com",
        birthday="",
    )
    contact_obj.email_addresses[0].email = "demo@abc.com"
    contact_obj.phone_numbers[0].phone_number = "123456789"
    source_contact = (
        microsoft_outlook_con_obj.convert_contacts_to_workplace_search_documents(
            contact_obj
        )
    )
    assert expected_contact == source_contact
