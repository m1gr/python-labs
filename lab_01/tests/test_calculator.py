import pytest

from toolkit.calculator import (
    calculate,
    evaluate_rpn,
    is_number,
    to_rpn,
    tokenize,
    validate_tokens,
)


def test_tokenize() -> None:
    """Проверяет разбиение выражений на числа, операции и скобки."""
    case = [
        ("12+3", ["12", "+", "3"]),
        ("12.5 / 2", ["12.5", "/", "2"]),
        ("-7+2", ["-", "7", "+", "2"]),
        ("((2+3))", ["(", "(", "2", "+", "3", ")", ")"]),
        (" 12 + 3 ", ["12", "+", "3"]),
    ]

    for expression, expected in case:
        tokens = tokenize(expression)
        assert tokens == expected


def test_is_number() -> None:
    """Проверяет распознавание допустимых и недопустимых числовых токенов."""
    cases = [
        ("0", True),
        ("7", True),
        ("123", True),
        ("12.5", True),
        ("0.001", True),
        ("0.0", True),
        ("007", False),
        ("00", False),
        ("007.5", False),
        (".5", False),
        ("12.", False),
        ("2..5", False),
        ("abc", False),
        ("12abc", False),
        ("1 2", False),
        ("", False),
        ("-7", False),
        ("+", False),
    ]

    for token, expected in cases:
        flag = is_number(token)
        assert flag is expected


def test_validate_tokens_valid() -> None:
    """Проверяет, что допустимые токены проходят проверку."""
    cases = [
        ["12", "+", "3"],
        ["-", "0.5"],
        ["(", "2", "+", "3", ")", "*", "4"],
        ["0"],
        ["(", "(", "2", "+", "3", ")", ")"],
        ["2", "-", "-", "3"],
        ["2", "*", "+", "3"],
        ["-", "(", "2", "+", "3", ")"],
        ["(", "-", "2", ")", "/", "3"],
    ]

    for tokens in cases:
        validate_tokens(tokens)


def test_validate_tokens_invalid() -> None:
    """Проверяет отказ при пустом списке и недопустимых токенах."""
    cases = [
        [],
        ["abc"],
        ["2", "+", "abc"],
        ["1 2"],
        ["007"],
        ["2..5"],
        ["2", "^", "3"],
        ["(", "2", "+", "3"],
        ["2", "+", "3", ")"],
        [")", "("],
        ["2", "+"],
        ["-"],
        ["2", "3"],
        ["(", ")"],
        ["2", "(", "3", ")"],
        ["(", "2", ")", "3"],
        ["2", "*", "/", "3"],
        ["-", "-", "3"],
        ["2", "+", "+", "+", "3"],
    ]

    for tokens in cases:
        with pytest.raises(ValueError):
            validate_tokens(tokens)


def test_to_rpn() -> None:
    """Проверяет приоритет операций, скобки и порядок вычислений в ОПЗ."""
    cases = [
        ("2 + 3 * 4", ["2", "3", "4", "*", "+"]),
        ("(2 + 3) * 4", ["2", "3", "+", "4", "*"]),
        ("8 / 4 * 2", ["8", "4", "/", "2", "*"]),
        ("10 - 3 - 2", ["10", "3", "-", "2", "-"]),
        ("7", ["7"]),
        ("-3", ["3", "u-"]),
        ("+3", ["3", "u+"]),
        ("2 * -3", ["2", "3", "u-", "*"]),
        ("2 + -3", ["2", "3", "u-", "+"]),
        ("2 - -3", ["2", "3", "u-", "-"]),
        ("-(2 + 3) * 4", ["2", "3", "+", "u-", "4", "*"]),
        ("-(-3)", ["3", "u-", "u-"]),
        ("(2 + 3) - 4", ["2", "3", "+", "4", "-"]),
    ]

    for expression, expected in cases:
        tokens = tokenize(expression)
        result = to_rpn(tokens)
        assert result == expected


def test_evaluate_rpn() -> None:
    """Проверяет вычисление ОПЗ и тип результата."""
    cases = [
        (["7"], 7.0),
        (["2", "3", "+"], 5.0),
        (["8", "3", "-"], 5.0),
        (["3", "8", "-"], -5.0),
        (["2", "3", "4", "*", "+"], 14.0),
        (["8", "2", "/"], 4.0),
        (["2", "8", "/"], 0.25),
        (["3", "u+"], 3.0),
        (["3", "u-"], -3.0),
        (["3", "u-", "u-"], 3.0),
        (["2", "3", "+", "u-", "4", "*"], -20.0),
        (["0.1", "0.2", "+"], 0.3),
    ]

    for tokens, expected in cases:
        result = evaluate_rpn(tokens)
        assert result == pytest.approx(expected)
        assert isinstance(result, float)


def test_evaluate_rpn_invalid() -> None:
    """Проверяет отказ при некорректной ОПЗ."""
    cases = [
        [],
        ["2", "3"],
        ["+"],
        ["2", "+"],
        ["u-"],
        ["u+", "3"],
        ["2", "3", "+", "*"],
        ["abc"],
        ["2", "3", "^"],
    ]

    for tokens in cases:
        with pytest.raises(ValueError):
            evaluate_rpn(tokens)


def test_evaluate_rpn_division_by_zero() -> None:
    """Проверяет деление на явный и вычисленный ноль."""
    cases = [
        ["5", "0", "/"],
        ["5", "2", "2", "-", "/"],
    ]

    for tokens in cases:
        with pytest.raises(ZeroDivisionError):
            evaluate_rpn(tokens)


def test_calculate() -> None:
    """Проверяет вычисление выражений с приоритетами, скобками и знаками."""
    cases = [
        ("7", 7.0),
        ("2 + 3 * 4", 14.0),
        ("(2 + 3) * 4", 20.0),
        ("10 - 3 - 2", 5.0),
        ("8 / 4 * 2", 4.0),
        ("12.5 / 2", 6.25),
        ("-3 + 5", 2.0),
        ("+3", 3.0),
        ("2 * -3", -6.0),
        ("2 - -3", 5.0),
        ("-(2 + 3) * 4", -20.0),
        ("-(-3)", 3.0),
        ("  0.1 + 0.2  ", 0.3),
    ]

    for expression, expected in cases:
        result = calculate(expression)
        assert result == pytest.approx(expected)
        assert isinstance(result, float)


def test_calculate_invalid_expression() -> None:
    """Проверяет отказ при некорректной записи выражения."""
    cases = [
        "",
        "   ",
        "2 +",
        "2 ** 3",
        "(2 + 3",
        "2 + 3)",
        "()",
        "2(3 + 4)",
        "1 2 + 3",
        "2 + abc",
        "2..5 + 1",
        "007 + 1",
        "--3",
        "5++++4-3",
    ]

    for expression in cases:
        with pytest.raises(ValueError):
            calculate(expression)


def test_calculate_division_by_zero() -> None:
    """Проверяет деление на явный, вычисленный и отрицательный ноль."""
    cases = [
        "5 / 0",
        "5 / (2 - 2)",
        "1 / -0",
    ]

    for expression in cases:
        with pytest.raises(ZeroDivisionError):
            calculate(expression)
