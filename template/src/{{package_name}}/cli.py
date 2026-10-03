"""Command line: ask, serve, eval, and a stand-in model server for demos and CI."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__, evaluation
from .config import Settings
from .llm import OpenAICompatibleModel, RecordingModel, ReplayMiss, StandInModel
from .service import AnswerService


def build_model(args: argparse.Namespace, settings: Settings):
    if args.model == "standin":
        return StandInModel()
    live = None
    if args.model == "live":
        live = OpenAICompatibleModel(
            settings.model_base_url, settings.model_name, settings.model_api_key, settings.timeout_s
        )
    if getattr(args, "recordings", None):
        return RecordingModel(live, Path(args.recordings), offline=args.model == "replay")
    if live is None:
        sys.exit("--model replay needs --recordings")
    return live


def cmd_ask(args, settings):
    service = AnswerService(settings, build_model(args, settings))
    result = service.answer(args.question)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.text)
        for c in result.citations:
            print(f"  [{c.ref}] {c.title}, {c.section}")
    return 0 if result.status in {"answered", "not_found"} else 1


def cmd_eval(args, settings):
    service = AnswerService(settings, build_model(args, settings))
    try:
        summary = evaluation.run(service, evaluation.load_cases(Path(args.cases)))
    except ReplayMiss as exc:
        print(f"replay miss: {exc}", file=sys.stderr)
        return 2
    print(evaluation.report(summary))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    ok = summary["pass_rate"] >= args.min_pass and summary["safety_failures"] == 0
    return 0 if ok else 1


def cmd_serve(args, settings):
    import uvicorn

    from .api import create_app

    app = create_app(AnswerService(settings, build_model(args, settings)))
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


def cmd_standin_model(args, settings):
    """Serve the stand-in model over the OpenAI chat API, for the demo container profile."""
    model = StandInModel()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # health check
            self._send(200, {"status": "ok", "model": model.name})

        def do_POST(self):
            if not self.path.endswith("/chat/completions"):
                return self._send(404, {"error": "not found"})
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            msgs = {m["role"]: m["content"] for m in body.get("messages", [])}
            reply = model.complete(msgs.get("system", ""), msgs.get("user", ""))
            self._send(
                200,
                {
                    "model": model.name,
                    "choices": [
                        {"index": 0, "message": {"role": "assistant", "content": reply.text}}
                    ],
                    "usage": {
                        "prompt_tokens": reply.input_tokens,
                        "completion_tokens": reply.output_tokens,
                    },
                },
            )

        def _send(self, code, payload):
            data = json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    print(f"stand-in model on {args.host}:{args.port} (not a language model)", file=sys.stderr)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-v", "--verbose", action="store_true", help="print the audit log")
    sub = parser.add_subparsers(dest="command", required=True)

    def model_options(p, default="live"):
        p.add_argument(
            "--model",
            choices=["live", "standin", "replay"],
            default=default,
            help="live: the configured endpoint (Ollama by default); standin: "
            "deterministic, no model; replay: recorded replies only",
        )
        p.add_argument("--recordings", help="folder to record live replies to, or replay from")

    p = sub.add_parser("ask", help="answer one question")
    p.add_argument("question")
    p.add_argument("--json", action="store_true")
    model_options(p)
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("eval", help="run the evaluation cases")
    p.add_argument("--cases", default="evals/cases.jsonl")
    p.add_argument("--out", help="write the results as JSON")
    p.add_argument("--min-pass", type=float, default=1.0)
    model_options(p, default="standin")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("serve", help="run the HTTP API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    model_options(p)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("standin-model", help="serve the stand-in model (demo and CI)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=11500)
    p.set_defaults(func=cmd_standin_model)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
        stream=sys.stderr,
    )
    return args.func(args, Settings.from_env())


if __name__ == "__main__":
    raise SystemExit(main())
