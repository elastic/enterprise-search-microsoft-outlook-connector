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


def test_extract():
    """Test the extract content from tika"""
    target_content = utils.extract("hello")
    assert target_content == "\n\n\n\n\n\n\n\nhello\n"


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


def test_change_date_format():
    """Test for change date format"""
    target_date_format = utils.change_date_format("2022-04-02T08:20:30Z")
    assert target_date_format == datetime.datetime(
        2022, 4, 2, 8, 20, 30, tzinfo=EWSTimeZone(key="UTC")
    )


@pytest.mark.parametrize(
    "ids_list, source_documents",
    [
        (
            [
                {
                    "id": "1645460238462",
                    "type": "Mails",
                    "platform": "Office365",
                }
            ],
            [
                {
                    "id": "1645460238462",
                    "type": "Mails",
                    "platform": "Office365",
                }
            ],
        )
    ],
)
def test_insert_document_into_doc_id_storage(ids_list, source_documents):
    """Test method for inserting the ids into doc id"""
    target_documents = utils.insert_document_into_doc_id_storage(
        ids_list, "1645460238462", "Mails", "Office365"
    )
    assert source_documents == target_documents
