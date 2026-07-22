from pathlib import Path
import json

from app.domain.workflow_contract import WorkflowContract


class WorkflowRepository:
    def __init__(self, workflow_dir: Path):
        self.workflow_dir = workflow_dir

    def get_contract_path(self, workflow_slug: str) -> Path:
        return self.workflow_dir / f"{workflow_slug}.contract.json"

    def save_contract(self, workflow_slug: str, contract: WorkflowContract) -> Path:
        path = self.get_contract_path(workflow_slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(contract.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path
