import enum
from pathlib import Path


@enum.unique
class ScriptExecuterEnum(enum.Enum):
    BEFORE_SESSION_START = enum.auto()
    AFTER_SESSION_FINISH = enum.auto()


class ScriptExecuter:
    when = ScriptExecuterEnum

    def run_on(
        self,
        path_to_script: Path,
        /,
        *,
        when: ScriptExecuterEnum = ScriptExecuterEnum.BEFORE_SESSION_START,
    ) -> None:
        pass
