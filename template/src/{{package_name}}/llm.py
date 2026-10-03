"""Model access through one contract: the OpenAI-compatible chat API.

Ollama, vLLM, llama.cpp's server, LM Studio, LLM gateways and the major cloud providers all
speak it, so moving between a laptop, an on-premises GPU server and a cloud deployment is a
change of URL and model name, not of code.

- `OpenAICompatibleModel` calls any such endpoint.
- `StandInModel` is not a language model: it answers deterministically by quoting the source
  that best overlaps the question. CI and the demo profile use it, so the whole service builds,
  tests and evaluates with no key, no GPU and no network. It tests the plumbing and the
  guardrails, never answer quality.
- `RecordingModel` records a live run to disk and replays it offline, so a real evaluation
  against a local model can be committed and re-checked in CI for free.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import httpx


class ModelError(RuntimeError):
    pass


class ReplayMiss(ModelError):
    """Offline replay found no recording: the run must fail rather than silently change."""


@dataclass
class Reply:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    replayed: bool = False


class ChatModel(Protocol):
    name: str

    def complete(self, system: str, user: str, max_tokens: int = 400) -> Reply: ...


class OpenAICompatibleModel:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout_s: float = 180.0,
        client: httpx.Client | None = None,
    ):
        self.name = model
        self.url = base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.client = client or httpx.Client(timeout=timeout_s, headers=headers)

    def complete(self, system: str, user: str, max_tokens: int = 400) -> Reply:
        body = {
            "model": self.name,
            "temperature": 0,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        start = time.perf_counter()
        try:
            response = self.client.post(self.url, json=body)
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"] or ""
        except httpx.HTTPError as exc:
            raise ModelError(f"model endpoint {self.url}: {exc}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise ModelError(f"unexpected reply from {self.url}") from exc
        usage = data.get("usage") or {}
        return Reply(
            text=text.strip(),
            model=self.name,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            latency_ms=int((time.perf_counter() - start) * 1000),
        )


WORD = re.compile(r"[a-z0-9]+")
SOURCE = re.compile(r'<source id="(S\d+)"[^>]*>\n?(.*?)\n?</source>', re.S)


class StandInModel:
    """Deterministic stand-in: quotes the first sentence of the best-overlapping source."""

    name = "standin"

    def complete(self, system: str, user: str, max_tokens: int = 400) -> Reply:
        question = user.split("Question:", 1)[-1].split("\n", 1)[0]
        q_words = set(WORD.findall(question.lower())) - {"the", "a", "of", "to", "do", "i"}
        best, best_overlap = None, 0
        for sid, text in SOURCE.findall(user):
            overlap = len(q_words & set(WORD.findall(text.lower())))
            if overlap > best_overlap:
                best, best_overlap = (sid, text), overlap
        if best is None or best_overlap < 2:
            answer = "NOT_FOUND"
        else:
            body = best[1].split(": ", 1)[-1].strip()  # drop the "title, section:" label
            sentence = re.split(r"(?<=[.!?])\s+", body)[0]
            answer = f"{sentence} [{best[0]}]"
        return Reply(answer, self.name, len(user) // 4, len(answer) // 4, 0)


class RecordingModel:
    """Records live replies in a folder (one folder per model) and replays them offline.

    The key is a hash of the prompt, so a change to the prompt, the sources or the retrieval
    shows up as a replay miss in CI instead of a silently different result.
    """

    def __init__(self, inner: ChatModel | None, folder: Path, offline: bool = False):
        if inner is None and not offline:
            raise ValueError("a live model is needed unless replaying offline")
        self.inner, self.folder, self.offline = inner, folder, offline
        self.name = inner.name if inner else f"replay:{folder.name}"

    @staticmethod
    def key(system: str, user: str, max_tokens: int) -> str:
        blob = json.dumps([system, user, max_tokens], ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]

    def complete(self, system: str, user: str, max_tokens: int = 400) -> Reply:
        path = self.folder / f"{self.key(system, user, max_tokens)}.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return Reply(**{**data, "replayed": True})
        if self.offline or self.inner is None:
            raise ReplayMiss(f"no recording {path.name} in {self.folder}; record a live run first")
        reply = self.inner.complete(system, user, max_tokens)
        self.folder.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(reply), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return reply
