#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import collections
import os

from . import constant
from .utils import split_documents_into_equal_chunks

BATCH_SIZE = 100


class SyncEnterpriseSearch:
    """This class allows ingesting documents to Elastic Enterprise Search."""

    def __init__(self, config, logger, workplace_search_client, queue):
        self.config = config
        self.logger = logger
        self.workplace_search_client = workplace_search_client
        self.ws_source = config.get_value("enterprise_search.source_id")
        self.ws_auth = config.get_value("enterprise_search.api_key")
        self.enterprise_search_thread_count = config.get_value(
            "enterprise_search_sync_thread_count"
        )
        self.queue = queue
        self.checkpoint_list = []

    def filter_removed_item_by_id(self, item, id):
        """This method is used filter removed document by id
        :param item: Pass document
        :param id: Pass id of the document which having error from Workplace Search
        """
        return item["id"] == id

    def index_documents(self, documents):
        """This method indexes the documents to the Enterprise Search.
        :param documents: Documents to be indexed
        """
        try:
            if documents:
                total_records_dict = self.get_records_by_types(documents)
                responses = self.workplace_search_client.index_documents(
                    http_auth=self.ws_auth,
                    content_source_id=self.ws_source,
                    documents=documents,
                    request_timeout=1000,
                )
                for each in responses["results"]:
                    if each["errors"]:
                        item = list(
                            filter(
                                lambda seq: self.filter_removed_item_by_id(
                                    seq, each["id"]
                                ),
                                documents,
                            )
                        )
                        documents.remove(item[0])
                        self.logger.error(
                            f"Error while indexing {each['id']}. Error: {each['errors']}"
                        )
            total_inserted_record_dict = self.get_records_by_types(documents)
            for type, count in total_records_dict.items():
                self.logger.info(
                    f"Total {total_inserted_record_dict[type]} {type} indexed out of {count}."
                    if total_inserted_record_dict
                    else f"Total 0 {type} indexed out of {count}"
                )
        except Exception as exception:
            self.logger.error(f"Error while indexing the objects. Error: {exception}")
            os._exit(1)

    def delete_documents(self, final_deleted_list):
        """Deletes the documents of specified ids from Workplace Search
        :param final_deleted_list: List of ids to delete the documents from Workplace Search
        """
        for index in range(0, len(final_deleted_list), constant.BATCH_SIZE):
            final_list = final_deleted_list[index: index + constant.BATCH_SIZE]
            try:
                # Logic to delete documents from the Workplace Search
                self.workplace_search_client.delete_documents(
                    http_auth=self.ws_auth,
                    content_source_id=self.ws_source,
                    document_ids=final_list,
                )
            except Exception as exception:
                self.logger.exception(
                    f"Error while deleting the documents to the Workplace Search. Error: {exception}"
                )
                return []

    def get_records_by_types(self, documents):
        """This method is used to for grouping the document based on their type
        :param documents: Document to be indexed
        Returns:
             df_dict: Dictionary of type with its count
        """
        dict_count = {}
        if not documents:
            return {}
        grouped_documents = collections.defaultdict(list)
        for item in documents:
            grouped_documents[item["type"]].append(item)
        for model, group in grouped_documents.items():
            dict_count[model] = len(group)
        return dict_count

    def perform_sync(self):
        """Pull documents from the queue and synchronize it to the Enterprise Search."""
        try:
            signal_open = True
            while signal_open:
                documents_to_index, deleted_document = [], []
                while len(documents_to_index) < BATCH_SIZE:
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
                    elif documents.get("type") == "deletion":
                        deleted_document.extend(documents.get("data"))
                    else:
                        documents_to_index.extend(documents.get("data"))
                if documents_to_index:
                    for chunk in split_documents_into_equal_chunks(
                        documents_to_index, BATCH_SIZE
                    ):
                        self.index_documents(chunk)
                if deleted_document:
                    for chunk in split_documents_into_equal_chunks(
                        deleted_document, constant.BATCH_SIZE
                    ):
                        self.delete_documents(chunk)
                if not signal_open:
                    break

        except Exception as e:
            self.logger.error(e)
