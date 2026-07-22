from app.domain.workflow_contract import WorkflowContract


class WorkflowContractValidator:
    @staticmethod
    def validate(contract: WorkflowContract) -> list[str]:
        errors: list[str] = []
        if not contract.workflow_id:
            errors.append("workflow_id is required")
        if not contract.workflow_name:
            errors.append("workflow_name is required")
        if not contract.page.name:
            errors.append("page.name is required")
        if not contract.reuse_policy.resource_files:
            errors.append("at least one resource file is required")
        if contract.entry_page and not contract.entry_page.name:
            errors.append("entry_page.name is required when entry_page is provided")
        if contract.target_page and not contract.target_page.name:
            errors.append("target_page.name is required when target_page is provided")
        if contract.navigation_steps and not (contract.entry_page and contract.entry_page.url):
            errors.append("entry_page.url is required when navigation steps are present")

        for index, step in enumerate(contract.navigation_steps or []):
            if not isinstance(step, dict):
                errors.append(f"navigation_steps[{index}] must be an object")
                continue
            action = str(step.get("action", "")).strip()
            if not action:
                errors.append(f"navigation_steps[{index}].action is required")
                continue
            if action == "reuseApprovedEntryContext":
                flow_id = str(step.get("flowId", "")).strip()
                if not flow_id:
                    errors.append(f"navigation_steps[{index}].flowId is required for reuseApprovedEntryContext")

        return errors
