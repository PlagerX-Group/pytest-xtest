from xtest.pom.locators import AdvancedLocator


class GoogleComPageSearchResultsPageLocators:
    RESULTS = AdvancedLocator(
        loc="div[data-async-context='query:{0}'] > div:nth-child(3) > div",
        desc="Список результатов на странице выдачи",
    )


class GoogleComPageLocators:
    INPUT_SEARCH = AdvancedLocator(loc="textarea[name='q']", desc="Поле ввода запроса")
