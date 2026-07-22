from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.page_state_repository import PageStateRepository
from app.services.platform.logger import PlatformLogger
from app.services.workflows.page_state_merge_service import PageStateMergeService


class PageStateService:
    def __init__(self, page_state_repository: PageStateRepository, page_state_merge_service: PageStateMergeService | None = None, persist_descriptors: bool = False, logger: PlatformLogger | None = None):
        self.page_state_repository = page_state_repository
        self.page_state_merge_service = page_state_merge_service or PageStateMergeService()
        self.persist_descriptors = persist_descriptors
        self.logger = logger or PlatformLogger(__name__)

    def build_state_descriptor(self, contract: WorkflowContract) -> dict[str, Any]:
        page_name = str(contract.page.name or "").strip()
        if not page_name:
            return {}

        state_variants_payload = self.page_state_repository.load_state_variants(page_name)
        variants = state_variants_payload.get("variants", []) if isinstance(state_variants_payload.get("variants", []), list) else []
        selected_variant = {}
        contract_state_id = str(contract.page_state or contract.page.state or "").strip()
        contract_signal_set = [dict(item) for item in (contract.target_signals or []) if isinstance(item, dict)]
        for item in variants:
            if not isinstance(item, dict):
                continue
            if contract_state_id and str(item.get("state_id", "")).strip() == contract_state_id:
                selected_variant = dict(item)
                break
            item_signals = [dict(signal) for signal in item.get("signals", []) if isinstance(signal, dict)] if isinstance(item.get("signals", []), list) else []
            if item_signals == contract_signal_set:
                selected_variant = dict(item)
                break
        if not selected_variant and variants:
            selected_variant = dict(variants[0]) if isinstance(variants[0], dict) else {}

        artifact_errors = self.page_state_repository.validate_descriptor_payload(selected_variant) if selected_variant else ["missing state artifact"]
        artifact_snapshot = self.page_state_repository.get_state_source_snapshot(page_name, "artifact")
        contract_snapshot = self.page_state_repository.get_state_source_snapshot(page_name, "contract_fallback")
        artifact_descriptor = self.page_state_repository.build_descriptor(page_name, selected_variant if not artifact_errors else {}).to_dict()
        fallback_descriptor = self.page_state_repository.build_descriptor(page_name, {
            "stateId": str(contract.page_state or contract.page.state or "").strip(),
            "stateType": str(contract.page_state or contract.page.state or "").strip(),
            "sourceArtifacts": [
                str(item).strip()
                for item in (contract.reuse_policy.resource_files or [])
                if str(item).strip()
            ],
            "signals": [
                dict(item)
                for item in (contract.target_signals or [])
                if isinstance(item, dict)
            ],
            "metadata": {},
        }).to_dict()

        descriptor = self.page_state_merge_service.merge(
            artifact_descriptor if not artifact_errors else {},
            fallback_descriptor,
        )
        descriptor_metadata = descriptor.get("metadata", {}) if isinstance(descriptor.get("metadata", {}), dict) else {}
        state_source = "artifact" if not artifact_errors else "contract_fallback"
        source_snapshot = artifact_snapshot if not artifact_errors else contract_snapshot
        descriptor_metadata["stateSource"] = state_source
        descriptor_metadata["artifactPath"] = source_snapshot.get("artifactPath", "")
        descriptor_metadata["normalizedSourceType"] = source_snapshot.get("normalizedSourceType", "")
        descriptor_metadata["fallbackUsed"] = bool(artifact_errors)
        descriptor_metadata["sourceSnapshot"] = source_snapshot
        descriptor_metadata["stateVariants"] = [dict(item) for item in variants if isinstance(item, dict)]
        if artifact_errors:
            descriptor_metadata["artifactValidationErrors"] = artifact_errors
        descriptor["metadata"] = descriptor_metadata

        descriptor_errors = self.page_state_repository.validate_descriptor_payload(descriptor)
        persisted_variants_payload = self.page_state_repository.load_state_variants(page_name) if self.persist_descriptors else {"page_name": page_name, "variants": []}
        persisted_variants = persisted_variants_payload.get("variants", []) if isinstance(persisted_variants_payload.get("variants", []), list) else []
        persisted_descriptor = {}
        for item in persisted_variants:
            if not isinstance(item, dict):
                continue
            persisted_state_id = str(item.get("state_id", "")).strip()
            descriptor_state_id = str(descriptor.get("state_id", "")).strip()
            if descriptor_state_id and persisted_state_id == descriptor_state_id:
                persisted_descriptor = dict(item)
                break
            if item == descriptor:
                persisted_descriptor = dict(item)
                break
        persisted_descriptor_errors = self.page_state_repository.validate_descriptor_payload(persisted_descriptor) if persisted_descriptor else ["missing persisted descriptor"]
        persisted_snapshot = ((persisted_descriptor.get("metadata", {}) if isinstance(persisted_descriptor.get("metadata", {}), dict) else {}).get("sourceSnapshot", {})) if persisted_descriptor else {}
        if self.persist_descriptors and not descriptor_errors:
            if not persisted_descriptor_errors and persisted_descriptor == descriptor and self.page_state_repository.snapshot_matches(page_name, persisted_snapshot, state_source):
                self.logger.info(
                    "page_state_reused",
                    page_name=page_name,
                    state_source=state_source,
                    source_snapshot=source_snapshot,
                    persisted=True,
                )
                return persisted_descriptor
            updated_variants: list[dict[str, Any]] = []
            replaced = False
            descriptor_state_id = str(descriptor.get("state_id", "")).strip()
            for item in persisted_variants:
                if not isinstance(item, dict):
                    continue
                item_state_id = str(item.get("state_id", "")).strip()
                if descriptor_state_id and item_state_id == descriptor_state_id:
                    updated_variants.append(descriptor)
                    replaced = True
                else:
                    updated_variants.append(dict(item))
            if not replaced:
                updated_variants.append(descriptor)
            self.page_state_repository.save_state_variants(page_name, {
                "page_name": page_name,
                "variants": updated_variants,
            })
            self.logger.info(
                "page_state_persisted",
                page_name=page_name,
                state_source=state_source,
                source_snapshot=source_snapshot,
                persisted=True,
                variant_count=len(updated_variants),
            )
        elif descriptor_errors:
            descriptor_metadata["descriptorValidationErrors"] = descriptor_errors
            descriptor["metadata"] = descriptor_metadata
            self.logger.info(
                "page_state_invalid",
                page_name=page_name,
                state_source=state_source,
                source_snapshot=source_snapshot,
                error_count=len(descriptor_errors),
            )
        else:
            self.logger.info(
                "page_state_resolved",
                page_name=page_name,
                state_source=state_source,
                source_snapshot=source_snapshot,
                persisted=False,
            )

        return descriptor

    def are_plan_states_aligned(self, persisted_plan: dict[str, Any] | None, runtime_page_state: dict[str, Any] | None) -> dict[str, Any]:
        normalized_runtime_page_state = dict(runtime_page_state) if isinstance(runtime_page_state, dict) else {}
        persisted_page_context = persisted_plan.get("pageContext", {}) if isinstance((persisted_plan or {}).get("pageContext", {}), dict) else {}
        persisted_page_state = persisted_page_context.get("pageState", {}) if isinstance(persisted_page_context.get("pageState", {}), dict) else {}
        runtime_page_state_snapshot = self._get_source_snapshot(normalized_runtime_page_state)
        persisted_page_state_snapshot = self._get_source_snapshot(persisted_page_state)
        page_state_aligned = (not normalized_runtime_page_state and not persisted_page_state) or (persisted_page_state == normalized_runtime_page_state)
        page_state_snapshot_aligned = (not runtime_page_state_snapshot and not persisted_page_state_snapshot) or (persisted_page_state_snapshot == runtime_page_state_snapshot)
        return {
            "persistedPageState": persisted_page_state,
            "persistedPageStateSnapshot": persisted_page_state_snapshot,
            "runtimePageStateSnapshot": runtime_page_state_snapshot,
            "pageStateAligned": page_state_aligned,
            "pageStateSnapshotAligned": page_state_snapshot_aligned,
        }

    @staticmethod
    def _get_source_snapshot(page_state: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(page_state, dict):
            return {}
        metadata = page_state.get("metadata", {}) if isinstance(page_state.get("metadata", {}), dict) else {}
        return metadata.get("sourceSnapshot", {}) if isinstance(metadata.get("sourceSnapshot", {}), dict) else {}
