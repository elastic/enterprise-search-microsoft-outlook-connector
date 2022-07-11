#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
from unittest.mock import Mock

from ees_microsoft_outlook.configuration import Configuration
from ees_microsoft_outlook.microsoft_outlook_mails import MicrosoftOutlookMails
from exchangelib.ewsdatetime import EWSTimeZone


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
    # Setup
    inbox_response = [
        {
            "type": "Inbox Mails",
            "id": "123456789",
            "title": "demo for attachments",
            "body": "Sender Email: abc@xyz.com \n Receiver Email: , pqr@xyz.com \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
            "created_at": "2022-04-21T12:12:30Z",
        }
    ]
    expected_mails = [
        {
            "type": "Inbox Mails",
            "id": "123456789",
            "title": "demo for attachments",
            "body": "Sender Email: abc@xyz.com \n Receiver Email: , pqr@xyz.com \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
            "created_at": "2022-04-21T12:12:30Z",
        }
    ]
    account = Mock()
    accounts = [account]
    microsoft_outlook_mails_obj = create_mail_obj()
    microsoft_outlook_mails_obj.get_mail_documents = Mock(return_value=inbox_response)
    start_date = "2022-04-21T12:10:00Z"
    end_date = "2022-04-21T12:13:00Z"

    # Execute
    source_mails = microsoft_outlook_mails_obj.get_mails(
        [], start_date, end_date, accounts
    )

    # Assert
    assert expected_mails == source_mails


def test_get_mail_documents():
    """Test method to get mail documents"""
    # Setup
    mail_response = {
        "type": "Inbox Mails",
        "Id": "123456789",
        "DisplayName": "demo for attachments",
        "Description": "Sender Email: abc@xyz.com \n Receiver Email: , pqr@xyz.com \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
        "Created": "2022-04-21T12:12:30Z",
    }
    expected_mails_documents = [
        {
            "_allow_permissions": ["abc@xyz.com"],
            "type": "Inbox Mails",
            "id": "123456789",
            "title": "demo for attachments",
            "body": "Sender Email: abc@xyz.com \n Receiver Email: , pqr@xyz.com \
\nCC:  \n BCC:  \n Importance: Normal \n Category: None \nBody: demo body",
            "created_at": "2022-04-21T12:12:30Z",
        }
    ]
    account = Mock()
    microsoft_outlook_mails_obj = create_mail_obj()
    microsoft_outlook_mails_obj.time_zone = EWSTimeZone("Asia/Calcutta")
    microsoft_outlook_mails_obj.convert_mails_to_workplace_search_documents = Mock(
        return_value=mail_response
    )
    mail_obj = [Mock()]
    account.primary_smtp_address = "abc@xyz.com"

    # Execute
    source_mails_documents = microsoft_outlook_mails_obj.get_mail_documents(
        account,
        [],
        "Inbox Mails",
        mail_obj
    )

    # Assert
    assert expected_mails_documents == source_mails_documents
