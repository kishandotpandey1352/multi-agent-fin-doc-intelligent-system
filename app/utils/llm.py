from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen

from app.config.settings import load_settings


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate_text(self, prompt: str, system: Optional[str] = None) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        response = self._post_json(payload)
        return str(response.get("response", "")).strip()

    def generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        if system:
            payload["system"] = system
        response = self._post_json(payload)
        text = str(response.get("response", "")).strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    def _post_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        data = json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content = response.read().decode("utf-8")
                return json.loads(content)
        except Exception:
            return {}


def get_ollama_client() -> Optional[OllamaClient]:
    settings = load_settings()
    base_url = getattr(settings, "ollama_base_url", "").strip() or "http://localhost:11434"
    model = getattr(settings, "ollama_model", "").strip() or "qwen2.5:7b-instruct"
    if not base_url or not model:
        return None
    return OllamaClient(base_url=base_url, model=model)
