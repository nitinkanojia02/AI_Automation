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

    def are_plan_contexts_aligned(self, persisted_plan: dict[str, Any] | None, runtime_context: dict[str, Any] | None) -> dict[str, Any]:
        normalized_runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        runtime_provenance = normalized_runtime_context.get("provenance", {}) if isinstance(normalized_runtime_context.get("provenance", {}), dict) else {}
        persisted_mcp = persisted_plan.get("mcp", {}) if isinstance((persisted_plan or {}).get("mcp", {}), dict) else {}
        persisted_provenance = persisted_mcp.get("provenance", {}) if isinstance(persisted_mcp.get("provenance", {}), dict) else {}
        persisted_adapter = persisted_mcp.get("adapter", {}) if isinstance(persisted_mcp.get("adapter", {}), dict) else {}
        persisted_dispatch = persisted_mcp.get("dispatch", {}) if isinstance(persisted_mcp.get("dispatch", {}), dict) else {}
        persisted_execution = persisted_mcp.get("execution", {}) if isinstance(persisted_mcp.get("execution", {}), dict) else {}

        runtime_adapter = self.resolve_execution_adapter(normalized_runtime_context)
        runtime_dispatch = self.build_execution_dispatch(normalized_runtime_context)
        runtime_execution = self.resolve_execution_mode(normalized_runtime_context)

        provenance_aligned = (not runtime_provenance and not persisted_provenance) or (persisted_provenance == runtime_provenance)
        adapter_aligned = (not persisted_adapter and not runtime_adapter) or (persisted_adapter == runtime_adapter)
        dispatch_aligned = (not persisted_dispatch and not runtime_dispatch) or (persisted_dispatch == runtime_dispatch)
        execution_aligned = (not persisted_execution and not runtime_execution) or (persisted_execution == runtime_execution)

        return {
            "persistedProvenance": persisted_provenance,
            "runtimeProvenance": runtime_provenance,
            "persistedAdapter": persisted_adapter,
            "runtimeAdapter": runtime_adapter,
            "persistedDispatch": persisted_dispatch,
            "runtimeDispatch": runtime_dispatch,
            "persistedExecution": persisted_execution,
            "runtimeExecution": runtime_execution,
            "provenanceAligned": provenance_aligned,
            "adapterAligned": adapter_aligned,
            "dispatchAligned": dispatch_aligned,
            "executionAligned": execution_aligned,
        }

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
                "stateId": str(normalized_page_state.get("state_id", "")).strip(),
                "stateType": str(normalized_page_state.get("state_type", "")).strip(),
                "sourceArtifacts": [
                    str(item).strip()
                    for item in normalized_page_state.get("source_artifacts", [])
                    if str(item).strip()
                ] if isinstance(normalized_page_state.get("source_artifacts", []), list) else [],
                "signals": [
                    dict(item)
                    for item in normalized_page_state.get("signals", [])
                    if isinstance(item, dict)
                ] if isinstance(normalized_page_state.get("signals", []), list) else [],
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

    def build_extraction_runtime_payload(self, execution_runtime: dict[str, Any] | None = None) -> dict[str, Any]:
        normalized_execution_runtime = execution_runtime if isinstance(execution_runtime, dict) else {}
        normalized_mcp = normalized_execution_runtime.get("mcp", {}) if isinstance(normalized_execution_runtime.get("mcp", {}), dict) else {}
        return {
            "executionRuntime": normalized_execution_runtime,
            "pageState": normalized_execution_runtime.get("pageState", {}) if isinstance(normalized_execution_runtime.get("pageState", {}), dict) else {},
            "mcpExecution": normalized_mcp.get("execution", {}) if isinstance(normalized_mcp.get("execution", {}), dict) else {},
            "mcpDispatch": normalized_mcp.get("dispatch", {}) if isinstance(normalized_mcp.get("dispatch", {}), dict) else {},
            "mcpAdapter": normalized_mcp.get("adapter", {}) if isinstance(normalized_mcp.get("adapter", {}), dict) else {},
            "mcpEnabled": bool(normalized_mcp.get("enabled", False)),
        }
