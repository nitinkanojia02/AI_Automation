from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class McpRuntimeContext:
    enabled: bool
    provider: str = ""
    endpoint: str = ""
    transport: str = ""
    capability_scope: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "transport": self.transport,
            "capabilityScope": list(self.capability_scope),
        }


class McpService:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def build_runtime_context(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = config if isinstance(config, dict) else {}
        provider = str(payload.get("provider", "")).strip()
        endpoint = str(payload.get("endpoint", "")).strip()
        transport = str(payload.get("transport", "")).strip()
        capability_scope = tuple(
            str(item).strip()
            for item in payload.get("capabilityScope", [])
            if str(item).strip()
        ) if isinstance(payload.get("capabilityScope", []), list) else ()
        return McpRuntimeContext(
            enabled=bool(self.enabled),
            provider=provider,
            endpoint=endpoint,
            transport=transport,
            capability_scope=capability_scope,
        ).to_dict()
