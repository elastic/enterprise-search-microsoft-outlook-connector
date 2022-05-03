#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to fetch mails from Microsoft Outlook.
"""

from iteration_utilities import unique_everseen

from . import constant
from .utils import (change_date_format, change_datetime_format, extract,
                    get_schema_fields, html_to_text,
                    insert_document_into_doc_id_storage)


class MicrosoftOutlookMails:
    """This class fetches mails for all users from Microsoft Outlook"""

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config

    def get_mail_attachments(self, ids_list_mails, mail_obj, user_email_address):
        """Method is used to fetch attachment from mail object store in dictionary
        :param ids_list_mails: Documents ids of mails
        :param mail_obj: Object of account
        :param user_email_address: Email address of user
        Returns:
            mail_attachments: Dictionary of attachment
        """
        mail_attachments = []

        # Logic for mail last modified time
        mail_created = ""
        if mail_obj.last_modified_time:
            mail_created = change_datetime_format(mail_obj.last_modified_time)

        for attachment in mail_obj.attachments:
            attachments = {
                "type": constant.MAILS_ATTACHMENTS_OBJECT,
                "id": attachment.attachment_id.id,
                "title": attachment.name,
                "created": mail_created,
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
        self, ids_list_mails, mail_type, mail_obj, user_email_address
    ):
        """Method is used to convert mail data into Workplace Search document
        :param ids_list_mails: Documents ids of mails
        :param mail_type: Type of the mail like inbox, sent, junk
        :param mail_obj: Object of account
        :param user_email_address: Email address of user
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
            for recipient in mail_obj.to_recipients:
                receiver_email = receiver_email + ", " + recipient.email_address

        # Logic for email cc
        cc = ""
        if mail_obj.cc_recipients:
            for cc_recipient in mail_obj.cc_recipients:
                cc = cc + ", " + cc_recipient.email_address

        # Logic for email bcc
        bcc = ""
        if mail_obj.bcc_recipients:
            for bcc_recipient in mail_obj.bcc_recipients:
                bcc = bcc + ", " + bcc_recipient.email_address

        # Logic for mail last modified time
        mail_created = ""
        if mail_obj.last_modified_time:
            mail_created = change_datetime_format(mail_obj.last_modified_time)

        # Logic to create document body
        mail_document = {
            "type": mail_type,
            "Id": mail_obj.id,
            "DisplayName": mail_obj.subject,
            "Description": f"Sender Email: {sender_email}\n Receiver Email: {receiver_email}\n"
            f"CC: {cc}\n BCC: {bcc}\n Importance: {mail_obj.importance}\n"
            f"Category: {mail_obj.categories}\n Body: {html_to_text(mail_obj.body)}",
            "Created": mail_created,
        }

        # Logic to fetches attachments
        mail_attachments_documents = []
        if mail_obj.has_attachments:
            mail_attachments_documents = self.get_mail_attachments(
                ids_list_mails, mail_obj, user_email_address
            )

        return mail_document, mail_attachments_documents

    def get_mail_documents(self, account, ids_list_mails, mail_type, mail_objs):
        """This method is used to get mail's data and mapped with fields
        :param account: User account object
        :param ids_list_mails: Documents ids list
        :param mail_type: Type of mail like inbox, sent, junk
        :param mail_obj: Object of account
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
                ids_list_mails, mail_type, mail_obj, account.primary_smtp_address
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
        start_time = change_date_format(start_time)
        end_time = change_date_format(end_time)
        for account in accounts:

            try:
                # Logic to fetch Inbox emails
                inbox_obj = account.inbox.all().filter(
                    last_modified_time__gt=start_time,
                    last_modified_time__lt=end_time,
                )
                mail_documents = self.get_mail_documents(
                    account, ids_list_mails, constant.INBOX_MAIL_OBJECT, inbox_obj
                )
                documents.extend(mail_documents)

                # Logic to fetch Sent emails
                sent_obj = account.sent.all().filter(
                    last_modified_time__gt=start_time,
                    last_modified_time__lt=end_time,
                )
                mail_documents = self.get_mail_documents(
                    account, ids_list_mails, constant.SENT_MAIL_OBJECT, sent_obj
                )
                documents.extend(mail_documents)

                # Logic to fetch Junk emails
                junk_obj = account.junk.all().filter(
                    last_modified_time__gt=start_time,
                    last_modified_time__lt=end_time,
                )
                mail_documents = self.get_mail_documents(
                    account, ids_list_mails, constant.JUNK_MAIL_OBJECT, junk_obj
                )
                documents.extend(mail_documents)

                # Logic to fetch Archive emails
                archive_folder = account.root / "Top of Information Store" / "Archive"
                archive_obj = archive_folder.all().filter(
                    last_modified_time__gt=start_time,
                    last_modified_time__lt=end_time,
                )
                mail_documents = self.get_mail_documents(
                    account, ids_list_mails, constant.ARCHIVE_MAIL_OBJECT, archive_obj
                )
                documents.extend(mail_documents)
            except Exception as exception:
                self.logger.info(
                    f"Error while fetching mails data for {account.primary_smtp_address}. Error: {exception}"
                )
                pass

        return list(unique_everseen(documents))
