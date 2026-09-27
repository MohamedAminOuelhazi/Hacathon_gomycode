import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from app.agent.llm import create_llm_client, get_api_key, get_model_name  # noqa: E402


def main() -> int:
    try:
        get_api_key()
    except RuntimeError as error:
        print(f"Configuration error: {error}")
        return 2

    model = get_model_name()
    print(f"Model: {model}")
    started = time.perf_counter()
    try:
        response = create_llm_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Write a limerick about the wonders of GPU computing."}],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}},
            stream=True,
        )
        print("Response:", end=" ", flush=True)
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                print(reasoning, end="", flush=True)
            if delta.content is not None:
                print(delta.content, end="", flush=True)
        print()
        return 0
    except AuthenticationError:
        print("Authentication failed. Check or regenerate NVIDIA_API_KEY in .env.")
    except APITimeoutError:
        print("NVIDIA hosted API timed out. Check endpoint/model availability and try again.")
    except APIConnectionError:
        print("Could not connect to the NVIDIA hosted API. Check network access and NVIDIA_API_BASE.")
    except RateLimitError:
        print("NVIDIA API rate limit or quota reached. Check your NVIDIA account limits.")
    except APIStatusError as error:
        print(f"NVIDIA API returned HTTP {error.status_code}.")
    except OpenAIError as error:
        print(f"OpenAI SDK request failed ({type(error).__name__}).")
    except Exception as error:
        print(f"Unexpected request error ({type(error).__name__}).")
    finally:
        print(f"Request latency: {time.perf_counter() - started:.2f}s")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
