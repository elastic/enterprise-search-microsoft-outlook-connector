#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module is used to get users accounts from microsoft exchange server.
"""

import warnings
from urllib.parse import urlparse

import requests.adapters
from exchangelib import (IMPERSONATION, Account, Configuration, Credentials,
                         FaultTolerance)
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from ldap3 import SAFE_SYNC, Connection, Server

global_dns_name = ""
global_ssl_certificate_path = ""


class RootCAAdapter(requests.adapters.HTTPAdapter):
    """This class is use to verify ssl certificate"""

    def cert_verify(self, conn, url, ssl_certificate_file, cert):
        """This method is used to verify certificate
        :param conn: The urllib3 connection object associated with the cert.
        :param url: The requested URL.
        :param ssl_certificate_file: Dictionary which contain ssl certificate
        :param cert: The SSL certificate to verify.
        """
        ssl_certificate_file = {
            global_dns_name: global_ssl_certificate_path,
        }[urlparse(url).hostname]
        super().cert_verify(conn=conn, url=url, verify=ssl_certificate_file, cert=cert)


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

            domain_name_list = self.config.get_value("microsoft_exchange.domain").split(
                "."
            )
            ldap_domain_name_list = ["DC=" + domain for domain in domain_name_list]
            search_query = ",".join(map(str, ldap_domain_name_list))

            status, _, response, _ = conn.search(
                search_query,
                "(&(objectCategory=person)(objectClass=user)(givenName=*))",
                attributes=["mail"],
            )
            if status:
                return response
            else:
                raise Exception(
                    "Error while searching users from Exchange Active Directory."
                )
        except Exception as exception:
            raise Exception(
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
            # Logic to establish secure connection when SSL is enabled into exchange server host name
            if self.config.get_value("microsoft_exchange.secure_connection"):
                global global_dns_name, global_ssl_certificate_path
                global_dns_name = self.config.get_value("microsoft_exchange.server")
                global_ssl_certificate_path = self.config.get_value(
                    "microsoft_exchange.certificate_path"
                )

                BaseProtocol.HTTP_ADAPTER_CLS = RootCAAdapter
            else:
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
                        retry_policy=FaultTolerance(max_wait=900),
                    )
                    user_account = Account(
                        primary_smtp_address=user["attributes"]["mail"],
                        config=config,
                        access_type=IMPERSONATION,
                    )
                    users_accounts.append(user_account)
            return users_accounts
        except Exception as exception:
            raise Exception(
                f"Error while fetching users account from exchange server. Error: {exception}"
            )
