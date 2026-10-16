from datetime import UTC, datetime

import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import parse_timestamp, validate_event


def test_validate_event_valid() -> None:
    """Проверяет, что корректное событие проходит валидацию."""
    event = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "INFO",
        "source": "server",
        "message": "",
    }

    validate_event(event)


def test_validate_event_missing_field() -> None:
    """Проверяет отказ при отсутствии обязательного поля."""
    event = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "INFO",
        "source": "server",
        "message": "",
    }
    del event["source"]

    with pytest.raises(InvalidEventError):
        validate_event(event)


def test_validate_event_invalid_source() -> None:
    """Проверяет отказ при пустом источнике или неверном типе."""
    cases = ["", "   ", 123, None]

    for source in cases:
        event = {
            "timestamp": "2026-10-13T18:00:00Z",
            "level": "INFO",
            "source": source,
            "message": "",
        }

        with pytest.raises(InvalidEventError):
            validate_event(event)


def test_validate_event_invalid_message() -> None:
    """Проверяет отказ, если сообщение не является строкой."""
    cases: list[object] = [123, None, [], {}]

    for message in cases:
        event = {
            "timestamp": "2026-10-13T18:00:00Z",
            "level": "INFO",
            "source": "server",
            "message": message,
        }

        with pytest.raises(InvalidEventError):
            validate_event(event)


def test_validate_event_invalid_level() -> None:
    """Проверяет отказ при недопустимом уровне события."""
    cases = ["", "info", "UNKNOWN", 123, None]

    for level in cases:
        event = {
            "timestamp": "2026-10-13T18:00:00Z",
            "level": level,
            "source": "server",
            "message": "",
        }

        with pytest.raises(InvalidEventError):
            validate_event(event)


def test_validate_event_invalid_timestamp() -> None:
    """Проверяет отказ при некорректной временной метке."""
    cases = [
        "",
        "не дата",
        "2026-15-13T18:00:00Z",
        "2026-02-30T18:00:00Z",
        123,
        None,
        "2026-10-13X18:00:00",
        "2026-10-13T18:00:00+00:60",
        "0001-01-01T00:00:00+01:00",
        "9999-12-31T23:59:59-01:00",
    ]

    for timestamp in cases:
        event = {
            "timestamp": timestamp,
            "level": "INFO",
            "source": "server",
            "message": "",
        }

        with pytest.raises(InvalidTimestampError):
            validate_event(event)


def test_parse_timestamp_utc() -> None:
    """Проверяет приведение временных меток к UTC."""
    cases = [
        "2026-10-13T18:00:00Z",
        "2026-10-13T21:00:00+03:00",
        "2026-10-13T13:00:00-05:00",
        "2026-10-13T18:00:00",
    ]

    expected = datetime(2026, 10, 13, 18, 0, 0, tzinfo=UTC)

    for value in cases:
        result = parse_timestamp(value)

        assert result == expected
        assert result.tzinfo is UTC


def test_parse_timestamp_supported_formats() -> None:
    """Проверяет поддерживаемые варианты записи даты и времени."""
    cases = [
        ("2026-10-13", datetime(2026, 10, 13, tzinfo=UTC)),
        (
            "2026-10-13T18:00",
            datetime(2026, 10, 13, 18, 0, tzinfo=UTC),
        ),
        (
            "2026-10-13 18:00:00",
            datetime(2026, 10, 13, 18, 0, tzinfo=UTC),
        ),
        (
            "2026-10-13T21:00:00.123+03:00",
            datetime(2026, 10, 13, 18, 0, 0, 123000, tzinfo=UTC),
        ),
    ]

    for value, expected in cases:
        result = parse_timestamp(value)

        assert result == expected
        assert result.tzinfo is UTC
