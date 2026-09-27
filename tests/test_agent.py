from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agent import graph


def _tool_call(name, arguments, call_id):
    return {
        "name": name,
        "args": arguments,
        "id": call_id,
        "type": "tool_call",
    }


def test_agent_includes_business_scope_boundary(monkeypatch):
    captured = {}

    class FakeModel:
        def invoke(self, messages):
            captured["messages"] = messages
            return AIMessage(content="I can help with the company's business data and documents.")

    monkeypatch.setattr(graph, "_model_with_tools", lambda: FakeModel())

    result = graph.run_agent("What juice tastes best?")

    system_prompt = captured["messages"][0].content
    assert "Do not answer unrelated general-knowledge" in system_prompt
    assert "do not call tools" in system_prompt
    assert result["tool_events"] == []


def test_agent_receives_recent_turns_for_follow_up(monkeypatch):
    captured = {}

    class FakeModel:
        def invoke(self, messages):
            captured["messages"] = messages
            return AIMessage(content="I will compare the two periods.")

    monkeypatch.setattr(graph, "_model_with_tools", lambda: FakeModel())

    graph.run_agent("Compare it with 2025", [
        {"role": "user", "content": "What was the total revenue for 2026?"},
        {"role": "assistant", "content": "Revenue was $3,000,000."},
    ])

    messages = captured["messages"]
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert messages[1].content == "What was the total revenue for 2026?"
    assert isinstance(messages[2], AIMessage)
    assert messages[2].content == "Revenue was $3,000,000."
    assert isinstance(messages[3], HumanMessage)
    assert messages[3].content == "Compare it with 2025"


def test_agent_observes_sql_error_retries_and_calls_multiple_tools(monkeypatch):
    sql_calls = []

    def fake_sql(sql):
        sql_calls.append(sql)
        if "wrong_column" in sql:
            return {"error": "column wrong_column does not exist", "error_type": "ProgrammingError"}
        return {
            "columns": ["category", "revenue"],
            "rows": [["Electronics", 125000], ["Furniture", 97000]],
            "row_count": 2,
        }

    class FakeModel:
        def __init__(self):
            self.turn = 0

        def invoke(self, messages):
            self.turn += 1
            if self.turn == 1:
                return AIMessage(content="", tool_calls=[_tool_call(
                    "execute_sql", {"sql": "SELECT wrong_column FROM products"}, "sql-1"
                )])
            if self.turn == 2:
                assert "wrong_column" in messages[-1].content
                return AIMessage(content="", tool_calls=[_tool_call(
                    "execute_sql", {"sql": "SELECT category FROM products"}, "sql-2"
                )])
            if self.turn == 3:
                return AIMessage(content="", tool_calls=[
                    _tool_call("calculator", {"expression": "125000 / 222000 * 100"}, "calc-1"),
                    _tool_call("create_visualization", {
                        "data": [
                            {"category": "Electronics", "revenue": 125000},
                            {"category": "Furniture", "revenue": 97000},
                        ],
                        "chart_type": "bar",
                        "x_column": "category",
                        "y_column": "revenue",
                        "title": "Revenue by category",
                    }, "chart-1"),
                ])
            return AIMessage(content="Electronics leads with 56.3% of the total.")

    monkeypatch.setattr(graph, "run_sql", fake_sql)
    model = FakeModel()
    monkeypatch.setattr(graph, "_model_with_tools", lambda: model)

    result = graph.run_agent("Which category leads and show a chart?")

    assert len(sql_calls) == 2
    assert [event["tool"] for event in result["tool_events"]] == [
        "execute_sql", "execute_sql", "calculator", "create_visualization"
    ]
    assert [event["status"] for event in result["tool_events"]] == [
        "error", "completed", "completed", "completed"
    ]
    assert result["answer"].startswith("Electronics leads")
    assert result["visualizations"][0]["chartType"] == "bar"


def test_nemotron_agent_uses_fast_tool_routing(monkeypatch):
    captured = {}

    class FakeChatModel:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def bind_tools(self, tools):
            captured["tools"] = tools
            return self

    monkeypatch.setattr(graph, "ChatOpenAI", FakeChatModel)
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    graph._model_with_tools()

    assert captured["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert captured["max_tokens"] == 2048
    assert captured["extra_body"]["chat_template_kwargs"] == {"enable_thinking": False}
