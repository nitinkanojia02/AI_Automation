from __future__ import annotations

from typing import Any

from app.domain.workflow_contract import WorkflowContract
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.platform.logger import PlatformLogger


class RagContextService:
    MAX_VARIABLES_PER_RESOURCE = 25
    MAX_KEYWORDS_PER_RESOURCE = 25
    MAX_FLOWS_PER_RESOURCE = 25
    MAX_NAVIGATION_STEPS = 25
    MAX_TARGET_SIGNALS = 25

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

    @staticmethod
    def _limit_list(values: list[Any], max_items: int) -> list[Any]:
        return values[:max_items] if max_items >= 0 else list(values)

    @staticmethod
    def _normalize_page_reference(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        normalized: dict[str, Any] = {}
        for key in ("name", "url", "state"):
            raw = value.get(key, "")
            cleaned = str(raw).strip() if isinstance(raw, str) else raw
            if cleaned not in ("", None, {}, []):
                normalized[key] = cleaned
        return normalized

    @staticmethod
    def _normalize_navigation_step(step: Any) -> dict[str, Any]:
        if not isinstance(step, dict):
            return {}
        normalized: dict[str, Any] = {}
        for key in ("action", "page", "element", "value", "flowId"):
            raw = step.get(key, "")
            cleaned = str(raw).strip() if isinstance(raw, str) else raw
            if cleaned not in ("", None, {}, []):
                normalized[key] = cleaned
        return normalized

    @staticmethod
    def _normalize_target_signal(signal: Any) -> dict[str, Any]:
        if not isinstance(signal, dict):
            return {}
        normalized: dict[str, Any] = {}
        for key in ("type", "value"):
            raw = signal.get(key, "")
            cleaned = str(raw).strip() if isinstance(raw, str) else raw
            if cleaned not in ("", None, {}, []):
                normalized[key] = cleaned
        return normalized

    @staticmethod
    def _normalize_workflow_knowledge(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(item, dict) and item:
                normalized[key] = item
        return normalized

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
            resource_file = str(item.get("resourceFile", "")).strip()
            page_name = str(item.get("pageName", "")).strip()
            variables = self._limit_list([
                {
                    "variableName": str(variable.get("variableName", "")).strip(),
                    "kind": str(variable.get("kind", "")).strip(),
                    "approvedName": str(variable.get("approvedName", "")).strip(),
                }
                for variable in item.get("variables", [])
                if isinstance(variable, dict) and str(variable.get("variableName", "")).strip()
            ], self.MAX_VARIABLES_PER_RESOURCE)
            reviewed_keywords = self._limit_list([
                {
                    "keywordName": str(keyword.get("keywordName", "")).strip(),
                    "targetElement": str(keyword.get("targetElement", "")).strip(),
                    "action": str(keyword.get("action", "")).strip(),
                }
                for keyword in item.get("reviewedKeywords", [])
                if isinstance(keyword, dict) and str(keyword.get("keywordName", "")).strip()
            ], self.MAX_KEYWORDS_PER_RESOURCE)
            reusable_flows = self._limit_list([
                {
                    "flowId": str(flow.get("flowId", "")).strip(),
                    "entryPage": self._normalize_page_reference(flow.get("entryPage", {})),
                    "targetPage": self._normalize_page_reference(flow.get("targetPage", {})),
                    "stepCount": len(flow.get("steps", [])) if isinstance(flow.get("steps", []), list) else 0,
                }
                for flow in item.get("reusableFlows", [])
                if isinstance(flow, dict) and str(flow.get("flowId", "")).strip()
            ], self.MAX_FLOWS_PER_RESOURCE)
            retrieved_resources.append({
                "resourceFile": resource_file,
                "pageName": page_name,
                "variables": variables,
                "reviewedKeywords": reviewed_keywords,
                "reusableFlows": reusable_flows,
            })

        workflow_resource_files = workflow.get("resourceFiles", []) if isinstance(workflow.get("resourceFiles", []), list) else []
        contract_resource_files = contract_artifact.get("reuse_policy", {}).get("resource_files", []) if isinstance(contract_artifact.get("reuse_policy", {}), dict) else []
        resource_files = self._dedupe_list([
            *[item for item in contract_resource_files if str(item).strip()],
            *[item for item in workflow_resource_files if str(item).strip()],
            *[item.get("resourceFile", "") for item in retrieved_resources if item.get("resourceFile", "")],
        ])

        workflow_page = workflow.get("pages", [{}])[0] if isinstance(workflow.get("pages", []), list) and workflow.get("pages") else {}
        navigation_steps = self._limit_list([
            normalized_step
            for normalized_step in [
                self._normalize_navigation_step(item)
                for item in self._first_non_empty(contract_artifact.get("navigation_steps", []), workflow.get("navigationSteps", []), default=[])
            ]
            if normalized_step
        ], self.MAX_NAVIGATION_STEPS)
        target_signals = self._limit_list([
            normalized_signal
            for normalized_signal in [
                self._normalize_target_signal(item)
                for item in self._first_non_empty(contract_artifact.get("target_signals", []), workflow.get("targetPageSignals", []), default=[])
            ]
            if normalized_signal
        ], self.MAX_TARGET_SIGNALS)
        canonical_context = {
            "workflow": {
                "workflowId": self._first_non_empty(contract_artifact.get("workflow_id", ""), workflow.get("workflowId", ""), default=""),
                "workflowName": self._first_non_empty(contract_artifact.get("workflow_name", ""), workflow.get("workflowName", ""), workflow_slug, default=workflow_slug),
                "feature": self._first_non_empty(contract_artifact.get("feature", ""), workflow.get("feature", ""), default=""),
                "resourceFiles": resource_files,
            },
            "contract": {
                "page": self._normalize_page_reference(self._first_non_empty(contract_artifact.get("page", {}), workflow_page, default={})),
                "entryPage": self._normalize_page_reference(self._first_non_empty(contract_artifact.get("entry_page", {}), workflow.get("entryPage", {}), default={})),
                "targetPage": self._normalize_page_reference(self._first_non_empty(contract_artifact.get("target_page", {}), workflow.get("targetPage", {}), default={})),
                "navigationSteps": navigation_steps,
                "targetSignals": target_signals,
            },
            "resources": retrieved_resources,
            "workflowKnowledge": {
                "resourceKnowledge": self._normalize_workflow_knowledge(workflow_knowledge.get("resourceKnowledge", {})),
                "manualCoverage": self._normalize_workflow_knowledge(workflow_knowledge.get("manualCoverage", {})),
                "automationKnowledge": self._normalize_workflow_knowledge(workflow_knowledge.get("automationKnowledge", {})),
                "provenance": self._normalize_workflow_knowledge(workflow_knowledge.get("provenance", {})),
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
                "limits": {
                    "variablesPerResource": self.MAX_VARIABLES_PER_RESOURCE,
                    "keywordsPerResource": self.MAX_KEYWORDS_PER_RESOURCE,
                    "flowsPerResource": self.MAX_FLOWS_PER_RESOURCE,
                    "navigationSteps": self.MAX_NAVIGATION_STEPS,
                    "targetSignals": self.MAX_TARGET_SIGNALS,
                },
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
