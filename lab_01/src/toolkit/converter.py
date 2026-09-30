from toolkit.constants import (
    ABSOLUTE_ZERO_BY_UNIT,
    FAHRENHEIT_OFFSET,
    FAHRENHEIT_SCALE,
    KELVIN_OFFSET,
    LENGTH_TO_METERS,
    MASS_TO_KILOGRAMS,
    UNIT_GROUPS,
)


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """Переводит длину между поддерживаемыми единицами измерения."""
    from_unit, to_unit = from_unit.lower(), to_unit.lower()

    if from_unit not in LENGTH_TO_METERS:
        raise ValueError(f"Неизвестная единица длины: {from_unit}")

    if to_unit not in LENGTH_TO_METERS:
        raise ValueError(f"Неизвестная единица длины: {to_unit}")

    to_meters = value * LENGTH_TO_METERS[from_unit]

    result = to_meters / LENGTH_TO_METERS[to_unit]

    return result


def convert_mass(value: float, from_unit: str, to_unit: str) -> float:
    """Переводит массу между поддерживаемыми единицами измерения."""
    from_unit, to_unit = from_unit.lower(), to_unit.lower()

    if from_unit not in MASS_TO_KILOGRAMS:
        raise ValueError(f"Неизвестная единица массы: {from_unit}")

    if to_unit not in MASS_TO_KILOGRAMS:
        raise ValueError(f"Неизвестная единица массы: {to_unit}")

    to_kilograms = value * MASS_TO_KILOGRAMS[from_unit]

    result = to_kilograms / MASS_TO_KILOGRAMS[to_unit]

    return result


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Переводит температуру между поддерживаемыми единицами измерения."""
    from_unit, to_unit = from_unit.lower(), to_unit.lower()

    if from_unit not in ["c", "f", "k"]:
        raise ValueError(f"Неизвестная единица температуры: {from_unit}")

    if to_unit not in ["c", "f", "k"]:
        raise ValueError(f"Неизвестная единица температуры: {to_unit}")

    if value < ABSOLUTE_ZERO_BY_UNIT[from_unit]:
        raise ValueError("Температура ниже абсолютного нуля")

    if from_unit == "c":
        if to_unit == "f":
            result = value * FAHRENHEIT_SCALE + FAHRENHEIT_OFFSET
        elif to_unit == "k":
            result = value + KELVIN_OFFSET
        else:
            result = value

    elif from_unit == "k":
        if to_unit == "c":
            result = value - KELVIN_OFFSET
        elif to_unit == "f":
            result = (value - KELVIN_OFFSET) * FAHRENHEIT_SCALE + FAHRENHEIT_OFFSET
        else:
            result = value

    else:
        if to_unit == "c":
            result = (value - FAHRENHEIT_OFFSET) / FAHRENHEIT_SCALE
        elif to_unit == "k":
            result = (value - FAHRENHEIT_OFFSET) / FAHRENHEIT_SCALE + KELVIN_OFFSET
        else:
            result = value

    return float(result)


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Переводит величину между совместимыми единицами измерения."""
    from_unit, to_unit = from_unit.lower(), to_unit.lower()

    if from_unit not in UNIT_GROUPS:
        raise ValueError(f"Неизвестная единица: {from_unit}")

    if to_unit not in UNIT_GROUPS:
        raise ValueError(f"Неизвестная единица: {to_unit}")

    from_group = UNIT_GROUPS[from_unit]
    to_group = UNIT_GROUPS[to_unit]

    if from_group != to_group:
        raise ValueError("Конвертация невозможна: единицы несовместимы.")

    if from_group == "length":
        return convert_length(value, from_unit, to_unit)

    elif from_group == "mass":
        return convert_mass(value, from_unit, to_unit)

    else:
        return convert_temperature(value, from_unit, to_unit)
