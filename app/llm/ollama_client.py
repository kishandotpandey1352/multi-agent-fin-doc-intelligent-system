import os
import requests
from typing import Optional


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    def generate(self, prompt: str, max_tokens: int = 128, temperature: float = 0.0) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        try:
            resp = requests.post(url, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            # Ollama response shapes vary; try common fields conservatively
            if isinstance(data, dict):
                # new format may include 'output' as list
                out = data.get("output") or data.get("choices") or data.get("results")
                if isinstance(out, list) and out:
                    first = out[0]
                    if isinstance(first, dict):
                        return first.get("text") or first.get("content") or str(first)
                    return str(first)
                # fallback to 'text'
                return data.get("text", "") or data.get("result", "") or ""
            return ""
        except Exception:
            return ""


_OLLAMA = OllamaClient()


def get_ollama_client() -> OllamaClient:
    return _OLLAMA
