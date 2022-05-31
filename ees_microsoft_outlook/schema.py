#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""schema module contains Connector configuration file schema.
"""
import datetime

from .constant import RFC_3339_DATETIME_FORMAT


def coerce_rfc_3339_date(input_date):
    """This function returns true if its argument is a valid RFC 3339 date."""
    if input_date:
        return datetime.datetime.strptime(input_date, RFC_3339_DATETIME_FORMAT)
    return False


schema = {
    "microsoft_exchange.active_directory_server": {
        "required": False,
        "type": "string",
        "empty": True,
    },
    "microsoft_exchange.server": {
        "required": False,
        "type": "string",
        "empty": True,
    },
    "microsoft_exchange.username": {
        "required": False,
        "type": "string",
        "empty": True,
    },
    "microsoft_exchange.password": {
        "required": False,
        "type": "string",
        "empty": True,
    },
    "office365.client_id": {
        "required": False,
        "type": "string",
        "empty": True,
    },
    "office365.tenant_id": {
        "required": False,
        "type": "string",
        "empty": True,
    },
    "office365.client_secret": {
        "required": False,
        "type": "string",
        "empty": True,
    },
    "enterprise_search.api_key": {
        "required": True,
        "type": "string",
        "empty": False,
    },
    "enterprise_search.source_id": {
        "required": True,
        "type": "string",
        "empty": False,
    },
    "enterprise_search.host_url": {
        "required": True,
        "type": "string",
        "empty": False,
    },
    "connector_platform_type": {
        "required": True,
        "type": "string",
        "default": "Office365",
        "allowed": ["Office365", "Microsoft Exchange"],
    },
    "enable_document_permission": {
        "required": False,
        "type": "boolean",
        "default": True,
    },
    "objects": {
        "type": "dict",
        "nullable": True,
        "schema": {
            "mails": {
                "nullable": True,
                "type": "dict",
                "schema": {
                    "include_fields": {"nullable": True, "type": "list"},
                    "exclude_fields": {"nullable": True, "type": "list"},
                },
            },
            "calendar": {
                "type": "dict",
                "nullable": True,
                "schema": {
                    "include_fields": {"nullable": True, "type": "list"},
                    "exclude_fields": {"nullable": True, "type": "list"},
                },
            },
            "tasks": {
                "type": "dict",
                "nullable": True,
                "schema": {
                    "include_fields": {"nullable": True, "type": "list"},
                    "exclude_fields": {"nullable": True, "type": "list"},
                },
            },
            "contacts": {
                "type": "dict",
                "nullable": True,
                "schema": {
                    "include_fields": {"nullable": True, "type": "list"},
                    "exclude_fields": {"nullable": True, "type": "list"},
                },
            },
        },
    },
    "start_time": {
        "required": False,
        "type": "datetime",
        "max": datetime.datetime.utcnow(),
        "default": (datetime.datetime.utcnow() - datetime.timedelta(days=180)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "coerce": coerce_rfc_3339_date,
    },
    "end_time": {
        "required": False,
        "type": "datetime",
        "max": datetime.datetime.utcnow(),
        "default": (datetime.datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "coerce": coerce_rfc_3339_date,
    },
    "log_level": {
        "required": False,
        "type": "string",
        "default": "INFO",
        "allowed": ["DEBUG", "INFO", "WARNING", "ERROR"],
    },
    "retry_count": {"required": False, "type": "integer", "default": 3, "min": 1},
    "source_sync_thread_count": {"required": True, "type": "integer", "default": 5},
    "enterprise_search_sync_thread_count": {
        "required": True,
        "type": "integer",
        "default": 5,
    },
    "connector.user_mapping": {"required": False, "type": "string"},
}
