import logging
import os
import sys

from ees_microsoft_outlook.constant import GRAPH_BASE_URL, MICROSOFTONLINE_URL
from ees_microsoft_outlook.office365_user import Office365User

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ees_microsoft_outlook.configuration import Configuration  # noqa


def settings():
    """This function loads configuration from the file and returns it along with retry_count setting."""
    configuration = Configuration(
        file_name=os.path.join(
            os.path.join(os.path.dirname(__file__), "config"),
            "microsoft_outlook_connector.yml",
        )
    )

    logger = logging.getLogger("unit_test_utils")
    return configuration, logger


def test_get_users(requests_mock):
    """Test for get users from outlook.
    :param requests_mock: Fixture for requests.get calls.
    """
    config, _ = settings()
    office365_obj = Office365User(config)

    requests_mock.post(
        f"{MICROSOFTONLINE_URL}/{office365_obj.tenant_id}/oauth2/v2.0/token",
        json={
            "token_type": "Bearer",
            "expires_in": 3599,
            "ext_expires_in": 3599,
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiw\
iaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        },
    )
    requests_mock.get(
        GRAPH_BASE_URL + "/users",
        json={
            "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users",
            "value": [
                {
                    "businessPhones": ["+1 111 222 333"],
                    "displayName": "John doe",
                    "givenName": "John",
                    "jobTitle": "Manager",
                    "mail": "John.doe@abc.com",
                    "mobilePhone": None,
                    "officeLocation": "demo",
                    "preferredLanguage": "en-US",
                    "surname": "doe",
                    "userPrincipalName": "John.doe@abc.com",
                    "id": "14e90cc9-e59b-4a2f-b50e-7568237f5bc7",
                },
            ],
        },
    )
    targeted_users = office365_obj.get_users()
    assert targeted_users == ["John.doe@abc.com"]
