import typing as t
from pprint import pformat
from urllib.parse import parse_qsl, urljoin, urlparse

from requests.cookies import RequestsCookieJar

from xtest.api import APIClientBase
from xtest.utils.keycloak.exceptions import KeycloakNotAuthorizationException, KeycloakException
from xtest.utils.keycloak.models import KeycloakUserModel


class KeycloakClient(APIClientBase):
    disable_status_code_verify = True

    def __init__(
        self,
        target_keycloak_url: str,
        client_id: str,
        client_secret: str,
        realm: str,
        /,
    ):
        self.__target_keycloak_url = target_keycloak_url
        self.__realm = realm
        self.__client_id = client_id
        self.__client_secret = client_secret
        super().__init__(self.__target_keycloak_url)

    @property
    def service_account_authorization_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.get_access_token_from_service_account()}',
        }

    def get_access_token_from_service_account(self) -> t.Optional[str]:
        url = urljoin(
            self.__target_keycloak_url,
            f"auth/realms/{self.__realm}/protocol/openid-connect/token",
        )
        data = {
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "grant_type": "client_credentials",
        }
        response = self.request(url=url, method="post", data=data)
        if response.status_code != 200:
            raise KeycloakNotAuthorizationException(pformat(response.json()))

        response_json = response.json()
        if token := response_json.get("access_token"):
            return str(token)
        return None

    def get_user_id_by_username(self, username: str) -> str:
        username = username.lower()
        url = urljoin(self.__target_keycloak_url, f"auth/admin/realms/{self.__realm}/users")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token_from_service_account()}",
        }
        params = {"username": username, "exact": True}
        response = self.request(url=url, headers=headers, params=params)  # type: ignore
        response_json = response.json()

        def __get_uuid_from_dict(dictionary: dict) -> t.Optional[str]:
            if username == dictionary.get("username"):
                return dictionary.get("id")
            return None

        if isinstance(response_json, list):
            for user in response_json:
                if ids := __get_uuid_from_dict(user):
                    return ids
        elif isinstance(response_json, dict):
            if ids := __get_uuid_from_dict(response_json):
                return ids
        raise KeycloakException(f"User not found by username. Username: {username}")

    def get_impersonate_cookies_by_username(self, username: str) -> RequestsCookieJar:
        user_uuid = self.get_user_id_by_username(username=username)
        url = urljoin(
            self.__target_keycloak_url,
            f"/auth/admin/realms/{self.__realm}/users/{user_uuid}/impersonation",
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token_from_service_account()}",
        }
        response = self.request(url=url, method="post", headers=headers)
        if response.status_code != 200:
            raise KeycloakException(response.json())

        return response.cookies

    def search_service_account_by_client_id(self, client_id: str) -> dict:
        url = urljoin(self.__target_keycloak_url, "/auth/admin/realms/globaltruck/clients")
        params = {"clientId": client_id, "max": 1, "search": True}
        headers = {"Authorization": f"Bearer {self.get_access_token_from_service_account()}"}
        response = self.request(url=url, params=params, headers=headers)  # type: ignore
        if response.status_code != 200:
            raise KeycloakException(response.text)
        response_json = response.json()
        for _client in response_json:
            if _client.get("clientId") == client_id:
                return _client
        raise KeycloakException(f"Client with ID '{client_id}' not found.")

    def get_token_by_username(self, username: str) -> t.Optional[str]:
        user_uuid = self.get_user_id_by_username(username=username)

        # Имперсонализация.
        impersonate_url = urljoin(
            self.__target_keycloak_url,
            f"/auth/admin/realms/{self.__realm}/users/{user_uuid}/impersonation",
        )
        impersonate_headers = {"Authorization": f"Bearer {self.get_access_token_from_service_account()}"}
        impersonate_response = self.request(url=impersonate_url, method="post", headers=impersonate_headers)
        assert impersonate_response.status_code == 200, (
            f"Got status code: {impersonate_response.status_code}\n" f"Response_text: {impersonate_response.text}"
        )

        # Авторизация пользователя
        auth_url = urljoin(
            self.__target_keycloak_url,
            f"/auth/realms/{self.__realm}/protocol/openid-connect/auth",
        )
        auth_params = {
            "response_mode": "fragment",
            "response_type": "token",
            "client_id": self.__client_id,
            "redirect_uri": self.__target_keycloak_url,
        }
        auth_response = self.request(auth_url, params=auth_params, headers=impersonate_headers)
        try:
            assert auth_response.history[0].status_code == 302
        except IndexError as ex:
            raise KeycloakUserNotAuthorizationError(username) from ex
        auth_url_replace = auth_response.url.replace("#", "?")
        auth_query_string = dict(parse_qsl(urlparse(auth_url_replace).query))
        return auth_query_string.get("access_token")

    def create_user(self, user: KeycloakUserModel, /) -> None:
        endpoint = f'auth/admin/realms/{self.__realm}/users'
        request_body = {
            'email': user.email,
            'emailVerified': user.is_verify_email,
            'enabled': user.is_enabled,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'username': user.username,
            'credentials': [
                {
                    'temporary': False,
                    'type': 'password',
                    'value': user.password,
                }
            ]
        }
        if user.attributes:
            request_body.update({'attributes': user.attributes})

        response = self.request(
            url=urljoin(self.__target_keycloak_url, endpoint),
            payload=request_body,
            method='post',
            headers=self.service_account_authorization_headers,
        )
        if response.status_code != 201:
            raise KeycloakCreateUserErrror(user.email, reason=response.text)

    def delete_user(self, username: str) -> None:
        user_uuid = self.get_user_id_by_username(username)
        url = urljoin(self.__target_keycloak_url, f'/auth/admin/realms/{self.__realm}/users/{user_uuid}')
        response = self.request(method='delete', url=url, headers=self.service_account_authorization_headers)
        if response.status_code != 204:
            raise KeycloakDeleteUserErrror(username, reason=response.text)

    def add_roles(self, username: str, roles: list[str], /) -> None:
        user_uuid = self.get_user_id_by_username(username)
        url = urljoin(
            self.__target_keycloak_url,
            f'/auth/admin/realms/{self.__realm}/users/{user_uuid}/role-mappings/realm',
        )
        response = self.request(
            method='post',
            url=url,
            headers=self.service_account_authorization_headers,
            payload=self.get_keycloak_roles_by_name(roles),
        )
        if response.status_code != 204:
            raise KeycloakUserNotUpdatedErrror(username, reason=response.text)

    def get_keycloak_roles_by_name(self, names: list[str], /) -> dict[str, t.Any]:
        roles = []
        for role_name in names:
            response = self.request(
                url=urljoin(self.__target_keycloak_url, f'/auth/admin/realms/{self.__realm}/roles'),
                method='get',
                params={
                    'first': 0,
                    'max': 20,
                    'search': role_name
                },
                headers=self.service_account_authorization_headers,
            )
            response_json = response.json()
            for role_dict in response_json or []:
                if role_dict.get('name') == role_name:
                    roles.append(role_dict)
        return roles
