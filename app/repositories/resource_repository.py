from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ResourceRepository:
    REQUIRED_FLOW_STEP_KEYS = {
        "clickKnownElement": {"page", "element"},
        "inputKnownElement": {"page", "element", "value"},
        "waitForUrlContains": {"value"},
        "waitForElementVisible": {"page", "element"},
    }

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.pom_dir = base_dir / "pom_pages"

    def _normalize_resource_file(self, resource_file: str) -> str:
        return str(resource_file or "").replace("\\", "/").strip()

    def _resource_path(self, resource_file: str) -> Path:
        return self.pom_dir / self._normalize_resource_file(resource_file)

    def _metadata_dir_from_resource(self, resource_file: str) -> Path:
        resource_path = self._resource_path(resource_file)
        return resource_path.parent / "metadata"

    def _page_name_from_resource(self, resource_file: str) -> str:
        return self._resource_path(resource_file).stem.strip()

    def _read_json_if_exists(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _validate_reusable_flows(self, resource_file: str, flows: list[Any]) -> list[dict[str, Any]]:
        validated_flows: list[dict[str, Any]] = []
        seen_flow_ids: set[str] = set()
        for index, flow in enumerate(flows):
            if not isinstance(flow, dict):
                raise ValueError(f"Reusable flow entry at index {index} in '{resource_file}' must be an object.")

            flow_id = str(flow.get("flowId", "")).strip()
            if not flow_id:
                raise ValueError(f"Reusable flow entry at index {index} in '{resource_file}' requires flowId.")
            if flow_id in seen_flow_ids:
                raise ValueError(f"Duplicate reusable flowId '{flow_id}' found in '{resource_file}'.")
            seen_flow_ids.add(flow_id)

            steps = flow.get("steps", [])
            if not isinstance(steps, list) or not steps:
                raise ValueError(f"Reusable flow '{flow_id}' in '{resource_file}' must contain a non-empty steps list.")

            normalized_steps: list[dict[str, Any]] = []
            for step_index, step in enumerate(steps):
                if not isinstance(step, dict):
                    raise ValueError(f"Reusable flow '{flow_id}' step at index {step_index} in '{resource_file}' must be an object.")
                action = str(step.get("action", "")).strip()
                if not action:
                    raise ValueError(f"Reusable flow '{flow_id}' step at index {step_index} in '{resource_file}' requires action.")
                if action == "reuseApprovedEntryContext":
                    raise ValueError(f"Reusable flow '{flow_id}' in '{resource_file}' cannot contain nested reuseApprovedEntryContext steps.")
                required_keys = self.REQUIRED_FLOW_STEP_KEYS.get(action)
                if required_keys is None:
                    raise ValueError(f"Reusable flow '{flow_id}' in '{resource_file}' uses unsupported action '{action}'.")
                missing_keys = [key for key in required_keys if not str(step.get(key, "")).strip()]
                if missing_keys:
                    raise ValueError(
                        f"Reusable flow '{flow_id}' step at index {step_index} in '{resource_file}' is missing required fields: {', '.join(missing_keys)}."
                    )
                normalized_steps.append(dict(step))

            validated_flow = dict(flow)
            validated_flow["steps"] = normalized_steps
            validated_flows.append(validated_flow)
        return validated_flows

    def load_resource_bundle(self, resource_file: str) -> dict[str, Any]:
        normalized_resource = self._normalize_resource_file(resource_file)
        resource_path = self._resource_path(normalized_resource)
        metadata_dir = self._metadata_dir_from_resource(normalized_resource)
        page_name = self._page_name_from_resource(normalized_resource)

        variables = self._read_json_if_exists(metadata_dir / f"{page_name}.variables.json")
        keywords = self._read_json_if_exists(metadata_dir / f"{page_name}.keywords.json")
        reviewed_keywords = self._read_json_if_exists(metadata_dir / f"{page_name}.keywords.reviewed.json")
        reusable_flows = self._read_json_if_exists(metadata_dir / f"{page_name}.flows.json")
        reusable_flow_entries = reusable_flows.get("flows", []) if isinstance(reusable_flows.get("flows", []), list) else []

        return {
            "resourceFile": normalized_resource,
            "resourcePath": str(resource_path),
            "pageName": page_name,
            "resourceExists": resource_path.exists(),
            "resourceContent": resource_path.read_text(encoding="utf-8") if resource_path.exists() else "",
            "variables": variables.get("variables", []) if isinstance(variables.get("variables", []), list) else [],
            "keywords": keywords.get("keywords", []) if isinstance(keywords.get("keywords", []), list) else [],
            "reviewedKeywords": reviewed_keywords.get("keywords", []) if isinstance(reviewed_keywords.get("keywords", []), list) else [],
            "reusableFlows": self._validate_reusable_flows(normalized_resource, reusable_flow_entries),
            "reusableFlowArtifact": reusable_flows,
        }

    def load_bundles(self, resource_files: list[str]) -> list[dict[str, Any]]:
        bundles: list[dict[str, Any]] = []
        seen: set[str] = set()
        for resource_file in resource_files or []:
            normalized = self._normalize_resource_file(resource_file)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            bundles.append(self.load_resource_bundle(normalized))
        return bundles
