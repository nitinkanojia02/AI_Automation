from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.resource_repository import ResourceRepository


class KnowledgeRepository:
    def __init__(self, base_dir: Path, resource_repository: ResourceRepository):
        self.base_dir = base_dir
        self.resource_repository = resource_repository
        self.workflow_dir = base_dir / "workflow_inputs"
        self.workflow_knowledge_dir = base_dir / "artifacts" / "workflow_knowledge"

    def _read_json_if_exists(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def load_workflow_artifact(self, workflow_slug: str) -> dict[str, Any]:
        return self._read_json_if_exists(self.workflow_dir / f"{workflow_slug}.json")

    def load_contract_artifact(self, workflow_slug: str) -> dict[str, Any]:
        return self._read_json_if_exists(self.workflow_dir / f"{workflow_slug}.contract.json")

    def load_workflow_knowledge_artifact(self, workflow_slug: str) -> dict[str, Any]:
        return self._read_json_if_exists(self.workflow_knowledge_dir / f"{workflow_slug}.json")

    def list_workflow_slugs(self) -> list[str]:
        slugs: list[str] = []
        for path in sorted(self.workflow_dir.glob("*.json")):
            if path.name.endswith(".status.json") or path.name.endswith(".contract.json"):
                continue
            slugs.append(path.stem)
        return slugs

    def build_retrieval_bundle(self, workflow_slug: str, contract: WorkflowContract | None = None) -> dict[str, Any]:
        workflow_artifact = self.load_workflow_artifact(workflow_slug)
        contract_artifact = contract.to_dict() if contract else self.load_contract_artifact(workflow_slug)
        workflow_knowledge = self.load_workflow_knowledge_artifact(workflow_slug)

        resource_files: list[str] = []
        for source in (contract_artifact, workflow_artifact):
            values = source.get("reuse_policy", {}).get("resource_files", []) if isinstance(source.get("reuse_policy"), dict) else source.get("resourceFiles", [])
            if not isinstance(values, list):
                continue
            for item in values:
                normalized = str(item or "").replace("\\", "/").strip()
                if normalized and normalized not in resource_files:
                    resource_files.append(normalized)

        resource_bundles = self.resource_repository.load_bundles(resource_files)
        return {
            "workflow": workflow_artifact,
            "contract": contract_artifact,
            "workflowKnowledge": workflow_knowledge,
            "resourceBundles": resource_bundles,
        }
