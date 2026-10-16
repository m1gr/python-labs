import argparse
import json
import logging
import sys
from typing import NoReturn

from streamstats.analysis import analyze_events, filter_events
from streamstats.errors import CLIConfigurationError, StreamStatsError
from streamstats.models import VALID_LEVELS, ReadStats, parse_timestamp
from streamstats.parsers import read_files
from streamstats.report import write_csv_report, write_json_report


class CommandLineParser(argparse.ArgumentParser):
    """Парсер, использующий ошибку командной строки нашего проекта."""

    def error(self, message: str) -> NoReturn:
        raise CLIConfigurationError(message)


def parse_arguments() -> argparse.Namespace:
    """Разбирает аргументы командной строки."""
    parser = CommandLineParser(
        prog="streamstats",
        description="Потоковый анализатор событий CSV и JSONL",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    analyze_parser = commands.add_parser(
        "analyze",
        help="Проанализировать файлы событий",
    )
    analyze_parser.add_argument(
        "inputs",
        nargs="+",
        help="Пути к входным файлам",
    )
    analyze_parser.add_argument(
        "--format",
        required=True,
        help="Формат входных файлов: csv или jsonl",
    )
    analyze_parser.add_argument(
        "--output",
        help="Путь к отчёту; без него JSON выводится в терминал",
    )
    analyze_parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Пропускать неверные записи с предупреждением",
    )
    analyze_parser.add_argument(
        "--report-format",
        choices=("json", "csv"),
        default="json",
        help="Формат отчёта: json или csv; по умолчанию json",
    )

    analyze_parser.add_argument(
        "--level",
        choices=VALID_LEVELS,
        help="Оставить события указанного уровня",
    )
    analyze_parser.add_argument(
        "--source",
        help="Оставить события указанного источника",
    )
    analyze_parser.add_argument(
        "--since",
        help="Начало периода в ISO 8601, включительно",
    )
    analyze_parser.add_argument(
        "--until",
        help="Конец периода в ISO 8601, включительно",
    )

    return parser.parse_args()


def main() -> int:
    """Запускает анализ файлов и выводит или сохраняет отчёт."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    try:
        args = parse_arguments()
        if args.report_format == "csv" and args.output is None:
            raise CLIConfigurationError("Для CSV-отчёта укажите путь через --output")
        stats = ReadStats()

        events = read_files(
            paths=args.inputs,
            input_format=args.format,
            skip_invalid=args.skip_invalid,
            stats=stats,
        )

        start_time = None
        end_time = None

        if args.since is not None:
            start_time = parse_timestamp(args.since)

        if args.until is not None:
            end_time = parse_timestamp(args.until)

        if start_time is not None and end_time is not None and start_time > end_time:
            raise CLIConfigurationError("Начало периода не должно быть позже конца")

        filtered_events = filter_events(
            events,
            level=args.level,
            source=args.source,
            start_time=start_time,
            end_time=end_time,
        )

        report = analyze_events(filtered_events, stats=stats)

        if args.report_format == "csv":
            write_csv_report(report, args.output)
        elif args.output is not None:
            write_json_report(report, args.output)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=4))

    except (StreamStatsError, OSError, UnicodeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
