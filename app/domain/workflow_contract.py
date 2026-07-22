from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PageRef:
    name: str
    url: str = ""
    state: str = ""


@dataclass
class WorkflowDependency:
    dependency_type: str
    name: str
    purpose: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReusePolicy:
    resource_files: list[str] = field(default_factory=list)
    page_model_mode: str = "reuse_existing"
    merge_strategy: str = "append_reviewed"


@dataclass
class WorkflowContract:
    workflow_id: str
    workflow_name: str
    source_type: str
    title: str
    feature: str
    page: PageRef
    entry_page: PageRef | None = None
    target_page: PageRef | None = None
    page_state: str = ""
    dependencies: list[WorkflowDependency] = field(default_factory=list)
    reuse_policy: ReusePolicy = field(default_factory=ReusePolicy)
    navigation_steps: list[dict[str, Any]] = field(default_factory=list)
    target_signals: list[dict[str, Any]] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    validation_expectations: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    external_context: dict[str, Any] = field(default_factory=dict)
    raw_workflow: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
