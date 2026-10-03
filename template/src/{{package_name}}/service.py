"""The answer flow: check the question, retrieve, ask the model, validate, log.

Every request writes one audit line (JSON) with what happened and what it cost, never the
question or answer text: the log can be shared with the people who run the service without
sharing what staff asked.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field

from . import documents, guardrails
from .config import Settings
from .llm import ChatModel, ModelError
from .retrieval import Index

audit = logging.getLogger(__name__ + ".audit")


@dataclass
class Citation:
    ref: str
    document: str
    title: str
    section: str


@dataclass
class Answer:
    status: str  # answered, not_found, rejected, error
    text: str
    citations: list[Citation] = field(default_factory=list)
    reason: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# The reason goes to the audit log and the API's `reason` field, never into the answer text:
# a rejected answer may contain exactly what must not be repeated (a planted link, for example).
WITHHELD = "No answer was released: it did not pass the checks. It has been logged for review."


class AnswerService:
    def __init__(self, settings: Settings, model: ChatModel):
        self.settings, self.model = settings, model
        passages, self.withheld = documents.load(settings.corpus_dir, settings.max_classification)
        self.index = Index(passages)
        self.passage_count = len(passages)

    def answer(self, question: str) -> Answer:
        start = time.perf_counter()
        try:
            q = guardrails.check_question(question, self.settings.max_question_chars)
        except guardrails.QuestionError as exc:
            return self._log(question, Answer("rejected", str(exc), reason=str(exc)), start, [])

        hits = self.index.search(q, self.settings.top_k, self.settings.min_score)
        if not hits:  # nothing relevant: no model call, no cost
            return self._log(
                q, Answer("not_found", "The approved documents do not cover this."), start, []
            )
        passages = [p for p, _ in hits]
        try:
            reply = self.model.complete(
                guardrails.SYSTEM_PROMPT,
                guardrails.build_prompt(q, passages),
                self.settings.max_answer_tokens,
            )
        except ModelError as exc:
            return self._log(
                q, Answer("error", "The model is not available.", reason=str(exc)), start, passages
            )

        verdict = guardrails.validate(reply.text, len(passages), self.settings.allowed_link_domains)
        usage = dict(
            model=reply.model, input_tokens=reply.input_tokens, output_tokens=reply.output_tokens
        )
        if verdict.status == "not_found":
            result = Answer("not_found", "The approved documents do not cover this.", **usage)
        elif verdict.status == "rejected":
            result = Answer("rejected", WITHHELD, reason=verdict.reason, **usage)
        else:
            cites = [passages[n - 1] for n in verdict.cited]
            result = Answer(
                "answered",
                reply.text,
                [Citation(p.id, p.doc_id, p.title, p.heading) for p in cites],
                **usage,
            )
        return self._log(q, result, start, passages)

    def _log(self, question: str, result: Answer, start: float, passages) -> Answer:
        result.latency_ms = int((time.perf_counter() - start) * 1000)
        audit.info(
            json.dumps(
                {
                    "event": "answer",
                    "question_sha": hashlib.sha256(question.encode("utf-8")).hexdigest()[:16],
                    "status": result.status,
                    "reason": result.reason,
                    "retrieved": [p.id for p in passages],
                    "cited": [c.ref for c in result.citations],
                    "model": result.model,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "latency_ms": result.latency_ms,
                }
            )
        )
        return result
