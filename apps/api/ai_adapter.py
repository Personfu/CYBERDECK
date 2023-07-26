"""
FLLC CyberDeck - Local AI Adapter Abstraction

Supports three backends:
  - none:                    No AI, app works fully without it
  - ollama:                  Local Ollama instance
  - openai-compatible-local: Any OpenAI-compatible local API

AI is used ONLY for:
  - Summarization
  - Draft finding language
  - Evidence clustering
  - Component naming suggestions
  - Report-writing assistance

AI is NEVER used for:
  - Payload generation
  - Exploitation
  - Credential harvesting
  - Evasion techniques
"""

from abc import ABC, abstractmethod
from typing import Optional
import os
import json


class AIAdapter(ABC):
    """Base adapter interface for local AI backends."""

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Generate a summary of the given text."""
        ...

    @abstractmethod
    def draft_finding(self, observations: str) -> str:
        """Draft finding language from analyst observations."""
        ...

    @abstractmethod
    def suggest_names(self, context: str) -> list[str]:
        """Suggest component or device names from context."""
        ...

    @abstractmethod
    def assist_report(self, report_data: dict) -> str:
        """Provide report-writing assistance."""
        ...

    @abstractmethod
    def cluster_evidence(self, items: list[str]) -> list[dict]:
        """Cluster evidence items into logical groups."""
        ...


class NoneAdapter(AIAdapter):
    """No-op adapter when AI is disabled. App works fully without AI."""

    def summarize(self, text: str) -> str:
        return text[:200] + "..." if len(text) > 200 else text

    def draft_finding(self, observations: str) -> str:
        return f"Finding based on observations: {observations[:100]}"

    def suggest_names(self, context: str) -> list[str]:
        return ["Device-A", "Component-B", "Module-C"]

    def assist_report(self, report_data: dict) -> str:
        return report_data.get("summary", "No summary available.")

    def cluster_evidence(self, items: list[str]) -> list[dict]:
        return [{"group": "default", "items": items}]


class OllamaAdapter(AIAdapter):
    """Adapter for local Ollama instance with health checking and real integration."""

    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "llama3"):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self._healthy = None

    def _health_check(self) -> bool:
        """Check if Ollama is reachable by querying /api/tags."""
        if self._healthy is not None:
            return self._healthy
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.endpoint}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                self._healthy = resp.status == 200
        except Exception:
            self._healthy = False
        return self._healthy

    def _call(self, prompt: str, system: str = "") -> str:
        if not self._health_check():
            return f"[Ollama not available at {self.endpoint} — using fallback]"
        try:
            import urllib.request
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            if system:
                payload["system"] = system
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.endpoint}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            return f"[Ollama error: {e}]"

    def summarize(self, text: str) -> str:
        return self._call(
            f"Summarize the following hardware analysis notes in 2-3 sentences:\n\n{text}",
            system="You are a hardware security analyst assistant. Provide concise technical summaries."
        )

    def draft_finding(self, observations: str) -> str:
        return self._call(
            f"Draft a professional security finding from these observations:\n\n{observations}",
            system="You are a security report writer. Draft formal findings with impact statements."
        )

    def suggest_names(self, context: str) -> list[str]:
        result = self._call(
            f"Suggest 3 short component names for:\n\n{context}",
            system="You are a hardware component naming assistant. Return exactly 3 names, one per line."
        )
        return [line.strip("- ").strip() for line in result.strip().split("\n") if line.strip()][:3] or ["Component-A"]

    def assist_report(self, report_data: dict) -> str:
        return self._call(
            f"Write a 2-paragraph executive summary for this hardware analysis report:\n\n{json.dumps(report_data, indent=2, default=str)}",
            system="You are a report writer for hardware security assessments."
        )

    def cluster_evidence(self, items: list[str]) -> list[dict]:
        result = self._call(
            f"Group these evidence items into logical clusters and explain each group:\n\n{json.dumps(items)}",
            system="You are an evidence analyst. Group items by category."
        )
        return [{"group": "ai-clustered", "items": items, "analysis": result}]


class OpenAICompatibleAdapter(AIAdapter):
    """Adapter for any OpenAI-compatible local API (e.g., LM Studio, text-generation-webui)."""

    def __init__(self, endpoint: str = "http://localhost:8080/v1", model: str = "local-model", api_key: str = "none"):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.api_key = api_key

    def _call(self, prompt: str) -> str:
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.endpoint}/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[AI unavailable: {e}]"

    def summarize(self, text: str) -> str:
        return self._call(f"Summarize the following hardware analysis notes in 2-3 sentences:\n\n{text}")

    def draft_finding(self, observations: str) -> str:
        return self._call(f"Draft a professional security finding from these observations:\n\n{observations}")

    def suggest_names(self, context: str) -> list[str]:
        result = self._call(f"Suggest 3 short component names for:\n\n{context}")
        return [line.strip("- ") for line in result.strip().split("\n") if line.strip()][:3]

    def assist_report(self, report_data: dict) -> str:
        return self._call(f"Write an executive summary for this report:\n\n{json.dumps(report_data, indent=2)}")

    def cluster_evidence(self, items: list[str]) -> list[dict]:
        result = self._call(f"Group these evidence items into logical clusters:\n\n{json.dumps(items)}")
        return [{"group": "ai-clustered", "items": items, "analysis": result}]


def get_adapter(settings: Optional[dict] = None) -> AIAdapter:
    """Factory: return the correct adapter based on settings."""
    if settings is None:
        return NoneAdapter()

    backend = settings.get("backend", "none")
    config = settings.get("config", {})

    if backend == "ollama":
        return OllamaAdapter(
            endpoint=config.get("endpoint", "http://localhost:11434"),
            model=config.get("model", "llama3"),
        )
    elif backend == "openai-compatible-local":
        return OpenAICompatibleAdapter(
            endpoint=config.get("endpoint", "http://localhost:8080/v1"),
            model=config.get("model", "local-model"),
            api_key=config.get("api_key", "none"),
        )
    else:
        return NoneAdapter()
