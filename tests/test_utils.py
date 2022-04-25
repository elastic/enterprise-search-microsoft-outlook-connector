#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import logging
import os
import sys


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
