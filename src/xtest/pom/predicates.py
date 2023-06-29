import re

from selenium.webdriver.remote.webdriver import WebDriver


def url_matches_without_get_parameters(pattern: str):
    """Работает аналогично 'expected_conditions.url_matches', только в данном случае игнорируются GET-параметры."""

    def _predicate(driver: WebDriver):
        return bool(re.search(pattern, driver.current_url.split("?")[0].split("#")[0]))

    return _predicate
