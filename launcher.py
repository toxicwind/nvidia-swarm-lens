#!/usr/bin/env python3.12
"""launcher.py — Main entry point for NVIDIA Swarm Lens."""
from __future__ import annotations
import asyncio, json, os, sys, time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from swarm.nvidia_swarm_core import NvidiaSwarm, SwarmDAG
from swarm.nvidia_swarm_agent import NvidiaAgent
from swarm.nvidia_swarm_transport import NvidiaNIMClient
from swarm.nvidia_swarm_zmq import ZMQEngine, ZMQTool
from swarm.nvidia_swarm_proxy import ProxyStack, DaemonTunnel
from swarm.nvidia_swarm_mcp import MCPManager
from swarm.nvidia_swarm_git import GitPushHelper
from swarm.nvidia_swarm_unshare import UnshareRoot
from swarm.nvidia_swarm_envd import EnvdMimicry
from lens.profiles import ALL_LENS_PROFILES, build_swarm_from_lens

class MockTransport:
    async def chat_completion(self, **kwargs) -> Dict[str, Any]:
        model = kwargs.get("model", "mock")
        messages = kwargs.get("messages", [])
        await asyncio.sleep(0.05)
        last = messages[-1]["content"] if messages else ""
        return {"content": f"[MOCK {model}] Processed: {last[:80]}...", "tool_calls": [],
                "_ttft_ms": 12.0, "_tps": 4200.0, "_latency_ms": 50.0, "transport": "mock"}
    async def stream_completion(self, **kwargs):
        yield {"type": "token", "content": "Mock", "accumulated": "Mock"}
        yield {"type": "token", "content": " response", "accumulated": "Mock response"}
        yield {"type": "done", "accumulated": "Mock response complete.", "latency_ms": 50.0}
    async def close(self): pass

class SwarmLauncher:
    def __init__(self, use_mock: bool = False, api_key: Optional[str] = None):
        self.use_mock = use_mock
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.pat = os.getenv("GITHUB_TOKEN", "")
        self.swarm: Optional[NvidiaSwarm] = None
        self.transport: Optional[Any] = None
        self.zmq: Optional[ZMQEngine] = None
        self.proxy: Optional[ProxyStack] = None
        self.mcp: Optional[MCPManager] = None
        self.git: Optional[GitPushHelper] = None
        self.unshare: Optional[UnshareRoot] = None
        self.envd: Optional[EnvdMimicry] = None
        self._metrics_log: List[Dict[str, Any]] = []

    async def init(self):
        if self.use_mock or not self.api_key:
            print("[LAUNCHER] MOCK transport")
            self.transport = MockTransport()
        else:
            print("[LAUNCHER] LIVE NVIDIA NIM transport")
            self.transport = NvidiaNIMClient(api_key=self.api_key)
        self.swarm = NvidiaSwarm(transport=self.transport, max_concurrent=50)
        try:
            self.zmq = ZMQEngine()
            print("[LAUNCHER] ZMQ engine connected")
        except Exception as e:
            print(f"[LAUNCHER] ZMQ unavailable: {e}")
        self.proxy = ProxyStack()
        proxy_status = self.proxy.deploy()
        print(f"[LAUNCHER] Proxy stack: {proxy_status}")
        self.mcp = MCPManager()
        self.git = GitPushHelper(pat=self.pat)
        self.unshare = UnshareRoot()
        self.envd = EnvdMimicry()
        print(f"[LAUNCHER] Envd health: {self.envd.health()}")

    async def run_task(self, task: str, lens_names: List[str] = None, context: Optional[Dict[str, Any]] = None, stream: bool = False) -> Dict[str, Any]:
        lens_names = lens_names or ["research", "code", "analysis", "orchestrator"]
        context = context or {}
        context["user_task"] = task
        context["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        context["envd_health"] = self.envd.health() if self.envd else {}
        context["proxy_status"] = self.proxy.status() if self.proxy else {}
        dag = build_swarm_from_lens(lens_names)
        messages = [{"role": "user", "content": task}]
        print(f"[LAUNCHER] Task: {task[:100]}...")
        print(f"[LAUNCHER] Lenses: {lens_names}")
        print(f"[LAUNCHER] DAG layers: {len(dag.topological_sort())}")
        if stream:
            print("[LAUNCHER] Streaming...")
            orch = ALL_LENS_PROFILES.get("orchestrator")
            if orch:
                async for chunk in self.transport.stream_completion(messages=messages):
                    if chunk["type"] == "token":
                        print(chunk["content"], end="", flush=True)
                    elif chunk["type"] == "done":
                        print(f"\n[LAUNCHER] Stream done ({chunk['latency_ms']:.0f}ms)")
                        return {"streamed": True, "final": chunk["accumulated"]}
        result = await self.swarm.run_dag(dag, messages, context)
        agg = self.swarm.get_aggregate_metrics()
        self._metrics_log.append({"task": task[:200], "lenses": lens_names,
            "total_latency_ms": result["total_latency_ms"], "aggregate": agg})
        print(f"[LAUNCHER] DAG done in {result['total_latency_ms']:.1f}ms")
        print(f"[LAUNCHER] Avg TTFT: {agg.get('avg_ttft_ms', 0):.1f}ms | Avg TPS: {agg.get('avg_tps', 0):.0f}")
        return result

    async def generate_readme(self, repo_url: str) -> str:
        task = (f"Generate a stunning README.md for {repo_url}. Include NVIDIA NIM badges, Llama 3.1 badge, "
                "async DAG badge, Python 3.12 badge, MIT license badge. Use shields.io. "
                "Structure: Title, Badges, Features, Installation, Quick Start, Architecture, Lens Profiles, Benchmarks, Contributing.")
        result = await self.run_task(task, lens_names=["research", "code"])
        for aid, res in result.get("results", {}).items():
            if "content" in res and res["content"]:
                return res["content"]
        return "# NVIDIA Swarm Lens\n\nGenerated by swarm."

    async def run_zmq_demo(self) -> Dict[str, Any]:
        if not self.zmq:
            return {"error": "ZMQ not available"}
        code = "import numpy as np, sys\nprint(f'Python {sys.version}')\nprint(f'NumPy mean of 1M randoms: {np.random.rand(1_000_000).mean():.6f}')"
        result = self.zmq.execute_with_capture(code, timeout=10)
        print(f"[LAUNCHER] ZMQ demo: {result['status']} in {result['elapsed_ms']:.0f}ms")
        print(f"[LAUNCHER] stdout: {result['stdout'][:200]}")
        return result

    async def run_git_demo(self) -> bool:
        if not self.git or not self.pat:
            print("[LAUNCHER] Git demo skipped (no PAT)")
            return False
        test_file = Path("/tmp/swarm_test.txt")
        test_file.write_text(f"Swarm test {time.time()}")
        return self.git.push_one("nvidia-swarm-lens", test_file, "test: swarm git push demo")

    async def close(self):
        if self.transport:
            await self.transport.close()
        if self.zmq:
            self.zmq.close()
        if self.proxy:
            self.proxy.teardown()

    def save_metrics(self, path: str = "swarm_metrics.json"):
        with open(path, "w") as f:
            json.dump(self._metrics_log, f, indent=2, default=str)
        print(f"[LAUNCHER] Metrics saved to {path}")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="NVIDIA Swarm Lens Launcher")
    parser.add_argument("--mock", action="store_true", help="Use mock transport")
    parser.add_argument("--task", type=str, default="", help="Task to run")
    parser.add_argument("--lenses", type=str, default="research,code,analysis,orchestrator", help="Comma-separated lens names")
    parser.add_argument("--stream", action="store_true", help="Enable streaming")
    parser.add_argument("--readme", action="store_true", help="Generate README.md")
    parser.add_argument("--repo-url", type=str, default="https://github.com/toxicwind/nvidia-swarm-lens", help="Repo URL")
    parser.add_argument("--zmq-demo", action="store_true", help="Run ZMQ bypass demo")
    parser.add_argument("--proxy-demo", action="store_true", help="Run proxy stack demo")
    parser.add_argument("--git-demo", action="store_true", help="Run git push demo")
    parser.add_argument("--full-demo", action="store_true", help="Run all demos")
    args = parser.parse_args()
    launcher = SwarmLauncher(use_mock=args.mock)
    await launcher.init()
    try:
        if args.full_demo:
            print("\n=== ZMQ DEMO ===")
            await launcher.run_zmq_demo()
            print("\n=== PROXY DEMO ===")
            print(launcher.proxy.status() if launcher.proxy else {})
            print("\n=== SWARM TASK ===")
            result = await launcher.run_task(
                "Write a complex Python function that computes the Mandelbrot set using NumPy vectorization, then prove its correctness with a mathematical argument.",
                lens_names=["research", "code", "proof"])
            for aid, res in result.get("results", {}).items():
                print(f"\n--- {aid} ---")
                print(res.get("content", "")[:800])
            print("\n=== GIT DEMO ===")
            await launcher.run_git_demo()
        elif args.zmq_demo:
            await launcher.run_zmq_demo()
        elif args.git_demo:
            await launcher.run_git_demo()
        elif args.readme:
            readme = await launcher.generate_readme(args.repo_url)
            with open("README.md", "w") as f:
                f.write(readme)
            print("[LAUNCHER] README.md generated")
        elif args.task:
            result = await launcher.run_task(args.task, lens_names=args.lenses.split(","), stream=args.stream)
            print(json.dumps(result, indent=2, default=str))
        else:
            result = await launcher.run_task(
                "Analyze the current codebase structure and suggest optimizations for NVIDIA NIM inference throughput.",
                lens_names=["research", "code", "analysis"])
            print("\n=== RESULT ===")
            for aid, res in result.get("results", {}).items():
                print(f"\n--- {aid} ---")
                print(res.get("content", "")[:500])
    finally:
        launcher.save_metrics()
        await launcher.close()

if __name__ == "__main__":
    asyncio.run(main())
