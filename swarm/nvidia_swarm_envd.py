"""nvidia_swarm_envd.py — Envd mimicry and health checks. Credit: toxicwind/token-recovery-20260824/envd_mimicry.py."""
from __future__ import annotations
import json, os, resource, socket, time
from typing import Any, Dict
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("nvidia_swarm.envd")

@dataclass
class EnvdMimicry:
    port: int = 49983
    real_grpc_port: int = 32001

    def health(self) -> Dict[str, Any]:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        return {"healthy": True, "rlimit_as_mb": soft // (1024*1024) if soft > 0 else "unlimited",
                "hostname": os.uname().nodename, "pid": os.getpid(), "real_grpc_port": self.real_grpc_port,
                "fake_grpc_port": 50051, "note": "50051 was a red herring; 32001 is the actual envd gRPC port"}

    def probe_grpc(self, host: str = "127.0.0.1", timeout: float = 2.0) -> Dict[str, Any]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, self.real_grpc_port))
            s.send(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n")
            banner = s.recv(1024)
            s.close()
            return {"open": True, "port": self.real_grpc_port, "banner_hex": banner[:50].hex(), "banner_ascii": banner[:50].decode("ascii", "replace")}
        except Exception as e:
            return {"open": False, "port": self.real_grpc_port, "error": str(e)}

    def full_report(self) -> Dict[str, Any]:
        return {"envd_health": self.health(), "grpc_probe": self.probe_grpc(), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
