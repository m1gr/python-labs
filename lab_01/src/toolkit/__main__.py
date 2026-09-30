import argparse
import sys

from toolkit.calculator import calculate
from toolkit.converter import convert


def main() -> int:
    """Обрабатывает аргументы командной строки и возвращает код завершения."""
    parser = argparse.ArgumentParser(
        prog="toolkit",
        description="Калькулятор и конвертер единиц",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    calc_parser = subparsers.add_parser("calc", help="Вычислить выражение")
    calc_parser.add_argument("expression", help="Арифметическое выражение")

    convert_parser = subparsers.add_parser("convert", help="Перевести единицы")
    convert_parser.add_argument("value", type=float, help="Исходное значение")
    convert_parser.add_argument(
        "--from",
        dest="from_unit",
        required=True,
        help="Исходная единица измерения",
    )
    convert_parser.add_argument(
        "--to",
        dest="to_unit",
        required=True,
        help="Целевая единица измерения",
    )

    arguments = sys.argv[1:]

    if (
        len(arguments) == 2
        and arguments[0] == "calc"
        and arguments[1] not in ("-h", "--help")
    ):
        arguments.insert(1, "--")

    args = parser.parse_args(arguments)

    try:
        if args.command == "calc":
            print(calculate(args.expression))
        elif args.command == "convert":
            print(convert(args.value, args.from_unit, args.to_unit))
    except (ValueError, ZeroDivisionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
