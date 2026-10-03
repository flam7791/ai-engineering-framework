"""HTTP API: GET /health and POST /answer."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .service import AnswerService


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


def create_app(service: AnswerService) -> FastAPI:
    app = FastAPI(title="Answer service", version="0.1.0", docs_url=None, redoc_url=None)

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "model": service.model.name,
            "max_classification": service.settings.max_classification,
            "passages": service.passage_count,
            "documents_withheld_above_ceiling": service.withheld,
        }

    @app.post("/answer")
    def answer(q: Question) -> dict:
        result = service.answer(q.question)
        if result.status == "error":
            raise HTTPException(status_code=503, detail=result.text)
        return result.to_dict()

    return app
