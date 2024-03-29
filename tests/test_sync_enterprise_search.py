#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
import sys
from unittest.mock import Mock

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_microsoft_outlook.configuration import Configuration  # noqa
from ees_microsoft_outlook.connector_queue import ConnectorQueue  # noqa
from ees_microsoft_outlook.sync_enterprise_search import SyncEnterpriseSearch  # noqa
from elastic_enterprise_search import WorkplaceSearch  # noqa


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )
    logger = logging.getLogger("unit_test_enterprisesearch")
    return configuration, logger


def create_enterprise_search_obj():
    """This function create Enterprise Search object for test."""
    configs, logger = settings()
    enterprise_search_host = configs.get_value("enterprise_search.host_url")
    workplace_search_client = WorkplaceSearch(
        enterprise_search_host,
        http_auth=configs.get_value("enterprise_search.api_key"),
    )
    queue = ConnectorQueue(logger)
    queue.end_signal()
    return SyncEnterpriseSearch(configs, logger, workplace_search_client, queue)


@pytest.mark.parametrize(
    "documents, mock_response, log_msg",
    [
        (
            [
                {
                    "id": 0,
                    "title": "file0",
                    "body": "Not much. It is a made up thing.",
                    "url": "dummy_folder/file0.txt",
                    "created_at": "2019-06-01T12:00:00+00:00",
                    "type": "text",
                },
                {
                    "id": 1,
                    "title": "file1",
                    "body": "Not much. It is a made up thing.",
                    "url": "dummy_folder/file1.txt",
                    "created_at": "2019-06-01T12:00:00+00:00",
                    "type": "text",
                },
            ],
            {"results": [{"id": "0", "errors": []}, {"id": "1", "errors": []}]},
            "Total text indexed: 2 out of 2.",
        )
    ],
)
def test_index_documents(documents, mock_response, log_msg, caplog):
    """Test Method to Index Documents into Workplace Search"""
    # Setup
    caplog.set_level("INFO")
    indexer_obj = create_enterprise_search_obj()
    indexer_obj.workplace_search_custom_client.index_documents = Mock(
        return_value=mock_response
    )

    # Execute
    indexer_obj.index_documents(documents)

    # Assert
    assert log_msg in caplog.text


def test_get_records_by_types():
    """Test method to get records by types of documents"""
    # Setup
    input_document = [
        {
            "id": 0,
            "title": "file0",
            "body": "Not much. It is a made up thing.",
            "url": "dummy_folder/file0.txt",
            "created_at": "2019-06-01T12:00:00+00:00",
            "type": "text",
        }
    ]
    indexer_obj = create_enterprise_search_obj()

    # Execute
    target_response = indexer_obj.get_records_by_types(input_document)

    # Assert
    assert {"text": [0]} == target_response
