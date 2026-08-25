"""nvidia_swarm_proxy.py — Daemon tunnel + Squid + FlareSolverr. Credit: toxicwind/proxy-stack-swarm-final."""
from __future__ import annotations
import asyncio, json, os, socket, subprocess, time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("nvidia_swarm.proxy")

@dataclass
class PortRelay:
    src_port: int
    dst_port: int
    pid: Optional[int] = field(default=None, repr=False)

    def start(self) -> int:
        cmd = ["socat", f"TCP-LISTEN:{self.src_port},fork,reuseaddr", f"TCP:127.0.0.1:{self.dst_port}"]
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.pid = p.pid
        time.sleep(0.5)
        return p.pid

    def stop(self):
        if self.pid:
            subprocess.run(["kill", str(self.pid)], capture_output=True)
            self.pid = None

    def is_active(self) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(("127.0.0.1", self.src_port))
            s.close()
            return True
        except Exception:
            return False

@dataclass
class DaemonTunnel:
    relays: List[PortRelay] = field(default_factory=list)
    _active: bool = field(default=False, repr=False)

    def __post_init__(self):
        self.relays = [PortRelay(80, 5901), PortRelay(443, 6080), PortRelay(5900, 5901), PortRelay(50051, 32001)]

    def start_all(self) -> Dict[str, Any]:
        results = {}
        for relay in self.relays:
            pid = relay.start()
            results[f"{relay.src_port}->{relay.dst_port}"] = {"pid": pid, "active": relay.is_active()}
        self._active = True
        return results

    def stop_all(self):
        for relay in self.relays:
            relay.stop()
        self._active = False

    def status(self) -> Dict[str, Any]:
        return {"active": self._active, "relays": {f"{r.src_port}->{r.dst_port}": {"pid": r.pid, "active": r.is_active()} for r in self.relays}}

@dataclass
class SquidProxy:
    host: str = "127.0.0.1"
    port: int = 53128
    username: str = "proxyuser"
    password: str = "b0lNSJ1Q2ZeiTf"
    def get_proxy_url(self) -> str:
        return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
    def is_reachable(self) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            s.connect((self.host, self.port))
            s.close()
            return True
        except Exception:
            return False

@dataclass
class FlareSolverrGateway:
    host: str = "127.0.0.1"
    port: int = 58088
    async def solve(self, url: str, method: str = "GET", max_timeout: int = 120000) -> Dict[str, Any]:
        payload = {"cmd": "request.get" if method == "GET" else "request.post", "url": url, "maxTimeout": max_timeout}
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(f"http://{self.host}:{self.port}/v1", json=payload) as resp:
                return await resp.json()
    def health(self) -> Dict[str, Any]:
        try:
            import urllib.request
            req = urllib.request.Request(f"http://{self.host}:{self.port}/health")
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())
        except Exception as e:
            return {"status": "error", "error": str(e)}

@dataclass
class ProxyStack:
    squid: SquidProxy = field(default_factory=SquidProxy)
    gateway: FlareSolverrGateway = field(default_factory=FlareSolverrGateway)
    tunnel: DaemonTunnel = field(default_factory=DaemonTunnel)

    def deploy(self) -> Dict[str, Any]:
        tunnel_status = self.tunnel.start_all()
        return {"tunnel": tunnel_status, "squid_reachable": self.squid.is_reachable(), "gateway_health": self.gateway.health(), "proxy_url": self.squid.get_proxy_url()}

    def teardown(self):
        self.tunnel.stop_all()

    def status(self) -> Dict[str, Any]:
        return {"tunnel": self.tunnel.status(), "squid_reachable": self.squid.is_reachable(), "gateway_health": self.gateway.health(), "proxy_url": self.squid.get_proxy_url()}
