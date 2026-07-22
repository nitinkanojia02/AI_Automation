from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.page_state_repository import PageStateRepository
from app.services.workflows.page_state_merge_service import PageStateMergeService


class PageStateService:
    def __init__(self, page_state_repository: PageStateRepository, page_state_merge_service: PageStateMergeService | None = None, persist_descriptors: bool = False):
        self.page_state_repository = page_state_repository
        self.page_state_merge_service = page_state_merge_service or PageStateMergeService()
        self.persist_descriptors = persist_descriptors

    def build_state_descriptor(self, contract: WorkflowContract) -> dict[str, Any]:
        page_name = str(contract.page.name or "").strip()
        if not page_name:
            return {}

        state_payload = self.page_state_repository.load_state_artifact(page_name)
        artifact_errors = self.page_state_repository.validate_state_artifact(state_payload) if state_payload else ["missing state artifact"]
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
        descriptor_metadata["stateSource"] = "artifact" if not artifact_errors else "contract_fallback"
        if artifact_errors:
            descriptor_metadata["artifactValidationErrors"] = artifact_errors
        descriptor["metadata"] = descriptor_metadata

        descriptor_errors = self.page_state_repository.validate_descriptor_payload(descriptor)
        if self.persist_descriptors and not descriptor_errors:
            self.page_state_repository.save_state_artifact(page_name, descriptor)
        elif descriptor_errors:
            descriptor_metadata["descriptorValidationErrors"] = descriptor_errors
            descriptor["metadata"] = descriptor_metadata

        return descriptor
