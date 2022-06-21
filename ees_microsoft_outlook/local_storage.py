import json


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
