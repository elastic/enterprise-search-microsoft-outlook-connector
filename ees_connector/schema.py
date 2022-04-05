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
    'enterprise_search.api_key': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'enterprise_search.source_id': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'enterprise_search.host_url': {
        'required': True,
        'type': 'string',
        'empty': False
    },
    'include': {
        'nullable': True,
        'type': 'dict',
    },
    'exclude': {
        'nullable': True,
        'type': 'dict',
    },
    'start_time': {
        'required': False,
        'type': 'datetime',
        'max': datetime.datetime.utcnow(),
        'default': '1970-01-01T00:00:00Z',
        'coerce': coerce_rfc_3339_date
    },
    'end_time': {
        'required': False,
        'type': 'datetime',
        'max': datetime.datetime.utcnow(),
        'default': (datetime.datetime.utcnow()).strftime(RFC_3339_DATETIME_FORMAT),
        'coerce': coerce_rfc_3339_date
    },
    'log_level': {
        'required': False,
        'type': 'string',
        'default': 'INFO',
        'allowed': ['DEBUG', 'INFO', 'WARNING', 'ERROR ']
    },
    'retry_count': {
        'required': False,
        'type': 'integer',
        'default': 3,
        'min': 1
    },
    'source_sync_thread_count': {
        'required': False,
        'type': 'integer',
        'default': 5,
        'min': 1
    },
    'enterprise_search_sync_thread_count': {
        'required': False,
        'type': 'integer',
        'default': 5,
        'min': 1
    },
    'enable_document_permission': {
        'required': False,
        'type': 'boolean',
        'default': True
    },
    'connector.user_mapping': {
        'required': False,
        'type': 'string',
    }
}
