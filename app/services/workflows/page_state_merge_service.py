from __future__ import annotations

from typing import Any


class PageStateMergeService:
    def merge(self, primary: dict[str, Any] | None, fallback: dict[str, Any] | None) -> dict[str, Any]:
        primary_payload = dict(primary) if isinstance(primary, dict) else {}
        fallback_payload = dict(fallback) if isinstance(fallback, dict) else {}
        if not primary_payload:
            return fallback_payload
        if not fallback_payload:
            return primary_payload

        merged = dict(primary_payload)
        for field_name in ("page_name", "state_id", "state_type"):
            if not str(merged.get(field_name, "")).strip():
                merged[field_name] = fallback_payload.get(field_name, "")

        merged["source_artifacts"] = self._merge_string_lists(
            primary_payload.get("source_artifacts", []),
            fallback_payload.get("source_artifacts", []),
        )
        merged["signals"] = self._merge_object_lists(
            primary_payload.get("signals", []),
            fallback_payload.get("signals", []),
        )
        merged["metadata"] = self._merge_metadata(
            primary_payload.get("metadata", {}),
            fallback_payload.get("metadata", {}),
        )
        return merged

    @staticmethod
    def _merge_string_lists(primary: list[Any] | None, fallback: list[Any] | None) -> list[str]:
        merged: list[str] = []
        for collection in (primary or [], fallback or []):
            for item in collection:
                value = str(item).strip()
                if value and value not in merged:
                    merged.append(value)
        return merged

    @staticmethod
    def _merge_object_lists(primary: list[Any] | None, fallback: list[Any] | None) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for collection in (primary or [], fallback or []):
            for item in collection:
                if not isinstance(item, dict):
                    continue
                normalized = dict(item)
                marker = str(normalized)
                if marker in seen:
                    continue
                seen.add(marker)
                merged.append(normalized)
        return merged

    @staticmethod
    def _merge_metadata(primary: dict[str, Any] | None, fallback: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(fallback) if isinstance(fallback, dict) else {}
        if isinstance(primary, dict):
            merged.update(primary)
        return merged
