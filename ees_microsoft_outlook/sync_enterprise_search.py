#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import collections

from . import constant
from .utils import split_documents_into_equal_chunks, split_documents_into_equal_bytes


class SyncEnterpriseSearch:
    """This class allows ingesting documents to Elastic Enterprise Search."""

    def __init__(self, config, logger, workplace_search_custom_client, queue):
        self.config = config
        self.logger = logger
        self.workplace_search_custom_client = workplace_search_custom_client
        self.ws_source = config.get_value("enterprise_search.source_id")
        self.ws_auth = config.get_value("enterprise_search.api_key")
        self.enterprise_search_thread_count = config.get_value(
            "enterprise_search_sync_thread_count"
        )
        self.queue = queue
        self.checkpoint_list = []
        self.max_allowed_bytes = 10000000

    def fetch_documents_by_id(self, response, documents):
        """Filters the documents which are getting failed while indexing
        :param response: Response getting from the Workplace Search
        :param documents: Documents to be indexed into the Workplace Search
        """
        return list(filter(lambda seq: seq["id"] == response["id"], documents,))

    def index_documents(self, documents):
        """This method indexes the documents to the Enterprise Search.
        :param documents: Documents to be indexed
        """
        try:
            if documents:
                error_count = 0
                total_records_dict = self.get_records_by_types(documents)
                responses = self.workplace_search_custom_client.index_documents(
                    documents,
                    constant.CONNECTION_TIMEOUT,
                )
                if responses:
                    for each in responses["results"]:
                        if each["errors"]:
                            failed_document_list = self.fetch_documents_by_id(each, documents)
                            # Removing the failed document from the successfully indexed document count
                            documents = [document for document in documents if document not in failed_document_list]
                            error_count += 1
            total_inserted_record_dict = self.get_records_by_types(documents)
            for type, count in total_records_dict.items():
                self.logger.info(
                    f"Total {total_inserted_record_dict[type]} {type} indexed out of {count}."
                    if total_inserted_record_dict
                    else "There is no record found to index into Workplace Search"
                )
            if error_count:
                self.logger.info(
                    f"Total {error_count} documents missed due to some error and it will sync in next full-sync cycle"
                )
        except Exception as exception:
            self.logger.info(
                f"Error while indexing {len(documents)} documents into Workplace Search. Error: {exception}"
            )

    def get_records_by_types(self, documents):
        """This method is used to for grouping the document based on their type
        :param documents: Document to be indexed
        Returns:
             dict_count: Dictionary of type with its count
        """
        if not documents:
            return {}
        dict_count = collections.defaultdict(int)
        for item in documents:
            dict_count[item["type"]] += 1
        return dict_count

    def perform_sync(self):
        """Pull documents from the queue and synchronize it to the Enterprise Search."""
        try:
            signal_open = True
            while signal_open:
                documents_to_index = []
                while len(documents_to_index) < constant.BATCH_SIZE and len(str(documents_to_index)) < self.max_allowed_bytes:
                    documents = self.queue.get()
                    if documents.get("type") == "signal_close":
                        signal_open = False
                        break
                    elif documents.get("type") == "checkpoint":
                        checkpoint_dict = {
                            "current_time": documents.get("data")[1],
                            "index_type": documents.get("data")[2],
                            "object_type": documents.get("data")[0],
                        }
                        self.checkpoint_list.append(checkpoint_dict)
                        break
                    else:
                        documents_to_index.extend(documents.get("data"))
                # This loop is to ensure if the last document fetched from the queue exceeds the size of
                # documents_to_index to more than the permitted chunk size, then we split the documents as per the limit
                if documents_to_index:
                    for chunk in split_documents_into_equal_chunks(
                        documents_to_index, constant.BATCH_SIZE
                    ):
                        for documents in split_documents_into_equal_bytes(chunk, self.max_allowed_bytes):
                            self.index_documents(documents)
                if not signal_open:
                    break

        except Exception as exception:
            self.logger.info(f"Error while indexing the objects. Error: {exception}")
