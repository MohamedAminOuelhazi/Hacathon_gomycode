import json
import logging
import os
import time
from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.agent.llm import get_api_key, get_base_url, get_model_name
from app.tools.calculator_tool import calculator as calculate
from app.tools.rag_tool import search_company_documents as search_documents
from app.tools.schema_tool import get_database_schema as inspect_schema
from app.tools.sql_tool import execute_sql as run_sql
from app.tools.visualization_tool import create_visualization as make_visualization

logger = logging.getLogger("soufet.agent")


@tool
def get_database_schema() -> dict:
    """Inspect the structured business database before writing unfamiliar SQL.

    Use when a database question requires table/column discovery, relationship
    verification, or column types. Do not call if the current conversation already
    has sufficient schema information. This returns structure only, never business
    records or query results. It takes no arguments. Normally inspect before
    execute_sql unless the schema is already known in the current context.
    """
    return inspect_schema()


@tool
def execute_sql(sql: str) -> dict:
    """Run one READ-ONLY PostgreSQL query against structured business data.

    Use for database facts, filters, joins, aggregations (SUM/COUNT/AVG/MIN/MAX),
    rankings, and time-based analysis, including data needed by calculator or
    create_visualization. Do not use for company documents, standalone arithmetic,
    or data changes. Input is exactly one SELECT or read-only WITH query; writes,
    DDL, multiple statements, and mutating SQL are rejected and PostgreSQL also
    enforces a read-only transaction. Returns columns, rows, row_count, truncation
    status, or an error. Never invent results. On an error, inspect it, fix the SQL,
    and retry when reasonable. Inspect schema first unless already known.
    """
    return run_sql(sql)


@tool
def calculator(expression: str) -> dict:
    """Deterministically calculate using numeric values already in context.

    MUST use for every derived percentage, ratio, growth rate, difference, margin,
    average, or other calculation that combines/transforms numeric values. When
    inputs are in the database, first use execute_sql to get the component values
    (SQL may aggregate with COUNT or SUM), then pass those values here. Do not
    calculate the final derived metric in SQL, mentally, or in application code.
    Do not use to retrieve database facts or redundantly calculate a direct SQL
    result such as a COUNT or SUM. Input is an arithmetic expression using numeric
    literals and +, -, *, /, %, and **. Returns the expression and numeric result,
    or an error. Never invent input values.
    """
    return calculate(expression)


@tool
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
    """Build a structured chart JSON object from data already retrieved.

    Use when the user requests a chart/graph/visualization, or when a visual
    materially helps explain numerical comparisons or trends. Do not use for a
    simple factual answer or without reliable data. This tool never queries the
    database and must receive complete rows from SQL or another tool without
    sampling, changing granularity, or inventing values. Choose line for time
    trends, bar for category/ranking comparisons, pie only for a small part-to-whole
    breakdown, and scatter for two numeric variables. Inputs: row-object data,
    chart_type, x_column, y_column, title, and optional description/axis/value
    formatting. Returns only the frontend visualization JSON contract or an error.
    For pie, x_column is the category name and y_column is its numeric value.
    """
    return make_visualization(
        data,
        chart_type,
        x_column,
        y_column,
        title,
        description,
        x_axis_label,
        value_label,
        value_format,
        value_prefix,
        value_suffix,
    )


@tool
def search_company_documents(query: str) -> dict:
    """Search unstructured company documents for policy and internal knowledge.

    Use for refund policies, procedures, contracts, product documentation, HR
    policies, and other uploaded company rules. Do not use for structured metrics
    such as customers, sales, orders, or revenue; use execute_sql for those. If a
    request needs both documents and database facts, use this and SQL, then combine
    their results. Input is a focused natural-language query. Returns matching
    document names, excerpts, and relevance; it does not query PostgreSQL. Never
    claim a policy fact that is absent from returned excerpts.
    """
    return search_documents(query)


TOOLS = [get_database_schema, execute_sql, calculator, create_visualization, search_company_documents]
TOOLS_BY_NAME = {item.name: item for item in TOOLS}


def _model_with_tools():
    return ChatOpenAI(
        model=get_model_name(),
        base_url=get_base_url(),
        api_key=get_api_key(),
        temperature=0.2,
        max_tokens=2048,
        timeout=float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "120")),
        max_retries=0,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False,
            }
        },
    ).bind_tools(TOOLS)


def _result_summary(name: str, result: Any) -> str:
    if isinstance(result, dict) and "error" in result:
        return f"{result.get('error_type', 'ToolError')}: execution failed"
    if name == "execute_sql":
        return f"{result.get('row_count', 0)} rows returned" if isinstance(result, dict) else "SQL completed"
    if name == "get_database_schema":
        return f"{len(result.get('tables', {}))} tables inspected"
    if name == "search_company_documents":
        return f"{len(result.get('results', []))} document chunks found"
    if name == "create_visualization":
        return f"{result.get('chartType', 'Chart')} visualization created"
    return "Calculation completed"


def _safe_argument_summary(name: str, arguments: dict) -> dict:
    if name == "execute_sql":
        return {"sql_length": len(str(arguments.get("sql", "")))}
    if name == "calculator":
        return {"expression_length": len(str(arguments.get("expression", "")))}
    if name == "create_visualization":
        data = arguments.get("data", [])
        return {
            "chart_type": arguments.get("chart_type"),
            "row_count": len(data) if isinstance(data, list) else None,
        }
    if name == "search_company_documents":
        return {"query_length": len(str(arguments.get("query", "")))}
    return {}


def _llm_node(state: AgentState) -> dict:
    started = time.perf_counter()
    logger.info(json.dumps({"event": "llm_started", "message_count": len(state["messages"])}))
    try:
        response = _model_with_tools().invoke(state["messages"])
    except Exception as error:
        logger.error(json.dumps({
            "event": "llm_failed",
            "error_type": type(error).__name__,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }))
        raise
    logger.info(json.dumps({
        "event": "llm_finished",
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "tool_call_count": len(response.tool_calls),
    }))
    if not response.tool_calls:
        return {"messages": [response], "final_response": _text_content(response.content)}
    return {"messages": [response]}


def _text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part if isinstance(part, str) else str(part.get("text", ""))
            for part in content
            if isinstance(part, str) or isinstance(part, dict)
        ).strip()
    return "" if content is None else str(content)


def _tool_node(state: AgentState) -> dict:
    assistant_message = state["messages"][-1]
    tool_messages = []
    events = []
    visualizations = []

    for call in assistant_message.tool_calls:
        name = call.get("name", "unknown")
        arguments = call.get("args", {})
        if not isinstance(arguments, dict):
            arguments = {}
        started = time.perf_counter()
        logger.info(json.dumps({
            "event": "tool_started",
            "tool": name,
            "arguments": _safe_argument_summary(name, arguments),
        }))
        tool = TOOLS_BY_NAME.get(name)
        try:
            if tool is None:
                raise ValueError(f"Unknown tool: {name}")
            result = tool.invoke(arguments)
            status = "error" if isinstance(result, dict) and "error" in result else "completed"
        except Exception as error:
            result = {"error": str(error), "error_type": type(error).__name__}
            status = "error"
            logger.error(json.dumps({
                "event": "tool_failed",
                "tool": name,
                "error_type": type(error).__name__,
                "error": str(error),
            }))

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        summary = _result_summary(name, result)
        event = {
            "tool": name,
            "status": status,
            "duration_ms": duration_ms,
            "summary": summary,
        }
        events.append(event)
        if name == "create_visualization" and status == "completed":
            visualizations.append(result)
        logger.info(json.dumps({"event": "tool_finished", **event}))
        tool_messages.append(
            ToolMessage(
                content=json.dumps(result, default=str),
                tool_call_id=call.get("id") or f"missing-id-{len(tool_messages)}",
                name=name,
            )
        )
    return {"messages": tool_messages, "tool_events": events, "visualizations": visualizations}


def _route(state: AgentState) -> str:
    message = state["messages"][-1]
    return "tools" if isinstance(message, AIMessage) and message.tool_calls else END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("llm", _llm_node, retry_policy=RetryPolicy(max_attempts=1))
    graph.add_node("tools", _tool_node)
    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", _route, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")
    return graph.compile()


def run_agent(message: str, history: list[Any] | None = None) -> dict:
    logger.info(json.dumps({"event": "user_message", "message_length": len(message)}))
    prior_messages = []
    for item in (history or [])[-12:]:
        role = item.role if hasattr(item, "role") else item.get("role")
        content = item.content if hasattr(item, "content") else item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str) or not content.strip():
            continue
        prior_messages.append(HumanMessage(content=content[:4_000]) if role == "user" else AIMessage(content=content[:4_000]))
    initial: AgentState = {
        "user_message": message,
        "messages": [SystemMessage(content=SYSTEM_PROMPT), *prior_messages, HumanMessage(content=message)],
        "tool_events": [],
        "visualizations": [],
    }
    result = build_graph().invoke(initial, config={"recursion_limit": 24})
    answer = result.get("final_response", "")
    logger.info(json.dumps({"event": "final_answer", "answer": answer}))
    return {
        "answer": answer,
        "tool_events": result.get("tool_events", []),
        "visualizations": result.get("visualizations", []),
    }
