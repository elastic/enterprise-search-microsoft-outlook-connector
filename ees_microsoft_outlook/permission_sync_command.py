#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to synchronize the user permissions from Microsoft Outlook to the Workplace Search.
"""


class PermissionSyncCommand:
    """This class contains logic to sync user permissions from Microsoft Outlook."""

    def __init__(self, logger, config, workplace_search_client):
        self.logger = logger
        self.workplace_search_client = workplace_search_client
        self.config = config
        self.ws_auth = config.get_value("enterprise_search.api_key")

    def remove_all_permissions(self):
        """Removes all the permissions present in the Workplace Search"""
        try:
            user_permission = self.workplace_search_client.list_permissions(
                http_auth=self.ws_auth,
                content_source_id=self.config.get_value("enterprise_search.source_id"),
            )

            if user_permission:
                self.logger.debug(
                    "Removing the permissions from the Workplace Search..."
                )
                permission_list = user_permission["results"]
                for permission in permission_list:
                    permission_ids = list(permission["permissions"])
                    self.workplace_search_client.remove_user_permissions(
                        content_source_id=self.config.get_value(
                            "enterprise_search.source_id"
                        ),
                        http_auth=self.ws_auth,
                        user=permission["user"],
                        body={"permissions": permission_ids},
                    )
                self.logger.info("Removed the permissions from the Workplace Search.")
        except Exception as exception:
            self.logger.exception(
                f"Error while removing the permissions from the Workplace Search. Error: {exception}"
            )
            raise exception
