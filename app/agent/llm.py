import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_API_BASE = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"


def get_api_key() -> str:
    api_key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not api_key or api_key.lower() in {"your_key", "your_nvidia_api_key"}:
        raise RuntimeError("NVIDIA_API_KEY is missing. Add your NVIDIA hosted API key to .env.")
    return api_key


def get_base_url() -> str:
    return os.getenv("NVIDIA_API_BASE", DEFAULT_API_BASE).strip().rstrip("/")


def get_model_name() -> str:
    return os.getenv("NVIDIA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def create_llm_client() -> OpenAI:
    """Create the OpenAI SDK client for NVIDIA's hosted API."""
    return OpenAI(
        base_url=get_base_url(),
        api_key=get_api_key(),
        timeout=float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "120")),
        max_retries=0,
    )
