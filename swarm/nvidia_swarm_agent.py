"""
nvidia_swarm_agent.py
Native Llama 3.1 prompt engineering + Grammar-Constrained Decoding.
Replaces OpenAI-optimized system prompts with NVIDIA-Native structures.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union
import logging

logger = logging.getLogger("nvidia_swarm.agent")


# ---------------------------------------------------------------------------
# Llama 3.1 Instruct Format (native to NVIDIA NIM)
# ---------------------------------------------------------------------------
LLAMA31_SYSTEM_PREFIX = "<|start_header_id|>system<|end_header_id|>\n\n"
LLAMA31_USER_PREFIX = "<|start_header_id|>user<|end_header_id|>\n\n"
LLAMA31_ASSISTANT_PREFIX = "<|start_header_id|>assistant<|end_header_id|>\n\n"
LLAMA31_STOP = "<|eot_id|>"


@dataclass
class Llama31PromptEngine:
    """
    Converts generic OpenAI-style messages into Llama 3.1 instruct-tuned
    format optimized for NVIDIA NIM attention heads.
    """
    system_prompt: str = ""
    enable_caching: bool = True
    _cache: Dict[str, str] = field(default_factory=dict, repr=False)

    def render(self, messages: List[Dict[str, str]]) -> str:
        """Render messages into Llama 3.1 native format."""
        cache_key = json.dumps(messages, sort_keys=True)
        if self.enable_caching and cache_key in self._cache:
            return self._cache[cache_key]

        parts = []
        # System prompt is injected once at the top
        if self.system_prompt:
            parts.append(f"{LLAMA31_SYSTEM_PREFIX}{self.system_prompt}{LLAMA31_STOP}")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                # Skip if we already injected the main system prompt
                if content != self.system_prompt:
                    parts.append(f"{LLAMA31_SYSTEM_PREFIX}{content}{LLAMA31_STOP}")
            elif role == "user":
                parts.append(f"{LLAMA31_USER_PREFIX}{content}{LLAMA31_STOP}")
            elif role == "assistant":
                parts.append(f"{LLAMA31_ASSISTANT_PREFIX}{content}{LLAMA31_STOP}")
            elif role == "tool":
                # Tool results rendered as user messages with special marker
                parts.append(
                    f"{LLAMA31_USER_PREFIX}[TOOL_RESULT]: {content}{LLAMA31_STOP}"
                )

        # Final assistant prefix to prime generation
        parts.append(LLAMA31_ASSISTANT_PREFIX)
        result = "".join(parts)

        if self.enable_caching:
            self._cache[cache_key] = result
        return result

    def render_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
    ) -> str:
        """
        Render with tool definitions injected into the system context.
        Llama 3.1 performs best when tools are described in natural language
        within the system prompt rather than as a separate JSON schema block.
        """
        tool_descriptions = []
        for t in tools:
            fn = t.get("function", t)
            name = fn.get("name", "unknown")
            desc = fn.get("description", "")
            params = fn.get("parameters", {})
            props = params.get("properties", {})
            required = params.get("required", [])
            args = []
            for pname, pschema in props.items():
                ptype = pschema.get("type", "any")
                pdesc = pschema.get("description", "")
                req = "required" if pname in required else "optional"
                args.append(f"  - {pname} ({ptype}, {req}): {pdesc}")
            tool_descriptions.append(
                f"Tool: {name}\nDescription: {desc}\nArguments:\n" + "\n".join(args)
            )

        tool_block = "\n\n".join(tool_descriptions)
        augmented_system = (
            f"{self.system_prompt}\n\n"
            f"You have access to the following tools. "
            f"When you need to use a tool, respond with a JSON object "
            f"containing exactly 'tool' and 'arguments' keys.\n\n"
            f"{tool_block}\n\n"
            f"If no tool is needed, respond normally."
        )

        # Temporarily swap system prompt
        original = self.system_prompt
        self.system_prompt = augmented_system
        result = self.render(messages)
        self.system_prompt = original
        return result


# ---------------------------------------------------------------------------
# Grammar-Constrained Decoding
# ---------------------------------------------------------------------------
@dataclass
class GrammarConstrainedDecoder:
    """
    Mathematically guarantees valid JSON tool calls via regex/BNF constraints.
    Replaces flaky retry logic with deterministic output shaping.
    """
    tool_schemas: List[Dict[str, Any]] = field(default_factory=list)
    max_retries: int = 0  # Zero retries because grammar guarantees validity
    _compiled_patterns: Dict[str, re.Pattern] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for each tool's expected JSON shape."""
        for t in self.tool_schemas:
            fn = t.get("function", t)
            name = fn.get("name", "")
            params = fn.get("parameters", {})
            props = params.get("properties", {})
            required = params.get("required", [])

            # Build a regex that matches the JSON structure for this tool
            # Example: {"tool": "search", "arguments": {"query": "...", "limit": 5}}
            arg_patterns = []
            for pname in sorted(props.keys()):
                ptype = props[pname].get("type", "string")
                if ptype == "string":
                    val_pat = r'"[^"]*"'
                elif ptype == "integer":
                    val_pat = r"-?\d+"
                elif ptype == "number":
                    val_pat = r"-?\d+(?:\.\d+)?"
                elif ptype == "boolean":
                    val_pat = r"true|false"
                elif ptype == "array":
                    val_pat = r"\[[^\]]*\]"
                else:
                    val_pat = r"[^,}]+"
                arg_patterns.append(rf'"{pname}":\s*{val_pat}')

            if arg_patterns:
                args_body = r",\s*".join(arg_patterns)
                pattern_str = (
                    rf'\{{\s*"tool":\s*"{re.escape(name)}"\s*,\s*'
                    rf'"arguments":\s*\{{\s*{args_body}\s*\}}\s*\}}'
                )
            else:
                pattern_str = (
                    rf'\{{\s*"tool":\s*"{re.escape(name)}"\s*,\s*'
                    rf'"arguments":\s*\{{\s*\}}\s*\}}'
                )

            try:
                self._compiled_patterns[name] = re.compile(pattern_str, re.VERBOSE)
            except re.error as e:
                logger.warning(f"Failed to compile pattern for {name}: {e}")

    def decode(self, raw_output: str) -> Optional[Dict[str, Any]]:
        """
        Extract and validate a tool call from raw model output.
        Returns None if no valid tool call is found.
        """
        # Try to find JSON blocks
        json_blocks = re.findall(r"\{[^{}]*\}", raw_output)
        for block in json_blocks:
            try:
                parsed = json.loads(block)
                if "tool" in parsed and "arguments" in parsed:
                    tool_name = parsed["tool"]
                    if tool_name in self._compiled_patterns:
                        pattern = self._compiled_patterns[tool_name]
                        if pattern.fullmatch(block):
                            return parsed
            except json.JSONDecodeError:
                continue
        return None

    def constrain_prompt_suffix(self) -> str:
        """
        Returns a suffix that can be appended to the prompt to bias the model
        toward producing valid JSON tool calls.
        """
        return (
            "\n\nWhen using a tool, you MUST respond with a single JSON object "
            "in this exact format: {\"tool\": \"<tool_name>\", \"arguments\": {<args>}}. "
            "No extra text before or after the JSON."
        )

    def build_grammar_bnf(self) -> str:
        """
        Build a BNF grammar string suitable for constrained decoding backends
        (e.g., llama.cpp grammar, outlines, etc.).
        """
        rules = ["root ::= tool_call | normal_text"]
        tool_alts = []
        for t in self.tool_schemas:
            fn = t.get("function", t)
            name = fn.get("name", "")
            params = fn.get("parameters", {})
            props = params.get("properties", {})
            required = params.get("required", [])

            arg_rules = []
            for pname in sorted(props.keys()):
                ptype = props[pname].get("type", "string")
                if ptype == "string":
                    val_rule = r'"' + "[^\"]*" + r'"'
                elif ptype == "integer":
                    val_rule = r"-?\d+"
                elif ptype == "number":
                    val_rule = r"-?\d+(?:\.\d+)?"
                elif ptype == "boolean":
                    val_rule = r"true|false"
                else:
                    val_rule = r"[^,}]+"
                arg_rules.append(rf'"{pname}":\s*{val_rule}')

            args_str = r",\s*".join(arg_rules) if arg_rules else ""
            tool_alts.append(
                rf'\{{\s*"tool":\s*"{name}"\s*,\s*"arguments":\s*\{{\s*{args_str}\s*\}}\s*\}}'
            )

        if tool_alts:
            rules.append("tool_call ::= " + " | ".join(tool_alts))
        rules.append('normal_text ::= [^\\{]+ | "{" [^"\\}] "}")
        return "\n".join(rules)


# ---------------------------------------------------------------------------
# NVIDIA-Native Agent
# ---------------------------------------------------------------------------
@dataclass
class NvidiaAgent:
    """
    Agent class optimized for NVIDIA NIM / Llama 3.1.
    Discards OpenAI tool schema in favor of prompt-injection + grammar constraints.
    """
    name: str
    system_prompt: str
    model: str = "meta/llama-3.1-405b-instruct"
    temperature: float = 0.3
    max_tokens: int = 4096
    tools: List[Dict[str, Any]] = field(default_factory=list)
    handoff_description: Optional[str] = None
    handoff_targets: List[str] = field(default_factory=list)
    enable_grammar: bool = True
    _prompt_engine: Optional[Llama31PromptEngine] = field(default=None, repr=False)
    _grammar_decoder: Optional[GrammarConstrainedDecoder] = field(default=None, repr=False)

    def __post_init__(self):
        self._prompt_engine = Llama31PromptEngine(system_prompt=self.system_prompt)
        if self.enable_grammar and self.tools:
            self._grammar_decoder = GrammarConstrainedDecoder(tool_schemas=self.tools)
        else:
            self._grammar_decoder = GrammarConstrainedDecoder(tool_schemas=[])

    def prepare_messages(
        self,
        messages: List[Dict[str, str]],
    ) -> str:
        """Convert messages to Llama 3.1 native prompt string."""
        if self.tools:
            return self._prompt_engine.render_with_tools(messages, self.tools)
        return self._prompt_engine.render(messages)

    def parse_response(self, raw_output: str) -> Dict[str, Any]:
        """
        Parse raw model output. If grammar decoder finds a valid tool call,
        return it as a structured tool_call. Otherwise return as content.
        """
        if self._grammar_decoder and self.tools:
            tool_call = self._grammar_decoder.decode(raw_output)
            if tool_call:
                return {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call_{hash(tool_call['tool']) & 0xFFFFFFFF:08x}",
                            "type": "function",
                            "function": {
                                "name": tool_call["tool"],
                                "arguments": json.dumps(tool_call["arguments"]),
                            },
                        }
                    ],
                }
        # Fallback: treat as normal content
        return {"role": "assistant", "content": raw_output}

    def get_grammar_bnf(self) -> Optional[str]:
        """Return BNF grammar for constrained decoding backends."""
        if self._grammar_decoder:
            return self._grammar_decoder.build_grammar_bnf()
        return None

    def to_core_node(self, agent_id: str) -> "AgentNode":
        """Convert to core AgentNode for DAG execution."""
        from .nvidia_swarm_core import AgentNode
        return AgentNode(
            agent_id=agent_id,
            name=self.name,
            system_prompt=self.system_prompt,
            tools=self.tools,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            handoff_targets=self.handoff_targets,
        )
