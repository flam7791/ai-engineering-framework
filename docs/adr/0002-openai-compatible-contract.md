# ADR 0002: The OpenAI-compatible API is the model contract

Status: accepted · 2026-10

## Context

Services must move between a laptop, an on-premises GPU server, a gateway and cloud providers
without rewrites, and the model market changes every quarter.

## Decision

Applications call models only through the OpenAI-compatible chat and embeddings API, normally
through the gateway. Provider SDKs are used only inside the gateway, or in a service where a
feature is not portable, recorded as a decision.

## Consequences

- Ollama, vLLM, llama.cpp, LM Studio, LiteLLM, the gateway and the main cloud providers are
  interchangeable by configuration.
- Features outside the common subset (some tool-use formats, provider-specific caching) need an
  adapter, as governed-agents does for Claude's native tool use.
