from abc import ABC

from library.pom.locators import (
    GoogleComPageLocators,
    GoogleComPageSearchResultsPageLocators,
)
from selenium.webdriver import Keys

from xtest.pom.exceptions import PageNotLoadedError
from xtest.pom.pages import BasePageActions


class BaseGoogleComPage(BasePageActions, ABC):
    def build_url(self) -> str:
        return "https://google.com/"


class GoogleComPageSearchResultsPage(BaseGoogleComPage):
    locators = GoogleComPageSearchResultsPageLocators()
    endpoint = "/search"
    endpoint_pattern = "/search$"

    def __init__(self, query: str, *args, **kwargs) -> None:
        self.query = query
        self.get_parameters = {"q": query}
        self.page_name = f"Результат поиска по запросу: {query}"
        super().__init__(*args, **kwargs)

    def is_loading_page(self) -> bool:
        if not self.is_visible_element():
            raise PageNotLoadedError(self.page_name, reason='Не произошел переход на страницу с результатами.')
        return True

    @property
    def count_results(self) -> int:
        return self.get_count_elements_on_page(self.locators.RESULTS(self.query))


class GoogleComPage(BaseGoogleComPage):
    page_name = "Главная Google"
    endpoint = "/"
    endpoint_pattern = "/$"
    locators = GoogleComPageLocators()

    def is_loading_page(self) -> bool:
        if not self.is_visible_element(self.locators.INPUT_SEARCH):
            raise PageNotLoadedError(self.page_name, reason='Страница с полем ввода не загружена.')
        return True

    def search(self, query: str, /) -> GoogleComPageSearchResultsPage:
        self.send_keys(self.locators.INPUT_SEARCH, query)
        self.action_chains.send_keys(Keys.ENTER).perform()

        page = GoogleComPageSearchResultsPage(self.driver, query)
        page.is_loading_page()
        return page
