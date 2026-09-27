from app.tools.calculator_tool import calculator
from app.tools.rag_tool import search_company_documents
from app.tools.sql_tool import _validate_read_query
from app.tools.visualization_tool import create_visualization


def test_calculator_handles_arithmetic_and_rejects_code():
    assert calculator("125000 / 500000 * 100")["result"] == 25
    assert "error" in calculator("__import__('os').system('whoami')")


def test_sql_validator_allows_select_and_rejects_writes_and_multiple_statements():
    _validate_read_query("SELECT category, SUM(quantity * unit_price) FROM order_items GROUP BY category")
    _validate_read_query("WITH totals AS (SELECT 1 AS value) SELECT value FROM totals")
    for sql in ("DELETE FROM orders", "SELECT 1; SELECT 2", "WITH gone AS (DELETE FROM orders RETURNING *) SELECT * FROM gone"):
        try:
            _validate_read_query(sql)
        except ValueError:
            continue
        raise AssertionError(f"Unsafe SQL was accepted: {sql}")


def test_visualization_validates_columns_and_returns_spec():
    result = create_visualization(
        [{"category": "Electronics", "revenue": 10}], "bar", "category", "revenue", "Revenue"
    )
    assert result["chartType"] == "bar"
    assert set(("chartType", "meta", "xKey", "series", "data")) <= result.keys()
    assert result["data"][0]["revenue"] == 10
    assert "error" in create_visualization([], "bar", "bad", "y", "Invalid")


def test_visualization_preserves_all_rows_and_emits_pie_contract():
    data = [{"category": f"Category {index}", "revenue": index * 100} for index in range(1, 13)]

    result = create_visualization(data, "pie", "category", "revenue", "Revenue share")

    assert result["chartType"] == "pie"
    assert result["nameKey"] == "category"
    assert result["valueKey"] == "revenue"
    assert result["data"] == data
    assert result["series"][0]["dataKey"] == "revenue"


def test_visualization_formats_complete_consecutive_months_for_people():
    data = [
        {"month": f"2026-{month:02d}-01", "revenue": month * 100.0}
        for month in range(1, 13)
    ]

    result = create_visualization(data, "line", "month", "revenue", "Monthly Revenue")

    assert [row["month"] for row in result["data"]] == [
        "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", "May 2026", "Jun 2026",
        "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026", "Dec 2026",
    ]
    assert len(result["data"]) == len(data)
    assert data[0]["month"] == "2026-01-01"


def test_visualization_rejects_non_numeric_scatter_values():
    result = create_visualization([{"x": 1, "y": "high"}], "scatter", "x", "y", "Relation")

    assert "error" in result


def test_rag_finds_refund_policy_document():
    result = search_company_documents("refund policy")

    assert result["results"]
    assert result["results"][0]["document"] == "refund_policy.md"
    assert "30 calendar days" in result["results"][0]["content"]
