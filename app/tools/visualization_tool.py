from datetime import date
from typing import Any, Literal


SUPPORTED_CHARTS = {"bar", "line", "pie", "scatter"}


def _format_month_axis(data: list[dict[str, Any]], x_column: str) -> list[dict[str, Any]]:
    """Format complete, consecutive month-start dates without changing granularity."""
    parsed = []
    for row in data:
        value = row.get(x_column)
        if not isinstance(value, str):
            return data
        try:
            month = date.fromisoformat(value[:10])
        except ValueError:
            return data
        if month.day != 1:
            return data
        parsed.append(month)

    if not parsed or len(parsed) > 24:
        return data
    for previous, current in zip(parsed, parsed[1:]):
        expected_month = previous.month % 12 + 1
        expected_year = previous.year + (previous.month == 12)
        if (current.year, current.month) != (expected_year, expected_month):
            return data

    return [
        {**row, x_column: month.strftime("%b %Y")}
        for row, month in zip(data, parsed)
    ]


def create_visualization(
    data: list[dict[str, Any]],
    chart_type: Literal["bar", "line", "pie", "scatter"],
    x_column: str,
    y_column: str,
    title: str,
    description: str = "",
    x_axis_label: str = "",
    value_label: str = "",
    value_format: Literal["compact", "number", "currency", "percent"] = "compact",
    value_prefix: str = "",
    value_suffix: str = "",
) -> dict:
    """Transform supplied records into a chart JSON spec without querying data."""
    if chart_type not in SUPPORTED_CHARTS:
        return {"error": f"chart_type must be one of {sorted(SUPPORTED_CHARTS)}."}
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        return {"error": "data must be a list of row objects."}
    if not data:
        return {"error": "data must contain at least one row."}
    if not x_column or not y_column or any(
        x_column not in row or y_column not in row for row in data
    ):
        return {"error": "x_column and y_column must exist in every supplied row."}
    if not isinstance(title, str) or not title.strip():
        return {"error": "title must be a non-empty string."}
    if chart_type in {"bar", "line", "pie", "scatter"} and any(
        not isinstance(row[y_column], (int, float)) or isinstance(row[y_column], bool)
        for row in data
    ):
        return {"error": "The chart value column must contain numeric values."}
    if chart_type == "pie" and any(row[y_column] < 0 for row in data):
        return {"error": "Pie chart values cannot be negative."}

    series = {
        "dataKey": y_column,
        "label": value_label or y_column.replace("_", " ").title(),
        "valueFormat": value_format,
    }
    if chart_type != "pie":
        series["axisLabel"] = value_label or y_column.replace("_", " ").title()
    if value_prefix:
        series["valuePrefix"] = value_prefix
    if value_suffix:
        series["valueSuffix"] = value_suffix

    spec = {
        "chartType": chart_type,
        "meta": {
            "title": title.strip(),
            "description": description.strip(),
        },
        "series": [series],
        "data": _format_month_axis(data, x_column) if chart_type in {"bar", "line"} else data,
    }
    if chart_type == "pie":
        spec["nameKey"] = x_column
        spec["valueKey"] = y_column
    else:
        spec["xKey"] = x_column
        spec["xAxisLabel"] = x_axis_label or x_column.replace("_", " ").title()
    return spec
