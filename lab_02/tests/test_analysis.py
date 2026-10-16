import json
from pathlib import Path

from streamstats.analysis import analyze_events, filter_events
from streamstats.models import ReadStats, parse_timestamp
from streamstats.parsers import read_files


def test_analyze_events_statistics() -> None:
    """Проверяет счётчики, источники ошибок и диапазон времени."""
    events = [
        {
            "timestamp": "2026-10-13T18:10:00Z",
            "level": "INFO",
            "source": "server",
            "message": "Запуск",
        },
        {
            "timestamp": "2026-10-13T21:05:00+03:00",
            "level": "ERROR",
            "source": "database",
            "message": "Ошибка соединения",
        },
        {
            "timestamp": "2026-10-13T18:20:00Z",
            "level": "CRITICAL",
            "source": "database",
            "message": "База недоступна",
        },
        {
            "timestamp": "2026-10-13T18:15:00Z",
            "level": "WARNING",
            "source": "server",
            "message": "Высокая нагрузка",
        },
    ]

    result = analyze_events(iter(events))

    assert result == {
        "total_events": 4,
        "by_level": {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 1,
            "ERROR": 1,
            "CRITICAL": 1,
        },
        "by_source": {
            "server": 2,
            "database": 2,
        },
        "top_error_sources": [
            {"source": "database", "count": 2},
        ],
        "first_timestamp": "2026-10-13T18:05:00+00:00",
        "last_timestamp": "2026-10-13T18:20:00+00:00",
        "skipped_lines": 0,
    }


def test_analyze_events_empty() -> None:
    """Проверяет статистику при отсутствии событий."""
    result = analyze_events(iter([]))

    assert result == {
        "total_events": 0,
        "by_level": {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        },
        "by_source": {},
        "top_error_sources": [],
        "first_timestamp": None,
        "last_timestamp": None,
        "skipped_lines": 0,
    }


def test_analyze_multiple_files(tmp_path: Path) -> None:
    """Проверяет объединение событий и пропусков нескольких файлов."""
    first_event = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "INFO",
        "source": "server",
        "message": "Запуск",
    }
    second_event = {
        "timestamp": "2026-10-13T18:05:00Z",
        "level": "ERROR",
        "source": "database",
        "message": "Нет соединения",
    }

    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"

    first_path.write_text(
        json.dumps(first_event) + "\nневерный JSON\n",
        encoding="utf-8",
    )
    second_path.write_text(
        "[]\n" + json.dumps(second_event) + "\n",
        encoding="utf-8",
    )

    stats = ReadStats()
    events = read_files(
        [str(first_path), str(second_path)],
        input_format="jsonl",
        skip_invalid=True,
        stats=stats,
    )

    result = analyze_events(events, stats=stats)

    assert result["total_events"] == 2
    assert result["by_level"]["INFO"] == 1
    assert result["by_level"]["ERROR"] == 1
    assert result["by_source"] == {"server": 1, "database": 1}
    assert result["top_error_sources"] == [
        {"source": "database", "count": 1},
    ]
    assert result["skipped_lines"] == 2


def test_filter_events() -> None:
    """Проверяет фильтры по уровню, источнику и времени."""
    events = [
        {
            "timestamp": "2026-10-13T18:00:00Z",
            "level": "INFO",
            "source": "server",
            "message": "Запуск",
        },
        {
            "timestamp": "2026-10-13T18:05:00Z",
            "level": "ERROR",
            "source": "database",
            "message": "Ошибка базы",
        },
        {
            "timestamp": "2026-10-13T18:10:00Z",
            "level": "ERROR",
            "source": "server",
            "message": "Ошибка сервера",
        },
    ]

    start = parse_timestamp("2026-10-13T21:05:00+03:00")
    end = parse_timestamp("2026-10-13T18:10:00Z")

    assert list(filter_events(iter(events))) == events
    assert list(filter_events(iter(events), level="ERROR")) == [events[1], events[2]]
    assert list(filter_events(iter(events), source="server")) == [events[0], events[2]]
    assert list(filter_events(iter(events), start_time=start)) == [events[1], events[2]]
    assert list(filter_events(iter(events), end_time=start)) == [events[0], events[1]]
    assert list(filter_events(iter(events), source="unknown")) == []

    result = list(
        filter_events(
            iter(events),
            level="ERROR",
            source="server",
            start_time=start,
            end_time=end,
        )
    )
    assert result == [events[2]]
