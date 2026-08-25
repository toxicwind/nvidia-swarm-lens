"""NVIDIA-NIM-Swarm Merger — All 3 Options + Integrations."""
__version__ = "0.2.0"
from .nvidia_swarm_core import NvidiaSwarm, SwarmDAG, AgentNode
from .nvidia_swarm_agent import NvidiaAgent, Llama31PromptEngine, GrammarConstrainedDecoder
from .nvidia_swarm_transport import TritonTransport, NvidiaNIMClient, PersistentConnectionPool
from .nvidia_swarm_zmq import ZMQEngine, ZMQTool, ZMQExecutionResult
from .nvidia_swarm_proxy import DaemonTunnel, SquidProxy, FlareSolverrGateway, ProxyStack
from .nvidia_swarm_mcp import MCPManager, MCPServer, MCP_REGISTRY
from .nvidia_swarm_git import GitPushHelper
from .nvidia_swarm_unshare import UnshareRoot
from .nvidia_swarm_envd import EnvdMimicry
