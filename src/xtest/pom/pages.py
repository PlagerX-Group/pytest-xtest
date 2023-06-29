from __future__ import annotations

import abc
import re
import time
import typing as t
from abc import ABC
from urllib.parse import parse_qs, urljoin, urlparse

from requests.cookies import RequestsCookieJar
from selenium.common import TimeoutException, exceptions
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from xtest.pom.exceptions import (AttributeNotPresentInWebElementError,
                                  ElementNotDisappearedOnPageError,
                                  ElementNotPresentOnPageError,
                                  PageNotLoadedError,
                                  TextNotPresentInElementError)
from xtest.pom.locators import AdvancedLocator
from xtest.pom.predicates import url_matches_without_get_parameters
from xtest.utils.decorators import wait


class _BaseActions(ABC):
    def __init__(self, driver: WebDriver, /):
        self.driver = driver

    @property
    def action_chains(self) -> ActionChains:
        return ActionChains(self.driver)

    @property
    def get_params(self) -> dict[str, list[str]]:
        """GET-параметры на странице.

        Returns:
            dict[str, list[str]]: get-параметры.
        """
        parsed_url = urlparse(self.driver.current_url)
        return parse_qs(parsed_url.query)

    def is_stale_of(
        self, element: WebElement, /, *, timeout: t.Optional[int] = None
    ) -> bool:
        try:
            return self.wait(timeout=timeout).until(ec.staleness_of(element))
        except exceptions.TimeoutException:
            return False

    def press_tab(self) -> _BaseActions:
        self.action_chains.send_keys(Keys.TAB).perform()
        return self

    def click(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> None:
        wait(
            method=lambda: self.find_visible_element(locator, timeout=1).click(),
            timeout=timeout,
            error=(
                exceptions.ElementClickInterceptedException,
                exceptions.ElementNotInteractableException,
                exceptions.StaleElementReferenceException,
                ElementNotPresentOnPageError,
                AttributeError,
            ),
        )

    def click_on_select_elements(
        self,
        locator: AdvancedLocator,
        value: str,
        /,
        *,
        timeout: t.Optional[int] = None,
    ) -> None:
        def wrapper():
            for element in self.find_visible_elements(locator, timeout=1):
                if element.is_displayed() and element.text.strip() == value:
                    element.click()
                    return
            raise exceptions.ElementNotVisibleException(
                f"Элемент отсутствует на странице со значением: {value}"
            )

        return wait(
            method=wrapper,
            error=(exceptions.ElementNotVisibleException, ElementNotPresentOnPageError),
            timeout=timeout,
        )

    def send_keys(
        self, locator: AdvancedLocator, send_data: str, /, *, auto_clear: bool = True
    ) -> None:
        web_element = self.find_visible_element(locator)
        web_element.click()

        if auto_clear:
            while web_element.get_attribute("value") != "":
                web_element.send_keys(Keys.BACKSPACE)
                web_element.send_keys(Keys.DELETE)

        web_element.send_keys(send_data)
        time.sleep(0.7)

    def send_keys_by_key(
        self,
        locator: AdvancedLocator,
        send_data: str,
        /,
        *,
        auto_clear: bool = True,
        send_timeout: float = None,
    ):

        if send_data in [None, ""]:
            return

        web_element = self.find_visible_element(locator)

        if auto_clear:
            while web_element.get_attribute("value") != "":
                web_element.send_keys(Keys.BACKSPACE)
                web_element.send_keys(Keys.DELETE)

        for char in str(send_data):
            web_element.send_keys(char)
            if isinstance(send_timeout, float):
                time.sleep(send_timeout)

    def wait(self, /, *, timeout: t.Optional[int] = None) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout=timeout or 10, poll_frequency=0.001)

    def is_visible_element(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> bool:
        try:
            self.find_visible_element(locator, timeout=timeout)
            return True
        except (exceptions.ElementNotVisibleException, ElementNotPresentOnPageError):
            return False

    def find_element(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> WebElement:
        try:
            return self.wait(timeout=timeout).until(
                method=ec.presence_of_element_located(locator),
                message=f"Элемент не найден на странице (timeout={timeout}). Локатор: {locator}.",
            )
        except exceptions.TimeoutException as ex:
            raise ElementNotPresentOnPageError(locator, timeout=timeout) from ex

    def is_disabled_element(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> bool:
        try:
            return (
                self.get_attr_from_obj("disabled", locator, timeout=timeout) == "true"
            )
        except exceptions.ElementClickInterceptedException:
            return False

    def find_visible_element(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> WebElement:
        try:
            return self.wait(timeout=timeout).until(
                method=ec.visibility_of_element_located(locator.as_locator),
                message=f"Элемент не отображается на странице (timeout={timeout}). Локатор: {locator.as_locator}.",
            )
        except exceptions.TimeoutException as ex:
            raise ElementNotPresentOnPageError(locator, timeout=timeout) from ex

    def find_elements(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> t.List[WebElement]:
        try:
            return list(
                self.wait(timeout=timeout).until(
                    ec.presence_of_all_elements_located(locator)
                )
            )
        except exceptions.TimeoutException:
            return []

    def find_visible_elements(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> list[WebElement]:
        try:
            return self.wait(timeout=timeout).until(
                method=ec.visibility_of_all_elements_located(locator.as_locator),
                message=f"Не найдены элементы на странице (timeout={timeout}). Локатор: {locator.as_locator}.",
            )
        except exceptions.TimeoutException as ex:
            raise ElementNotPresentOnPageError(locator, timeout=timeout) from ex

    def wait_hide_element(
        self, locator: AdvancedLocator, /, *, timeout: int = None
    ) -> WebElement:
        try:
            return self.wait(timeout=timeout).until(
                method=ec.invisibility_of_element_located(locator.as_locator),
                message=f"Элемент не исчез со страницы (timeout={timeout}). Локатор: {locator}.",
            )
        except exceptions.TimeoutException as ex:
            raise ElementNotDisappearedOnPageError(locator, timeout=timeout) from ex

    def __is_present_text_in_web_element(
        self,
        locator: AdvancedLocator,
        callable_method: t.Callable,
        /,
        *,
        timeout: float = None,
    ) -> t.Any:
        def wrapper():
            element_text = callable_method(locator, timeout=1)
            if isinstance(element_text, str):
                if len(element_text.strip()) > 0:
                    return True
            raise TextNotPresentInElementError(locator, "", timeout=timeout)

        return wait(
            method=wrapper,
            timeout=timeout,
            check=True,
            error=(TextNotPresentInElementError, ElementNotPresentOnPageError),
        )

    def wait_text_present(
        self, locator: AdvancedLocator, text: str, /, *, timeout: int = None
    ) -> str:
        def wrapper():
            element_text = self.get_text_from_obj(locator, timeout=1)
            if isinstance(element_text, str):
                if text == element_text.strip():
                    return text
            raise TextNotPresentInElementError(locator, text, timeout=timeout)

        return wait(
            method=wrapper,
            timeout=timeout,
            check=True,
            error=(TextNotPresentInElementError, ElementNotPresentOnPageError),
        )

    def wait_text_appear_in_array_texts(
        self,
        locator: AdvancedLocator,
        expected_text: str,
        /,
        *,
        timeout: int = None,
    ) -> bool:
        def wrapper() -> bool:
            texts = self.get_texts_by_locator(locator, timeout=1)
            if expected_text in texts:
                return True
            return None

        return (
            wait(wrapper, timeout=timeout, check=True, raise_exception=False) or False
        )

    def is_present_text_in_element(
        self, locator: AdvancedLocator, /, *, timeout: int = None
    ) -> bool:
        return self.__is_present_text_in_web_element(
            locator, self.get_text_from_obj, timeout=timeout
        )

    def is_present_text_in_input(
        self, locator: AdvancedLocator, /, *, timeout: float = None
    ) -> bool:
        return self.__is_present_text_in_web_element(
            locator, self.get_value_from_obj, timeout=timeout
        )

    def wait_text_change_from(
        self, locator: AdvancedLocator, text: str, /, *, timeout: int = None
    ) -> bool:
        def _method():
            _text = self.get_text_from_obj(locator, timeout=1)
            if isinstance(_text, str) and len(_text) > 0 and _text != text:
                return True
            raise ElementNotDisappearedOnPageError(
                locator, reason=f'Текст не сменился с "{text}".'
            )

        return wait(
            method=_method,
            timeout=timeout,
            interval=1,
            check=True,
            error=ElementNotDisappearedOnPageError,
        )

    def __get_text_from_object(
        self,
        callback: t.Callable[..., t.Any],
        /,
        *,
        exc: bool = True,
        timeout: t.Optional[int] = None,
    ) -> t.Optional[str]:
        result = wait(
            method=callback,
            timeout=timeout,
            check=True,
            error=(
                exceptions.StaleElementReferenceException,
                ElementNotPresentOnPageError,
                TextNotPresentInElementError,
            ),
            raise_exception=exc,
        )
        if result is not None:
            return str(result)
        return None

    def get_text_from_obj(
        self,
        locator: AdvancedLocator,
        /,
        *,
        timeout: t.Optional[int] = None,
    ) -> t.Optional[str]:
        def wrapper():
            if element := self.find_visible_element(locator, timeout=1):
                return element.text
            raise TextNotPresentInElementError(locator, "", timeout=timeout)

        return self.__get_text_from_object(wrapper, timeout=timeout)

    def get_text_from_hidden_obj(
        self,
        locator: AdvancedLocator,
        /,
        *,
        timeout: t.Optional[int] = None,
    ) -> t.Optional[str]:
        def wrapper():
            if element := self.find_element(locator, timeout=timeout):
                return element.text
            raise TextNotPresentInElementError(locator, "", timeout=timeout)

        return self.__get_text_from_object(wrapper, timeout=timeout)

    def get_attr_from_obj(
        self,
        attribute_name: str,
        locator: AdvancedLocator,
        /,
        *,
        timeout: t.Optional[int] = None,
    ) -> t.Optional[str]:
        def wrapper() -> str:
            if element := self.find_visible_element(locator, timeout=1):
                attribute_value = element.get_attribute(attribute_name)
                if isinstance(attribute_value, str):
                    return attribute_value
                raise AttributeNotPresentInWebElementError(
                    locator, attribute_name, timeout=timeout
                )
            raise ElementNotPresentOnPageError(locator, timeout=timeout)

        return wait(
            method=wrapper,
            timeout=timeout,
            check=True,
            error=(ElementNotPresentOnPageError, AttributeNotPresentInWebElementError),
        )

    def get_link_from_obj(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> t.Optional[str]:
        return self.get_attr_from_obj("href", locator, timeout=timeout)

    def get_value_from_obj(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> t.Optional[str]:
        return self.get_attr_from_obj("value", locator, timeout=timeout)

    def get_values_from_objects(
        self, locator: AdvancedLocator, /, *, timeout: float = None
    ) -> list[t.Any]:
        return [
            element.get_attribute("value")
            for element in self.find_visible_elements(locator, timeout=timeout)
        ]

    ##################################
    def get_selected_from_obj(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> t.Optional[bool]:
        return bool(
            wait(
                method=lambda: self.find_visible_element(
                    locator, timeout=timeout
                ).is_selected(),
                timeout=timeout,
                check=True,
            )
        )

    def set_value_to_checkbox(self, locator: AdvancedLocator, value: bool, /):
        web_element = self.find_visible_element(locator)
        web_element_selected = web_element.is_selected()
        if value and not web_element_selected:
            web_element.click()
        elif not value and web_element_selected:
            web_element.click()
        time.sleep(0.5)

    def get_visible_elements_by_locator(
        self,
        locator: AdvancedLocator,
        /,
        *,
        timeout: t.Optional[int] = None,
    ) -> list[WebElement]:
        try:
            return self.wait(timeout=timeout).until(
                ec.visibility_of_all_elements_located(locator)
            )
        except exceptions.TimeoutException:
            return []

    def is_exists_elements(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> bool:
        return len(self.get_visible_elements_by_locator(locator, timeout=timeout)) > 0

    def is_enabled_element(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> bool:
        try:
            return self.find_visible_element(locator, timeout=timeout).is_enabled()
        except ElementNotPresentOnPageError:
            return False

    def is_enabled_hidden_element(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> bool:
        try:
            return self.find_element(locator, timeout=timeout).is_enabled()
        except ElementNotPresentOnPageError:
            return False

    def get_count_elements_on_page(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> int:
        return len(self.find_visible_elements(locator, timeout=timeout))

    def get_texts_by_locator(
        self, locator: AdvancedLocator, /, *, timeout: t.Optional[int] = None
    ) -> t.List[str]:
        return [
            element.text
            for element in self.find_visible_elements(locator, timeout=timeout)
        ]

    def get_element_style(
        self,
        locator: AdvancedLocator,
        css_style: str,
        /,
        *,
        timeout: t.Optional[int] = None,
    ) -> t.Optional[str]:
        return self.find_visible_element(
            locator, timeout=timeout
        ).value_of_css_property(css_style)

    def is_exists_value_in_html_attribute(
        self, locator: AdvancedLocator, attribute: str, expected_value: str, /
    ) -> bool:
        def wrapper():
            selected_attribute = self.get_attr_from_obj(attribute, locator)
            if selected_attribute is not None:
                return expected_value in selected_attribute
            return None

        return wait(method=wrapper, check=True, raise_exception=False)

    def wait_number_of_elements_to_appear(
        self,
        locator: AdvancedLocator,
        count_elements: int,
        /,
        *,
        is_visibility: bool = True,
        timeout: int = None,
    ) -> bool:
        def wrapper() -> bool:
            if is_visibility:
                elements = self.wait(timeout=1).until(
                    ec.visibility_of_all_elements_located(locator.as_locator)
                )
            else:
                elements = self.wait(timeout=1).until(
                    ec.presence_of_all_elements_located(locator.as_locator)
                )
            if len(elements) == count_elements:
                return True
            return None

        try:
            return (
                wait(method=wrapper, check=True, timeout=timeout, raise_exception=False)
                or False
            )
        except exceptions.TimeoutException as ex:
            raise ElementNotPresentOnPageError(locator, timeout=timeout) from ex

    def wait_number_of_more_elements_to_appear(
        self,
        locator: AdvancedLocator,
        count_elements: int,
        /,
        *,
        is_visibility: bool = True,
        timeout: int = None,
    ) -> bool:
        def wrapper() -> bool:
            if is_visibility:
                elements = self.wait(timeout=1).until(
                    ec.visibility_of_all_elements_located(locator.as_locator)
                )
            else:
                elements = self.wait(timeout=1).until(
                    ec.presence_of_all_elements_located(locator.as_locator)
                )
            if len(elements) >= count_elements:
                return True
            return None

        try:
            return (
                wait(method=wrapper, check=True, timeout=timeout, raise_exception=False)
                or False
            )
        except exceptions.TimeoutException as ex:
            raise ElementNotPresentOnPageError(locator, timeout=timeout) from ex


class BasePageActions(_BaseActions, ABC):

    # Название страницы.
    page_name: str

    # Endpoint данной страницы.
    endpoint: str

    # URL pattern
    endpoint_pattern: str

    # GET параметры для страницы
    get_parameters: t.Optional[dict[str, t.Any]] = None

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} с ссылкой '{self.endpoint}' (id={id(self)})'>"
        )

    def __str__(self) -> str:
        return (
            f"<{self.__class__.__name__} с ссылкой '{self.endpoint}' (id={id(self)})'>"
        )

    @abc.abstractmethod
    def build_url(self) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def post_open_page(self) -> None:
        raise NotImplementedError()

    @property
    def browser_url_tabs(self) -> list[str]:
        urls = []
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            urls.append(self.driver.current_url.split("?")[0])
        self.driver.switch_to.window(self.driver.window_handles[0])
        return urls

    @property
    def get_endpoint_pattern_groups(self) -> t.Optional[tuple]:
        if result := re.search(self.endpoint_pattern, self.driver.current_url):
            return result.groups()
        return None

    def open_page(self):

        # Открытие страницы по URL.
        self.driver.get(urljoin(endpoint=self.endpoint, parameters=self.get_parameters))

        # Обновление страницы (на всякий случай, пусть будет пока что тут)
        self.refresh_page()

        # Проверяем, что страница обновилась по паттерну URL.
        if not self.wait_change_url_by_pattern(timeout=35):
            raise PageNotLoadedError(
                self.page_name, reason="Не произошел переход по URL"
            )

        # Ожидаем загрузку фронта.
        def wait_loading_page():
            if self.driver.execute_script("return document.readyState;") == "complete":
                return self.is_loading_page()
            return None

        wait_result = wait(
            method=wait_loading_page,
            check=True,
            interval=0.1,
            timeout=10,
        )
        self.post_open_page()
        return wait_result

    def refresh_page(self) -> BasePageActions:
        self.driver.refresh()
        return self

    def set_cookies(self, cookies: RequestsCookieJar, /):
        for cookie in cookies:
            self.driver.add_cookie(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "httpOnly": False,
                }
            )

    def is_loading_page(self) -> bool:
        raise NotImplementedError()

    def wait_change_url_to(self, url: str, /, *, timeout: int = None) -> bool:
        try:
            self.wait(timeout=timeout).until(ec.url_to_be(url))
            return True
        except TimeoutException:
            return False

    def wait_change_url_by_pattern(self, /, *, timeout: int = None) -> bool:
        url_pattern = urljoin(self.build_url(), self.endpoint_pattern.lstrip("/"))
        try:
            self.wait(timeout=timeout).until(
                url_matches_without_get_parameters(url_pattern)
            )
            return True
        except TimeoutException:
            return False


_T = t.TypeVar("_T", bound=_BaseActions)


class BaseElementActions(_BaseActions):
    page_instance: _T

    def __init__(self, driver: WebDriver, page_instance: _T, /) -> None:
        super().__init__(driver)
        self.page_instance = page_instance

    def is_loading_element(self) -> bool:
        raise NotImplementedError()
