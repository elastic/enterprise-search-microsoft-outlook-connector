#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module contains all the constants used throughout the code.
"""

import datetime

RFC_3339_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
BATCH_SIZE = 100
CONNECTOR_TYPE_OFFICE365 = "Office365"
CONNECTOR_TYPE_MICROSOFT_EXCHANGE = "Microsoft Exchange"
CURRENT_TIME = (datetime.datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%SZ")
