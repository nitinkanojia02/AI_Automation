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

        state_payload = self.page_state_repository.load_state_artifact(page_name)
        artifact_errors = self.page_state_repository.validate_descriptor_payload(state_payload) if state_payload else ["missing state artifact"]
        artifact_snapshot = self.page_state_repository.get_state_source_snapshot(page_name, "artifact")
        contract_snapshot = self.page_state_repository.get_state_source_snapshot(page_name, "contract_fallback")
        artifact_descriptor = self.page_state_repository.build_descriptor(page_name, state_payload if not artifact_errors else {}).to_dict()
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
        if artifact_errors:
            descriptor_metadata["artifactValidationErrors"] = artifact_errors
        descriptor["metadata"] = descriptor_metadata

        descriptor_errors = self.page_state_repository.validate_descriptor_payload(descriptor)
        persisted_descriptor = self.page_state_repository.load_state_artifact(page_name) if self.persist_descriptors else {}
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
            self.page_state_repository.save_state_artifact(page_name, descriptor)
            self.logger.info(
                "page_state_persisted",
                page_name=page_name,
                state_source=state_source,
                source_snapshot=source_snapshot,
                persisted=True,
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
