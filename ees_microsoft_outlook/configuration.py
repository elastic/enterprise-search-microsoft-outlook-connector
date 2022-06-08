#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""Configuration module allows manipulations with application configuration.

    This module can be used to read and validate configuration file that defines
    the settings of the Microsoft Outlook connector.
"""

import yaml
from cerberus import Validator
from yaml.error import YAMLError

from .constant import (
    CONNECTOR_TYPE_MICROSOFT_EXCHANGE,
    CONNECTOR_TYPE_OFFICE365,
    RFC_3339_DATETIME_FORMAT,
)
from .schema import schema


class ConfigurationInvalidException(Exception):
    """Exception raised when configuration was invalid.

    Attributes:
        errors - errors found in the configuration
        message -- explanation of the error
    """

    def __init__(self, errors):
        super().__init__(f"Provided configuration was invalid. Errors: {errors}.")
        self.errors = errors


class ConfigurationParsingException(Exception):
    """Exception raised when configuration could not be parsed.

    Attributes:
        file_name - name of the file that could not be parsed
    """

    def __init__(self, file_name, inner_exception):
        super().__init__("Failed to parse configuration file.")

        self.file_name = file_name
        self.inner_exception = inner_exception


class Configuration:
    """Configuration class is responsible for parsing, validating and accessing
    configuration options from connector configuration file."""

    def __init__(self, file_name):
        self.__configurations = {}
        self.file_name = file_name
        try:
            with open(file_name, encoding="utf-8") as stream:
                self.__configurations = yaml.safe_load(stream)
        except YAMLError as exception:
            raise ConfigurationParsingException(file_name, exception)
        self.__configurations = self.validate()
        if self.__configurations["start_time"] >= self.__configurations["end_time"]:
            raise ConfigurationInvalidException(
                f"The start_time: {self.__configurations['start_time']}  "
                f"cannot be greater than or equal to the end_time: {self.__configurations['end_time']}"
            )
        # Converting datetime object to string
        for date_config in ["start_time", "end_time"]:
            value = self.__configurations[date_config]
            self.__configurations[date_config] = self.__parse_date_config_value(value)

    def validate(self):
        """Validates each properties defined in the yaml configuration file"""
        if (
            self.__configurations["connector_platform_type"]
            and isinstance(self.__configurations["connector_platform_type"], str)
            and CONNECTOR_TYPE_OFFICE365
            in self.__configurations["connector_platform_type"]
        ):
            schema.update(
                {
                    "microsoft_exchange.secure_connection": {
                        "required": False,
                        "type": "boolean",
                        "default": True,
                    },
                    "microsoft_exchange.certificate_path": {
                        "required": False,
                        "type": "string",
                        "empty": True,
                    },
                    "office365.client_id": {
                        "required": True,
                        "type": "string",
                        "empty": False,
                    },
                    "office365.tenant_id": {
                        "required": True,
                        "type": "string",
                        "empty": False,
                    },
                    "office365.client_secret": {
                        "required": True,
                        "type": "string",
                        "empty": False,
                    },
                }
            )
        elif (
            self.__configurations["connector_platform_type"]
            and isinstance(self.__configurations["connector_platform_type"], str)
            and CONNECTOR_TYPE_MICROSOFT_EXCHANGE
            in self.__configurations["connector_platform_type"]
        ):
            if self.__configurations["microsoft_exchange.secure_connection"] is False:
                schema.update(
                    {
                        "microsoft_exchange.secure_connection": {
                            "required": True,
                            "type": "boolean",
                            "default": True,
                        },
                        "microsoft_exchange.certificate_path": {
                            "required": False,
                            "type": "string",
                            "empty": True,
                        },
                    }
                )
            schema.update(
                {
                    "microsoft_exchange.active_directory_server": {
                        "required": True,
                        "type": "string",
                        "empty": False,
                    },
                    "microsoft_exchange.server": {
                        "required": True,
                        "type": "string",
                        "empty": False,
                    },
                    "microsoft_exchange.username": {
                        "required": True,
                        "type": "string",
                        "empty": False,
                    },
                    "microsoft_exchange.password": {
                        "required": True,
                        "type": "string",
                        "empty": False,
                    },
                    "microsoft_exchange.domain": {
                        "required": True,
                        "type": "string",
                        "regex": r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$",
                        "empty": False,
                    },
                }
            )
        else:
            raise ConfigurationInvalidException(
                "Enter valid connector platform type. Allowed values are 'Microsoft Outlook' and 'Office365'"
            )

        validator = Validator(schema)
        validator.validate(self.__configurations, schema)
        if validator.errors:
            raise ConfigurationInvalidException(validator.errors)

        return validator.document

    def get_value(self, key):
        """Returns a configuration value that matches the key argument"""

        return self.__configurations.get(key)

    @staticmethod
    def __parse_date_config_value(string):
        """Change string to Datetime format"""
        return string.strftime(RFC_3339_DATETIME_FORMAT)
