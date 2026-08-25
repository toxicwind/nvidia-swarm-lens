"""lens/profiles.py — Lens profiles with maximal NVIDIA NIM model support."""
from typing import Any, Dict, List, Optional, Tuple
import sys
sys.path.insert(0, "/workspace/nvidia-swarm")
from swarm.nvidia_swarm_agent import NvidiaAgent
from swarm.nvidia_swarm_core import SwarmDAG, AgentNode

MODEL_PRIMARY = "meta/llama-3.1-405b-instruct"
MODEL_MOE = "thinkingmachines/inkling"
MODEL_FAST = "meta/llama-3.1-70b-instruct"
MODEL_ANALYSIS = "nvidia/nemotron-4-340b-instruct"
MAX_OUTPUT_TOKENS = 16384
CONTEXT_WINDOW = 1048576
STREAM = True
TIMEOUT_SECONDS = 300
DEFAULT_TEMP = 0.2
DEFAULT_MAX_TOKENS = 16384

RESEARCH_LENS = NvidiaAgent(
    name="research_lens",
    system_prompt=("You are a Research Lens agent powered by NVIDIA Llama 3.1 405B. "
        "Your role is to gather, synthesize, and summarize information. "
        "You excel at web search, academic paper analysis, and fact verification. "
        "Always cite sources and flag uncertainties. You can write full complex code, "
        "mathematical proofs, and detailed technical analyses when requested."),
    model=MODEL_PRIMARY, temperature=DEFAULT_TEMP, max_tokens=DEFAULT_MAX_TOKENS,
    tools=[
        {"type": "function", "function": {"name": "web_search", "description": "Search the web",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "num_results": {"type": "integer", "default": 5}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "fetch_url", "description": "Fetch and summarize a URL",
            "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "max_length": {"type": "integer", "default": 2000}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "execute_python_zmq", "description": "Execute Python via ZMQ kernel bypass",
            "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer", "default": 30}}, "required": ["code"]}}},
    ],
    handoff_description="Research and information gathering with ZMQ bypass",
    handoff_targets=["code_lens", "analysis_lens"],
)

CODE_LENS = NvidiaAgent(
    name="code_lens",
    system_prompt=("You are a Code Lens agent powered by NVIDIA Llama 3.1 70B. "
        "Your role is to write, review, debug, and optimize code. "
        "You specialize in Python, Rust, Go, and systems programming. "
        "Always provide runnable code with comments and type hints. "
        "You can generate full applications, complex algorithms, mathematical proofs in code, "
        "and ridiculous things that actually work."),
    model=MODEL_FAST, temperature=0.1, max_tokens=DEFAULT_MAX_TOKENS,
    tools=[
        {"type": "function", "function": {"name": "execute_python_zmq", "description": "Execute Python via ZMQ kernel bypass",
            "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer", "default": 30}}, "required": ["code"]}}},
        {"type": "function", "function": {"name": "lint_code", "description": "Lint and type-check code",
            "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "language": {"type": "string", "default": "python"}}, "required": ["code"]}}},
        {"type": "function", "function": {"name": "mcp_filesystem", "description": "Access filesystem via MCP",
            "parameters": {"type": "object", "properties": {"command": {"type": "string"}, "args": {"type": "string"}}, "required": ["command"]}}},
    ],
    handoff_description="Code generation, review, and debugging with ZMQ",
    handoff_targets=["research_lens", "analysis_lens"],
)

ANALYSIS_LENS = NvidiaAgent(
    name="analysis_lens",
    system_prompt=("You are an Analysis Lens agent powered by NVIDIA Nemotron 4 340B. "
        "Your role is to analyze data, detect patterns, and produce actionable insights. "
        "You excel at statistical analysis, anomaly detection, and trend forecasting. "
        "Always show your work, include confidence intervals, and highlight risks."),
    model=MODEL_ANALYSIS, temperature=0.15, max_tokens=DEFAULT_MAX_TOKENS,
    tools=[
        {"type": "function", "function": {"name": "analyze_dataset", "description": "Analyze a dataset",
            "parameters": {"type": "object", "properties": {"data": {"type": "string"}, "analysis_type": {"type": "string", "enum": ["summary", "correlation", "regression", "anomaly"]}}, "required": ["data", "analysis_type"]}}},
        {"type": "function", "function": {"name": "visualize", "description": "Generate visualization description",
            "parameters": {"type": "object", "properties": {"data": {"type": "string"}, "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "heatmap"]}}, "required": ["data", "chart_type"]}}},
        {"type": "function", "function": {"name": "execute_python_zmq", "description": "Execute Python for data analysis via ZMQ",
            "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer", "default": 30}}, "required": ["code"]}}},
    ],
    handoff_description="Data analysis and insight generation with Nemotron",
    handoff_targets=["research_lens", "code_lens", "orchestrator_lens"],
)

ORCHESTRATOR_LENS = NvidiaAgent(
    name="orchestrator_lens",
    system_prompt=("You are an Orchestrator Lens agent powered by NVIDIA Llama 3.1 405B. "
        "Your role is to coordinate other agents, manage task decomposition, "
        "and ensure coherent multi-agent workflows. You decide which agent "
        "should handle each subtask and synthesize their outputs into a "
        "unified response. You are the conductor of the swarm."),
    model=MODEL_PRIMARY, temperature=0.25, max_tokens=DEFAULT_MAX_TOKENS,
    tools=[
        {"type": "function", "function": {"name": "delegate", "description": "Delegate a subtask to another agent",
            "parameters": {"type": "object", "properties": {"agent": {"type": "string", "enum": ["research_lens", "code_lens", "analysis_lens"]}, "task": {"type": "string"}, "context": {"type": "string"}}, "required": ["agent", "task"]}}},
        {"type": "function", "function": {"name": "synthesize", "description": "Synthesize outputs from multiple agents",
            "parameters": {"type": "object", "properties": {"outputs": {"type": "string"}, "goal": {"type": "string"}}, "required": ["outputs", "goal"]}}},
        {"type": "function", "function": {"name": "git_push_one", "description": "Push a single file to GitHub without git init",
            "parameters": {"type": "object", "properties": {"repo": {"type": "string"}, "filepath": {"type": "string"}, "message": {"type": "string"}}, "required": ["repo", "filepath"]}}},
    ],
    handoff_description="Task orchestration, synthesis, and git push",
    handoff_targets=["research_lens", "code_lens", "analysis_lens"],
)

PROOF_LENS = NvidiaAgent(
    name="proof_lens",
    system_prompt=("You are a Proof Lens agent powered by NVIDIA Llama 3.1 405B. "
        "Your role is to construct, verify, and explain mathematical proofs, "
        "formal verification, and logical arguments. You work in Lean, Coq, "
        "Isabelle, and Python-based proof assistants. You can generate "
        "ridiculously complex proofs that are fully rigorous and correct."),
    model=MODEL_PRIMARY, temperature=0.1, max_tokens=DEFAULT_MAX_TOKENS,
    tools=[
        {"type": "function", "function": {"name": "execute_python_zmq", "description": "Execute Python for symbolic math and proofs",
            "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer", "default": 60}}, "required": ["code"]}}},
    ],
    handoff_description="Mathematical proofs and formal verification",
    handoff_targets=["research_lens", "code_lens"],
)

ALL_LENS_PROFILES: Dict[str, NvidiaAgent] = {
    "research": RESEARCH_LENS, "code": CODE_LENS, "analysis": ANALYSIS_LENS,
    "orchestrator": ORCHESTRATOR_LENS, "proof": PROOF_LENS,
}

def build_swarm_from_lens(lens_names: List[str], dag_edges: Optional[List[Tuple[str, List[str]]]] = None) -> SwarmDAG:
    dag = SwarmDAG(name="lens_swarm")
    for name in lens_names:
        if name not in ALL_LENS_PROFILES:
            raise ValueError(f"Unknown lens: {name}. Available: {list(ALL_LENS_PROFILES.keys())}")
        agent = ALL_LENS_PROFILES[name]
        node = agent.to_core_node(agent_id=name)
        dag.add_node(node)
    if dag_edges:
        for source, targets in dag_edges:
            if source in dag.nodes:
                dag.nodes[source].handoff_targets = targets
                for t in targets:
                    if t in dag.nodes:
                        dag.nodes[t].dependencies.add(source)
    else:
        for name, agent in ALL_LENS_PROFILES.items():
            if name in dag.nodes:
                for target in agent.handoff_targets:
                    if target in dag.nodes:
                        dag.nodes[target].dependencies.add(name)
    return dag
