import subprocess
import sys

import pytest


def test_cli_success() -> None:
    """Проверяет результат, код завершения и потоки вывода успешных команд CLI."""
    cases = [
        (["calc", "2 + 3 * 4"], 14.0),
        (["calc", "(2 + 3) * 4"], 20.0),
        (["convert", "2", "--from", "m", "--to", "cm"], 200.0),
        (["convert", "0", "--from", "c", "--to", "f"], 32.0),
        (["calc", "-3+5"], 2.0),
        (["calc", "-(2+3)"], -5.0),
    ]

    for arguments, expected in cases:
        result = subprocess.run(
            [sys.executable, "-m", "toolkit", *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert float(result.stdout.strip()) == pytest.approx(expected)
        assert result.stderr == ""


def test_cli_errors() -> None:
    """Проверяет код завершения и потоки вывода при ошибочном вводе."""
    cases = [
        ["calc", "5 / 0"],
        ["calc", "2 +"],
        ["convert", "2", "--from", "abc", "--to", "m"],
        ["convert", "2", "--from", "m", "--to", "kg"],
        ["convert", "abc", "--from", "m", "--to", "cm"],
    ]
    for arguments in cases:
        result = subprocess.run(
            [sys.executable, "-m", "toolkit", *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2
        assert result.stdout == ""
        assert result.stderr.strip()


def test_cli_help() -> None:
    "Проверяет вывод справки и наличие доступных команд."
    result = subprocess.run(
        [sys.executable, "-m", "toolkit", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "calc" in result.stdout
    assert "convert" in result.stdout
    assert result.stderr == ""
