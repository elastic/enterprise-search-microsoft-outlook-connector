#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module is used to get users accounts from microsoft exchange server.
"""

import warnings

from exchangelib import IMPERSONATION, Account, Configuration, Credentials
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from ldap3 import SAFE_SYNC, Connection, Server

from .utils import CustomException


class MicrosoftExchangeServerUser:
    """This class fetch users and user accounts"""

    def __init__(self, config):
        self.config = config

    def get_users(self):
        """Fetch users from Exchange Active Directory
        Returns:
            response: Fetched response from Exchange Active Directory
        """
        warnings.filterwarnings("ignore")
        try:
            server = Server(
                self.config.get_value("microsoft_exchange.active_directory_server")
            )
            conn = Connection(
                server,
                self.config.get_value("microsoft_exchange.username"),
                self.config.get_value("microsoft_exchange.password"),
                client_strategy=SAFE_SYNC,
                auto_bind=True,
            )

            domain_name_list = self.config.get_value("microsoft_exchange.domain").split(".")
            ldap_domain_name_list = ["DC=" + domain for domain in domain_name_list]
            search_query = ','.join(map(str, ldap_domain_name_list))

            status, _, response, _ = conn.search(
                search_query,
                "(&(objectCategory=person)(objectClass=user)(givenName=*))",
                attributes=["mail"],
            )
            if status:
                return response
            else:
                raise CustomException(
                    "Error while searching users from Exchange Active Directory."
                )
        except Exception as exception:
            raise CustomException(
                f"Error while fetching users from Exchange Active Directory. Error: {exception}"
            )

    def get_users_accounts(self, users):
        """Fetch user account from exchange server
        :param users: Fetch users from Exchange Active Directory
        Returns:
            users_accounts: List of all user accounts
        """
        users_accounts = []
        try:
            BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
            for user in users:
                if "searchResRef" not in user["type"]:
                    credentials = Credentials(
                        self.config.get_value("microsoft_exchange.username"),
                        self.config.get_value("microsoft_exchange.password"),
                    )
                    config = Configuration(
                        server=self.config.get_value("microsoft_exchange.server"),
                        credentials=credentials,
                    )
                    user_account = Account(
                        primary_smtp_address=user["attributes"]["mail"],
                        config=config,
                        access_type=IMPERSONATION,
                    )
                    users_accounts.append(user_account)
            return users_accounts
        except Exception as exception:
            raise CustomException(
                f"Error while fetching users account from exchange server. Error: {exception}"
            )
