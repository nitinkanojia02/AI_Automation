from dataclasses import dataclass
from typing import Any

from app.repositories.mcp_repository import McpRepository


@dataclass(frozen=True)
class McpRuntimeContext:
    enabled: bool
    provider: str = ""
    endpoint: str = ""
    transport: str = ""
    capability_scope: tuple[str, ...] = ()
    adapter_mode: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "transport": self.transport,
            "capabilityScope": list(self.capability_scope),
            "adapterMode": self.adapter_mode,
        }


class McpService:
    def __init__(self, enabled: bool = False, repository: McpRepository | None = None):
        self.enabled = enabled
        self.repository = repository

    def build_runtime_context(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = config if isinstance(config, dict) else {}
        if not payload and self.repository is not None:
            payload = self.repository.load_runtime_config()
        provider = str(payload.get("provider", "")).strip()
        endpoint = str(payload.get("endpoint", "")).strip()
        transport = str(payload.get("transport", "")).strip()
        capability_scope = tuple(
            str(item).strip()
            for item in payload.get("capabilityScope", [])
            if str(item).strip()
        ) if isinstance(payload.get("capabilityScope", []), list) else ()
        runtime_context = McpRuntimeContext(
            enabled=bool(self.enabled),
            provider=provider,
            endpoint=endpoint,
            transport=transport,
            capability_scope=capability_scope,
            adapter_mode="config_backed_runtime_context" if self.enabled else "disabled",
        ).to_dict()
        if self.repository is not None:
            runtime_context["provenance"] = self.repository.get_runtime_snapshot()
        return runtime_context

    def build_execution_adapter(self, runtime_context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, dict) else self.build_runtime_context()
        return {
            "enabled": bool(context.get("enabled", False)),
            "adapterType": "mcp_runtime_context",
            "provider": str(context.get("provider", "")).strip(),
            "transport": str(context.get("transport", "")).strip(),
            "endpoint": str(context.get("endpoint", "")).strip(),
            "capabilityScope": [
                str(item).strip()
                for item in context.get("capabilityScope", [])
                if str(item).strip()
            ] if isinstance(context.get("capabilityScope", []), list) else [],
            "provenance": context.get("provenance", {}) if isinstance(context.get("provenance", {}), dict) else {},
        }

    def resolve_execution_adapter(self, runtime_context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, dict) else self.build_runtime_context()
        adapter = self.build_execution_adapter(context)
        adapter["selectionMode"] = "feature_flag_runtime_context"
        return adapter
