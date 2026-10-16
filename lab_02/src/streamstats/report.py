import csv
import json

from streamstats.models import Report


def write_json_report(report: Report, path: str) -> None:
    """Сохраняет статистический отчёт в JSON-файл."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=4,
        )
        file.write("\n")


def write_csv_report(report: Report, path: str) -> None:
    """Сохраняет готовую статистику в CSV без повторных расчётов."""
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["section", "name", "value"])

        writer.writerow(["summary", "total_events", report["total_events"]])
        writer.writerow(["summary", "skipped_lines", report["skipped_lines"]])

        for level, count in report["by_level"].items():
            writer.writerow(["by_level", level, count])

        for source, count in report["by_source"].items():
            writer.writerow(["by_source", source, count])

        for item in report["top_error_sources"]:
            writer.writerow(["top_error_sources", item["source"], item["count"]])

        writer.writerow(["time", "first_timestamp", report["first_timestamp"]])
        writer.writerow(["time", "last_timestamp", report["last_timestamp"]])
