from pathlib import Path
import json
from typing import Any


class ExecutionPlanRepository:
    def __init__(self, workflow_dir: Path):
        self.workflow_dir = workflow_dir

    def get_plan_path(self, workflow_slug: str) -> Path:
        return self.workflow_dir / f"{workflow_slug}.plan.json"

    def load_plan(self, workflow_slug: str) -> dict | None:
        path = self.get_plan_path(workflow_slug)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_plan(self, workflow_slug: str, plan: dict) -> Path:
        path = self.get_plan_path(workflow_slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def get_plan_freshness_context(self, workflow_slug: str) -> dict[str, Any]:
        plan_path = self.get_plan_path(workflow_slug)
        freshness: dict[str, Any] = {
            "planPath": str(plan_path),
            "planExists": plan_path.exists(),
            "planMtime": plan_path.stat().st_mtime if plan_path.exists() else None,
            "artifacts": {},
        }
        for label, suffix in (("workflow", ".json"), ("contract", ".contract.json")):
            artifact_path = self.workflow_dir / f"{workflow_slug}{suffix}"
            freshness["artifacts"][label] = {
                "path": str(artifact_path),
                "exists": artifact_path.exists(),
                "mtime": artifact_path.stat().st_mtime if artifact_path.exists() else None,
            }
        return freshness

    def get_source_snapshot(self, workflow_slug: str) -> dict[str, Any]:
        freshness = self.get_plan_freshness_context(workflow_slug)
        artifacts = freshness.get("artifacts", {}) if isinstance(freshness.get("artifacts", {}), dict) else {}
        return {
            "workflowSlug": workflow_slug,
            "workflowArtifact": dict(artifacts.get("workflow", {})) if isinstance(artifacts.get("workflow", {}), dict) else {},
            "contractArtifact": dict(artifacts.get("contract", {})) if isinstance(artifacts.get("contract", {}), dict) else {},
        }

    def is_plan_stale(self, workflow_slug: str) -> bool:
        freshness = self.get_plan_freshness_context(workflow_slug)
        plan_mtime = freshness.get("planMtime")
        if plan_mtime is None:
            return True
        artifacts = freshness.get("artifacts", {}) if isinstance(freshness.get("artifacts", {}), dict) else {}
        for artifact in artifacts.values():
            if not isinstance(artifact, dict):
                continue
            artifact_mtime = artifact.get("mtime")
            if artifact.get("exists") and artifact_mtime is not None and artifact_mtime > plan_mtime:
                return True
        return False
