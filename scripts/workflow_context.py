import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
POM_DIR = BASE_DIR / "pom_pages"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_load_json(path: Path) -> Dict[str, Any] | None:
    try:
        if path.exists():
            return load_json(path)
    except Exception:
        return None
    return None


def resource_summary(resource_file: str) -> Dict[str, Any]:
    rel = str(resource_file).replace("\\", "/").strip()
    resource_path = POM_DIR / rel
    page_key = Path(rel).stem
    summary: Dict[str, Any] = {
        "resourceFile": rel,
        "pageKey": page_key,
        "exists": resource_path.exists(),
    }
    if resource_path.exists():
        try:
            text = resource_path.read_text(encoding="utf-8")
            summary["lineCount"] = len(text.splitlines())
        except Exception:
            pass
    return summary


def build_workflow_resource_context(workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    resource_files = [
        str(x).replace("\\", "/").strip()
        for x in workflow_input.get("resourceFiles", [])
        if str(x).strip()
    ]
    authoritative: List[str] = []
    for item in resource_files:
        if item not in authoritative:
            authoritative.append(item)

    return {
        "workflowName": str(workflow_input.get("workflowName", "")).strip() or "workflow",
        "resourceFiles": authoritative,
        "resourceSummaries": [resource_summary(item) for item in authoritative],
    }
