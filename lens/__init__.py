"""Lens profiles for NVIDIA Swarm agents with maximal model support."""
from .profiles import (
    RESEARCH_LENS, CODE_LENS, ANALYSIS_LENS, ORCHESTRATOR_LENS, PROOF_LENS,
    ALL_LENS_PROFILES, build_swarm_from_lens,
    MODEL_PRIMARY, MODEL_MOE, MODEL_FAST, MODEL_ANALYSIS,
    MAX_OUTPUT_TOKENS, CONTEXT_WINDOW, STREAM, TIMEOUT_SECONDS,
)
from .profile import LensProfile
from .loader import discover_lenses, load_lens_module
