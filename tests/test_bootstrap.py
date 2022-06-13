#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#

import argparse
import os
import sys
from unittest.mock import Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_microsoft_outlook.bootstrap_command import BootstrapCommand  # noqa

CONFIG_FILE = os.path.join(
    os.path.join(os.path.dirname(__file__), "config"),
    "microsoft_outlook_connector.yml",
)


def test_execute(caplog):
    """Test execute method in Bootstrap file creates a content source in the Enterprise Search."""
    # Setup
    args = argparse.Namespace()
    args.name = "dummy"
    args.config_file = CONFIG_FILE
    caplog.set_level("INFO")
    mock_response = {"id": "1234"}
    bootstrap_obj = BootstrapCommand(args)
    bootstrap_obj.workplace_search_custom_client.create_content_source = Mock(
        return_value=mock_response
    )
    schema = {
        "title": "text",
        "type": "text",
        "body": "text",
        "url": "text",
        "created_at": "date",
    }
    display = {
        "title_field": "title",
        "url_field": "url",
        "detail_fields": [
            {"field_name": "title", "label": "Title"},
            {"field_name": "body", "label": "Content"},
            {"field_name": "created_at", "label": "Created At"},
        ],
        "color": "#000000",
    }
    name = "dummy"

    # Execute
    bootstrap_obj.execute()

    # Assert
    bootstrap_obj.workplace_search_custom_client.create_content_source.assert_called_with(
        schema, display, name, is_searchable=True
    )


def test_execute_with_username():
    """Test execute method in Bootstrap file creates a content source in the Enterprise Search."""
    # Setup
    args = argparse.Namespace()
    args.name = "dummy"
    args.config_file = CONFIG_FILE
    args.user = "user1"
    args.password = "abcd1234"
    mock_response = {"id": "1234"}
    bootstrap_obj = BootstrapCommand(args)
    bootstrap_obj.workplace_search_custom_client.create_content_source = Mock(
        return_value=mock_response
    )
    schema = {
        "title": "text",
        "type": "text",
        "body": "text",
        "url": "text",
        "created_at": "date",
    }
    display = {
        "title_field": "title",
        "url_field": "url",
        "detail_fields": [
            {"field_name": "title", "label": "Title"},
            {"field_name": "body", "label": "Content"},
            {"field_name": "created_at", "label": "Created At"},
        ],
        "color": "#000000",
    }
    name = "dummy"

    # Execute
    bootstrap_obj.execute()

    # Assert
    bootstrap_obj.workplace_search_custom_client.create_content_source.assert_called_with(
        schema, display, name, is_searchable=True
    )
