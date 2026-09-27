import pytest
from langchain_core.messages import AIMessage

from app.agent import graph


MONTHS_2026 = [
    {"month": f"{month} 2026", "revenue": float(month_number * 1000)}
    for month_number, month in enumerate(
        ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
        start=1,
    )
]
CATEGORY_REVENUE = [
    {"category": "Furniture", "revenue": 800.0},
    {"category": "Electronics", "revenue": 700.0},
]


CASES = [
    {
        "question": "How many customers do we have?",
        "steps": [("get_database_schema", {}), ("execute_sql", {"sql": "SELECT COUNT(*) AS customer_count FROM customers"})],
        "sql_results": [{"columns": ["customer_count"], "rows": [[120]], "row_count": 1}],
        "expected": ["get_database_schema", "execute_sql"],
        "sql_contains": ["COUNT(*)", "FROM customers"],
        "answer": "There are 120 customers.",
    },
    {
        "question": "Show monthly revenue for 2026.",
        "steps": [
            ("get_database_schema", {}),
            ("execute_sql", {"sql": "SELECT DATE_TRUNC('month', o.order_date) AS month, SUM(oi.quantity * oi.unit_price) AS revenue FROM order_items oi JOIN orders o USING (order_id) WHERE o.status = 'completed' AND o.order_date >= DATE '2026-01-01' AND o.order_date < DATE '2027-01-01' GROUP BY month ORDER BY month"}),
            ("create_visualization", {"data": MONTHS_2026, "chart_type": "line", "x_column": "month", "y_column": "revenue", "title": "Monthly Revenue - 2026"}),
        ],
        "sql_results": [{"columns": ["month", "revenue"], "rows": [[row["month"], row["revenue"]] for row in MONTHS_2026], "row_count": 12}],
        "expected": ["get_database_schema", "execute_sql", "create_visualization"],
        "sql_contains": ["DATE_TRUNC('month'", "SUM(oi.quantity * oi.unit_price)", "2026-01-01", "2027-01-01", "ORDER BY month"],
        "chart_type": "line",
        "chart_data": MONTHS_2026,
        "answer": "Monthly completed-order revenue is shown in the chart.",
    },
    {
        "question": "Which product category generated the most revenue?",
        "steps": [
            ("get_database_schema", {}),
            ("execute_sql", {"sql": "SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue FROM products p JOIN order_items oi USING (product_id) JOIN orders o USING (order_id) WHERE o.status = 'completed' GROUP BY p.category ORDER BY revenue DESC LIMIT 1"}),
        ],
        "sql_results": [{"columns": ["category", "revenue"], "rows": [["Furniture", 800.0]], "row_count": 1}],
        "expected": ["get_database_schema", "execute_sql"],
        "sql_contains": ["SUM(oi.quantity * oi.unit_price)", "GROUP BY p.category", "ORDER BY revenue DESC", "LIMIT 1"],
        "answer": "Furniture generated the most revenue.",
    },
    {
        "question": "Which product category generated the most revenue and what percentage of total revenue did it represent?",
        "steps": [
            ("get_database_schema", {}),
            ("execute_sql", {"sql": "SELECT p.category, SUM(oi.quantity * oi.unit_price) AS category_revenue, (SELECT SUM(oi2.quantity * oi2.unit_price) FROM order_items oi2 JOIN orders o2 USING (order_id) WHERE o2.status = 'completed') AS total_revenue FROM products p JOIN order_items oi USING (product_id) JOIN orders o USING (order_id) WHERE o.status = 'completed' GROUP BY p.category ORDER BY category_revenue DESC LIMIT 1"}),
            ("calculator", {"expression": "800 / 2000 * 100"}),
        ],
        "sql_results": [{"columns": ["category", "category_revenue", "total_revenue"], "rows": [["Furniture", 800.0, 2000.0]], "row_count": 1}],
        "expected": ["get_database_schema", "execute_sql", "calculator"],
        "sql_contains": ["category_revenue", "total_revenue", "GROUP BY p.category"],
        "sql_excludes": ["AS percentage", "AS share", " / SUM("],
        "answer": "Furniture represented 40% of revenue.",
    },
    {
        "question": "Which product category generated the most revenue and show me a chart?",
        "steps": [
            ("get_database_schema", {}),
            ("execute_sql", {"sql": "SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue FROM products p JOIN order_items oi USING (product_id) JOIN orders o USING (order_id) WHERE o.status = 'completed' GROUP BY p.category ORDER BY revenue DESC"}),
            ("create_visualization", {"data": CATEGORY_REVENUE, "chart_type": "bar", "x_column": "category", "y_column": "revenue", "title": "Revenue by Category"}),
        ],
        "sql_results": [{"columns": ["category", "revenue"], "rows": [[row["category"], row["revenue"]] for row in CATEGORY_REVENUE], "row_count": 2}],
        "expected": ["get_database_schema", "execute_sql", "create_visualization"],
        "sql_contains": ["SUM(oi.quantity * oi.unit_price)", "GROUP BY p.category"],
        "chart_type": "bar",
        "chart_data": CATEGORY_REVENUE,
        "answer": "Furniture leads; the chart compares category revenue.",
    },
    {
        "question": "What is our refund policy?",
        "steps": [("search_company_documents", {"query": "refund policy"})],
        "sql_results": [],
        "expected": ["search_company_documents"],
        "answer": "The refund policy allows returns within 30 calendar days.",
    },
    {
        "question": "What is our refund policy and what was our refund rate in 2026?",
        "steps": [
            ("get_database_schema", {}),
            ("search_company_documents", {"query": "refund policy"}),
            ("execute_sql", {"sql": "SELECT COUNT(*) FILTER (WHERE status = 'refunded') AS refunds, COUNT(*) FILTER (WHERE status IN ('completed', 'refunded')) AS eligible FROM orders WHERE order_date >= DATE '2026-01-01' AND order_date < DATE '2027-01-01'"}),
            ("calculator", {"expression": "20 / 320 * 100"}),
        ],
        "sql_results": [{"columns": ["refunds", "eligible"], "rows": [[20, 320]], "row_count": 1}],
        "expected": ["get_database_schema", "search_company_documents", "execute_sql", "calculator"],
        "sql_contains": ["COUNT(*) FILTER (WHERE status = 'refunded')", "COUNT(*) FILTER (WHERE status IN ('completed', 'refunded'))", "2026-01-01", "2027-01-01"],
        "sql_excludes": ["AS refund_rate", "AS percentage", " / COUNT("],
        "answer": "The policy allows returns within 30 days; the 2026 refund rate was 6.25%.",
    },
    {
        "question": "Show me the relationship between order value and customer segment.",
        "steps": [("get_database_schema", {})],
        "sql_results": [],
        "expected": ["get_database_schema"],
        "answer": "The database has no customer segment field; would country work as a proxy?",
    },
    {
        "question": "Show revenue by product category.",
        "steps": [
            ("get_database_schema", {}),
            ("execute_sql", {"sql": "SELECT product_category FROM products"}),
            ("execute_sql", {"sql": "SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue FROM products p JOIN order_items oi USING (product_id) JOIN orders o USING (order_id) WHERE o.status = 'completed' GROUP BY p.category"}),
        ],
        "sql_results": [
            {"error": "column product_category does not exist", "error_type": "ProgrammingError"},
            {"columns": ["category", "revenue"], "rows": [["Furniture", 800.0]], "row_count": 1},
        ],
        "expected": ["get_database_schema", "execute_sql", "execute_sql"],
        "expected_statuses": ["completed", "error", "completed"],
        "sql_contains": ["product_category", "SUM(oi.quantity * oi.unit_price)", "GROUP BY p.category"],
        "answer": "Furniture revenue is 800.",
    },
]


@pytest.mark.parametrize("case", CASES, ids=[str(i) for i in range(1, 10)])
def test_requested_tool_sequences_and_outputs(monkeypatch, case):
    class ScriptedModel:
        def __init__(self):
            self.turn = 0

        def invoke(self, messages):
            if self.turn == len(case["steps"]):
                return AIMessage(content=case["answer"])
            name, arguments = case["steps"][self.turn]
            self.turn += 1
            return AIMessage(content="", tool_calls=[{
                "name": name,
                "args": arguments,
                "id": f"call-{self.turn}",
                "type": "tool_call",
            }])

    scripted_model = ScriptedModel()
    sql_results = iter(case["sql_results"])
    sql_statements = []
    monkeypatch.setattr(graph, "_model_with_tools", lambda: scripted_model)
    monkeypatch.setattr(graph, "inspect_schema", lambda: {
        "tables": {
            "customers": {"columns": {"id": "INTEGER", "country": "VARCHAR"}},
            "orders": {"columns": {"customer_id": "INTEGER", "status": "VARCHAR", "order_date": "DATE"}},
            "products": {"columns": {"category": "VARCHAR", "price": "NUMERIC"}},
            "order_items": {"columns": {"order_id": "INTEGER", "product_id": "INTEGER", "quantity": "INTEGER", "unit_price": "NUMERIC"}},
        }
    })

    def fake_sql(sql):
        sql_statements.append(sql)
        return next(sql_results)

    monkeypatch.setattr(graph, "run_sql", fake_sql)
    monkeypatch.setattr(graph, "search_documents", lambda query: {
        "results": [{"document": "refund_policy.md", "content": "Returns accepted within 30 calendar days."}]
    })

    result = graph.run_agent(case["question"])

    assert [event["tool"] for event in result["tool_events"]] == case["expected"]
    assert result["answer"] == case["answer"]
    assert [event["status"] for event in result["tool_events"]] == case.get(
        "expected_statuses", ["completed"] * len(case["expected"])
    )
    for fragment in case.get("sql_contains", []):
        assert any(fragment in sql for sql in sql_statements)
    for fragment in case.get("sql_excludes", []):
        assert all(fragment not in sql for sql in sql_statements)
    if "chart_type" in case:
        chart = result["visualizations"][0]
        assert chart["chartType"] == case["chart_type"]
        assert chart["data"] == case["chart_data"]
        assert {"chartType", "meta", "series", "data"} <= chart.keys()
