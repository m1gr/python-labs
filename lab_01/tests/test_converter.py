import pytest

from toolkit.converter import convert, convert_length, convert_mass, convert_temperature


def test_convert_length_unknown_from_unit() -> None:
    """Проверяет отказ при неизвестной исходной единице."""
    with pytest.raises(ValueError):
        convert_length(140, "abc", "km")


def test_convert_length_unknown_to_unit() -> None:
    """Проверяет отказ при неизвестной целевой единице."""
    with pytest.raises(ValueError):
        convert_length(140, "m", "abc")


def test_convert_mass_unknown_from_unit() -> None:
    """Проверяет отказ при неизвестной исходной единице."""
    with pytest.raises(ValueError):
        convert_mass(140, "abc", "kg")


def test_convert_mass_unknown_to_unit() -> None:
    """Проверяет отказ при неизвестной целевой единице."""
    with pytest.raises(ValueError):
        convert_mass(140, "g", "abc")


def test_convert_temperature_unknown_from_unit() -> None:
    """Проверяет отказ при неизвестной исходной единице."""
    with pytest.raises(ValueError):
        convert_temperature(140, "abc", "k")


def test_convert_temperature_unknown_to_unit() -> None:
    """Проверяет отказ при неизвестной целевой единице."""
    with pytest.raises(ValueError):
        convert_temperature(140, "k", "abc")


def test_convert_unknown_from_unit() -> None:
    """Проверяет отказ при неизвестной исходной единице."""
    with pytest.raises(ValueError):
        convert(140, "abc", "m")


def test_convert_unknown_to_unit() -> None:
    """Проверяет отказ при неизвестной целевой единице."""
    with pytest.raises(ValueError):
        convert(140, "m", "abc")


def test_convert_incompatible_units() -> None:
    """Проверяет отказ при несовместимых единицах."""
    with pytest.raises(ValueError):
        convert(140, "m", "k")


def test_convert_length() -> None:
    """Проверяет перевод длины между единицами и тип результата."""
    cases = [
        (2, "m", "cm", 200.0),
        (250, "cm", "mm", 2500.0),
        (1500, "mm", "m", 1.5),
        (0.5, "km", "m", 500.0),
        (7, "m", "m", 7.0),
        (0, "km", "mm", 0.0),
        (150, "CM", "MM", 1500.0),
    ]

    for value, from_unit, to_unit, expected in cases:
        result = convert_length(value, from_unit, to_unit)
        assert result == expected
        assert isinstance(result, float)


def test_convert_mass() -> None:
    """Проверяет перевод массы между единицами и тип результата."""
    cases = [
        (2, "kg", "g", 2000.0),
        (250, "g", "kg", 0.25),
        (0.5, "kg", "g", 500.0),
        (7, "kg", "kg", 7.0),
        (0, "g", "kg", 0.0),
        (1500, "G", "KG", 1.5),
    ]

    for value, from_unit, to_unit, expected in cases:
        result = convert_mass(value, from_unit, to_unit)
        assert result == expected
        assert isinstance(result, float)


def test_convert_temperature() -> None:
    """Проверяет перевод температуры между единицами и тип результата."""
    cases = [
        (0, "c", "f", 32.0),
        (100, "c", "f", 212.0),
        (0, "c", "k", 273.15),
        (32, "f", "c", 0.0),
        (212, "f", "c", 100.0),
        (32, "f", "k", 273.15),
        (273.15, "k", "c", 0.0),
        (273.15, "k", "f", 32.0),
        (20, "c", "c", 20.0),
        (68, "f", "f", 68.0),
        (300, "k", "k", 300.0),
        (-40, "c", "f", -40.0),
        (98.6, "f", "c", 37.0),
        (20, "C", "K", 293.15),
        (0, "k", "c", -273.15),
        (-273.15, "c", "k", 0.0),
        (-459.67, "f", "k", 0.0),
    ]

    for value, from_unit, to_unit, expected in cases:
        result = convert_temperature(value, from_unit, to_unit)
        assert result == pytest.approx(expected)  # проверка с погрешностью
        assert isinstance(result, float)


def test_convert_temperature_below_absolute_zero() -> None:
    """Проверяет отказ при температуре ниже абсолютного нуля."""
    cases = [
        (-274, "c", "f"),
        (-460, "f", "c"),
        (-1, "k", "c"),
        (-1, "k", "k"),
    ]

    for value, from_unit, to_unit in cases:
        with pytest.raises(ValueError):
            convert_temperature(value, from_unit, to_unit)


def test_convert() -> None:
    """Проверяет общую конвертацию, регистр единиц и тип результата."""
    cases = [
        (2, "m", "cm", 200.0),
        (2500, "g", "kg", 2.5),
        (0, "c", "f", 32.0),
        (68, "f", "k", 293.15),
        (150, "CM", "MM", 1500.0),
        (1, "KG", "g", 1000.0),
    ]

    for value, from_unit, to_unit, expected in cases:
        result = convert(value, from_unit, to_unit)
        assert result == pytest.approx(expected)
        assert isinstance(result, float)
