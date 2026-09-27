import logging

from fastapi import FastAPI, HTTPException
from langchain_openai.chat_models.base import OpenAITimeoutError

from app.agent.graph import run_agent
from app.models.api import ChatRequest, ChatResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Soufet Agent API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = run_agent(request.message, request.history)
        return ChatResponse(**result)
    except OpenAITimeoutError as error:
        logging.getLogger("soufet.api").error("NVIDIA hosted API request timed out")
        raise HTTPException(
            status_code=504,
            detail="NVIDIA hosted API did not respond before the timeout. Check NVIDIA_API_BASE, NVIDIA_MODEL, network access, and API availability.",
        ) from error
    except Exception as error:
        logging.getLogger("soufet.api").exception("Agent request failed")
        raise HTTPException(
            status_code=502,
            detail="The agent could not complete the request. Check the NVIDIA hosted API and PostgreSQL connectivity.",
        ) from error
