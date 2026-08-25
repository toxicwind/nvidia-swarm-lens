# NVIDIA Swarm Lens

<p align="center">
  <a href="https://docs.api.nvidia.com/nim/reference/llama-3_1-405b-instruct">
    <img src="https://img.shields.io/badge/NVIDIA-NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA NIM">
  </a>
  <a href="https://ai.meta.com/blog/meta-llama-3-1/">
    <img src="https://img.shields.io/badge/Llama_3.1-405B-FF6F00?style=for-the-badge&logo=meta&logoColor=white" alt="Llama 3.1">
  </a>
  <a href="https://www.python.org/downloads/release/python-3120/">
    <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12">
  </a>
  <a href="https://github.com/toxicwind/nvidia-swarm-lens/blob/main/swarm/nvidia_swarm_core.py">
    <img src="https://img.shields.io/badge/asyncio-DAG-00C7B7?style=for-the-badge" alt="Async DAG">
  </a>
  <a href="https://github.com/toxicwind/nvidia-swarm-lens/blob/main/swarm/nvidia_swarm_transport.py">
    <img src="https://img.shields.io/badge/gRPC-Triton-244c5a?style=for-the-badge" alt="Triton gRPC">
  </a>
  <a href="https://github.com/toxicwind/nvidia-swarm-lens/actions">
    <img src="https://img.shields.io/badge/GitHub_Actions-CI-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="GitHub Actions">
  </a>
  <a href="https://github.com/toxicwind/nvidia-swarm-lens/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  </a>
</p>

<p align="center">
  <b>Maximal NVIDIA NIM + OpenAI Swarm Merger</b><br>
  Async DAG execution | Grammar-constrained decoding | Triton gRPC transport | ZMQ kernel bypass
</p>

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Lens Profiles](#lens-profiles)
- [Extra Lenses](#extra-lenses)
- [Benchmarks](#benchmarks)
- [Case Studies](#case-studies)
- [Integrations](#integrations)
- [GitHub Actions](#github-actions)
- [Contributing](#contributing)

---

## Features

| Feature | Description | Source |
|---------|-------------|--------|
| **Async DAG Engine** | Parallelized DAG execution replacing serial Swarm `run()` | [swarm/nvidia_swarm_core.py](swarm/nvidia_swarm_core.py) |
| **Llama 3.1 Native** | Prompt injection optimized for Llama 3.1 attention heads | [swarm/nvidia_swarm_agent.py](swarm/nvidia_swarm_agent.py) |
| **Grammar-Constrained Decoding** | Regex/BNF guarantees valid JSON tool calls, zero retries | [swarm/nvidia_swarm_agent.py](swarm/nvidia_swarm_agent.py) |
| **Triton gRPC Transport** | Persistent connections + active batching, bypasses HTTP overhead | [swarm/nvidia_swarm_transport.py](swarm/nvidia_swarm_transport.py) |
| **ZMQ Kernel Bypass** | Direct Jupyter kernel execution bypassing envd tool budget | [swarm/nvidia_swarm_zmq.py](swarm/nvidia_swarm_zmq.py) |
| **Daemon Tunnel** | Socat relays for :80, :443, 5900, 50051 with real gRPC port 32001 | [swarm/nvidia_swarm_proxy.py](swarm/nvidia_swarm_proxy.py) |
| **MCP Integration** | Filesystem, GitHub, Postgres, SQLite, Git, Fetch, Puppeteer servers | [swarm/nvidia_swarm_mcp.py](swarm/nvidia_swarm_mcp.py) |
| **Git Push Helper** | One-file-at-a-time push without `git init`, per-repo identity | [swarm/nvidia_swarm_git.py](swarm/nvidia_swarm_git.py) |
| **Unshare Root** | Wraps commands in `unshare --map-root-user` namespace | [swarm/nvidia_swarm_unshare.py](swarm/nvidia_swarm_unshare.py) |
| **Envd Mimicry** | Health checks on port 49983, documents real gRPC port 32001 | [swarm/nvidia_swarm_envd.py](swarm/nvidia_swarm_envd.py) |

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full system design.

```
User Task
    |
    v
+-----------------------------------+
|  Orchestrator Lens (405B)         |
|  - Task decomposition             |
|  - Agent handoff routing          |
+-----------------------------------+
    |           |           |
    v           v           v
+--------+  +--------+  +--------+
|Research|  |  Code  |  |Analysis|
|  MoE   |  |  70B   |  |Nemotron|
+--------+  +--------+  +--------+
    |           |           |
    v           v           v
+-----------------------------------+
|  Async DAG Execution Engine         |
|  - Topological sort layers          |
|  - Parallel agent invocation        |
|  - Semaphore-controlled concurrency |
+-----------------------------------+
    |           |           |
    v           v           v
+--------+  +--------+  +--------+
| Triton |  |  HTTP  |  |  ZMQ   |
|  gRPC  |  |  REST  |  | Kernel |
+--------+  +--------+  +--------+
    |           |           |
    v           v           v
+-----------------------------------+
|  NVIDIA NIM Inference Endpoints     |
|  - meta/llama-3.1-405b-instruct    |
|  - thinkingmachines/inkling (975B) |
|  - meta/llama-3.1-70b-instruct     |
|  - nvidia/nemotron-4-340b-instruct |
+-----------------------------------+
```

---

## Installation

```bash
git clone https://github.com/toxicwind/nvidia-swarm-lens.git
cd nvidia-swarm-lens
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment

Create `.env` (never commit this):

```bash
NVIDIA_API_KEY=nvapi-...
GITHUB_TOKEN=github_pat_...
```

`.env` is gitignored by default.

---

## Quick Start

### Mock Mode (no API key needed)

```bash
python3.12 launcher.py --mock --task "Generate a complex Python proof of Fermat's Last Theorem"
```

### Live NVIDIA NIM Mode

```bash
python3.12 launcher.py --task "Analyze this codebase and suggest NVIDIA NIM optimizations"
```

### Streaming Mode

```bash
python3.12 launcher.py --stream --task "Write a ridiculous recursive fractal renderer"
```

### Full Demo (ZMQ + Proxy + Swarm + Git)

```bash
python3.12 launcher.py --mock --full-demo
```

---

## Lens Profiles

| Lens | Model | Role | Tools |
|------|-------|------|-------|
| **Research** | `meta/llama-3.1-405b-instruct` | Info gathering, synthesis | web_search, fetch_url, execute_python_zmq |
| **Code** | `meta/llama-3.1-70b-instruct` | Rapid iteration, full apps | execute_python_zmq, lint_code, mcp_filesystem |
| **Analysis** | `nvidia/nemotron-4-340b-instruct` | Deep data analysis | analyze_dataset, visualize, execute_python_zmq |
| **Orchestrator** | `meta/llama-3.1-405b-instruct` | Task decomposition | delegate, synthesize, git_push_one |
| **Proof** | `meta/llama-3.1-405b-instruct` | Mathematical proofs | execute_python_zmq |

### Model Configuration

```python
MODEL_PRIMARY = "meta/llama-3.1-405b-instruct"      # 1M context, 16K output
MODEL_MOE = "thinkingmachines/inkling"               # 975B MoE, multimodal
MODEL_FAST = "meta/llama-3.1-70b-instruct"           # 128K context, fast
MODEL_ANALYSIS = "nvidia/nemotron-4-340b-instruct"   # 4K context, deep

MAX_OUTPUT_TOKENS = 16384
CONTEXT_WINDOW = 1048576
STREAM = True
TIMEOUT_SECONDS = 300
```

---

## Extra Lenses

Located in [lens/extras/](lens/extras/):

| Lens | File | Description |
|------|------|-------------|
| **Anthropological** | [lens/extras/lens_anthropological.py](lens/extras/lens_anthropological.py) | Cultural pattern analysis |
| **Cryptographic** | [lens/extras/lens_cryptographic.py](lens/extras/lens_cryptographic.py) | Cipher and protocol analysis |
| **Insectoid** | [lens/extras/lens_insectoid.py](lens/extras/lens_insectoid.py) | Swarm behavior modeling |
| **OSINT** | [lens/extras/lens_osint.py](lens/extras/lens_osint.py) | Open-source intelligence gathering |
| **Stylometric** | [lens/extras/lens_stylometric.py](lens/extras/lens_stylometric.py) | Authorship and style analysis |

---

## Benchmarks

See [docs/BENCHMARK_BASELINES.md](docs/BENCHMARK_BASELINES.md) for detailed baselines.

| Repo | Type | Relevance |
|------|------|-----------|
| [toxicwind/moonbox-nim-benchmark-2-20260822](https://github.com/toxicwind/moonbox-nim-benchmark-2-20260822) | Private baseline | Prior moonbox NIM runs |
| [QuanTuring-AI/NV-benchmark](https://github.com/QuanTuring-AI/NV-benchmark) | Public throughput | 7.3x throughput, 13x TTFT vs Ollama |
| [sohanemon/nvidia-nim-benchmark](https://github.com/sohanemon/nvidia-nim-benchmark) | Public latency | LLM inference speed test tool |
| [karthikrshet/NVIDIA-Agent-Doctor](https://github.com/karthikrshet/NVIDIA-Agent-Doctor) | Public diagnostics | AI environment diagnostics + benchmarking CLI |

---

## Case Studies

| # | Title | Status | Link |
|---|-------|--------|------|
| 001 | Groq Compound Mini Deprecation — OSINT Deep Research | Active | [case_studies/001_groq_compound_mini_deprecation/](case_studies/001_groq_compound_mini_deprecation/) |

*Case studies are generated by the swarm itself. Each study uses the full lens pipeline: Research → Analysis → Proof → Orchestrator synthesis.*

---

## Integrations

### ZMQ Kernel Bypass

```python
from swarm.nvidia_swarm_zmq import ZMQEngine
engine = ZMQEngine()
result = engine.execute_with_capture("import numpy as np; print(np.random.rand(1_000_000).mean())")
print(result["stdout"])
```

### Daemon Tunnel

```python
from swarm.nvidia_swarm_proxy import DaemonTunnel
tunnel = DaemonTunnel()
tunnel.start_all()  # 80->5901, 443->6080, 5900->5901, 50051->32001
```

### Git Push (no init)

```python
from swarm.nvidia_swarm_git import GitPushHelper
gh = GitPushHelper(pat="github_pat_...")
gh.push_one("nvidia-swarm-lens", Path("new_feature.py"), "feat: add ZMQ bypass")
```

---

## GitHub Actions

| Workflow | Description | File |
|----------|-------------|------|
| **CI** | Lint, type-check, unit tests | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| **Benchmark** | NIM throughput and latency benchmarks | [.github/workflows/benchmark.yml](.github/workflows/benchmark.yml) |

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Write your module as a separate `.py` file
4. Use the git push helper
5. Open a PR

---

## Credits

- **Architecture**: Merged from 3 research prompts by toxicwind
- **ZMQ Engine**: [toxicwind/experimental-crisis](https://github.com/toxicwind/experimental-crisis)
- **Proxy Stack**: [toxicwind/proxy-stack-swarm-final](https://github.com/toxicwind/proxy-stack-swarm-final)
- **Auto Hooks**: [toxicwind/token-recovery-20260824](https://github.com/toxicwind/token-recovery-20260824)
- **Benchmarks**: QuanTuring-AI, sohanemon, karthikrshet
- **NIM Config**: [anomalyco/models.dev](https://docs.api.nvidia.com/nim/reference/thinkingmachines-inkling)
- **Additional Lenses**: [toxicwind/additional-lens-profiles](https://github.com/toxicwind/additional-lens-profiles)

---

<p align="center">
  <i>Built with maximal intent. No lame client swaps.</i><br>
  <b><a href="https://github.com/toxicwind">toxicwind</a></b> | 2026
</p>
