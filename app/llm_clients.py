import time
import requests
from typing import Tuple, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class OllamaChatClient:
    """
    Minimal Ollama client via HTTP API.
    Assumes Ollama runs on http://localhost:11434
    """

    def __init__(self, base_url: str = "http://localhost:11434",timeout_s: int = 180):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError, requests.HTTPError)),
    )

    def chat(self, model: str, user_text: str, system_text: str = "") -> Tuple[str, int, Dict[str, Any]]:
        t0 = time.perf_counter()

        payload = {
            "model": model,
            "messages": [],
            "stream": False,
        }
        if system_text:
            payload["messages"].append({"role": "system", "content": system_text})
        payload["messages"].append({"role": "user", "content": user_text})

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout_s,
        )
        resp.raise_for_status()

        data = resp.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)
        answer = data.get("message", {}).get("content", "")

        usage = {"input_tokens": None, "output_tokens": None, "total_tokens": None}
        return answer, latency_ms, usage

    def list_models(self) -> Dict[str, Any]:
        resp = requests.get(f"{self.base_url}/api/tags", timeout=30)
        resp.raise_for_status()
        return resp.json()


