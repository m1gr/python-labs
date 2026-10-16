import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from streamstats import parsers
from streamstats.errors import InvalidEventError
from streamstats.models import ReadStats, validate_event
from streamstats.parsers import read_csv, read_jsonl


def test_read_jsonl_valid(tmp_path: Path) -> None:
    """Проверяет чтение нескольких корректных событий."""
    events = [
        {
            "timestamp": "2026-10-13T18:00:00Z",
            "level": "INFO",
            "source": "server",
            "message": "Сервер запущен",
        },
        {
            "timestamp": "2026-10-13T18:05:00Z",
            "level": "ERROR",
            "source": "database",
            "message": "Нет соединения",
        },
    ]

    path = tmp_path / "events.jsonl"

    with path.open("w", encoding="utf-8") as file:
        for event in events:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")

    result = list(read_jsonl(str(path)))

    assert result == events


def test_read_jsonl_invalid_json(tmp_path: Path) -> None:
    """Проверяет ошибку с указанием файла и строки при повреждённом JSON."""
    path = tmp_path / "broken.jsonl"
    path.write_text('{"level": "INFO"\n', encoding="utf-8")

    with pytest.raises(InvalidEventError) as error_info:
        list(read_jsonl(str(path)))

    message = str(error_info.value)
    assert str(path) in message
    assert "строка 1:" in message
    assert "некорректный JSON" in message


def test_read_jsonl_empty(tmp_path: Path) -> None:
    """Проверяет чтение пустого файла."""
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")

    result = list(read_jsonl(str(path)))

    assert result == []


def test_read_jsonl_skip_invalid(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Проверяет пропуск неверных строк и запись предупреждений."""
    event = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "INFO",
        "source": "server",
        "message": "Сервер запущен",
    }

    path = tmp_path / "mixed.jsonl"
    lines = [
        json.dumps(event, ensure_ascii=False),
        '{"level":',
        "[]",
        '{"level": "INFO"}',
        json.dumps(event, ensure_ascii=False),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stats = ReadStats()
    with caplog.at_level(logging.WARNING, logger="streamstats.parsers"):
        result = list(read_jsonl(str(path), skip_invalid=True, stats=stats))

    assert result == [event, event]
    assert stats.skipped_lines == 3

    warnings = [
        record
        for record in caplog.records
        if record.name == "streamstats.parsers" and record.levelno == logging.WARNING
    ]
    assert len(warnings) == 3

    for line_number, record in zip((2, 3, 4), warnings):
        assert str(path) in record.getMessage()
        assert f"строка {line_number}:" in record.getMessage()


def test_read_csv_valid(tmp_path: Path) -> None:
    """Проверяет чтение CSV с заголовком и русским текстом."""
    path = tmp_path / "events.csv"
    text = (
        "timestamp,level,source,message\n"
        "2026-10-13T18:00:00Z,INFO,server,Сервер запущен\n"
        '2026-10-13T18:05:00Z,ERROR,database,"Ошибка, нет соединения"\n'
    )
    path.write_text(text, encoding="utf-8")

    result = list(read_csv(str(path)))

    expected = [
        {
            "timestamp": "2026-10-13T18:00:00Z",
            "level": "INFO",
            "source": "server",
            "message": "Сервер запущен",
        },
        {
            "timestamp": "2026-10-13T18:05:00Z",
            "level": "ERROR",
            "source": "database",
            "message": "Ошибка, нет соединения",
        },
    ]

    assert result == expected


def test_read_csv_invalid_event(tmp_path: Path) -> None:
    """Проверяет отказ при недопустимом уровне события в CSV."""
    path = tmp_path / "invalid.csv"
    text = (
        "timestamp,level,source,message\n"
        "2026-10-13T18:00:00Z,UNKNOWN,server,Сервер запущен\n"
    )
    path.write_text(text, encoding="utf-8")

    with pytest.raises(InvalidEventError) as error_info:
        list(read_csv(str(path)))

    message = str(error_info.value)
    assert str(path) in message
    assert "строка 2:" in message
    assert "Недопустимый уровень события" in message


def test_read_csv_skip_invalid(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Проверяет пропуск неверных записей CSV и счётчик пропусков."""
    path = tmp_path / "mixed.csv"
    text = (
        "timestamp,level,source,message\n"
        "2026-10-13T18:00:00Z,INFO,server,Запуск\n"
        "2026-10-13T18:01:00Z,UNKNOWN,server,Ошибка уровня\n"
        "2026-10-13T18:02:00Z,ERROR,,Нет источника\n"
        "2026-10-13T18:03:00Z,INFO,server,Продолжение\n"
    )
    path.write_text(text, encoding="utf-8")

    stats = ReadStats()

    with caplog.at_level(logging.WARNING, logger="streamstats.parsers"):
        result = list(read_csv(str(path), skip_invalid=True, stats=stats))

    assert len(result) == 2
    assert result[0]["message"] == "Запуск"
    assert result[1]["message"] == "Продолжение"
    assert stats.skipped_lines == 2

    assert "строка 3:" in caplog.text
    assert "строка 4:" in caplog.text


def test_read_csv_invalid_header(tmp_path: Path) -> None:
    """Проверяет отказ при неверном заголовке CSV."""
    cases = [
        "timestamp,level,source\n",
        "timestamp,level,source,message,message\n",
    ]

    path = tmp_path / "invalid_header.csv"

    for header in cases:
        path.write_text(header, encoding="utf-8")

        for skip_invalid in (False, True):
            with pytest.raises(InvalidEventError) as error_info:
                list(read_csv(str(path), skip_invalid=skip_invalid))

            message = str(error_info.value)
            assert str(path) in message
            assert "строка 1:" in message


def test_read_csv_empty(tmp_path: Path) -> None:
    """Проверяет пустой CSV и CSV только с заголовком."""
    cases = [
        "",
        "timestamp,level,source,message\n",
    ]

    path = tmp_path / "empty.csv"

    for text in cases:
        path.write_text(text, encoding="utf-8")
        stats = ReadStats()

        result = list(read_csv(str(path), stats=stats))

        assert result == []
        assert stats.skipped_lines == 0


def test_register_parser(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Проверяет подключение пользовательской функции чтения."""

    def read_text(
        path: str,
        skip_invalid: bool = False,
        stats: ReadStats | None = None,
    ) -> Iterator[dict[str, object]]:
        with open(path, encoding="utf-8") as file:
            for line in file:
                event: dict[str, object] = {
                    "timestamp": "2026-10-13T18:00:00Z",
                    "level": "INFO",
                    "source": "text",
                    "message": line.rstrip("\n"),
                }
                validate_event(event)
                yield event

    monkeypatch.setattr(parsers, "PARSERS", parsers.PARSERS.copy())
    parsers.register_parser("text", read_text)

    path = tmp_path / "events.txt"
    path.write_text("Запуск\nОстановка\n", encoding="utf-8")

    result = list(parsers.read_files([str(path)], input_format="text"))

    assert len(result) == 2
    assert result[0]["message"] == "Запуск"
    assert result[1]["message"] == "Остановка"
    assert result[0]["source"] == "text"


def test_read_csv_delimiters(tmp_path: Path) -> None:
    """Проверяет запятую и точку с запятой как разделители CSV."""
    expected = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "INFO",
        "source": "server",
        "message": 'Запуск, проверка; статус "готов"',
    }
    path = tmp_path / "events.csv"

    for delimiter in (",", ";"):
        header = delimiter.join(["timestamp", "level", "source", "message"])
        row = delimiter.join(
            [
                "2026-10-13T18:00:00Z",
                "INFO",
                "server",
                '"Запуск, проверка; статус ""готов"""',
            ]
        )
        path.write_text(header + "\n" + row + "\n", encoding="utf-8")

        result = list(read_csv(str(path)))

        assert result == [expected]


def test_read_jsonl_large_number(tmp_path: Path) -> None:
    """Проверяет обработку слишком большого JSON-числа."""
    path = tmp_path / "large_number.jsonl"

    event = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "INFO",
        "source": "server",
        "message": "Корректное событие",
    }

    invalid_line = '{"message": ' + "1" * 5000 + "}"
    path.write_text(
        invalid_line + "\n" + json.dumps(event) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidEventError):
        list(read_jsonl(str(path)))

    stats = ReadStats()
    result = list(read_jsonl(str(path), skip_invalid=True, stats=stats))

    assert result == [event]
    assert stats.skipped_lines == 1


def test_read_csv_broken_header(tmp_path: Path) -> None:
    """Проверяет номер строки при повреждённом заголовке CSV."""
    path = tmp_path / "broken_header.csv"
    path.write_text(
        '"timestamp,level,source,message\n',
        encoding="utf-8",
    )

    for skip_invalid in (False, True):
        with pytest.raises(InvalidEventError) as error_info:
            list(read_csv(str(path), skip_invalid=skip_invalid))

        message = str(error_info.value)

        assert str(path) in message
        assert "строка 1:" in message
        assert "некорректный заголовок CSV" in message
