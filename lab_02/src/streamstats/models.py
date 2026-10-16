import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypedDict

from streamstats.errors import InvalidEventError, InvalidTimestampError

REQUIRED_FIELDS = ("timestamp", "level", "source", "message")
VALID_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass
class ReadStats:
    """Хранит статистику чтения входных файлов."""

    skipped_lines: int = 0


class ErrorSource(TypedDict):
    """Описывает словарь источника ошибок в отчёте."""

    source: str
    count: int


class Report(TypedDict):
    """Описывает поля и типы значений статистического отчёта."""

    total_events: int
    by_level: dict[str, int]
    by_source: dict[str, int]
    top_error_sources: list[ErrorSource]
    first_timestamp: str | None
    last_timestamp: str | None
    skipped_lines: int


def parse_timestamp(value: object) -> datetime:
    """Проверяет временную метку и приводит её к UTC."""
    if not isinstance(value, str):
        raise InvalidTimestampError("Поле timestamp должно быть строкой")

    pattern = (
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
        r"([T ][0-9]{2}:[0-9]{2}"
        r"(:[0-9]{2}([.,][0-9]+)?)?"
        r"(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])?)?"
    )

    if re.fullmatch(pattern, value) is None:
        raise InvalidTimestampError(f"Некорректная временная метка: {value}")

    try:
        timestamp = datetime.fromisoformat(value)

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        return timestamp.astimezone(UTC)

    except (ValueError, OverflowError) as error:
        raise InvalidTimestampError(f"Некорректная временная метка: {value}") from error


def validate_event(data: Mapping[str, object]) -> None:
    """Проверяет обязательные поля и значения события."""
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise InvalidEventError(f"Отсутствует обязательное поле: {field}")

    source = data["source"]
    if not isinstance(source, str):
        raise InvalidEventError("Поле source должно быть строкой")
    if not source.strip():
        raise InvalidEventError("Поле source не должно быть пустым")

    message = data["message"]
    if not isinstance(message, str):
        raise InvalidEventError("Поле message должно быть строкой")

    level = data["level"]
    if not isinstance(level, str):
        raise InvalidEventError("Поле level должно быть строкой")
    if level not in VALID_LEVELS:
        raise InvalidEventError(f"Недопустимый уровень события: {level}")

    parse_timestamp(data["timestamp"])
