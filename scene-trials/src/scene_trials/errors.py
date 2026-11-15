"""Error types and the exhaustiveness helper."""

from __future__ import annotations

from typing import NoReturn


class SceneTrialsError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class ConfigError(SceneTrialsError):
    pass


class SafetyError(SceneTrialsError):
    pass


class BackendError(SceneTrialsError):
    pass


def unreachable(value: object) -> NoReturn:
    raise AssertionError(f"unhandled variant: {value!r}")
