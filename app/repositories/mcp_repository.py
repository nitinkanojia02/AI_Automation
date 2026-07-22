from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class McpRepository:
    REQUIRED_CONFIG_KEYS = ("provider", "endpoint", "transport", "capabilityScope")

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_dir = base_dir / "config"

    def get_config_path(self) -> Path:
        return self.config_dir / "mcp.runtime.json"

    def load_runtime_config(self) -> dict[str, Any]:
        path = self.get_config_path()
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        normalized = self.normalize_runtime_config(payload if isinstance(payload, dict) else {})
        validation_errors = self.validate_runtime_config(normalized) if normalized else ["missing MCP runtime config"]
        return normalized if not validation_errors else {}

    def validate_runtime_config(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(payload, dict):
            return ["MCP runtime config must be an object"]
        for key in self.REQUIRED_CONFIG_KEYS:
            if key not in payload:
                errors.append(f"MCP runtime config missing required key: {key}")
        if not str(payload.get("provider", "")).strip():
            errors.append("MCP runtime config provider is required")
        if not str(payload.get("endpoint", "")).strip():
            errors.append("MCP runtime config endpoint is required")
        if not str(payload.get("transport", "")).strip():
            errors.append("MCP runtime config transport is required")
        if not isinstance(payload.get("capabilityScope", []), list):
            errors.append("MCP runtime config capabilityScope must be a list")
        return errors

    def normalize_runtime_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        config = payload if isinstance(payload, dict) else {}
        capability_scope = [
            str(item).strip()
            for item in config.get("capabilityScope", [])
            if str(item).strip()
        ] if isinstance(config.get("capabilityScope", []), list) else []
        return {
            "provider": str(config.get("provider", "")).strip(),
            "endpoint": str(config.get("endpoint", "")).strip(),
            "transport": str(config.get("transport", "")).strip(),
            "capabilityScope": capability_scope,
        }

    def get_runtime_snapshot(self) -> dict[str, Any]:
        path = self.get_config_path()
        return {
            "configPath": str(path),
            "configExists": path.exists(),
            "configMtime": path.stat().st_mtime if path.exists() else None,
        }
