#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Checkpointing module allows to start sync from point in time.

    Checkpointing module contains functions that allow to manage checkpoints,
    such as set a checkpoint and get a checkpoint.

    Checkpoints help with incremental or interrupted synchronizations,
    remembering the last moment of time when sync successfully finished,
    so that later next sync can continue from that place.
"""
import json
import os

from . import constant
from .schema import coerce_rfc_3339_date

CHECKPOINT_PATH_OFFICE365 = os.path.join(
    os.path.dirname(__file__), "checkpoint_office365.json"
)
CHECKPOINT_PATH_MICROSOFT_EXCHANGE = os.path.join(
    os.path.dirname(__file__), "checkpoint_microsoft_exchange.json"
)


class IncorrectFormatError(Exception):
    """Exception raised when checkpoint time is not in correct format

    Attributes:
        checkpoint -- the checkpoint time
    """

    def __init__(self, obj_type, checkpoint, inner_exception, CHECKPOINT_PATH):
        super().__init__(
            f"Start time: {checkpoint} for {obj_type} in the checkpoint file {CHECKPOINT_PATH} is not in \
            the correct format. Expected format: {constant.RFC_3339_DATETIME_FORMAT}. Remove the checkpoint entry \
            for the {obj_type} or fix the format to continue indexing"
        )
        self.checkpoint = checkpoint
        self.inner_exception = inner_exception


class Checkpoint:
    """Checkpoints class is responsible for checkpoint operations.

    This class allows to get and set checkpoints, storing them in
    file system.
    """

    def __init__(self, logger, config):
        self.config = config
        self.logger = logger
        if "Office365" in self.config.get_value("connector_platform_type"):
            self.CHECKPOINT_PATH = CHECKPOINT_PATH_OFFICE365
        elif "Microsoft Exchange" in self.config.get_value("connector_platform_type"):
            self.CHECKPOINT_PATH = CHECKPOINT_PATH_MICROSOFT_EXCHANGE

    def get_checkpoint(self, current_time, obj_type):
        """Fetches the checkpoint from the checkpoint file in
        the local storage. If the file does not exist, it takes the
        checkpoint details from the configuration file.

        Args:
            current_time: Current time
            obj_type: Microsoft Outlook for which checkpoint is fetched

        Returns:
            start_time, end_time: Return start_time and end_time
        """
        self.logger.info(
            f"Fetching the checkpoint details for {obj_type} from the checkpoint file: {self.CHECKPOINT_PATH}"
        )

        start_time = self.config.get_value("start_time")
        end_time = self.config.get_value("end_time")

        if os.path.exists(self.CHECKPOINT_PATH) and os.path.getsize(self.CHECKPOINT_PATH) > 0:
            self.logger.info(
                "Checkpoint file exists and has contents, hence considering the checkpoint time instead "
                "of start_time and end_time"
            )
            with open(self.CHECKPOINT_PATH, encoding="UTF-8") as checkpoint_store:
                try:
                    checkpoint_list = json.load(checkpoint_store)

                    if not checkpoint_list.get(obj_type):
                        self.logger.debug(
                            "The checkpoint file is present but it does not contain the start_time for "
                            f"{obj_type}, hence considering the start_time and end_time from the "
                            "configuration file instead of the last successful fetch time"
                        )
                    else:
                        try:
                            start_time = coerce_rfc_3339_date(
                                checkpoint_list.get(obj_type)
                            ).strftime(constant.RFC_3339_DATETIME_FORMAT)
                            if start_time >= constant.CURRENT_TIME:
                                raise Exception(
                                    "Checkpoint file contain greater time than current time"
                                )
                            end_time = current_time
                        except ValueError as exception:
                            raise IncorrectFormatError(
                                obj_type,
                                checkpoint_list.get(obj_type),
                                exception,
                                self.CHECKPOINT_PATH,
                            )
                except ValueError as exception:
                    self.logger.exception(
                        "Error while parsing the json file of the checkpoint store from path: "
                        f"{self.CHECKPOINT_PATH} Error: {exception}"
                    )
                    self.logger.info(
                        "Considering the start_time and end_time from the configuration file"
                    )

        else:
            self.logger.debug(
                f"Checkpoint file does not exist at {self.CHECKPOINT_PATH}, considering the "
                "start_time and end_time from the configuration file"
            )

        self.logger.debug(
            f"Contents of the start_time: {start_time} and end_time: {end_time} for {obj_type}",
        )
        return start_time, end_time

    def set_checkpoint(self, current_time, index_type, obj_type):
        """Updates the existing checkpoint json file or creates
        a new checkpoint json file in case it is not present

        Args:
            current_time: Current time
            index_type: Indexing type from "incremental" or "full_sync"
            obj_type: Object type to set the checkpoint
        """
        try:
            with open(self.CHECKPOINT_PATH, encoding="UTF-8") as checkpoint_store:
                checkpoint_list = json.load(checkpoint_store)
                if checkpoint_list.get(obj_type):
                    self.logger.debug(
                        f"Setting the checkpoint contents: {current_time} for the {obj_type} to the "
                        f"checkpoint path: {self.CHECKPOINT_PATH}"
                    )
                    checkpoint_list[obj_type] = current_time
                else:
                    self.logger.debug(
                        f"Setting the checkpoint contents: {self.config.get_value('end_time')} for the "
                        f"{obj_type} to the checkpoint path: {self.CHECKPOINT_PATH}"
                    )
                    checkpoint_list[obj_type] = self.config.get_value("end_time")
        except Exception as exception:
            if isinstance(exception, FileNotFoundError):
                self.logger.debug(
                    f"Checkpoint file not found on path: {self.CHECKPOINT_PATH}. Generating the checkpoint file"
                )
            else:
                self.logger.exception(
                    "Error while fetching the json file of the checkpoint store from path: "
                    f"{self.CHECKPOINT_PATH} Error: {exception}"
                )
            if index_type == "incremental":
                checkpoint_time = self.config.get_value("end_time")
            else:
                checkpoint_time = current_time
            self.logger.debug(
                f"Setting the checkpoint contents: {checkpoint_time} for the {obj_type} to "
                f"the checkpoint path: {self.CHECKPOINT_PATH}"
            )
            checkpoint_list = {obj_type: checkpoint_time}

        with open(self.CHECKPOINT_PATH, "w", encoding="UTF-8") as checkpoint_store:
            try:
                json.dump(checkpoint_list, checkpoint_store, indent=4)
                self.logger.info("Successfully saved the checkpoint")
            except ValueError as exception:
                self.logger.exception(
                    "Error while updating the existing checkpoint json file. Adding the new "
                    f"content directly instead of updating. Error: {exception}"
                )
