from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.services.workflows.page_state_service import PageStateService


class WorkflowPlanningAgent:
    def __init__(self, page_state_service: PageStateService | None = None):
        self.page_state_service = page_state_service

    def build_plan(
        self,
        contract: WorkflowContract,
        navigation_steps: list[dict[str, Any]] | None = None,
        rag_context: dict[str, Any] | None = None,
        plan_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_navigation_steps = [
            dict(step)
            for step in (navigation_steps or contract.navigation_steps or [])
            if isinstance(step, dict)
        ]
        normalized_target_signals = [
            dict(signal)
            for signal in (contract.target_signals or [])
            if isinstance(signal, dict)
        ]

        normalized_resource_files: list[str] = []
        for item in contract.reuse_policy.resource_files or []:
            value = str(item).strip()
            if value and value not in normalized_resource_files:
                normalized_resource_files.append(value)

        rag_payload = rag_context if isinstance(rag_context, dict) else {}
        rag_provenance = rag_payload.get("provenance", {}) if isinstance(rag_payload.get("provenance"), dict) else {}
        plan_payload = plan_context if isinstance(plan_context, dict) else {}
        source_snapshot = plan_payload.get("sourceSnapshot", {}) if isinstance(plan_payload.get("sourceSnapshot"), dict) else {}
        mcp_context = plan_payload.get("mcpContext", {}) if isinstance(plan_payload.get("mcpContext"), dict) else {}
        mcp_adapter = plan_payload.get("mcpAdapter", {}) if isinstance(plan_payload.get("mcpAdapter"), dict) else {}
        mcp_dispatch = plan_payload.get("mcpDispatch", {}) if isinstance(plan_payload.get("mcpDispatch"), dict) else {}
        mcp_execution = plan_payload.get("mcpExecution", {}) if isinstance(plan_payload.get("mcpExecution"), dict) else {}
        plan_provenance = {
            "planningMode": "deterministic_structural",
            "navigationSource": str(plan_payload.get("navigationSource", "contract_or_runtime")).strip() or "contract_or_runtime",
            "targetSignalSource": str(plan_payload.get("targetSignalSource", "contract")).strip() or "contract",
            "ragAttached": bool(rag_payload),
            "ragSourcePreference": rag_provenance.get("sourcePreference", []) if isinstance(rag_provenance.get("sourcePreference", []), list) else [],
            "contractResourceFileCount": len(normalized_resource_files),
            "sourceSnapshot": source_snapshot,
        }

        page_state = self.page_state_service.build_state_descriptor(contract) if self.page_state_service else {}

        return {
            "workflow": {
                "workflowId": contract.workflow_id,
                "workflowName": contract.workflow_name,
                "feature": contract.feature,
                "sourceType": contract.source_type,
            },
            "pageContext": {
                "page": contract.page.to_dict(),
                "entryPage": contract.entry_page.to_dict() if contract.entry_page else {},
                "targetPage": contract.target_page.to_dict() if contract.target_page else {},
                "pageState": page_state,
            },
            "execution": {
                "navigationSteps": normalized_navigation_steps,
                "targetSignals": normalized_target_signals,
                "stepCount": len(normalized_navigation_steps),
            },
            "resources": {
                "resourceFiles": normalized_resource_files,
            },
            "rag": {
                "provenance": rag_provenance,
            },
            "mcp": {
                **mcp_context,
                "adapter": mcp_adapter,
                "dispatch": mcp_dispatch,
                "execution": mcp_execution,
            },
            "provenance": plan_provenance,
        }
