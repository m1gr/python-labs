import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_analyze_csv(tmp_path: Path) -> None:
    """Проверяет запуск CLI и сохранение JSON-отчёта."""
    input_path = tmp_path / "events.csv"
    output_path = tmp_path / "report.json"

    input_path.write_text(
        "timestamp,level,source,message\n"
        "2026-10-13T18:00:00Z,INFO,server,Запуск\n"
        "2026-10-13T18:05:00Z,ERROR,database,Ошибка\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_path),
            "--format",
            "csv",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""

    report = json.loads(output_path.read_text(encoding="utf-8"))

    assert report["total_events"] == 2
    assert report["by_source"] == {"server": 1, "database": 1}
    assert report["skipped_lines"] == 0


def test_cli_invalid_event(tmp_path: Path) -> None:
    """Проверяет сообщение и код завершения при неверном событии."""
    input_path = tmp_path / "invalid.jsonl"
    input_path.write_text(
        '{"timestamp": "2026-10-13T18:00:00Z", '
        '"level": "UNKNOWN", "source": "server", "message": ""}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_path),
            "--format",
            "jsonl",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert str(input_path) in result.stderr
    assert "строка 1:" in result.stderr
    assert "Недопустимый уровень события" in result.stderr


def test_cli_skip_invalid(tmp_path: Path) -> None:
    """Проверяет пропуск неверной строки и вывод отчёта в терминал."""
    input_path = tmp_path / "mixed.jsonl"
    event = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "INFO",
        "source": "server",
        "message": "Запуск",
    }
    input_path.write_text(
        "неверный JSON\n" + json.dumps(event) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_path),
            "--format",
            "jsonl",
            "--skip-invalid",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 0

    report = json.loads(result.stdout)
    assert report["total_events"] == 1
    assert report["by_source"] == {"server": 1}
    assert report["skipped_lines"] == 1

    assert "WARNING" in result.stderr
    assert str(input_path) in result.stderr
    assert "строка 1:" in result.stderr


def test_cli_csv_report(tmp_path: Path) -> None:
    """Проверяет создание CSV-отчёта из файла JSONL через CLI."""
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "report.csv"

    event = {
        "timestamp": "2026-10-13T18:00:00Z",
        "level": "ERROR",
        "source": "сервер",
        "message": "Ошибка",
    }
    input_path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_path),
            "--format",
            "jsonl",
            "--report-format",
            "csv",
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""

    with output_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))

    assert rows[0] == ["section", "name", "value"]
    assert ["summary", "total_events", "1"] in rows
    assert ["by_source", "сервер", "1"] in rows
    assert ["top_error_sources", "сервер", "1"] in rows


def test_cli_filters(tmp_path: Path) -> None:
    """Проверяет применение фильтров через командную строку."""
    input_path = tmp_path / "events.csv"
    input_path.write_text(
        "timestamp,level,source,message\n"
        "2026-10-13T18:00:00Z,ERROR,database,Слишком рано\n"
        "2026-10-13T18:05:00Z,ERROR,database,Нужное событие\n"
        "2026-10-13T18:05:00Z,INFO,database,Другой уровень\n"
        "2026-10-13T18:05:00Z,ERROR,server,Другой источник\n"
        "2026-10-13T18:10:00Z,ERROR,database,Слишком поздно\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_path),
            "--format",
            "csv",
            "--level",
            "ERROR",
            "--source",
            "database",
            "--since",
            "2026-10-13T18:03:00Z",
            "--until",
            "2026-10-13T18:07:00Z",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )

    assert result.returncode == 0
    assert result.stderr == ""

    report = json.loads(result.stdout)

    assert report["total_events"] == 1
    assert report["by_level"]["ERROR"] == 1
    assert report["by_source"] == {"database": 1}
    assert report["first_timestamp"] == "2026-10-13T18:05:00+00:00"
    assert report["last_timestamp"] == "2026-10-13T18:05:00+00:00"
    assert report["skipped_lines"] == 0
