import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from library.pom.pages import GoogleComPage


@pytest.fixture(scope="session")
def driver() -> WebDriver:
    # Фикстура для получение драйвера Selenium.
    pass


@pytest.fixture(scope="class")
def page_google_com(driver):
    page = GoogleComPage(driver)
    page.open_page()
    return page


def test_search_google(page_google_com):
    # Проверка количества результатов выдачи для запроса 'Python'.

    assert page_google_com.search('Python').count_results == 8
