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

        execution_runtime = plan.get("executionRuntime", {})
        if execution_runtime is not None and not isinstance(execution_runtime, dict):
            errors.append("executionRuntime must be an object when provided")
        elif isinstance(execution_runtime, dict) and execution_runtime:
            runtime_page_state = execution_runtime.get("pageState", {})
            runtime_mcp = execution_runtime.get("mcp", {})
            if runtime_page_state is not None and not isinstance(runtime_page_state, dict):
                errors.append("executionRuntime.pageState must be an object when provided")
            elif isinstance(runtime_page_state, dict) and runtime_page_state:
                source_snapshot = runtime_page_state.get("sourceSnapshot", {})
                state_variants = runtime_page_state.get("stateVariants", [])
                if source_snapshot is not None and not isinstance(source_snapshot, dict):
                    errors.append("executionRuntime.pageState.sourceSnapshot must be an object when provided")
                if state_variants is not None and not isinstance(state_variants, list):
                    errors.append("executionRuntime.pageState.stateVariants must be a list when provided")
            if runtime_mcp is not None and not isinstance(runtime_mcp, dict):
                errors.append("executionRuntime.mcp must be an object when provided")
            elif isinstance(runtime_mcp, dict) and runtime_mcp:
                runtime_mcp_provenance = runtime_mcp.get("provenance", {})
                if runtime_mcp_provenance is not None and not isinstance(runtime_mcp_provenance, dict):
                    errors.append("executionRuntime.mcp.provenance must be an object when provided")
                runtime_mcp_adapter = runtime_mcp.get("adapter", {})
                runtime_mcp_dispatch = runtime_mcp.get("dispatch", {})
                runtime_mcp_execution = runtime_mcp.get("execution", {})
                if runtime_mcp_adapter is not None and not isinstance(runtime_mcp_adapter, dict):
                    errors.append("executionRuntime.mcp.adapter must be an object when provided")
                if runtime_mcp_dispatch is not None and not isinstance(runtime_mcp_dispatch, dict):
                    errors.append("executionRuntime.mcp.dispatch must be an object when provided")
                if runtime_mcp_execution is not None and not isinstance(runtime_mcp_execution, dict):
                    errors.append("executionRuntime.mcp.execution must be an object when provided")

        mcp = plan.get("mcp", {})
        if mcp is not None and not isinstance(mcp, dict):
            errors.append("mcp must be an object when provided")
        elif isinstance(mcp, dict):
            provenance = mcp.get("provenance", {})
            if provenance is not None and not isinstance(provenance, dict):
                errors.append("mcp.provenance must be an object when provided")
            adapter = mcp.get("adapter", {})
            if adapter is not None and not isinstance(adapter, dict):
                errors.append("mcp.adapter must be an object when provided")
            elif isinstance(adapter, dict) and adapter:
                if not isinstance(adapter.get("enabled", False), bool):
                    errors.append("mcp.adapter.enabled must be a boolean when adapter is provided")
                if not str(adapter.get("adapterType", "")).strip():
                    errors.append("mcp.adapter.adapterType is required when adapter is provided")
                if not str(adapter.get("selectionMode", "")).strip():
                    errors.append("mcp.adapter.selectionMode is required when adapter is provided")
                capability_scope = adapter.get("capabilityScope", [])
                if capability_scope is not None and not isinstance(capability_scope, list):
                    errors.append("mcp.adapter.capabilityScope must be a list when provided")
                adapter_provenance = adapter.get("provenance", {})
                if adapter_provenance is not None and not isinstance(adapter_provenance, dict):
                    errors.append("mcp.adapter.provenance must be an object when provided")
            dispatch = mcp.get("dispatch", {})
            execution_mode = mcp.get("execution", {})
            if execution_mode is not None and not isinstance(execution_mode, dict):
                errors.append("mcp.execution must be an object when provided")
            elif isinstance(execution_mode, dict) and execution_mode:
                if not str(execution_mode.get("dispatchMode", "")).strip():
                    errors.append("mcp.execution.dispatchMode is required when execution is provided")
                if not str(execution_mode.get("executionMode", "")).strip():
                    errors.append("mcp.execution.executionMode is required when execution is provided")
            if dispatch is not None and not isinstance(dispatch, dict):
                errors.append("mcp.dispatch must be an object when provided")
            elif isinstance(dispatch, dict) and dispatch:
                selected_adapter = dispatch.get("selectedAdapter", {})
                fallback_adapter = dispatch.get("fallbackAdapter", {})
                if not isinstance(selected_adapter, dict) or not selected_adapter:
                    errors.append("mcp.dispatch.selectedAdapter must be a non-empty object when dispatch is provided")
                if not isinstance(fallback_adapter, dict) or not fallback_adapter:
                    errors.append("mcp.dispatch.fallbackAdapter must be a non-empty object when dispatch is provided")
                if not str(dispatch.get("dispatchMode", "")).strip():
                    errors.append("mcp.dispatch.dispatchMode is required when dispatch is provided")
                if not str(dispatch.get("executionMode", "")).strip():
                    errors.append("mcp.dispatch.executionMode is required when dispatch is provided")
                if isinstance(execution_mode, dict) and execution_mode:
                    if dispatch.get("dispatchMode") != execution_mode.get("dispatchMode"):
                        errors.append("mcp.dispatch.dispatchMode must match mcp.execution.dispatchMode when both are provided")
                    if dispatch.get("executionMode") != execution_mode.get("executionMode"):
                        errors.append("mcp.dispatch.executionMode must match mcp.execution.executionMode when both are provided")
                for dispatch_name, dispatch_adapter in (("selectedAdapter", selected_adapter), ("fallbackAdapter", fallback_adapter)):
                    if isinstance(dispatch_adapter, dict):
                        if not isinstance(dispatch_adapter.get("enabled", False), bool):
                            errors.append(f"mcp.dispatch.{dispatch_name}.enabled must be a boolean when provided")
                        if not str(dispatch_adapter.get("adapterType", "")).strip():
                            errors.append(f"mcp.dispatch.{dispatch_name}.adapterType is required when provided")
                        if not str(dispatch_adapter.get("selectionMode", "")).strip():
                            errors.append(f"mcp.dispatch.{dispatch_name}.selectionMode is required when provided")
                        capability_scope = dispatch_adapter.get("capabilityScope", [])
                        if capability_scope is not None and not isinstance(capability_scope, list):
                            errors.append(f"mcp.dispatch.{dispatch_name}.capabilityScope must be a list when provided")
                        dispatch_provenance = dispatch_adapter.get("provenance", {})
                        if dispatch_provenance is not None and not isinstance(dispatch_provenance, dict):
                            errors.append(f"mcp.dispatch.{dispatch_name}.provenance must be an object when provided")

        if isinstance(execution_runtime, dict) and execution_runtime:
            runtime_page_state = execution_runtime.get("pageState", {}) if isinstance(execution_runtime.get("pageState", {}), dict) else {}
            runtime_mcp = execution_runtime.get("mcp", {}) if isinstance(execution_runtime.get("mcp", {}), dict) else {}
            plan_page_state = page_context.get("pageState", {}) if isinstance(page_context.get("pageState", {}), dict) else {}
            if runtime_page_state and plan_page_state:
                if runtime_page_state.get("pageName", "") != plan_page_state.get("page_name", ""):
                    errors.append("executionRuntime.pageState.pageName must match pageContext.pageState.page_name when both are provided")
                if runtime_page_state.get("sourceSnapshot", {}) != ((plan_page_state.get("metadata", {}) or {}).get("sourceSnapshot", {}) if isinstance(plan_page_state.get("metadata", {}), dict) else {}):
                    errors.append("executionRuntime.pageState.sourceSnapshot must match pageContext.pageState.metadata.sourceSnapshot when both are provided")
                if runtime_page_state.get("stateVariants", []) != ((plan_page_state.get("metadata", {}) or {}).get("stateVariants", []) if isinstance(plan_page_state.get("metadata", {}), dict) else []):
                    errors.append("executionRuntime.pageState.stateVariants must match pageContext.pageState.metadata.stateVariants when both are provided")
            if runtime_mcp and isinstance(mcp, dict) and mcp:
                if runtime_mcp.get("enabled", False) != mcp.get("enabled", False):
                    errors.append("executionRuntime.mcp.enabled must match mcp.enabled when both are provided")
                if runtime_mcp.get("provenance", {}) != mcp.get("provenance", {}):
                    errors.append("executionRuntime.mcp.provenance must match mcp.provenance when both are provided")
                if runtime_mcp.get("adapter", {}) != mcp.get("adapter", {}):
                    errors.append("executionRuntime.mcp.adapter must match mcp.adapter when both are provided")
                if runtime_mcp.get("dispatch", {}) != mcp.get("dispatch", {}):
                    errors.append("executionRuntime.mcp.dispatch must match mcp.dispatch when both are provided")
                if runtime_mcp.get("execution", {}) != mcp.get("execution", {}):
                    errors.append("executionRuntime.mcp.execution must match mcp.execution when both are provided")

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
