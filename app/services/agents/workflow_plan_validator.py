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

        return errors
