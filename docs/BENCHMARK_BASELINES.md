# Benchmark Baselines

## Prior Art

### 1. llm-serving-benchmark (deepaksatna)
- **What:** Direct NIM vs vLLM/SGLang/TGI comparison on Kubernetes
- **Result:** NIM achieves 31.70 tok/s (Llama-3-8B on A10), 10-18% higher than alternatives
- **Our delta:** They benchmark single-model inference; we benchmark multi-agent concurrent DAG execution

### 2. NIMStats (MauroDruwel)
- **What:** Automated hourly benchmarks for 20+ NIM models with live dashboard
- **Result:** 163.3 TPS average, 90.6% uptime, top model: nemotron-3-nano-omni-30b
- **Our delta:** They measure models in isolation; we measure agent-to-agent handoff latency

### 3. exemplar-performance (NVIDIA official)
- **What:** Official recipes for Llama 3.1 405B pretraining and inference at scale
- **Result:** 256-512 GB200 GPUs for pretraining, 32-40 GPUs for TRT-LLM Dynamo inference
- **Our delta:** They benchmark data-parallel training; we benchmark task-parallel agent inference

### 4. triton-perf_analyzer (NVIDIA official)
- **What:** gRPC/async inference benchmarking tool
- **Result:** 407.866 infer/sec at concurrency 1, p99 latency 4172 usec
- **Our delta:** They benchmark raw endpoints; we benchmark agent-level orchestration

## Our Targets

| Metric | Target | Baseline |
|--------|--------|----------|
| Agent handoff latency | < 100ms | N/A (new metric) |
| Single-model throughput | > 3100 tok/s | 31.70 tok/s (8B baseline) |
| Concurrent agents | 16 parallel | 1 (serial baseline) |
| Grammar decode success | 100% first-try | ~85% (OpenAI retry logic) |
| Context packing efficiency | 95%+ KV-cache hit | ~60% (naive truncation) |

## Methodology

1. Deploy NIM Llama 3.1 405B on H100
2. Run `llm-serving-benchmark` single-model baseline
3. Overlay `NvidiaSwarmDAG` with 16 concurrent agents
4. Measure: throughput, latency, KV-cache efficiency, grammar decode accuracy
