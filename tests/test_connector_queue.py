#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_microsoft_outlook.connector_queue import ConnectorQueue  # noqa
from ees_microsoft_outlook.utils import get_current_time  # noqa


def create_connector_queue_object():
    """Create connector queue object"""
    logger = logging.getLogger("unit_test_connector_queue")
    return ConnectorQueue(logger)


def test_end_signal():
    """Tests that the end signal is sent to the queue to notify it to stop listening for new incoming data"""
    expected_message = {"type": "signal_close"}
    queue = create_connector_queue_object()
    queue.put("Example data")
    queue.end_signal()
    queue.get()
    current_message = queue.get()
    assert current_message == expected_message


def test_put_checkpoint():
    """Tests that the update the checkpoint in queue"""
    current_time = get_current_time()
    expected_message = {"type": "checkpoint", "data": ("key", current_time, "full")}
    queue = create_connector_queue_object()
    queue.put("Example data")
    queue.put_checkpoint("key", current_time, "full")
    queue.end_signal()

    queue.get()
    current_message = queue.get()
    queue.get()
    assert current_message == expected_message


def test_append_to_queue():
    """Tests that the append data in queue"""
    data = []
    for count in range(10):
        data.append(count)
    expected_message = {"type": "document_list", "data": data}

    queue = create_connector_queue_object()
    queue.append_to_queue("document_list", data)
    queue.end_signal()

    current_message = queue.get()
    queue.get()

    assert current_message == expected_message
