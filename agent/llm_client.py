import os
from openai import OpenAI

MODEL_ID: str = ""
_client: OpenAI | None = None

CALL_KWARGS = {
    "temperature": 0.2,
    "max_tokens": 1024,
    "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
}


def make_client() -> OpenAI:
    global _client, MODEL_ID

    api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "NVIDIA_API_KEY is not set.\n"
            "Add it to a .env file (see .env.example) or export it as an environment variable."
        )

    MODEL_ID = os.environ.get("NVIDIA_LLM_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b").strip()
    base_url = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()

    _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client


def get_client() -> OpenAI:
    if _client is None:
        raise RuntimeError("Call make_client() before get_client()")
    return _client
