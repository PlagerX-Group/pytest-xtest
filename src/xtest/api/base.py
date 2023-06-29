"""Базовый модуль для отправки HTTP-запросов."""
import typing as t
from urllib.parse import urljoin

from requests import ConnectionError, HTTPError, Response, Session


def retry_request(func: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
    def wrapper(*args, **kwargs) -> t.Any:
        count_retry = 3

        last_exc = None
        last_exc_msg = None
        for _ in list(range(count_retry)):
            try:
                return func(*args, **kwargs)
            except ConnectionError as exception_msg:
                last_exc = ConnectionError
                last_exc_msg = exception_msg
        raise last_exc(last_exc_msg)  # type: ignore

    return wrapper


class APIClientBase:
    """Базовый класс для отправки HTTP-запросов."""

    disable_status_code_verify: bool = False

    def __init__(self, base_url: str, /, *, access_token: str = None):
        self._base_url = base_url
        self._session = Session()
        self.access_token = access_token

    @property
    def headers_bearer_authorizaton(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    @retry_request
    def request(
        self,
        endpoint: str,
        *,
        method: str = "get",
        headers: dict = None,
        data: dict = None,
        params: dict = None,
        payload: dict = None,
        files: dict = None,
        jsonify: bool = False,
        verify: bool = False,
        allow_redirects: bool = True,
        expected_status_code: int = 200,
        timeouts: t.Optional[t.Union[float, tuple[float, float], tuple[float, None]]] = (120, 120),
    ) -> t.Union[Response, t.Dict[str, t.Any], t.List[t.Any]]:

        response = self._session.request(
            method,
            url=urljoin(self._base_url, endpoint),
            headers=headers,
            data=data,
            params=params,
            json=payload,
            allow_redirects=allow_redirects,
            files=files,
            verify=verify,
            timeout=timeouts,
        )

        if response.status_code != expected_status_code and not self.disable_status_code_verify:
            raise HTTPError(
                f'Ошибка при HTTP-запросе (expected_code={expected_status_code}, got_code={response.status_code})\n'
                f'Ответ: {response.text}.'
            )

        if jsonify:
            return response.json()
        return response
