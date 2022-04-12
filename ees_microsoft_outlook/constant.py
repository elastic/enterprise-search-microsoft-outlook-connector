#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module contains all the constants used throughout the code.
"""

import datetime
import os

CONNECTOR_TYPE_OFFICE365 = "Office365"
CONNECTOR_TYPE_MICROSOFT_EXCHANGE = "Microsoft Exchange"
CURRENT_TIME = (datetime.datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%SZ")
RFC_3339_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
API_SCOPE = "https://graph.microsoft.com/.default"
MICROSOFTONLINE_URL = "https://login.microsoftonline.com"
EWS_ENDPOINT = "https://outlook.office365.com/EWS/Exchange.asmx"
MAIL_DELETION_PATH = os.path.join(
    os.path.dirname(__file__), "doc_ids", "microsoft_outlook_mails_doc_ids.json"
)
CONTACTS_OBJECT = "contacts"
MAILS_OBJECT = "mails"
MAILS_ATTACHMENTS_OBJECT = "mails attachments"
BATCH_SIZE = 100
