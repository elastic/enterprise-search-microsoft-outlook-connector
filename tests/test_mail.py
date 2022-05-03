#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from datetime import datetime
from unittest.mock import MagicMock, Mock

from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.microsoft_outlook_mails import MicrosoftOutlookMails
from exchangelib import Message


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )
    logger = logging.getLogger("unit_test_mails")
    return configuration, logger


def create_mail_obj():
    """This function create object of MicrosoftOutlookMails class for test"""
    config, logger = settings()
    return MicrosoftOutlookMails(logger, config)


def test_get_mails():
    """Test method to get mail documents from Microsoft Outlook"""
    inbox_response = [
        {
            "type": "Inbox Mails",
            "id": "123456789",
            "title": "demo for attachments",
            "body": "Sender Email: rinkesh.mistry@exchange.demo \n Receiver Email: , Moxarth.Rathod@exchange.demo \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
            "created_at": "2022-04-21T12:12:30Z",
        }
    ]
    expected_mails = [
        {
            "type": "Inbox Mails",
            "id": "123456789",
            "title": "demo for attachments",
            "body": "Sender Email: rinkesh.mistry@exchange.demo \n Receiver Email: , Moxarth.Rathod@exchange.demo \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
            "created_at": "2022-04-21T12:12:30Z",
        }
    ]
    account = Mock()
    accounts = [account]
    account.root = MagicMock()
    microsoft_outlook_mails_obj = create_mail_obj()
    microsoft_outlook_mails_obj.get_mail_documents = Mock(return_value=inbox_response)
    start_date = "2022-04-21T12:10:00Z"
    end_date = "2022-04-21T12:13:00Z"
    source_mails = microsoft_outlook_mails_obj.get_mails(
        [], start_date, end_date, accounts
    )
    assert expected_mails == source_mails


def test_get_mail_documents():
    """Test method to get mail documents"""
    mail_response = {
        "type": "Inbox Mails",
        "Id": "123456789",
        "DisplayName": "demo for attachments",
        "Description": "Sender Email: rinkesh.mistry@exchange.demo \n Receiver Email: , Moxarth.Rathod@exchange.demo \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
        "Created": "2022-04-21T12:12:30Z",
    }
    attachments_response = [
        {
            "type": "Mails Attachments",
            "id": "987654321",
            "title": "Demo",
            "body": "Hello world",
        }
    ]
    expected_mails_documents = [
        {
            "_allow_permissions": ["abc@xyz.com"],
            "type": "Inbox Mails",
            "id": "123456789",
            "title": "demo for attachments",
            "body": "Sender Email: rinkesh.mistry@exchange.demo \n Receiver Email: , Moxarth.Rathod@exchange.demo \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
            "created_at": "2022-04-21T12:12:30Z",
        },
        {
            "type": "Mails Attachments",
            "id": "987654321",
            "title": "Demo",
            "body": "Hello world",
        },
    ]
    account = Mock()
    microsoft_outlook_mails_obj = create_mail_obj()
    microsoft_outlook_mails_obj.convert_mails_to_workplace_search_documents = Mock(
        return_value=(mail_response, attachments_response)
    )
    mail_obj = [Mock()]
    account.primary_smtp_address = "abc@xyz.com"
    source_mails_documents = microsoft_outlook_mails_obj.get_mail_documents(
        account, [], "Inbox Mails", mail_obj
    )
    assert expected_mails_documents == source_mails_documents


def test_convert_mails_to_workplace_search_documents():
    """Test method to convert mail attribute to workplace search documents"""
    attachments_response = [
        {
            "type": "Mails Attachments",
            "id": "987654321",
            "title": "Demo",
            "body": "Hello world",
        }
    ]
    expected_mail_document = {
        "type": "Inbox",
        "Id": "123456789",
        "DisplayName": "Demo",
        "Description": "Sender Email: abc@xyz.com\n Receiver Email: , abc@xyz.com\nCC: , abc@xyz.com\n \
BCC: , abc@xyz.com\n Importance: Normal\nCategory: None\n Body: demo",
        "Created": "2022-04-11T02:13:00Z",
    }
    expected_attachments_documents = [
        {
            "type": "Mails Attachments",
            "id": "987654321",
            "title": "Demo",
            "body": "Hello world",
        }
    ]
    microsoft_outlook_mails_obj = create_mail_obj()
    mail_obj = Mock()
    mail_obj = Message(
        sender=Mock(),
        to_recipients=[Mock()],
        cc_recipients=[Mock()],
        bcc_recipients=[Mock()],
        last_modified_time=datetime(2022, 4, 11, 2, 13, 00),
        id="123456789",
        subject="Demo",
        importance="Normal",
        categories="None",
        body="demo",
        has_attachments=True,
    )
    mail_obj.sender.email_address = "abc@xyz.com"
    mail_obj.to_recipients[0].email_address = "abc@xyz.com"
    mail_obj.cc_recipients[0].email_address = "abc@xyz.com"
    mail_obj.bcc_recipients[0].email_address = "abc@xyz.com"
    microsoft_outlook_mails_obj.get_mail_attachments = Mock(
        return_value=attachments_response
    )
    (
        source_mail,
        source_mail_attachments,
    ) = microsoft_outlook_mails_obj.convert_mails_to_workplace_search_documents(
        [], "Inbox", mail_obj, "abc@xyz.com"
    )
    assert expected_mail_document == source_mail
    assert expected_attachments_documents == source_mail_attachments
