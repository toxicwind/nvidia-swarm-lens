"""
NVIDIA-NIM-Swarm Merger
Merges all 3 architectural options:
  1. Async DAG execution engine (Option 1)
  2. Native Llama 3.1 prompt engineering + grammar-constrained decoding (Option 2)
  3. Triton gRPC transport layer with persistent connections (Option 3)
"""
__version__ = "0.1.0"
from .nvidia_swarm_core import NvidiaSwarm, SwarmDAG, AgentNode
from .nvidia_swarm_agent import NvidiaAgent, Llama31PromptEngine, GrammarConstrainedDecoder
from .nvidia_swarm_transport import TritonTransport, NvidiaNIMClient, PersistentConnectionPool
