import csv
import json
import logging
from collections.abc import Callable, Iterator

from streamstats.errors import (
    InvalidEventError,
    StreamStatsError,
    UnsupportedFormatError,
)
from streamstats.models import REQUIRED_FIELDS, ReadStats, validate_event

logger = logging.getLogger(__name__)


def read_jsonl(
    path: str, skip_invalid: bool = False, stats: ReadStats | None = None
) -> Iterator[dict[str, object]]:
    """Читает JSONL и учитывает пропущенные ошибочные строки."""
    if stats is None:
        stats = ReadStats()

    with open(path, encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                data = json.loads(line)
            except ValueError as error:
                if skip_invalid:
                    stats.skipped_lines += 1
                    logger.warning(
                        "%s, строка %s: некорректный JSON", path, line_number
                    )
                    continue
                raise InvalidEventError(
                    f"{path}, строка {line_number}: некорректный JSON"
                ) from error

            try:
                if not isinstance(data, dict):
                    raise InvalidEventError("Событие должно быть JSON-объектом")

                validate_event(data)
            except StreamStatsError as error:
                if skip_invalid:
                    stats.skipped_lines += 1
                    logger.warning("%s, строка %s: %s", path, line_number, error)
                    continue

                raise type(error)(f"{path}, строка {line_number}: {error}") from error

            yield data


def read_csv(
    path: str,
    skip_invalid: bool = False,
    stats: ReadStats | None = None,
) -> Iterator[dict[str, object]]:
    """Читает CSV с разделителем-запятой или точкой с запятой."""
    if stats is None:
        stats = ReadStats()

    with open(path, encoding="utf-8", newline="") as file:
        header = file.readline()
        file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(header, delimiters=",;")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        reader = csv.DictReader(
            file,
            delimiter=delimiter,
            strict=True,
        )

        try:
            fields = reader.fieldnames
        except csv.Error as error:
            line_number = reader.reader.line_num
            raise InvalidEventError(
                f"{path}, строка {line_number}: некорректный заголовок CSV"
            ) from error

        if fields is None:
            return

        for field in REQUIRED_FIELDS:
            if field not in fields:
                raise InvalidEventError(
                    f"{path}, строка 1: отсутствует столбец {field}"
                )

        if len(fields) != len(set(fields)):
            raise InvalidEventError(f"{path}, строка 1: названия столбцов повторяются")

        while True:
            try:
                data = next(reader)
            except StopIteration:
                break
            except csv.Error as error:
                line_number = reader.reader.line_num

                if skip_invalid:
                    stats.skipped_lines += 1
                    logger.warning(
                        "%s, строка %s: некорректный CSV",
                        path,
                        line_number,
                    )
                    continue

                raise InvalidEventError(
                    f"{path}, строка {line_number}: некорректный CSV"
                ) from error

            line_number = reader.line_num

            try:
                if None in data or None in data.values():
                    raise InvalidEventError(
                        "Количество значений не совпадает с заголовком"
                    )

                validate_event(data)
            except StreamStatsError as error:
                if skip_invalid:
                    stats.skipped_lines += 1
                    logger.warning(
                        "%s, строка %s: %s",
                        path,
                        line_number,
                        error,
                    )
                    continue

                raise type(error)(f"{path}, строка {line_number}: {error}") from error

            yield data


PARSERS = {
    "jsonl": read_jsonl,
    "csv": read_csv,
}


def register_parser(
    name: str,
    parser: Callable[..., Iterator[dict[str, object]]],
) -> None:
    """Добавляет или заменяет функцию чтения указанного формата."""
    PARSERS[name] = parser


def read_files(
    paths: list[str],
    input_format: str,
    skip_invalid: bool = False,
    stats: ReadStats | None = None,
) -> Iterator[dict[str, object]]:
    """Выдаёт события нескольких файлов через выбранный парсер."""
    if stats is None:
        stats = ReadStats()

    if input_format not in PARSERS:
        raise UnsupportedFormatError(f"Неподдерживаемый формат: {input_format}")

    reader = PARSERS[input_format]

    for path in paths:
        yield from reader(
            path,
            skip_invalid=skip_invalid,
            stats=stats,
        )
