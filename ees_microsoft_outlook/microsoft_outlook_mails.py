#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to fetch mails from Microsoft Outlook.
"""

from iteration_utilities import unique_everseen

from . import constant
from .utils import (change_datetime_ews_format, change_datetime_format,
                    extract, get_schema_fields, html_to_text,
                    insert_document_into_doc_id_storage)


class MicrosoftOutlookMails:
    """This class fetches mails for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.time_zone = constant.DEFAULT_TIME_ZONE

    def get_mails(self, ids_list_mails, start_time, end_time, accounts):
        """This method is used to get documents of mails and mapped with Workplace Search fields
        :param ids_list_mails: List of ids of documents
        :param start_time: Start time for fetching the mails
        :param end_time: End time for fetching the mails
        :param accounts: List of user accounts
        Returns:
            documents: List of all types of mail documents
        """
        documents = []
        mail_type = [
            {
                "folder": "inbox",
                "constant": constant.INBOX_MAIL_OBJECT,
            },
            {
                "folder": "sent",
                "constant": constant.SENT_MAIL_OBJECT,
            },
            {
                "folder": "junk",
                "constant": constant.JUNK_MAIL_OBJECT,
            },
            {
                "folder": "archive",
                "constant": constant.ARCHIVE_MAIL_OBJECT,
            },
        ]
        start_time = change_datetime_ews_format(start_time)
        end_time = change_datetime_ews_format(end_time)
        for account in accounts:

            # Logic to set time zone according to user account
            self.time_zone = account.default_timezone

            try:
                for type in mail_type:

                    # Logic to get mails folder
                    if "archive" in type["folder"]:
                        mail_type_obj_folder = (
                            account.root / "Top of Information Store" / "Archive"
                        )
                    else:
                        mail_type_obj_folder = getattr(account, type["folder"])

                    # Logic to fetch mails
                    mail_type_obj = (
                        mail_type_obj_folder.all()
                        .filter(
                            last_modified_time__gt=start_time,
                            last_modified_time__lt=end_time,
                        )
                        .only(
                            "sender",
                            "to_recipients",
                            "cc_recipients",
                            "bcc_recipients",
                            "last_modified_time",
                            "subject",
                            "importance",
                            "categories",
                            "body",
                            "has_attachments",
                            "attachments",
                        )
                    )
                    mail_type_documents = self.get_mail_documents(
                        account, ids_list_mails, type["constant"], mail_type_obj, start_time, end_time
                    )
                    documents.extend(mail_type_documents)
            except Exception as exception:
                self.logger.info(
                    f"Error while fetching mails data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass

        return list(unique_everseen(documents))
