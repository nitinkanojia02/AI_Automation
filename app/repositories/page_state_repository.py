from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.page_state_model import PageStateDescriptor


class PageStateRepository:
    REQUIRED_ARTIFACT_KEYS = ("stateId", "stateType", "sourceArtifacts", "signals", "metadata")
    PERSISTED_DESCRIPTOR_KEYS = ("page_name", "state_id", "state_type", "source_artifacts", "signals", "metadata")

    def __init__(self, pom_dir: Path):
        self.pom_dir = pom_dir

    def get_state_artifact_path(self, page_name: str) -> Path:
        return self.pom_dir / page_name / "metadata" / f"{page_name}.states.json"

    def load_state_artifact(self, page_name: str) -> dict[str, Any]:
        path = self.get_state_artifact_path(page_name)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def save_state_artifact(self, page_name: str, payload: dict[str, Any]) -> Path:
        path = self.get_state_artifact_path(page_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def validate_descriptor_payload(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(payload, dict):
            return ["page state descriptor must be an object"]
        for key in self.PERSISTED_DESCRIPTOR_KEYS:
            if key not in payload:
                errors.append(f"page state descriptor missing required key: {key}")
        if "source_artifacts" in payload and not isinstance(payload.get("source_artifacts"), list):
            errors.append("page state descriptor source_artifacts must be a list")
        if "signals" in payload and not isinstance(payload.get("signals"), list):
            errors.append("page state descriptor signals must be a list")
        if "metadata" in payload and not isinstance(payload.get("metadata"), dict):
            errors.append("page state descriptor metadata must be an object")
        if not str(payload.get("page_name", "")).strip():
            errors.append("page state descriptor page_name is required")
        return errors

    def validate_state_artifact(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(payload, dict):
            return ["page state artifact must be an object"]
        for key in self.REQUIRED_ARTIFACT_KEYS:
            if key not in payload:
                errors.append(f"page state artifact missing required key: {key}")
        if "sourceArtifacts" in payload and not isinstance(payload.get("sourceArtifacts"), list):
            errors.append("page state artifact sourceArtifacts must be a list")
        if "signals" in payload and not isinstance(payload.get("signals"), list):
            errors.append("page state artifact signals must be a list")
        if "metadata" in payload and not isinstance(payload.get("metadata"), dict):
            errors.append("page state artifact metadata must be an object")
        return errors

    def build_descriptor(self, page_name: str, state_payload: dict[str, Any] | None = None) -> PageStateDescriptor:
        payload = state_payload if isinstance(state_payload, dict) else {}
        source_artifacts = [
            str(item).strip()
            for item in payload.get("sourceArtifacts", [])
            if str(item).strip()
        ] if isinstance(payload.get("sourceArtifacts", []), list) else []
        signals = [
            dict(item)
            for item in payload.get("signals", [])
            if isinstance(item, dict)
        ] if isinstance(payload.get("signals", []), list) else []
        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
        return PageStateDescriptor(
            page_name=str(page_name).strip(),
            state_id=str(payload.get("stateId", "")).strip(),
            state_type=str(payload.get("stateType", "")).strip(),
            source_artifacts=source_artifacts,
            signals=signals,
            metadata=metadata,
        )
