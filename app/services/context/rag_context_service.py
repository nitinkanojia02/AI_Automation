from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.knowledge_repository import KnowledgeRepository


class RagContextService:
    def __init__(self, knowledge_repository: KnowledgeRepository):
        self.knowledge_repository = knowledge_repository

    def build_context(self, workflow_slug: str, contract: WorkflowContract | None = None) -> dict[str, Any]:
        bundle = self.knowledge_repository.build_retrieval_bundle(workflow_slug, contract)
        workflow = bundle.get("workflow", {}) if isinstance(bundle.get("workflow", {}), dict) else {}
        contract_artifact = bundle.get("contract", {}) if isinstance(bundle.get("contract", {}), dict) else {}
        workflow_knowledge = bundle.get("workflowKnowledge", {}) if isinstance(bundle.get("workflowKnowledge", {}), dict) else {}
        resource_bundles = bundle.get("resourceBundles", []) if isinstance(bundle.get("resourceBundles", []), list) else []

        retrieved_resources: list[dict[str, Any]] = []
        for item in resource_bundles:
            if not isinstance(item, dict):
                continue
            retrieved_resources.append({
                "resourceFile": item.get("resourceFile", ""),
                "pageName": item.get("pageName", ""),
                "variables": [
                    {
                        "variableName": str(variable.get("variableName", "")).strip(),
                        "kind": str(variable.get("kind", "")).strip(),
                        "approvedName": str(variable.get("approvedName", "")).strip(),
                    }
                    for variable in item.get("variables", [])
                    if isinstance(variable, dict) and str(variable.get("variableName", "")).strip()
                ],
                "reviewedKeywords": [
                    {
                        "keywordName": str(keyword.get("keywordName", "")).strip(),
                        "targetElement": str(keyword.get("targetElement", "")).strip(),
                        "action": str(keyword.get("action", "")).strip(),
                    }
                    for keyword in item.get("reviewedKeywords", [])
                    if isinstance(keyword, dict) and str(keyword.get("keywordName", "")).strip()
                ],
                "reusableFlows": [
                    {
                        "flowId": str(flow.get("flowId", "")).strip(),
                        "entryPage": flow.get("entryPage", {}),
                        "targetPage": flow.get("targetPage", {}),
                        "stepCount": len(flow.get("steps", [])) if isinstance(flow.get("steps", []), list) else 0,
                    }
                    for flow in item.get("reusableFlows", [])
                    if isinstance(flow, dict) and str(flow.get("flowId", "")).strip()
                ],
            })

        canonical_context = {
            "workflow": {
                "workflowId": str(workflow.get("workflowId", contract_artifact.get("workflow_id", ""))).strip(),
                "workflowName": str(workflow.get("workflowName", contract_artifact.get("workflow_name", workflow_slug))).strip(),
                "feature": str(workflow.get("feature", contract_artifact.get("feature", ""))).strip(),
                "resourceFiles": [item.get("resourceFile", "") for item in retrieved_resources if item.get("resourceFile", "")],
            },
            "contract": {
                "page": contract_artifact.get("page", {}),
                "entryPage": contract_artifact.get("entry_page", {}),
                "targetPage": contract_artifact.get("target_page", {}),
                "navigationSteps": contract_artifact.get("navigation_steps", []),
                "targetSignals": contract_artifact.get("target_signals", []),
            },
            "resources": retrieved_resources,
            "workflowKnowledge": {
                "resourceKnowledge": workflow_knowledge.get("resourceKnowledge", {}),
                "manualCoverage": workflow_knowledge.get("manualCoverage", {}),
                "automationKnowledge": workflow_knowledge.get("automationKnowledge", {}),
                "provenance": workflow_knowledge.get("provenance", {}),
            },
        }
        return canonical_context
