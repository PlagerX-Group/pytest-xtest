import typing as t

from xtest.pom.locators import AdvancedLocator


def generate_reason(reason: str, /) -> str:
    if isinstance(reason, str):
        if reason[0].isupper():
            reason = reason[0].lower() + reason[1:]
        return f" Причина: {reason.strip().rstrip('.')}."
    return ""


class BaseFrameworkException(Exception):
    pass


class ElementNotPresentOnPageError(BaseFrameworkException):
    def __init__(
        self, locator: AdvancedLocator, /, *, timeout: float = None, reason: str = None
    ) -> None:
        super().__init__(
            f'На странице отсутствует элемент с локатором "{locator.as_locator}"'
            f'{f". Таймаут: {timeout}." if timeout is not None else ""}.'
            f"{generate_reason(reason)}"
        )


class ElementNotDisappearedOnPageError(BaseFrameworkException):
    def __init__(
        self, locator: AdvancedLocator, /, *, timeout: float = None, reason: str = None
    ) -> None:
        super().__init__(
            f'На странице отсутствует элемент с локатором "{locator.as_locator}"'
            f'{f". Таймаут: {timeout}." if timeout is not None else ""}.'
            f"{generate_reason(reason)}"
        )


class TextNotPresentInElementError(BaseFrameworkException):
    def __init__(
        self, locator: AdvancedLocator, text: str, /, timeout: float = None
    ) -> None:
        super().__init__(
            f'Текст "{text}" отсутствует в элементе (timeout={timeout}). Локатор: {locator.as_locator}.'
        )


class AttributeNotPresentInWebElementError(BaseFrameworkException):
    def __init__(
        self, locator: AdvancedLocator, attr_name: str, /, timeout: float = None
    ) -> None:
        super().__init__(
            f'Атрибут "{attr_name}" не найден у элемента (timeout={timeout}). Локатор: {locator.as_locator}.'
        )


class WaitSkip(BaseFrameworkException):
    def __init__(self, /, *, ex: t.Type[Exception] = None) -> None:
        self.ex = ex or WaitSkip
        super().__init__()


class PageNotLoadedError(BaseFrameworkException):
    def __init__(self, page_name: str, /, reason: str = None) -> None:
        super().__init__(
            f'Страница "{page_name}" не загружена.{generate_reason(reason)}'
        )


class ConflictError(BaseFrameworkException):
    pass
