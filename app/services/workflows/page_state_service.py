from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.page_state_repository import PageStateRepository


class PageStateService:
    def __init__(self, page_state_repository: PageStateRepository):
        self.page_state_repository = page_state_repository

    def build_state_descriptor(self, contract: WorkflowContract) -> dict[str, Any]:
        page_name = str(contract.page.name or "").strip()
        if not page_name:
            return {}

        state_payload = self.page_state_repository.load_state_artifact(page_name)
        descriptor = self.page_state_repository.build_descriptor(page_name, state_payload)

        if not descriptor.state_id:
            descriptor.state_id = str(contract.page_state or contract.page.state or "").strip()
        if not descriptor.state_type:
            descriptor.state_type = str(contract.page_state or contract.page.state or "").strip()
        if not descriptor.signals:
            descriptor.signals = [
                dict(item)
                for item in (contract.target_signals or [])
                if isinstance(item, dict)
            ]
        if not descriptor.source_artifacts:
            descriptor.source_artifacts = [
                str(item).strip()
                for item in (contract.reuse_policy.resource_files or [])
                if str(item).strip()
            ]

        return descriptor.to_dict()
