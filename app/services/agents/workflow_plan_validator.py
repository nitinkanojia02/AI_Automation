from __future__ import annotations

from typing import Any


class WorkflowPlanValidator:
    @staticmethod
    def validate(plan: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(plan, dict):
            return ["execution plan must be an object"]

        workflow = plan.get("workflow", {})
        if not isinstance(workflow, dict):
            errors.append("workflow must be an object")
        else:
            if not str(workflow.get("workflowId", "")).strip():
                errors.append("workflow.workflowId is required")
            if not str(workflow.get("workflowName", "")).strip():
                errors.append("workflow.workflowName is required")

        page_context = plan.get("pageContext", {})
        if not isinstance(page_context, dict):
            errors.append("pageContext must be an object")
        else:
            page = page_context.get("page", {})
            if not isinstance(page, dict):
                errors.append("pageContext.page must be an object")
            elif not str(page.get("name", "")).strip():
                errors.append("pageContext.page.name is required")
            page_state = page_context.get("pageState", {})
            if page_state is not None and not isinstance(page_state, dict):
                errors.append("pageContext.pageState must be an object when provided")
            elif isinstance(page_state, dict) and page_state:
                if not str(page_state.get("page_name", "")).strip():
                    errors.append("pageContext.pageState.page_name is required when pageState is provided")
                if not isinstance(page_state.get("source_artifacts", []), list):
                    errors.append("pageContext.pageState.source_artifacts must be a list when pageState is provided")
                if not isinstance(page_state.get("signals", []), list):
                    errors.append("pageContext.pageState.signals must be a list when pageState is provided")
                if not isinstance(page_state.get("metadata", {}), dict):
                    errors.append("pageContext.pageState.metadata must be an object when pageState is provided")
                elif isinstance(page_state.get("metadata", {}), dict):
                    source_snapshot = page_state.get("metadata", {}).get("sourceSnapshot", {})
                    if source_snapshot is not None and not isinstance(source_snapshot, dict):
                        errors.append("pageContext.pageState.metadata.sourceSnapshot must be an object when provided")
                    state_variants = page_state.get("metadata", {}).get("stateVariants", [])
                    if state_variants is not None and not isinstance(state_variants, list):
                        errors.append("pageContext.pageState.metadata.stateVariants must be a list when provided")

        execution = plan.get("execution", {})
        if not isinstance(execution, dict):
            errors.append("execution must be an object")
            return errors

        navigation_steps = execution.get("navigationSteps", [])
        if not isinstance(navigation_steps, list):
            errors.append("execution.navigationSteps must be a list")
        else:
            for index, step in enumerate(navigation_steps):
                if not isinstance(step, dict):
                    errors.append(f"execution.navigationSteps[{index}] must be an object")
                    continue
                if not str(step.get("action", "")).strip():
                    errors.append(f"execution.navigationSteps[{index}].action is required")

        target_signals = execution.get("targetSignals", [])
        if not isinstance(target_signals, list):
            errors.append("execution.targetSignals must be a list")

        step_count = execution.get("stepCount", 0)
        if not isinstance(step_count, int):
            errors.append("execution.stepCount must be an integer")
        elif isinstance(navigation_steps, list) and step_count != len(navigation_steps):
            errors.append("execution.stepCount must equal the number of navigation steps")

        resources = plan.get("resources", {})
        if not isinstance(resources, dict):
            errors.append("resources must be an object")
        elif not isinstance(resources.get("resourceFiles", []), list):
            errors.append("resources.resourceFiles must be a list")

        rag = plan.get("rag", {})
        if rag is not None and not isinstance(rag, dict):
            errors.append("rag must be an object when provided")

        mcp = plan.get("mcp", {})
        if mcp is not None and not isinstance(mcp, dict):
            errors.append("mcp must be an object when provided")

        provenance = plan.get("provenance", {})
        if provenance is not None and not isinstance(provenance, dict):
            errors.append("provenance must be an object when provided")
        elif isinstance(provenance, dict):
            planning_mode = str(provenance.get("planningMode", "")).strip()
            if not planning_mode:
                errors.append("provenance.planningMode is required when provenance is provided")
            rag_source_preference = provenance.get("ragSourcePreference", [])
            if rag_source_preference is not None and not isinstance(rag_source_preference, list):
                errors.append("provenance.ragSourcePreference must be a list when provided")
            source_snapshot = provenance.get("sourceSnapshot", {})
            if source_snapshot is not None and not isinstance(source_snapshot, dict):
                errors.append("provenance.sourceSnapshot must be an object when provided")
            elif isinstance(source_snapshot, dict):
                workflow_slug = str(source_snapshot.get("workflowSlug", "")).strip()
                if not workflow_slug:
                    errors.append("provenance.sourceSnapshot.workflowSlug is required when sourceSnapshot is provided")
                for field_name in ("workflowArtifact", "contractArtifact"):
                    artifact = source_snapshot.get(field_name, {})
                    if artifact is not None and not isinstance(artifact, dict):
                        errors.append(f"provenance.sourceSnapshot.{field_name} must be an object when provided")

        return errors
