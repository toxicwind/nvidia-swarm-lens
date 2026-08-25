"""
nvidia_swarm_core.py
Async DAG execution engine for NVIDIA NIM Swarm.
Replaces the serial OpenAI Swarm run() with a parallelized
Directed Acyclic Graph execution engine tailored for
Llama 3.1 405B inference speeds.
"""
from __future__ import annotations
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger("nvidia_swarm.core")


@dataclass
class AgentNode:
    """A node in the Swarm DAG representing a single agent invocation."""
    agent_id: str
    name: str
    system_prompt: str
    tools: List[Dict[str, Any]] = field(default_factory=list)
    model: str = "meta/llama-3.1-405b-instruct"
    temperature: float = 0.3
    max_tokens: int = 4096
    dependencies: Set[str] = field(default_factory=set)
    handoff_targets: List[str] = field(default_factory=list)
    _result: Optional[Dict[str, Any]] = field(default=None, repr=False)
    _status: str = field(default="pending", repr=False)
    _latency_ms: float = field(default=0.0, repr=False)
    _ttft_ms: float = field(default=0.0, repr=False)  # Time To First Token
    _tps: float = field(default=0.0, repr=False)  # Tokens Per Second

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "model": self.model,
            "dependencies": list(self.dependencies),
            "handoff_targets": self.handoff_targets,
            "status": self._status,
            "latency_ms": self._latency_ms,
            "ttft_ms": self._ttft_ms,
            "tps": self._tps,
        }


class SwarmDAG:
    """Directed Acyclic Graph for parallel agent execution."""

    def __init__(self, name: str = "swarm_dag"):
        self.name = name
        self.nodes: Dict[str, AgentNode] = {}
        self.edges: Dict[str, Set[str]] = {}  # agent_id -> set of downstream agent_ids
        self._lock = asyncio.Lock()

    def add_node(self, node: AgentNode) -> "SwarmDAG":
        self.nodes[node.agent_id] = node
        if node.agent_id not in self.edges:
            self.edges[node.agent_id] = set()
        for dep in node.dependencies:
            if dep not in self.edges:
                self.edges[dep] = set()
            self.edges[dep].add(node.agent_id)
        return self

    def topological_sort(self) -> List[List[str]]:
        """Return layers of agent_ids that can execute in parallel."""
        in_degree = {aid: len(n.dependencies) for aid, n in self.nodes.items()}
        layers: List[List[str]] = []
        remaining = set(self.nodes.keys())
        while remaining:
            layer = [aid for aid in remaining if in_degree[aid] == 0]
            if not layer:
                raise ValueError("Cycle detected in SwarmDAG")
            layers.append(layer)
            for aid in layer:
                remaining.remove(aid)
                for downstream in self.edges.get(aid, set()):
                    in_degree[downstream] -= 1
        return layers

    def get_ready_nodes(self, completed: Set[str]) -> List[AgentNode]:
        ready = []
        for aid, node in self.nodes.items():
            if node._status != "pending":
                continue
            if node.dependencies.issubset(completed):
                ready.append(node)
        return ready


class NvidiaSwarm:
    """
    High-concurrency NVIDIA NIM Swarm orchestrator.
    Saturates NVIDIA token-per-second capabilities via:
    - asyncio non-blocking I/O
    - Parallel DAG layer execution
    - Persistent connection pooling
    - Active batching where supported
    """

    def __init__(
        self,
        transport: Any,
        max_concurrent: int = 50,
        batch_size: int = 8,
        enable_batching: bool = True,
    ):
        self.transport = transport
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.enable_batching = enable_batching
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._metrics: List[Dict[str, Any]] = []

    async def run_dag(
        self,
        dag: SwarmDAG,
        initial_messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a SwarmDAG with maximal parallelism."""
        context = context or {}
        completed: Set[str] = set()
        all_results: Dict[str, Any] = {}
        start_time = time.perf_counter()

        layers = dag.topological_sort()
        logger.info(f"DAG '{dag.name}' has {len(dag.nodes)} nodes across {len(layers)} layers")

        for layer_idx, layer in enumerate(layers):
            layer_start = time.perf_counter()
            tasks = []
            for aid in layer:
                node = dag.nodes[aid]
                # Merge context + upstream results into messages
                msgs = self._build_messages(node, initial_messages, all_results, context)
                tasks.append(self._execute_node(node, msgs, context))

            if self.enable_batching and len(tasks) > 1:
                # Batch parallel agents of the same model for KV-cache efficiency
                batched = self._batch_tasks(tasks)
                results = await asyncio.gather(*batched, return_exceptions=True)
            else:
                results = await asyncio.gather(*tasks, return_exceptions=True)

            for aid, res in zip(layer, results):
                if isinstance(res, Exception):
                    dag.nodes[aid]._status = "error"
                    logger.error(f"Node {aid} failed: {res}")
                    all_results[aid] = {"error": str(res)}
                else:
                    dag.nodes[aid]._status = "completed"
                    dag.nodes[aid]._result = res
                    all_results[aid] = res
                    completed.add(aid)

            layer_elapsed = (time.perf_counter() - layer_start) * 1000
            logger.info(f"Layer {layer_idx} completed in {layer_elapsed:.1f}ms")

        total_elapsed = (time.perf_counter() - start_time) * 1000
        return {
            "dag_name": dag.name,
            "total_latency_ms": total_elapsed,
            "layers_executed": len(layers),
            "nodes_completed": len(completed),
            "results": all_results,
            "node_metrics": {aid: n.to_dict() for aid, n in dag.nodes.items()},
        }

    async def _execute_node(
        self,
        node: AgentNode,
        messages: List[Dict[str, str]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with self._semaphore:
            t0 = time.perf_counter()
            try:
                response = await self.transport.chat_completion(
                    model=node.model,
                    messages=messages,
                    tools=node.tools if node.tools else None,
                    temperature=node.temperature,
                    max_tokens=node.max_tokens,
                )
                t1 = time.perf_counter()
                latency = (t1 - t0) * 1000
                node._latency_ms = latency
                # Extract TTFT and TPS from response headers if available
                node._ttft_ms = response.get("_ttft_ms", 0.0)
                node._tps = response.get("_tps", 0.0)
                self._metrics.append({
                    "agent_id": node.agent_id,
                    "latency_ms": latency,
                    "ttft_ms": node._ttft_ms,
                    "tps": node._tps,
                })
                return {
                    "agent_id": node.agent_id,
                    "content": response.get("content", ""),
                    "tool_calls": response.get("tool_calls", []),
                    "model": node.model,
                    "latency_ms": latency,
                }
            except Exception as e:
                logger.exception(f"Node {node.agent_id} execution failed")
                raise

    def _build_messages(
        self,
        node: AgentNode,
        initial_messages: List[Dict[str, str]],
        upstream_results: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        msgs = [{"role": "system", "content": node.system_prompt}]
        msgs.extend(initial_messages)
        # Inject upstream results as context
        for dep in node.dependencies:
            if dep in upstream_results:
                res = upstream_results[dep]
                if "content" in res:
                    msgs.append({"role": "user", "content": f"[Output from {dep}]: {res['content']}"})
        if context:
            msgs.append({"role": "user", "content": f"[Context]: {json.dumps(context, default=str)}"})
        return msgs

    def _batch_tasks(self, tasks: List[Coroutine]) -> List[Coroutine]:
        """Group tasks for active batching where the transport supports it."""
        # For now, return as-is; transport handles batching internally
        return tasks

    def get_metrics(self) -> List[Dict[str, Any]]:
        return self._metrics.copy()

    def get_aggregate_metrics(self) -> Dict[str, float]:
        if not self._metrics:
            return {}
        latencies = [m["latency_ms"] for m in self._metrics]
        ttfts = [m["ttft_ms"] for m in self._metrics if m["ttft_ms"] > 0]
        tps_vals = [m["tps"] for m in self._metrics if m["tps"] > 0]
        return {
            "avg_latency_ms": sum(latencies) / len(latencies),
            "max_latency_ms": max(latencies),
            "min_latency_ms": min(latencies),
            "avg_ttft_ms": sum(ttfts) / len(ttfts) if ttfts else 0.0,
            "avg_tps": sum(tps_vals) / len(tps_vals) if tps_vals else 0.0,
            "total_invocations": len(self._metrics),
        }
