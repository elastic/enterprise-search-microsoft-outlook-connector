#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module contains all the constants used throughout the code.
"""

import datetime
import os

RFC_3339_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
BATCH_SIZE = 100
CONNECTOR_TYPE_OFFICE365 = "Office365"
CONNECTOR_TYPE_MICROSOFT_EXCHANGE = "Microsoft Exchange"
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
API_SCOPE = "https://graph.microsoft.com/.default"
MICROSOFTONLINE_URL = "https://login.microsoftonline.com"
EWS_ENDPOINT = "https://outlook.office365.com/EWS/Exchange.asmx"
CONNECTION_TIMEOUT = 60  # Timeout in seconds
CURRENT_TIME = (datetime.datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%SZ")
DEFAULT_TIME_ZONE = "UTC"
MAILS_OBJECT = "Mails"
INBOX_MAIL_OBJECT = "Inbox Mails"
SENT_MAIL_OBJECT = "Sent Mails"
JUNK_MAIL_OBJECT = "Junk Mails"
ARCHIVE_MAIL_OBJECT = "Archive Mails"
MAILS_ATTACHMENTS_OBJECT = "Mails Attachments"
MAIL_DELETION_PATH = os.path.join(
    os.path.dirname(__file__), "doc_ids", "microsoft_outlook_mails_doc_ids.json"
)
TASKS_OBJECT = "Tasks"
TASKS_ATTACHMENTS_OBJECT = "Tasks Attachments"
TASK_DELETION_PATH = os.path.join(
    os.path.dirname(__file__), "doc_ids", "microsoft_outlook_tasks_doc_ids.json"
)
CONTACTS_OBJECT = "Contacts"
CONTACT_DELETION_PATH = os.path.join(
    os.path.dirname(__file__), "doc_ids", "microsoft_outlook_contacts_doc_ids.json"
)
CALENDARS_OBJECT = "Calendar"
CALENDAR_ATTACHMENTS_OBJECT = "Calendar Attachments"
CALENDAR_DELETION_PATH = os.path.join(
    os.path.dirname(__file__), "doc_ids", "microsoft_outlook_calendar_doc_ids.json"
)
SIGNAL_CLOSE = "signal_close"
CHECKPOINT = "checkpoint"
