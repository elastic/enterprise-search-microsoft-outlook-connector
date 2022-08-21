#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
import copy
import json
import os


class LocalStorage:
    """This class contains all the methods to perform operations on doc_id.json file.

    The doc_id.json file is a local storage that the connector uses to track the identifiers(IDs) of the documents
    that were successfully indexed to the Enterprise Search.
    This storage is then traversed during the deletion sync to validate if any of these indexed documents have been
    later deleted from the source, if so, the deletion sync will delete those documents from the Enterprise Search.

    The structure of the doc_id.json is {'global_keys': [], 'delete_keys':[]}:
        - global_keys: Stores all the document ids that are successfully indexed and present in the Enterprise Search.
        - delete_keys: Store all the document ids that are NOT recently updated, so the deletion sync
          would just check if those not recently updated documents are present anymore in the source

    Use this class to perform read/write operations to the doc_id.json file(Local Storage)
    """

    def __init__(self, logger):
        self.logger = logger

    def load_storage(self, ids_path):
        """This method fetches the contents of doc_id.json(local ids storage)
        :param ids_path: Path to the respective doc_ids.json
        """

        try:
            with open(ids_path, encoding="utf-8") as ids_file:
                try:
                    return json.load(ids_file)
                except ValueError as exception:
                    self.logger.exception(
                        f"Error while parsing the json file of the ids store from path: {ids_path}. Error: {exception}"
                    )
        except FileNotFoundError:
            self.logger.debug(
                f"Local storage for ids was not found with path: {ids_path}."
            )
            return {"global_keys": {}}

    def update_storage(self, ids, ids_path):
        """This method is used to update the ids stored in doc_id.json file
        :param ids: Updated ids to be stored in the doc_id.json file
        :param ids_path: Path to the respective doc_ids.json
        """
        with open(ids_path, "w", encoding="utf-8") as ids_file:
            try:
                json.dump(ids, ids_file, indent=4)
            except ValueError as exception:
                self.logger.exception(
                    f"Error while updating the doc_id json file. Error: {exception}"
                )

    def create_local_storage_directory(self):
        """Creates a doc_id directory if not present"""
        doc_ids_directory = os.path.dirname(os.path.join(
            os.path.dirname(__file__), "doc_ids", "microsoft_outlook_mails_doc_ids.json"))
        if not os.path.exists(doc_ids_directory):
            os.makedirs(doc_ids_directory)

    def get_storage_with_collection(self, local_storage, ids_path):
        """Returns a dictionary containing the locally stored IDs of mails, calendars, tasks and contacts.
        :param local_storage: The object of the local storage used to store the indexed document IDs
        """
        storage_with_collection = {"global_keys": [], "delete_keys": []}
        ids_collection = local_storage.load_storage(ids_path)
        storage_with_collection["delete_keys"] = copy.deepcopy(
            ids_collection.get("global_keys")
        )

        if not ids_collection["global_keys"]:
            ids_collection["global_keys"] = []

        storage_with_collection["global_keys"] = copy.deepcopy(
            ids_collection["global_keys"]
        )

        return storage_with_collection
