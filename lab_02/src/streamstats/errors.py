class StreamStatsError(Exception):
    """Базовая ошибка нашего анализатора."""


class InvalidEventError(StreamStatsError):
    """Ошибка в данных события."""


class InvalidTimestampError(StreamStatsError):
    """Некорректная временная метка события."""


class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат входного файла."""


class CLIConfigurationError(StreamStatsError):
    """Ошибка в аргументах командной строки."""
