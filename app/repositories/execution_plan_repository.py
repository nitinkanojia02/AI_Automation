from pathlib import Path
import json


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
