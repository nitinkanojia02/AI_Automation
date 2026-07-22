from dataclasses import dataclass
import os


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class FeatureFlags:
    enable_workflow_contracts: bool = _env_flag("ENABLE_WORKFLOW_CONTRACTS", True)
    enable_extended_navigation: bool = _env_flag("ENABLE_EXTENDED_NAVIGATION", False)
    enable_resource_reuse_agent: bool = _env_flag("ENABLE_RESOURCE_REUSE_AGENT", False)
    enable_rag: bool = _env_flag("ENABLE_RAG", False)
    enable_agents: bool = _env_flag("ENABLE_AGENTS", False)
    enable_execution_plan_persistence: bool = _env_flag("ENABLE_EXECUTION_PLAN_PERSISTENCE", True)
    enable_state_merge: bool = _env_flag("ENABLE_STATE_MERGE", False)
    enable_mcp: bool = _env_flag("ENABLE_MCP", False)


FEATURE_FLAGS = FeatureFlags()
