#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import datetime
import logging
import os
import sys

import pytest
from exchangelib import EWSTimeZone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_microsoft_outlook import utils  # noqa
from ees_microsoft_outlook.configuration import Configuration  # noqa


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_teams_connector.yml",
        )
    )

    logger = logging.getLogger("unit_test_utils")
    return configuration, logger


def test_url_encode():
    """Test that encode URL"""
    url_to_encode = '''http://ascii.cl?parameter="Click on 'URL Decode'!"'''
    target_encoded_url = utils.url_encode(url_to_encode)
    source_encoded_url = (
        "http%3A%2F%2Fascii.cl%3Fparameter%3D%22Click%20on%20''URL%20Decode''%21%22"
    )
    assert source_encoded_url == target_encoded_url


def test_split_list_into_buckets():
    """Test that divide large number of documents amongst the total buckets."""
    documents = [1, 2, 3, 4, 5, 6, 7, 8, 10]
    total_bucket = 3
    target_list = utils.split_list_into_buckets(documents, total_bucket)
    count = 0
    for id_list in target_list:
        for id in id_list:
            if id in documents:
                count += 1
    assert len(documents) == count


def test_change_datetime_ews_format():
    """Test for change date format"""
    # Execute
    target_date_format = utils.change_datetime_ews_format("2022-04-02T08:20:30Z")

    # Assert
    assert target_date_format == datetime.datetime(
        2022, 4, 2, 8, 20, 30, tzinfo=EWSTimeZone(key="UTC")
    )


def test_change_datetime_format():
    """Test for change_datetime_format"""
    # Setup
    date_obj = datetime.date(2020, 5, 17)

    # Execute
    actual_response = utils.change_datetime_format(date_obj, "UTC")

    # Assert
    assert actual_response == "2020-05-17"


@pytest.mark.parametrize(
    "ids_list, source_documents",
    [
        (
            [
                {
                    "id": "1645460238462",
                    "parent id": "123456",
                    "type": "Mails",
                    "platform": "Office365",
                }
            ],
            [
                {
                    "id": "1645460238462",
                    "parent id": "123456",
                    "type": "Mails",
                    "platform": "Office365",
                }
            ],
        )
    ],
)
def test_insert_document_into_doc_id_storage(ids_list, source_documents):
    """Test method for inserting the ids into doc id"""
    # Execute
    target_documents = utils.insert_document_into_doc_id_storage(
        ids_list, "1645460238462", "123456", "Mails", "Office365"
    )

    # Assert
    assert source_documents == target_documents


def test_is_document_in_present_data():
    """Test method for is_document_in_present_data"""
    # Setup
    document = {"id": "abcd1234", "name": "abcd"}

    # Execute
    actual_response = utils.is_document_in_present_data(document, "abcd1234")

    # Assert
    assert actual_response


def test_split_date_range_into_chunks():
    """Test Method to split dates into chunks"""
    # Setup
    expected_list = [
        "2022-04-01T00:00:00Z",
        "2022-04-02T19:12:00Z",
        "2022-04-04T14:24:00Z",
        "2022-04-06T09:36:00Z",
        "2022-04-08T04:48:00Z",
        "2022-04-10T00:00:00Z",
    ]

    # Execute
    target_list = utils.split_date_range_into_chunks(
        "2022-04-01T00:00:00Z", "2022-04-10T00:00:00Z", 5
    )

    # Assert
    assert expected_list == target_list


def test_split_documents_into_equal_bytes_with_optimum_size():
    """Tests split functionality based on size"""
    # Setup
    document_to_split = [
        {"name": "dummy1", "body": "dummy1_body"},
        {"name": "dummy2", "body": "dummy2_body"},
        {"name": "dummy3", "body": "dummy3_body"},
        {"name": "dummy4", "body": "dummy4_body"},
        {"name": "dummy5", "body": "dummy5_body"},
        {"name": "dummy6", "body": "dummy6_body"},
    ]
    allowed_size = 140
    expected_output = [
        [
            {"name": "dummy1", "body": "dummy1_body"},
            {"name": "dummy2", "body": "dummy2_body"},
            {"name": "dummy3", "body": "dummy3_body"},
        ],
        [
            {"name": "dummy4", "body": "dummy4_body"},
            {"name": "dummy5", "body": "dummy5_body"},
            {"name": "dummy6", "body": "dummy6_body"},
        ],
    ]

    # Execute
    returned_document = utils.split_documents_into_equal_bytes(
        document_to_split, allowed_size
    )

    # Assert
    assert returned_document == expected_output


def test_split_documents_into_equal_bytes_with_lowest_possible_size():
    """Tests split functionality based on size"""
    # Setup
    document_to_split = [
        {"name": "dummy1", "body": "dummy1_body"},
        {"name": "dummy2", "body": "dummy2_body"},
        {"name": "dummy3", "body": "dummy3_body"},
        {"name": "dummy4", "body": "dummy4_body"},
        {"name": "dummy5", "body": "dummy5_body"},
        {"name": "dummy6", "body": "dummy6_body"},
    ]
    allowed_size = 1
    expected_output = [
        [{"name": "dummy1", "body": None}],
        [{"name": "dummy2", "body": None}],
        [{"name": "dummy3", "body": None}],
        [{"name": "dummy4", "body": None}],
        [{"name": "dummy5", "body": None}],
        [{"name": "dummy6", "body": None}],
    ]

    # Execute
    returned_document = utils.split_documents_into_equal_bytes(
        document_to_split, allowed_size
    )

    # Assert
    assert returned_document == expected_output
