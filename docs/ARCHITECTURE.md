# Architecture

## Design Principles

1. **Async-first:** Every agent runs via `asyncio` with `aiohttp` HTTP/2 persistent connections
2. **DAG execution:** Replace serial `run()` with parallelized directed acyclic graph
3. **Grammar-constrained decoding:** Regex/BNF guarantees valid JSON tool calls, no retry logic
4. **Lens profiles:** Each agent type (researcher/coder/analyst/orchestrator) has optimized model selection, temperature, KV-cache strategy
5. **Stateless transport:** Context windows packed for optimal KV-cache, agents exist as packed prompts

## Component Diagram

```
User Task
    │
    ▼
┌─────────────────┐
│  Orchestrator   │──► Lens profile: orchestrator (405B, temp=0.4)
│   (405B NIM)    │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬────────────┐
    ▼         ▼            ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Research│ │ Analyst│ │ Coder  │ │ Monitor│
│  405B  │ │  70B   │ │  405B  │ │  8B    │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
    │          │          │          │
    └──────────┴──────────┴──────────┘
              │
              ▼
    ┌─────────────────────┐
    │  NvidiaSwarmDAG     │
    │  (max_concurrent=16)│
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
┌─────────────┐   ┌─────────────┐
│ HTTP/2 Pool │   │ gRPC Triton │
│ (aiohttp)   │   │ (fallback)  │
└──────┬──────┘   └──────┬──────┘
       │                 │
       └────────┬────────┘
                ▼
        ┌───────────────┐
        │ NVIDIA NIM    │
        │ Llama 3.1 405B│
        └───────────────┘
```

## KV-Cache Strategies

| Profile | Strategy | Description |
|---------|----------|-------------|
| Researcher | `sliding` | 20-turn window, discards oldest |
| Coder | `full` | Complete context, 128k token budget |
| Analyst | `sink` | Sink tokens (256) + recent context |
| Orchestrator | `full` | Complete DAG state tracking |

## Grammar-Constrained Decoding

Instead of OpenAI's function calling API (which retries on invalid JSON), we use regex grammars:

```python
grammar = (
    r'\{\s*"tool"\s*:\s*"(web_search|web_open_url|ipython)"\s*,\s*'
    r'"params"\s*:\s*\{[^}]*\}\s*\}'
)
```

This is passed as `extra_body={"grammar": grammar}` to NVIDIA NIM, guaranteeing valid JSON on first decode.
