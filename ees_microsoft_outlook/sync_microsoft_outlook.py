#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

from . import constant


class SyncMicrosoftOutlook:
    """This class is responsible for fetching the Microsoft Outlook objects and it's
    permissions from the Workplace Search."""

    def __init__(
        self,
        config,
        logger,
        workplace_search_custom_client,
        queue,
    ):
        self.logger = logger
        self.config = config
        self.workplace_search_custom_client = workplace_search_custom_client
        self.objects = config.get_value("objects")
        self.permission = config.get_value("enable_document_permission")
        self.microsoft_outlook_thread_count = config.get_value(
            "source_sync_thread_count"
        )
        self.ws_auth = config.get_value("enterprise_search.api_key")
        self.ws_source = config.get_value("enterprise_search.source_id")
        self.queue = queue

    def fetch_mails(
        self, ids_list, users_account, mail_object, is_deletion, start_time, end_time
    ):
        """This method is used to fetch mails from Microsoft Outlook
        :ids_list: List of ids of documents
        :param users_account: List of user accounts
        :param mail_object: Object of mails
        :param is_deletion: Boolean to check method called by deletion or indexer
        :param start_time: Start time for fetching the mails
        :param end_time: End time for fetching the mails
        """
        self.logger.info("Fetching Mails from Microsoft Outlook")
        try:
            documents = mail_object.get_mails(
                ids_list, start_time, end_time, users_account
            )
        except Exception as exception:
            self.logger.exception(f"Error while fetching Mails. Error: {exception}")
        self.logger.info("Successfully fetched Mails from Microsoft Outlook")
        if is_deletion:
            return documents
        self.queue.append_to_queue(constant.MAILS_OBJECT.lower(), documents)
