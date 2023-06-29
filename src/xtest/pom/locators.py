from __future__ import annotations

import typing as t

from pydantic import BaseModel, Field
from selenium.webdriver.common.by import By


class AdvancedLocator(BaseModel):
    loc: str = Field()
    by: str = Field(default=By.CSS_SELECTOR)
    desc: t.Optional[str] = None

    @property
    def as_locator(self) -> tuple[str, str]:
        return self.by, self.loc

    def __call__(self, /, *args, **kwargs) -> AdvancedLocator:
        self.__config__.allow_mutation = True
        self.loc = self.loc.format(*args, **kwargs)
        self.__config__.allow_mutation = False
        return self

    class Config:
        allow_mutation = False
