from dataclasses import dataclass
from typing import Any

from app.repositories.mcp_repository import McpRepository


DEFAULT_RUNTIME_ADAPTER = {
    "enabled": False,
    "adapterType": "default_runtime",
    "provider": "",
    "transport": "",
    "endpoint": "",
    "capabilityScope": [],
    "provenance": {},
    "selectionMode": "feature_disabled",
}

FALLBACK_RUNTIME_ADAPTER = {
    "enabled": True,
    "adapterType": "default_runtime",
    "provider": "",
    "transport": "",
    "endpoint": "",
    "capabilityScope": [],
    "provenance": {},
    "selectionMode": "deterministic_fallback",
}


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
        if not bool(context.get("enabled", False)):
            return dict(DEFAULT_RUNTIME_ADAPTER)
        return {
            "enabled": True,
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
        adapter["selectionMode"] = "feature_flag_runtime_context" if bool(context.get("enabled", False)) else "feature_disabled"
        return adapter

    def resolve_execution_mode(self, runtime_context: dict[str, Any] | None = None) -> dict[str, str]:
        context = runtime_context if isinstance(runtime_context, dict) else self.build_runtime_context()
        mcp_enabled = bool(context.get("enabled", False))
        return {
            "dispatchMode": "selected_or_fallback" if mcp_enabled else "fallback_only",
            "executionMode": "non_blocking_adapter_selection" if mcp_enabled else "current_runtime_only",
        }

    def build_execution_dispatch(self, runtime_context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, dict) else self.build_runtime_context()
        adapter = self.resolve_execution_adapter(context)
        execution_mode = self.resolve_execution_mode(context)
        return {
            "selectedAdapter": dict(adapter),
            "fallbackAdapter": dict(FALLBACK_RUNTIME_ADAPTER),
            **execution_mode,
        }

    def build_execution_runtime_attachment(
        self,
        runtime_context: dict[str, Any] | None = None,
        page_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, dict) else self.build_runtime_context()
        normalized_page_state = page_state if isinstance(page_state, dict) else {}
        page_state_metadata = normalized_page_state.get("metadata", {}) if isinstance(normalized_page_state.get("metadata", {}), dict) else {}
        return {
            "pageState": {
                "pageName": str(normalized_page_state.get("page_name", "")).strip(),
                "sourceSnapshot": page_state_metadata.get("sourceSnapshot", {}) if isinstance(page_state_metadata.get("sourceSnapshot", {}), dict) else {},
                "stateVariants": page_state_metadata.get("stateVariants", []) if isinstance(page_state_metadata.get("stateVariants", []), list) else [],
            },
            "mcp": {
                "enabled": bool(context.get("enabled", False)),
                "provenance": context.get("provenance", {}) if isinstance(context.get("provenance", {}), dict) else {},
                "adapter": self.resolve_execution_adapter(context),
                "dispatch": self.build_execution_dispatch(context),
                "execution": self.resolve_execution_mode(context),
            },
        }
