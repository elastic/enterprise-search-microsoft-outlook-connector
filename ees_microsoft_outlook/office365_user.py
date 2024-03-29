#
# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License 2.0;
# you may not use this file except in compliance with the Elastic License 2.0.
#
"""This module is used to get users and its account details from Office365."""

import json
import warnings

import requests
from exchangelib import (IMPERSONATION, OAUTH2, Account, Configuration,
                         FaultTolerance, Identity, OAuth2Credentials)

from .constant import (API_SCOPE, EWS_ENDPOINT, GRAPH_BASE_URL,
                       MICROSOFTONLINE_URL)


class Office365User:
    """This class fetch users and user accounts"""

    def __init__(self, config):
        self.config = config
        self.client_id = self.config.get_value("office365.client_id")
        self.tenant_id = self.config.get_value("office365.tenant_id")
        self.secret_value = self.config.get_value("office365.client_secret")

    def get_users(self):
        """Fetch users from Azure Active Directory
        Returns:
            user_request: Status of user endpoint
            users_mails: Fetched response from Azure Active Directory
        """
        warnings.filterwarnings("ignore")
        try:
            scope = API_SCOPE

            # Logic to generate access token
            try:
                token_request = requests.post(
                    f"{MICROSOFTONLINE_URL}/{self.tenant_id}/oauth2/v2.0/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.secret_value,
                        "scope": scope,
                    },
                    verify=False,
                )

                token_response = json.loads(token_request.text)
                access_token = token_response["access_token"]
            except requests.exceptions.HTTPError as http_error:
                raise requests.exceptions.HTTPError(f"Http Error. Error: {http_error}")
            except requests.exceptions.ConnectionError as connection_error:
                raise requests.exceptions.ConnectionError(
                    f"Error Connecting. Error: {connection_error}"
                )
            except requests.exceptions.Timeout as timeout_error:
                raise requests.exceptions.Timeout(
                    f"Timeout Error. Error: {timeout_error}"
                )
            except requests.exceptions.RequestException as request_error:
                raise requests.exceptions.RequestException(f"Error: {request_error}")

            # Logic to fetch users
            try:
                user_request = requests.get(
                    GRAPH_BASE_URL + "/users",
                    headers={"Authorization": f"Bearer {access_token}"},
                    verify=False,
                )

                user_res = json.loads(user_request.text)
                user_res_value = user_res["value"]
            except requests.exceptions.HTTPError as http_error:
                raise requests.exceptions.HTTPError(f"Http Error. Error: {http_error}")
            except requests.exceptions.ConnectionError as connection_error:
                raise requests.exceptions.ConnectionError(
                    f"Error Connecting. Error: {connection_error}"
                )
            except requests.exceptions.Timeout as timeout_error:
                raise requests.exceptions.Timeout(
                    f"Timeout Error. Error: {timeout_error}"
                )
            except requests.exceptions.RequestException as request_error:
                raise requests.exceptions.RequestException(f"Error: {request_error}")

            users_mails = []

            for user_mail in user_res_value:
                users_mails.append(user_mail["mail"])
            return users_mails
        except Exception as exception:
            raise Exception(
                f"Error while fetching users from Azure Active Directory. Error: {exception}"
            )

    def get_users_accounts(self, users):
        """Fetch user account from office365
        :param users: Azure active directory user list
        Returns:
            users_accounts: List of all user accounts
        """
        users_accounts = []
        try:

            for user_account in users:
                credentials = OAuth2Credentials(
                    client_id=self.client_id,
                    tenant_id=self.tenant_id,
                    client_secret=self.secret_value,
                    identity=Identity(primary_smtp_address=user_account),
                )
                conf = Configuration(
                    credentials=credentials,
                    auth_type=OAUTH2,
                    service_endpoint=EWS_ENDPOINT,
                    retry_policy=FaultTolerance(max_wait=900),
                )
                account = Account(
                    user_account,
                    config=conf,
                    autodiscover=False,
                    access_type=IMPERSONATION,
                )
                users_accounts.append(account)
            return users_accounts
        except Exception as exception:
            raise Exception(
                f"Error while creating users account objects. Error: {exception}"
            )
