import re

from toolkit.constants import OPERATOR_PRIORITY


def tokenize(expression: str) -> list[str]:
    """Разбивает арифметическое выражение на токены."""
    pattern = r"([-+*/()])"
    parts = re.split(pattern, expression)

    tokens = []

    for part in parts:
        token = part.strip()

        if token:
            tokens.append(token)

    return tokens


def is_number(token: str) -> bool:
    """Проверяет, является ли токен числом без знака и ведущих нулей."""
    pattern = r"(0|[1-9][0-9]*|(0|[1-9][0-9]*)[.][0-9]+)"

    flag = re.fullmatch(pattern, token)

    return bool(flag)


def validate_tokens(tokens: list[str]) -> None:
    """Проверяет список токенов и отклоняет недопустимые элементы."""

    if len(tokens) == 0:
        raise ValueError("Пустое выражение")

    for token in tokens:
        if is_number(token) or token in ["+", "-", "*", "/", "(", ")"]:
            continue
        else:
            raise ValueError(f"Недопустимый токен: {token}")

    balance = 0
    for token in tokens:
        if token == "(":
            balance += 1
        if token == ")":
            balance -= 1
        if balance < 0:
            raise ValueError("Неправильное расположение скобок.")

    if balance != 0:
        raise ValueError("Неправильное расположение скобок.")

    state = "operand"
    for token in tokens:
        if state == "operand":
            if is_number(token):
                state = "operator"
            elif token == "(":
                state = "operand"
            elif token in ("+", "-"):
                state = "after_sign"
            else:
                raise ValueError(f"Ожидалось число, знак или '(', получено: {token}")
        elif state == "after_sign":
            if is_number(token):
                state = "operator"
            elif token == "(":
                state = "operand"
            else:
                raise ValueError(f"Ожидалось число или '(', получено: {token}")
        else:
            if token in ("+", "-", "*", "/"):
                state = "operand"
            elif token == ")":
                state = "operator"
            else:
                raise ValueError(f"Ожидалось знак или ')', получено: {token}")

    if state != "operator":
        raise ValueError("Выражение не закончено.")


def to_rpn(tokens: list[str]) -> list[str]:
    """Преобразует проверенные токены выражения в обратную польскую запись."""

    expect_operand = True
    output = []  # Готовая запись в ОПЗ
    operators = []  # Стек отложенных операций и открывающих скобок

    for token in tokens:
        if is_number(token):
            output.append(token)
            expect_operand = False
        elif token == "(":
            operators.append(token)
            expect_operand = True
        elif token == ")":
            while operators[-1] != "(":
                output.append(operators.pop())
            operators.pop()
            expect_operand = False
        elif token in ("+", "-", "*", "/"):
            if token in ("+", "-") and expect_operand:
                operators.append("u" + token)
            else:
                while (
                    operators
                    and operators[-1] != "("
                    and OPERATOR_PRIORITY[operators[-1]] >= OPERATOR_PRIORITY[token]
                ):
                    output.append(operators.pop())
                operators.append(token)
            expect_operand = True

    output.extend(operators[::-1])

    return output


def evaluate_rpn(tokens: list[str]) -> float:
    """Вычисляет значение выражения в обратной польской записи с помощью стека."""
    stack: list[float] = []

    for token in tokens:
        if is_number(token):
            stack.append(float(token))
        elif token in ("u+", "u-"):
            if not stack:
                raise ValueError("Недостаточно чисел для унарной операции")
            if token == "u-":
                stack.append(-stack.pop())
        elif token in ("+", "-", "*", "/"):
            if len(stack) < 2:
                raise ValueError("Недостаточно чисел для бинарной операции")
            right = stack.pop()
            left = stack.pop()
            if token == "+":
                stack.append(left + right)
            if token == "-":
                stack.append(left - right)
            if token == "*":
                stack.append(left * right)
            if token == "/":
                if right == 0:
                    raise ZeroDivisionError("Деление на 0 недопустимо")
                else:
                    stack.append(left / right)
        else:
            raise ValueError(f"Неизвестный токен: {token}")
    if len(stack) != 1:
        raise ValueError("Некорректная ОПЗ: должен остаться один результат")

    return stack[0]


def calculate(expression: str) -> float:
    """Вычисляет значение арифметического выражения.

    Args:
        expression: Строка с числами, операциями +, -, *, / и скобками.

    Returns:
        Результат вычисления в виде float.

    Raises:
        ValueError: Если выражение пустое или записано некорректно.
        ZeroDivisionError: Если при вычислении возникает деление на ноль.
    """
    tokens = tokenize(expression)
    validate_tokens(tokens)
    rpn_tokens = to_rpn(tokens)
    return evaluate_rpn(rpn_tokens)
