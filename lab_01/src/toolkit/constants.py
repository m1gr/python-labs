LENGTH_TO_METERS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
}

MASS_TO_KILOGRAMS = {
    "g": 0.001,
    "kg": 1.0,
}

FAHRENHEIT_OFFSET = 32.0
FAHRENHEIT_SCALE = 1.8
KELVIN_OFFSET = 273.15

ABSOLUTE_ZERO_BY_UNIT = {
    "c": -273.15,
    "f": -459.67,
    "k": 0.0,
}

UNIT_GROUPS = {
    "mm": "length",
    "cm": "length",
    "m": "length",
    "km": "length",
    "g": "mass",
    "kg": "mass",
    "c": "temperature",
    "f": "temperature",
    "k": "temperature",
}

OPERATOR_PRIORITY = {"+": 1, "-": 1, "*": 2, "/": 2, "u+": 3, "u-": 3}
