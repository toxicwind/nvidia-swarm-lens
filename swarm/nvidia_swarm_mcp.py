"""nvidia_swarm_mcp.py — MCP server integration. Credit: toxicwind/token-recovery-20260824/mcp_helper.py."""
from __future__ import annotations
import json, os, subprocess
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger("nvidia_swarm.mcp")

MCP_REGISTRY: Dict[str, str] = {
    "filesystem": "modelcontextprotocol/server-filesystem",
    "github": "modelcontextprotocol/server-github",
    "postgres": "modelcontextprotocol/server-postgres",
    "sqlite": "modelcontextprotocol/server-sqlite",
    "git": "modelcontextprotocol/server-git",
    "fetch": "modelcontextprotocol/server-fetch",
    "puppeteer": "modelcontextprotocol/server-puppeteer",
}

@dataclass
class MCPServer:
    name: str
    repo: str
    install_dir: Path = field(default_factory=lambda: Path("/mnt/agents/output/workspace/mcp"))
    _installed: bool = field(default=False, repr=False)

    def install(self, pat: Optional[str] = None) -> bool:
        target = self.install_dir / self.name
        target.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        if pat:
            env["GITHUB_TOKEN"] = pat
        result = subprocess.run(["git", "clone", "--depth", "1", f"https://github.com/{self.repo}.git", str(target)],
                                capture_output=True, text=True, timeout=60, env=env)
        self._installed = result.returncode == 0
        return self._installed

    def get_config(self) -> Dict[str, Any]:
        target = self.install_dir / self.name
        return {"name": self.name, "repo": self.repo, "path": str(target), "installed": self._installed or target.exists()}

@dataclass
class MCPManager:
    servers: Dict[str, MCPServer] = field(default_factory=dict)
    install_dir: Path = field(default_factory=lambda: Path("/mnt/agents/output/workspace/mcp"))

    def __post_init__(self):
        for name, repo in MCP_REGISTRY.items():
            self.servers[name] = MCPServer(name=name, repo=repo, install_dir=self.install_dir)

    def install_all(self, pat: Optional[str] = None) -> Dict[str, bool]:
        return {name: server.install(pat) for name, server in self.servers.items()}

    def install(self, name: str, pat: Optional[str] = None) -> bool:
        if name not in self.servers:
            raise ValueError(f"Unknown MCP: {name}. Available: {list(MCP_REGISTRY.keys())}")
        return self.servers[name].install(pat)

    def list_servers(self) -> List[Dict[str, Any]]:
        return [s.get_config() for s in self.servers.values()]

    def to_tool_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for name, server in self.servers.items():
            if server.get_config()["installed"]:
                schemas.append({"type": "function", "function": {"name": f"mcp_{name}",
                    "description": f"Invoke MCP {name} server", "parameters": {"type": "object",
                    "properties": {"command": {"type": "string"}, "args": {"type": "string"}}, "required": ["command"]}}})
        return schemas
