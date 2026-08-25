"""nvidia_swarm_zmq.py — ZMQ Kernel Execution Engine. Credit: toxicwind/experimental-crisis."""
from __future__ import annotations
import zmq, json, hmac, hashlib, uuid, time, os, glob, traceback
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("nvidia_swarm.zmq")

@dataclass
class ZMQExecutionResult:
    status: str
    execution_count: Optional[int]
    stdout: List[str]
    stderr: List[str]
    display: List[Dict[str, Any]]
    error: Optional[Any]
    raw_messages: List[Dict[str, Any]]
    elapsed_ms: float

class ZMQEngine:
    def __init__(self, conn_file: Optional[str] = None):
        self.ctx = zmq.Context()
        self.shell: Optional[zmq.Socket] = None
        self.iopub: Optional[zmq.Socket] = None
        self.key: Optional[bytes] = None
        self.session = str(uuid.uuid4())
        self.conn_file = conn_file
        self._connect()
        self.exec_count = 0

    def _find_conn_file(self) -> str:
        if self.conn_file and os.path.exists(self.conn_file):
            return self.conn_file
        files = glob.glob("/tmp/tmp*.json")
        if not files:
            raise RuntimeError("No kernel connection file found")
        return max(files, key=os.path.getmtime)

    def _connect(self):
        conn_path = self._find_conn_file()
        with open(conn_path) as f:
            conn = json.load(f)
        self.key = conn["key"].encode()
        shell_addr = f"{conn['transport']}://{conn['ip']}:{conn['shell_port']}"
        iopub_addr = f"{conn['transport']}://{conn['ip']}:{conn['iopub_port']}"
        self.shell = self.ctx.socket(zmq.DEALER)
        self.shell.connect(shell_addr)
        self.iopub = self.ctx.socket(zmq.SUB)
        self.iopub.connect(iopub_addr)
        self.iopub.setsockopt_string(zmq.SUBSCRIBE, "")
        logger.info(f"ZMQ connected to kernel at {shell_addr}")

    def _sign(self, msg_list: List[bytes]) -> str:
        auth = hmac.new(self.key, digestmod=hashlib.sha256)
        for m in msg_list:
            auth.update(m if isinstance(m, bytes) else m.encode())
        return auth.hexdigest()

    def _make_msg(self, msg_type: str, content: Dict[str, Any]) -> List[bytes]:
        header = json.dumps({"msg_id": str(uuid.uuid4()), "username": "kernel", "session": self.session,
                             "msg_type": msg_type, "version": "5.3", "date": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        parent, metadata, content_json = json.dumps({}), json.dumps({}), json.dumps(content)
        msg_list = [header, parent, metadata, content_json]
        signature = self._sign(msg_list)
        return [b"<IDS|MSG>", signature.encode(), header.encode(), parent.encode(), metadata.encode(), content_json.encode()]

    def execute(self, code: str, timeout: float = 30.0) -> ZMQExecutionResult:
        self.exec_count += 1
        content = {"code": code, "silent": False, "store_history": True, "user_expressions": {}, "allow_stdin": False}
        self.shell.send_multipart(self._make_msg("execute_request", content))
        poller = zmq.Poller()
        poller.register(self.shell, zmq.POLLIN)
        poller.register(self.iopub, zmq.POLLIN)
        results = {"status": None, "execution_count": None, "stdout": [], "stderr": [], "display": [], "error": None, "raw_messages": []}
        t0 = time.perf_counter()
        while time.perf_counter() - t0 < timeout:
            socks = dict(poller.poll(500))
            if self.shell in socks:
                resp = self.shell.recv_multipart()
                results["raw_messages"].append({"source": "shell", "parts": [p[:200] for p in resp]})
                if len(resp) >= 6:
                    try:
                        header = json.loads(resp[2].decode())
                        content = json.loads(resp[5].decode())
                        if header.get("msg_type") == "execute_reply":
                            results["status"] = content.get("status")
                            results["execution_count"] = content.get("execution_count")
                            if results["status"] == "ok":
                                break
                    except Exception as e:
                        results["error"] = f"shell parse: {e}"
            if self.iopub in socks:
                resp = self.iopub.recv_multipart()
                if len(resp) >= 6:
                    try:
                        offset = 0 if resp[0] == b"<IDS|MSG>" else 1
                        header = json.loads(resp[offset + 2].decode())
                        content = json.loads(resp[offset + 5].decode())
                        msg_type = header.get("msg_type", "")
                        if msg_type == "stream":
                            name, text = content.get("name", ""), content.get("text", "")
                            if name == "stdout":
                                results["stdout"].append(text)
                            elif name == "stderr":
                                results["stderr"].append(text)
                        elif msg_type in ("execute_result", "display_data"):
                            results["display"].append(content.get("data", {}))
                        elif msg_type == "error":
                            results["error"] = content
                    except Exception:
                        pass
        elapsed = (time.perf_counter() - t0) * 1000
        return ZMQExecutionResult(status=results["status"] or "timeout", execution_count=results["execution_count"],
            stdout=results["stdout"], stderr=results["stderr"], display=results["display"], error=results["error"],
            raw_messages=results["raw_messages"], elapsed_ms=elapsed)

    def execute_with_capture(self, code: str, timeout: float = 30.0) -> Dict[str, Any]:
        result = self.execute(code, timeout)
        return {"status": result.status, "stdout": "".join(result.stdout), "stderr": "".join(result.stderr),
                "display": result.display, "error": result.error, "elapsed_ms": result.elapsed_ms, "execution_count": result.execution_count}

    def close(self):
        if self.shell:
            self.shell.close()
        if self.iopub:
            self.iopub.close()
        self.ctx.term()

class ZMQTool:
    def __init__(self, engine: Optional[ZMQEngine] = None):
        self.engine = engine or ZMQEngine()

    def to_tool_schema(self) -> Dict[str, Any]:
        return {"type": "function", "function": {"name": "execute_python_zmq",
            "description": "Execute Python via direct ZMQ kernel bypass. Bypasses tool budget. Use for complex computations, proofs, data analysis.",
            "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout": {"type": "integer", "default": 30}}, "required": ["code"]}}}

    async def run(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        return self.engine.execute_with_capture(code, timeout)
