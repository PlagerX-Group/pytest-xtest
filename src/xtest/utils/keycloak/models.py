from __future__ import annotations

import enum
import uuid
import typing as t

from pydantic import BaseModel


class KeycloakUserCreateRequeiredActions(enum.Enum):
    UPDATE_PASSWORD: str = 'UPDATE_PASSWORD'


class KeycloakUserModel(BaseModel):
    username: str
    password: str
    email: str
    first_name: str
    last_name: str
    is_verify_email: bool = True
    is_enabled: bool = True
    required_actions: list[KeycloakUserCreateRequeiredActions] = None
    attributes: dict[str, t.Any] = None

    @staticmethod
    def create_random_model(
        *,
        attributes: dict[str, str] = None,
        required_actions: list[KeycloakUserCreateRequeiredActions] = None,
    ) -> KeycloakUserModel:
        return KeycloakUserModel(
            username=f'autotests-{str(uuid.uuid4())[:8]}',
            password=str(uuid.uuid4()),
            email=f"autotests-{str(uuid.uuid4())[:8]}@domain.ru",
            first_name="Пользователь",
            last_name="Автотестов",
            required_actions=required_actions,
            attributes=attributes,
        )
