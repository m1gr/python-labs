import csv
import json
from pathlib import Path

from streamstats.models import Report
from streamstats.report import write_csv_report, write_json_report


def test_write_json_report(tmp_path: Path) -> None:
    """Проверяет сохранение отчёта и русского текста."""
    report: Report = {
        "total_events": 2,
        "by_level": {"INFO": 2},
        "by_source": {"сервер": 2},
        "top_error_sources": [],
        "first_timestamp": None,
        "last_timestamp": None,
        "skipped_lines": 0,
    }
    path = tmp_path / "report.json"

    write_json_report(report, str(path))

    text = path.read_text(encoding="utf-8")
    result = json.loads(text)

    assert result == report
    assert "сервер" in text


def test_write_csv_report(tmp_path: Path) -> None:
    """Проверяет сохранение всех разделов статистики в CSV."""
    report: Report = {
        "total_events": 2,
        "by_level": {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 0,
            "ERROR": 1,
            "CRITICAL": 0,
        },
        "by_source": {"сервер, основной": 2},
        "top_error_sources": [
            {"source": "сервер, основной", "count": 1},
        ],
        "first_timestamp": "2026-10-13T18:00:00+00:00",
        "last_timestamp": "2026-10-13T18:05:00+00:00",
        "skipped_lines": 1,
    }
    path = tmp_path / "report.csv"

    write_csv_report(report, str(path))

    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))

    assert rows == [
        ["section", "name", "value"],
        ["summary", "total_events", "2"],
        ["summary", "skipped_lines", "1"],
        ["by_level", "DEBUG", "0"],
        ["by_level", "INFO", "1"],
        ["by_level", "WARNING", "0"],
        ["by_level", "ERROR", "1"],
        ["by_level", "CRITICAL", "0"],
        ["by_source", "сервер, основной", "2"],
        ["top_error_sources", "сервер, основной", "1"],
        ["time", "first_timestamp", "2026-10-13T18:00:00+00:00"],
        ["time", "last_timestamp", "2026-10-13T18:05:00+00:00"],
    ]
