from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.platform.logger import PlatformLogger


class RagContextService:
    def __init__(self, knowledge_repository: KnowledgeRepository, logger: PlatformLogger | None = None):
        self.knowledge_repository = knowledge_repository
        self.logger = logger or PlatformLogger(__name__)

    @staticmethod
    def _first_non_empty(*values: Any, default: Any = "") -> Any:
        for value in values:
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    return cleaned
                continue
            if isinstance(value, dict) and value:
                return value
            if isinstance(value, list) and value:
                return value
            if value not in (None, ""):
                return value
        return default

    @staticmethod
    def _dedupe_list(values: list[Any]) -> list[Any]:
        result: list[Any] = []
        seen: set[str] = set()
        for value in values:
            marker = repr(value)
            if marker in seen:
                continue
            seen.add(marker)
            result.append(value)
        return result

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

        workflow_resource_files = workflow.get("resourceFiles", []) if isinstance(workflow.get("resourceFiles", []), list) else []
        contract_resource_files = contract_artifact.get("reuse_policy", {}).get("resource_files", []) if isinstance(contract_artifact.get("reuse_policy", {}), dict) else []
        resource_files = self._dedupe_list([
            *[item for item in contract_resource_files if str(item).strip()],
            *[item for item in workflow_resource_files if str(item).strip()],
            *[item.get("resourceFile", "") for item in retrieved_resources if item.get("resourceFile", "")],
        ])

        canonical_context = {
            "workflow": {
                "workflowId": self._first_non_empty(contract_artifact.get("workflow_id", ""), workflow.get("workflowId", ""), default=""),
                "workflowName": self._first_non_empty(contract_artifact.get("workflow_name", ""), workflow.get("workflowName", ""), workflow_slug, default=workflow_slug),
                "feature": self._first_non_empty(contract_artifact.get("feature", ""), workflow.get("feature", ""), default=""),
                "resourceFiles": resource_files,
            },
            "contract": {
                "page": self._first_non_empty(contract_artifact.get("page", {}), workflow.get("pages", [{}])[0] if isinstance(workflow.get("pages", []), list) and workflow.get("pages") else {}, default={}),
                "entryPage": self._first_non_empty(contract_artifact.get("entry_page", {}), workflow.get("entryPage", {}), default={}),
                "targetPage": self._first_non_empty(contract_artifact.get("target_page", {}), workflow.get("targetPage", {}), default={}),
                "navigationSteps": self._first_non_empty(contract_artifact.get("navigation_steps", []), workflow.get("navigationSteps", []), default=[]),
                "targetSignals": self._first_non_empty(contract_artifact.get("target_signals", []), workflow.get("targetPageSignals", []), default=[]),
            },
            "resources": retrieved_resources,
            "workflowKnowledge": {
                "resourceKnowledge": workflow_knowledge.get("resourceKnowledge", {}),
                "manualCoverage": workflow_knowledge.get("manualCoverage", {}),
                "automationKnowledge": workflow_knowledge.get("automationKnowledge", {}),
                "provenance": workflow_knowledge.get("provenance", {}),
            },
            "provenance": {
                "sourcePreference": [
                    "contract",
                    "workflow",
                    "resourceBundles",
                    "workflowKnowledge",
                ],
                "resourceBundleCount": len(retrieved_resources),
                "workflowKnowledgePresent": bool(workflow_knowledge),
            },
        }
        self.logger.info(
            "rag_context_built",
            workflow_slug=workflow_slug,
            resource_bundle_count=len(retrieved_resources),
            resource_file_count=len(resource_files),
            workflow_knowledge_present=bool(workflow_knowledge),
            contract_present=bool(contract_artifact),
            workflow_present=bool(workflow),
        )
        return canonical_context
