#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to synchronize the user permissions from Microsoft Outlook to the Workplace Search.
"""
from . import constant
from .base_command import BaseCommand
from .microsoft_exchange_server_user import MicrosoftExchangeServerUser
from .office365_user import Office365User
from .sync_microsoft_outlook import SyncMicrosoftOutlook


class PermissionSyncDisabledException(Exception):
    """Exception raised when permission sync is disabled, but expected to be enabled.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="The Permission flag is disabled."):
        super().__init__(message)


class PermissionSyncCommand(BaseCommand):
    """This class contains logic to sync user permissions from the Microsoft Outlook.

    It can be used to run the job that will periodically sync permissions
    from the Microsoft Outlook to Elastic Enterprise Search."""

    def __init__(self, args):
        super().__init__(args)

        config = self.config

        self.logger.debug("Initializing the permission indexing")
        self.ws_source = config.get_value("enterprise_search.source_id")
        self.ws_auth = config.get_value("enterprise_search.api_key")
        self.enable_document_permission = config.get_value("enable_document_permission")
        self.user_mapping = config.get_value("connector.user_mapping")
        self.product_type = config.get_value("connector_platform_type")

    def remove_all_permissions(self):
        """Removes all the permissions present in the Workplace Search"""
        try:
            user_permission = self.workplace_search_client.list_permissions(
                http_auth=self.ws_auth,
                content_source_id=self.ws_source,
            )

            if user_permission:
                self.logger.debug(
                    "Removing the permissions from the Workplace Search..."
                )
                permission_list = user_permission["results"]
                for permission in permission_list:
                    permission_ids = list(permission["permissions"])
                    self.workplace_search_client.remove_user_permissions(
                        http_auth=self.ws_auth,
                        content_source_id=self.ws_source,
                        user=permission["user"],
                        body={"permissions": permission_ids},
                    )
                self.logger.info("Removed the permissions from the Workplace Search.")
        except Exception as exception:
            self.logger.exception(
                f"Error while removing the permissions from the Workplace Search. Error: {exception}"
            )
            raise exception

    def set_permissions_to_users(self, users_accounts):
        """Method fetches users from Microsoft Outlook and adds fetched permissions to Enterprise Search users.
        :param users_accounts: List of Microsoft Outlook users
        """
        sync_microsoft_outlook = SyncMicrosoftOutlook(
            self.config,
            self.logger,
            self.workplace_search_client,
            [],
        )
        for account in users_accounts:
            sync_microsoft_outlook.map_ms_outlook_user_to_ws_user(
                account.primary_smtp_address, [account.primary_smtp_address]
            )

    def execute(self):
        """Runs the permission indexing logic.

        This method when invoked, checks the permission of the Microsoft Outlook users and update those user
        permissions in the Workplace Search.
        """
        self.logger.info("Starting the permission sync..")
        if not self.enable_document_permission:
            self.logger.warning("Exiting as the enable permission flag is set to False")
            raise PermissionSyncDisabledException

        # Logic to fetch users from Microsoft Exchange or Office365
        if constant.CONNECTOR_TYPE_OFFICE365 in self.product_type:
            office365_connection = Office365User(self.config)
            users = office365_connection.get_users()
            users_accounts = office365_connection.get_users_accounts(users)
        elif constant.CONNECTOR_TYPE_MICROSOFT_EXCHANGE in self.product_type:
            microsoft_exchange_server_connection = MicrosoftExchangeServerUser(
                self.config
            )
            users = microsoft_exchange_server_connection.get_users()
            users_accounts = microsoft_exchange_server_connection.get_users_accounts(
                users
            )

        if len(users_accounts) >= 0:
            self.logger.info(
                f"Successfully fetched users accounts from the {self.product_type}"
            )
        else:
            self.logger.info("Error while fetching users from the Active Directory")
            exit()

        self.remove_all_permissions()
        self.set_permissions_to_users(users_accounts)
