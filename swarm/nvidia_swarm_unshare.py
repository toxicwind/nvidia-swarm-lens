"""nvidia_swarm_unshare.py — Wrap commands in unshare root namespace. Credit: toxicwind/token-recovery-20260824/unshare_root_fix.py."""
from __future__ import annotations
import os, subprocess
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger("nvidia_swarm.unshare")

@dataclass
class UnshareRoot:
    unshare_bin: str = "/usr/bin/unshare"

    def __post_init__(self):
        if not os.path.exists(self.unshare_bin):
            fallback = "/mnt/agents/dot/bin/unshare"
            if os.path.exists(fallback):
                self.unshare_bin = fallback
            else:
                raise FileNotFoundError(f"unshare not found")

    def run(self, cmd: List[str], cwd: str = ".") -> subprocess.CompletedProcess:
        args = [self.unshare_bin, "--user", "--pid", "--fork", "--mount-proc", "--map-root-user"] + cmd
        logger.info(f"unshare root: {' '.join(cmd)}")
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True)

    def run_shell(self, script: str, cwd: str = ".") -> subprocess.CompletedProcess:
        return self.run(["bash", "-c", script], cwd=cwd)
