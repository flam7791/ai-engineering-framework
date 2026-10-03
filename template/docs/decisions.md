# Design decisions

Short records: the decision, why, and what would change it.

## D1. A local open-weight model is the default

Most questions are about internal documents. Running the model locally means the default
configuration sends nothing outside, needs no key and costs nothing per question. Quality and
latency are measured by the recorded evaluation, not assumed.
**Revisit when** the recorded evaluation shows a local model failing cases a larger model passes
and the documents allow an external endpoint: route through the gateway instead.

## D2. The model contract is the OpenAI-compatible chat API

Ollama, vLLM, llama.cpp, gateways and cloud providers all speak it, so the same code runs on a
laptop, an on-premises GPU server or a cloud deployment.
**Revisit when** a needed feature (structured output, tool use) is not portable across them.

## D3. Keyword retrieval first

BM25 is explainable, instant and needs no model. It is enough for a curated corpus of short
policy documents.
**Revisit when** the not-found rate shows paraphrases missing: add local embeddings and fuse
the rankings.

## D4. Documents above the ceiling are never loaded

Filtering at query time would leave restricted text one bug away from a prompt. Not loading it
removes the risk instead of managing it.

## D5. The validator decides what is released

The prompt asks for citations; the code checks them. An answer without a valid citation, or
with a link outside the allowed domains, is withheld with a reason.

## D6. A deterministic stand-in model for CI

CI must not depend on a model, a key or a GPU. The stand-in tests the plumbing and the
guardrails; answer quality comes from recorded live runs that CI replays.
