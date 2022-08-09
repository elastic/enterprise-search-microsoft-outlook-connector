#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module allows to synchronize the user permissions from Microsoft Outlook to the Workplace Search.
"""
from iteration_utilities import unique_everseen

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

    def remove_all_permissions(self, users_accounts):
        """Removes all the permissions present in the Workplace Search"""
        try:
            ws_users_permissions = (
                self.workplace_search_custom_client.list_permissions()
            )
            outlook_user_permissions = []
            indexes_of_existing_users = []
            deleted_users = ws_users_permissions["results"]

            # Create list of current users permissions.
            for account in users_accounts:
                outlook_user_permissions.append(account.primary_smtp_address)

            # Compare existing permission with Workplace Search condition
            # Create list of indexes of existing users to delete from deleted users list.
            for user_permission in range(len(deleted_users)):
                for key, permissions in deleted_users[user_permission].items():
                    if key == "permissions":
                        for permission in permissions:
                            if permission in outlook_user_permissions:
                                indexes_of_existing_users.append(user_permission)

            indexes_of_existing_users = list(unique_everseen(indexes_of_existing_users))

            # Delete existing users from deleted users list.
            for index in sorted(indexes_of_existing_users, reverse=True):
                del deleted_users[index]

            # Pass deleted users list to remove permission function.
            if deleted_users:
                self.logger.info(
                    "Removing the permissions from the Workplace Search..."
                )
                permission_list = deleted_users
                for permission in permission_list:
                    self.workplace_search_custom_client.remove_permissions(permission)
        except Exception as exception:
            self.logger.exception(
                f"Error while removing the permissions from the Workplace Search. Error: {exception}"
            )

    def set_permissions_to_users(self, users_accounts):
        """Method fetches users from Microsoft Outlook and adds fetched permissions to Enterprise Search users.
        :param users_accounts: List of Microsoft Outlook users
        """
        sync_microsoft_outlook = SyncMicrosoftOutlook(
            self.config,
            self.logger,
            self.workplace_search_custom_client,
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

        self.remove_all_permissions(users_accounts)
        self.set_permissions_to_users(users_accounts)
