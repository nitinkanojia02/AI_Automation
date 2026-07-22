from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.resource_repository import ResourceRepository


class ResourceReuseAgent:
    def __init__(self, resource_repository: ResourceRepository):
        self.resource_repository = resource_repository

    def resolve_navigation_steps(self, contract: WorkflowContract) -> list[dict[str, Any]]:
        steps = contract.navigation_steps if isinstance(contract.navigation_steps, list) else []
        if not steps:
            return []

        bundles = self.resource_repository.load_bundles(contract.reuse_policy.resource_files)
        flows_by_id: dict[str, dict[str, Any]] = {}
        for bundle in bundles:
            for flow in bundle.get("reusableFlows", []):
                if not isinstance(flow, dict):
                    continue
                flow_id = str(flow.get("flowId", "")).strip()
                if flow_id:
                    flows_by_id[flow_id] = flow

        resolved_steps: list[dict[str, Any]] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            action = str(step.get("action", "")).strip()
            if action != "reuseApprovedEntryContext":
                resolved_steps.append(dict(step))
                continue

            flow_ref = str(step.get("flowId", "")).strip()
            if not flow_ref:
                raise ValueError("reuseApprovedEntryContext requires flowId in the workflow contract.")
            flow = flows_by_id.get(flow_ref)
            if not flow:
                raise ValueError(f"Approved reusable flow not found for flowId '{flow_ref}'.")

            flow_steps = flow.get("steps", []) if isinstance(flow.get("steps", []), list) else []
            if not flow_steps:
                raise ValueError(f"Approved reusable flow '{flow_ref}' does not contain any steps.")

            for flow_step in flow_steps:
                if isinstance(flow_step, dict):
                    resolved_steps.append(dict(flow_step))

        return resolved_steps
