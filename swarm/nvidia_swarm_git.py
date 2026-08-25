"""nvidia_swarm_git.py — One-file git push without git init. Credit: toxicwind/token-recovery-20260824/git_push_helper.py."""
from __future__ import annotations
import os, subprocess, shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("nvidia_swarm.git")

@dataclass
class GitPushHelper:
    workspace: Path = field(default_factory=lambda: Path("/mnt/agents/output/repos"))
    pat: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    user_email: str = "toxicwind@users.noreply.github.com"
    user_name: str = "toxicwind"

    def __post_init__(self):
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _clone(self, repo: str) -> Path:
        repo_dir = self.workspace / repo
        if not (repo_dir / ".git").exists():
            url = f"https://toxicwind:{self.pat}@github.com/toxicwind/{repo}.git"
            result = subprocess.run(["git", "clone", "--depth", "1", url, str(repo_dir)], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError(f"Clone failed: {result.stderr[:200]}")
        return repo_dir

    def _set_identity(self, repo_dir: Path):
        subprocess.run(["git", "config", "user.email", self.user_email], cwd=str(repo_dir), capture_output=True)
        subprocess.run(["git", "config", "user.name", self.user_name], cwd=str(repo_dir), capture_output=True)

    def push_one(self, repo: str, filepath: Path, message: Optional[str] = None) -> bool:
        if not self.pat:
            raise RuntimeError("No GITHUB_TOKEN or PAT set")
        if not filepath.exists():
            raise FileNotFoundError(f"{filepath} not found")
        repo_dir = self._clone(repo)
        self._set_identity(repo_dir)
        target = repo_dir / filepath.name
        shutil.copy2(filepath, target)
        subprocess.run(["git", "add", str(target)], cwd=str(repo_dir), capture_output=True)
        msg = message or f"feat: add {filepath.name}"
        subprocess.run(["git", "commit", "-m", msg], cwd=str(repo_dir), capture_output=True, text=True)
        result = subprocess.run(["git", "push", "origin", "main"], cwd=str(repo_dir), capture_output=True, text=True, timeout=20)
        ok = result.returncode == 0
        if ok:
            logger.info(f"PUSHED {filepath.name} -> toxicwind/{repo}")
        return ok

    def push_all(self, repo: str, filepaths: list, message: Optional[str] = None) -> Dict[str, bool]:
        return {fp.name: self.push_one(repo, fp, message) for fp in filepaths}
