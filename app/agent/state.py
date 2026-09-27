from typing import Annotated, TypedDict
import operator

from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    user_message: str
    messages: Annotated[list[BaseMessage], operator.add]
    tool_events: Annotated[list[dict], operator.add]
    visualizations: Annotated[list[dict], operator.add]
    final_response: str
