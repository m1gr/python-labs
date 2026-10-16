from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime

from streamstats.models import (
    VALID_LEVELS,
    ErrorSource,
    ReadStats,
    Report,
    parse_timestamp,
)


def filter_events(
    events: Iterable[Mapping[str, object]],
    level: str | None = None,
    source: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Iterator[Mapping[str, object]]:
    """Выдаёт события, подходящие под все заданные условия."""
    for event in events:
        if level is not None and event["level"] != level:
            continue

        if source is not None and event["source"] != source:
            continue

        if start_time is not None or end_time is not None:
            timestamp = parse_timestamp(event["timestamp"])

            if start_time is not None and timestamp < start_time:
                continue

            if end_time is not None and timestamp > end_time:
                continue

        yield event


def analyze_events(
    events: Iterable[Mapping[str, object]],
    stats: ReadStats | None = None,
) -> Report:
    """Считает статистику проверенных событий за один проход."""
    total_events = 0
    by_level = {}
    by_source = {}
    error_sources = {}

    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None

    for level in VALID_LEVELS:
        by_level[level] = 0

    for event in events:
        level = str(event["level"])
        source = str(event["source"])
        timestamp = parse_timestamp(event["timestamp"])

        total_events += 1
        by_level[level] += 1

        if source not in by_source:
            by_source[source] = 0
        by_source[source] += 1

        if level in ("ERROR", "CRITICAL"):
            if source not in error_sources:
                error_sources[source] = 0
            error_sources[source] += 1

        if first_timestamp is None or timestamp < first_timestamp:
            first_timestamp = timestamp

        if last_timestamp is None or timestamp > last_timestamp:
            last_timestamp = timestamp

    sorted_sources = sorted(
        error_sources.items(),
        key=lambda item: (-item[1], item[0]),
    )

    top_error_sources: list[ErrorSource] = []
    for source, count in sorted_sources[:5]:
        top_error_sources.append({"source": source, "count": count})

    first_time = None
    last_time = None

    if first_timestamp is not None:
        first_time = first_timestamp.isoformat()

    if last_timestamp is not None:
        last_time = last_timestamp.isoformat()

    skipped_lines = 0
    if stats is not None:
        skipped_lines = stats.skipped_lines

    return {
        "total_events": total_events,
        "by_level": by_level,
        "by_source": by_source,
        "top_error_sources": top_error_sources,
        "first_timestamp": first_time,
        "last_timestamp": last_time,
        "skipped_lines": skipped_lines,
    }
