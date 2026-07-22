from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ResourceRepository:
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

    def load_resource_bundle(self, resource_file: str) -> dict[str, Any]:
        normalized_resource = self._normalize_resource_file(resource_file)
        resource_path = self._resource_path(normalized_resource)
        metadata_dir = self._metadata_dir_from_resource(normalized_resource)
        page_name = self._page_name_from_resource(normalized_resource)

        variables = self._read_json_if_exists(metadata_dir / f"{page_name}.variables.json")
        keywords = self._read_json_if_exists(metadata_dir / f"{page_name}.keywords.json")
        reviewed_keywords = self._read_json_if_exists(metadata_dir / f"{page_name}.keywords.reviewed.json")
        reusable_flows = self._read_json_if_exists(metadata_dir / f"{page_name}.flows.json")

        return {
            "resourceFile": normalized_resource,
            "resourcePath": str(resource_path),
            "pageName": page_name,
            "resourceExists": resource_path.exists(),
            "resourceContent": resource_path.read_text(encoding="utf-8") if resource_path.exists() else "",
            "variables": variables.get("variables", []) if isinstance(variables.get("variables", []), list) else [],
            "keywords": keywords.get("keywords", []) if isinstance(keywords.get("keywords", []), list) else [],
            "reviewedKeywords": reviewed_keywords.get("keywords", []) if isinstance(reviewed_keywords.get("keywords", []), list) else [],
            "reusableFlows": reusable_flows.get("flows", []) if isinstance(reusable_flows.get("flows", []), list) else [],
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
