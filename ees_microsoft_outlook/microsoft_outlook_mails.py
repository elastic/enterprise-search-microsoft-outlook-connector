#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to fetch mails from Microsoft Outlook.
"""

import requests
from iteration_utilities import unique_everseen

from . import constant
from .utils import (
    change_datetime_format,
    convert_datetime_to_ews_format,
    extract,
    get_schema_fields,
    html_to_text,
    insert_document_into_doc_id_storage,
    retry,
)


class MicrosoftOutlookMails:
    """This class fetches mails for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.time_zone = constant.DEFAULT_TIME_ZONE
        self.retry_count = self.config.get_value("retry_count")

    def get_mail_attachments(
        self, ids_list_mails, mail_obj, user_email_address, start_time, end_time
    ):
        """Method is used to fetch attachment from mail object store in dictionary
        :param ids_list_mails: Documents ids of mails
        :param mail_obj: Object of account
        :param user_email_address: Email address of user
        :param start_time: Start time for fetching the mails
        :param end_time: End time for fetching the mails
        Returns:
            mail_attachments: Dictionary of attachment
        """
        mail_attachments = []
        for attachment in mail_obj.attachments:

            # Logic for mail attachment last modified time
            attachment_created = ""
            if attachment.last_modified_time:
                attachment_created = change_datetime_format(
                    attachment.last_modified_time, self.time_zone
                )

            # Logic to fetch mail attachments
            if (
                attachment.last_modified_time >= start_time
                and attachment.last_modified_time < end_time
            ):
                attachments = {
                    "type": constant.MAILS_ATTACHMENTS_OBJECT,
                    "id": attachment.attachment_id.id,
                    "title": attachment.name,
                    "created": attachment_created,
                }
                attachments["_allow_permissions"] = []
                if self.config.get_value("enable_document_permission"):
                    attachments["_allow_permissions"] = [user_email_address]

                # Logic to insert mail attachment into global_keys object
                insert_document_into_doc_id_storage(
                    ids_list_mails,
                    attachment.attachment_id.id,
                    mail_obj.id,
                    constant.MAILS_ATTACHMENTS_OBJECT.lower(),
                    self.config.get_value("connector_platform_type"),
                )
                if hasattr(attachment, "content"):
                    attachments["body"] = extract(attachment.content)
                mail_attachments.append(attachments)

        return mail_attachments

    def convert_mails_to_workplace_search_documents(
        self,
        ids_list_mails,
        mail_type,
        mail_obj,
        user_email_address,
        start_time,
        end_time,
    ):
        """Method is used to convert mail data into Workplace Search document
        :param ids_list_mails: Documents ids of mails
        :param mail_type: Type of the mail like inbox, sent, junk
        :param mail_obj: Object of account
        :param user_email_address: Email address of user
        :param start_time: Start time for fetching the mails
        :param end_time: End time for fetching the mails
        Returns:
            mail_document: Dictionary of mail
            mail_attachments_documents: Dictionary of attachment
        """

        # Logic for email sender
        sender_email = ""
        if mail_obj.sender:
            sender_email = mail_obj.sender.email_address

        # Logic for email recipients
        receiver_email = ""
        if mail_obj.to_recipients:
            receiver_email_list = []
            for recipient in mail_obj.to_recipients:
                receiver_email_list.append(recipient.email_address)
            receiver_email = ", ".join(receiver_email_list)

        # Logic for email cc
        cc = ""
        if mail_obj.cc_recipients:
            cc_list = []
            for cc_recipient in mail_obj.cc_recipients:
                cc_list.append(cc_recipient.email_address)
            cc = ", ".join(cc_list)

        # Logic for email bcc
        bcc = ""
        if mail_obj.bcc_recipients:
            bcc_list = []
            for bcc_recipient in mail_obj.bcc_recipients:
                bcc_list.append(bcc_recipient.email_address)
            bcc = ", ".join(bcc_list)

        # Logic for mail last modified time
        mail_created = ""
        if mail_obj.last_modified_time:
            mail_created = change_datetime_format(
                mail_obj.last_modified_time, self.time_zone
            )

        # Logic for mail categories
        mail_categories = ""
        if mail_obj.categories:
            mail_categories_list = []
            for categories in mail_obj.categories:
                mail_categories_list.append(categories)
            mail_categories = ", ".join(mail_categories_list)

        # Logic to create document body
        mail_document = {
            "type": mail_type,
            "Id": mail_obj.id,
            "DisplayName": mail_obj.subject,
            "Description": f"Sender Email: {sender_email}\n Receiver Email: {receiver_email}\n"
            f"CC: {cc}\n BCC: {bcc}\n Importance: {mail_obj.importance}\n"
            f"Category: {mail_categories}\n Body: {html_to_text(mail_obj.body)}",
            "Created": mail_created,
        }

        # Logic to fetches attachments
        mail_attachments_documents = []
        if mail_obj.has_attachments:
            mail_attachments_documents = self.get_mail_attachments(
                ids_list_mails, mail_obj, user_email_address, start_time, end_time
            )

        return mail_document, mail_attachments_documents

    def get_mail_documents(
        self, account, ids_list_mails, mail_type, mail_objs, start_time, end_time
    ):
        """This method is used to get mail's data and mapped with fields
        :param account: User account object
        :param ids_list_mails: Documents ids list
        :param mail_type: Type of mail like inbox, sent, junk
        :param mail_obj: Object of account
        :param start_time: Start time for fetching the mails
        :param end_time: End time for fetching the mails
        Returns:
            documents: List of documents
        """
        documents = []
        mail_schema = get_schema_fields(
            constant.MAILS_OBJECT.lower(), self.config.get_value("objects")
        )
        for mail_obj in mail_objs:

            # Logic to insert mail into global_keys object
            insert_document_into_doc_id_storage(
                ids_list_mails,
                mail_obj.id,
                "",
                mail_type.lower(),
                self.config.get_value("connector_platform_type"),
            )
            (
                mail_dict,
                mail_attachment,
            ) = self.convert_mails_to_workplace_search_documents(
                ids_list_mails,
                mail_type,
                mail_obj,
                account.primary_smtp_address,
                start_time,
                end_time,
            )
            mail_map = {}
            mail_map["_allow_permissions"] = []
            if self.config.get_value("enable_document_permission"):
                mail_map["_allow_permissions"] = [account.primary_smtp_address]
            mail_map["type"] = mail_dict["type"]
            for ws_field, ms_fields in mail_schema.items():
                mail_map[ws_field] = mail_dict[ms_fields]
            documents.append(mail_map)
            if mail_attachment:
                documents.extend(mail_attachment)
        return documents

    @retry(exception_list=(requests.exceptions.RequestException,))
    def get_mails(self, ids_list_mails, accounts, start_time, end_time):
        """This method is used to get documents of mails and mapped with Workplace Search fields
        :param ids_list_mails: List of ids of documents
        :param accounts: List of user accounts
        :param start_time: Start time for fetching the mails
        :param end_time: End time for fetching the mails
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
        start_time = convert_datetime_to_ews_format(start_time)
        end_time = convert_datetime_to_ews_format(end_time)
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
                        account,
                        ids_list_mails,
                        type["constant"],
                        mail_type_obj,
                        start_time,
                        end_time,
                    )
                    documents.extend(mail_type_documents)
            except requests.exceptions.RequestException as request_error:
                raise requests.exceptions.RequestException(
                    f"Error while fetching mails data for {account.primary_smtp_address}. Error: {request_error}"
                )
            except Exception as exception:
                self.logger.info(
                    f"Error while fetching mails data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass

        return list(unique_everseen(documents))
