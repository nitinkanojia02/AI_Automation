from app.domain.workflow_contract import PageRef, ReusePolicy, WorkflowContract, WorkflowDependency


class WorkflowContractBuilder:
    @staticmethod
    def build(workflow: dict) -> WorkflowContract:
        pages = workflow.get("pages", []) if isinstance(workflow.get("pages"), list) else []
        first_page = pages[0] if pages and isinstance(pages[0], dict) else {}
        page = PageRef(
            name=str(first_page.get("name", "")).strip(),
            url=str(first_page.get("url", "")).strip(),
            state=str(first_page.get("state", "")).strip(),
        )

        entry_payload = workflow.get("entryPage") if isinstance(workflow.get("entryPage"), dict) else None
        target_payload = workflow.get("targetPage") if isinstance(workflow.get("targetPage"), dict) else None
        entry_page = PageRef(
            name=str(entry_payload.get("name", "")).strip(),
            url=str(entry_payload.get("url", "")).strip(),
            state=str(entry_payload.get("state", "")).strip(),
        ) if entry_payload else None
        target_page = PageRef(
            name=str(target_payload.get("name", "")).strip(),
            url=str(target_payload.get("url", "")).strip(),
            state=str(target_payload.get("state", "")).strip(),
        ) if target_payload else None

        source = workflow.get("source", {}) if isinstance(workflow.get("source"), dict) else {}
        external_context = workflow.get("externalContext", {}) if isinstance(workflow.get("externalContext"), dict) else {}
        dependencies = []
        if source.get("provider") == "azure_devops":
            dependencies.append(WorkflowDependency(dependency_type="external_story", name="azure_devops", purpose="workflow_input"))
        if workflow.get("entryPage"):
            dependencies.append(WorkflowDependency(dependency_type="page", name=str(entry_payload.get("name", "")).strip(), purpose="entry_page"))

        return WorkflowContract(
            workflow_id=str(workflow.get("workflowId", "")).strip(),
            workflow_name=str(workflow.get("workflowName", "")).strip(),
            source_type=str(source.get("provider", "manual")).strip() or "manual",
            title=str(workflow.get("workflowName", "")).strip(),
            feature=str(workflow.get("feature", "")).strip(),
            page=page,
            entry_page=entry_page,
            target_page=target_page,
            page_state=str(first_page.get("state", "")).strip(),
            dependencies=dependencies,
            reuse_policy=ReusePolicy(
                resource_files=[str(item).strip() for item in workflow.get("resourceFiles", []) if str(item).strip()],
                page_model_mode="reuse_existing",
                merge_strategy="append_reviewed",
            ),
            navigation_steps=workflow.get("navigationSteps", []) if isinstance(workflow.get("navigationSteps"), list) else [],
            target_signals=workflow.get("targetPageSignals", []) if isinstance(workflow.get("targetPageSignals"), list) else [],
            business_rules=workflow.get("observedPreconditions", []) if isinstance(workflow.get("observedPreconditions"), list) else [],
            validation_expectations=workflow.get("observedValidations", []) if isinstance(workflow.get("observedValidations"), list) else [],
            acceptance_criteria=external_context.get("acceptanceCriteria", []) if isinstance(external_context.get("acceptanceCriteria"), list) else [],
            external_context=external_context,
            raw_workflow=workflow,
        )
