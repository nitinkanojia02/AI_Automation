from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.page_state_model import PageStateDescriptor


class PageStateRepository:
    REQUIRED_ARTIFACT_KEYS = ("stateId", "stateType", "sourceArtifacts", "signals", "metadata")
    PERSISTED_DESCRIPTOR_KEYS = ("page_name", "state_id", "state_type", "source_artifacts", "signals", "metadata")
    NORMALIZED_DESCRIPTOR_KEYS = ("page_name", "state_id", "state_type", "source_artifacts", "signals", "metadata")
    VARIANT_COLLECTION_KEYS = ("page_name", "variants")
    STATE_SOURCE_METADATA_KEYS = ("stateSource", "artifactPath", "normalizedSourceType", "fallbackUsed")

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
        return self.normalize_state_artifact(page_name, payload if isinstance(payload, dict) else {})

    def load_state_variants(self, page_name: str) -> dict[str, Any]:
        path = self.get_state_artifact_path(page_name)
        if not path.exists():
            return {"page_name": str(page_name).strip(), "variants": []}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"page_name": str(page_name).strip(), "variants": []}
        return self.normalize_state_variants(page_name, payload if isinstance(payload, dict) else {})

    def save_state_artifact(self, page_name: str, payload: dict[str, Any]) -> Path:
        path = self.get_state_artifact_path(page_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized_payload = self.normalize_state_artifact(page_name, payload if isinstance(payload, dict) else {})
        path.write_text(json.dumps(normalized_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def save_state_variants(self, page_name: str, payload: dict[str, Any]) -> Path:
        path = self.get_state_artifact_path(page_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized_payload = self.normalize_state_variants(page_name, payload if isinstance(payload, dict) else {})
        path.write_text(json.dumps(normalized_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def get_state_freshness_context(self, page_name: str) -> dict[str, Any]:
        path = self.get_state_artifact_path(page_name)
        return {
            "artifactPath": str(path),
            "artifactExists": path.exists(),
            "artifactMtime": path.stat().st_mtime if path.exists() else None,
        }

    def get_state_source_snapshot(self, page_name: str, source_type: str = "") -> dict[str, Any]:
        freshness = self.get_state_freshness_context(page_name)
        return {
            "pageName": str(page_name).strip(),
            "artifactPath": freshness.get("artifactPath"),
            "artifactExists": freshness.get("artifactExists"),
            "artifactMtime": freshness.get("artifactMtime"),
            "normalizedSourceType": str(source_type).strip(),
        }

    def snapshot_matches(self, page_name: str, persisted_snapshot: dict[str, Any] | None, source_type: str = "") -> bool:
        if not isinstance(persisted_snapshot, dict):
            return False
        return persisted_snapshot == self.get_state_source_snapshot(page_name, source_type)

    def normalize_state_artifact(self, page_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        artifact_payload = payload if isinstance(payload, dict) else {}
        descriptor_errors = self.validate_descriptor_payload(artifact_payload) if artifact_payload else ["missing descriptor payload"]
        if not descriptor_errors:
            source_artifacts = [
                str(item).strip()
                for item in artifact_payload.get("source_artifacts", [])
                if str(item).strip()
            ] if isinstance(artifact_payload.get("source_artifacts", []), list) else []
            signals = [
                dict(item)
                for item in artifact_payload.get("signals", [])
                if isinstance(item, dict)
            ] if isinstance(artifact_payload.get("signals", []), list) else []
            metadata = artifact_payload.get("metadata", {}) if isinstance(artifact_payload.get("metadata", {}), dict) else {}
            return {
                "page_name": str(artifact_payload.get("page_name", page_name)).strip(),
                "state_id": str(artifact_payload.get("state_id", "")).strip(),
                "state_type": str(artifact_payload.get("state_type", "")).strip(),
                "source_artifacts": source_artifacts,
                "signals": signals,
                "metadata": metadata,
            }

        state_artifact_errors = self.validate_state_artifact(artifact_payload) if artifact_payload else ["missing state artifact"]
        if state_artifact_errors:
            return {}

        source_artifacts = [
            str(item).strip()
            for item in artifact_payload.get("sourceArtifacts", [])
            if str(item).strip()
        ] if isinstance(artifact_payload.get("sourceArtifacts", []), list) else []
        signals = [
            dict(item)
            for item in artifact_payload.get("signals", [])
            if isinstance(item, dict)
        ] if isinstance(artifact_payload.get("signals", []), list) else []
        metadata = artifact_payload.get("metadata", {}) if isinstance(artifact_payload.get("metadata", {}), dict) else {}
        return {
            "page_name": str(page_name).strip(),
            "state_id": str(artifact_payload.get("stateId", "")).strip(),
            "state_type": str(artifact_payload.get("stateType", "")).strip(),
            "source_artifacts": source_artifacts,
            "signals": signals,
            "metadata": metadata,
        }

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

    def validate_variant_collection_payload(self, payload: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(payload, dict):
            return ["page state variant collection must be an object"]
        for key in self.VARIANT_COLLECTION_KEYS:
            if key not in payload:
                errors.append(f"page state variant collection missing required key: {key}")
        if not str(payload.get("page_name", "")).strip():
            errors.append("page state variant collection page_name is required")
        variants = payload.get("variants", [])
        if not isinstance(variants, list):
            errors.append("page state variant collection variants must be a list")
            return errors
        for index, item in enumerate(variants):
            if not isinstance(item, dict):
                errors.append(f"page state variant collection variants[{index}] must be an object")
                continue
            descriptor_errors = self.validate_descriptor_payload(item)
            errors.extend([f"variants[{index}]: {error}" for error in descriptor_errors])
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

    def normalize_state_variants(self, page_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        collection_payload = payload if isinstance(payload, dict) else {}
        collection_errors = self.validate_variant_collection_payload(collection_payload) if collection_payload else ["missing variant collection payload"]
        if not collection_errors:
            normalized_variants = []
            for item in collection_payload.get("variants", []):
                normalized_item = self.normalize_state_artifact(page_name, item if isinstance(item, dict) else {})
                if normalized_item:
                    normalized_variants.append(normalized_item)
            return {
                "page_name": str(collection_payload.get("page_name", page_name)).strip(),
                "variants": normalized_variants,
            }

        normalized_single = self.normalize_state_artifact(page_name, collection_payload)
        if normalized_single:
            return {
                "page_name": str(normalized_single.get("page_name", page_name)).strip(),
                "variants": [normalized_single],
            }
        return {
            "page_name": str(page_name).strip(),
            "variants": [],
        }

    def build_descriptor(self, page_name: str, state_payload: dict[str, Any] | None = None) -> PageStateDescriptor:
        payload = self.normalize_state_artifact(page_name, state_payload if isinstance(state_payload, dict) else {})
        source_artifacts = [
            str(item).strip()
            for item in payload.get("source_artifacts", [])
            if str(item).strip()
        ] if isinstance(payload.get("source_artifacts", []), list) else []
        signals = [
            dict(item)
            for item in payload.get("signals", [])
            if isinstance(item, dict)
        ] if isinstance(payload.get("signals", []), list) else []
        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
        return PageStateDescriptor(
            page_name=str(payload.get("page_name", page_name)).strip(),
            state_id=str(payload.get("state_id", "")).strip(),
            state_type=str(payload.get("state_type", "")).strip(),
            source_artifacts=source_artifacts,
            signals=signals,
            metadata=metadata,
        )
