from pathlib import Path
from urllib.parse import urlparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys

import requests
import logging
from openpyxl import Workbook

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.datastructures import FormData
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

from app.config.feature_flags import FEATURE_FLAGS
from app.repositories.execution_plan_repository import ExecutionPlanRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.page_state_repository import PageStateRepository
from app.repositories.resource_repository import ResourceRepository
from app.repositories.mcp_repository import McpRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.services.agents.resource_reuse_agent import ResourceReuseAgent
from app.services.agents.workflow_planning_agent import WorkflowPlanningAgent
from app.services.agents.workflow_plan_validator import WorkflowPlanValidator
from app.services.context.rag_context_service import RagContextService
from app.services.platform.logger import PlatformLogger
from app.services.platform.mcp_service import McpService
from app.services.workflows.page_state_merge_service import PageStateMergeService
from app.services.workflows.page_state_service import PageStateService
from app.services.workflows.workflow_contract_builder import WorkflowContractBuilder
from app.services.workflows.workflow_contract_validator import WorkflowContractValidator

from scripts.generate_manual_tests_json import (
    build_prompt as build_manual_prompt,
    call_devex_ai,
    get_ai_token as get_manual_ai_token,
    load_config as load_manual_config,
    normalize_manual_test,
    validate_config as validate_manual_config,
)
from scripts.workflow_knowledge import save_workflow_knowledge, build_workflow_knowledge_context, discover_relevant_workflow_knowledge
from scripts.artifact_reuse import analyze_keyword_artifact_reuse, analyze_reuse_conflicts, normalize_name_tokens
from scripts.generate_robot_from_manual import (
    build_manual_refiner_prompt,
    build_manual_review_prompt,
    build_prompt as build_robot_prompt,
    build_review_prompt,
    build_validation_review_prompt,
    call_ai_chat,
    collect_resource_validation_keywords,
    extract_keywords_from_resource,
    extract_variables_from_resource,
    get_ai_token as get_robot_ai_token,
    load_json as load_robot_ai_json,
    parse_resource_file,
    validate_config as validate_robot_config,
    validate_manual_content,
    validate_resource_content,
    validate_robot_alignment_with_resource_context,
    validate_robot_content,
)
BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = BASE_DIR / "workflow_inputs"
MANUAL_DIR = BASE_DIR / "manual_tests"
TESTS_DIR = BASE_DIR / "tests"
POM_DIR = BASE_DIR / "pom_pages"
PROMPTS_DIR = BASE_DIR / "prompts"
WORKFLOW_STORY_NORMALIZER_PROMPT_PATH = PROMPTS_DIR / "workflow_story_normalizer.md"


def get_page_dir(page_name: str) -> Path:
    return POM_DIR / page_name


def get_page_metadata_dir(page_name: str) -> Path:
    return get_page_dir(page_name) / "metadata"


def get_manual_workflow_dir(workflow_name: str) -> Path:
    return MANUAL_DIR / workflow_name


def get_manual_json_path(workflow_name: str) -> Path:
    workflow_dir = get_manual_workflow_dir(workflow_name)
    return workflow_dir / f"{workflow_name}.json"


def get_manual_excel_path(workflow_name: str) -> Path:
    workflow_dir = get_manual_workflow_dir(workflow_name)
    return workflow_dir / f"{workflow_name}_approved_manual_tests.xlsx"


def get_automation_path(workflow_name: str, workflow: dict | None = None) -> Path:
    base_name = derive_workflow_artifact_slug(workflow, workflow_name)
    return TESTS_DIR / f"{base_name}_tests.robot"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
CONFIG_PATH = BASE_DIR / "config" / "page_model_config.json"

app = FastAPI(title="WashTab Automation MVP")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
logger = logging.getLogger(__name__)
platform_logger = PlatformLogger(__name__)
workflow_repository = WorkflowRepository(WORKFLOW_DIR)
execution_plan_repository = ExecutionPlanRepository(WORKFLOW_DIR)
page_state_repository = PageStateRepository(POM_DIR)
page_state_merge_service = PageStateMergeService()
page_state_service = PageStateService(
    page_state_repository,
    page_state_merge_service,
    persist_descriptors=FEATURE_FLAGS.enable_state_merge,
    logger=platform_logger,
)
resource_repository = ResourceRepository(BASE_DIR)
knowledge_repository = KnowledgeRepository(BASE_DIR, resource_repository)
resource_reuse_agent = ResourceReuseAgent(resource_repository)
workflow_planning_agent = WorkflowPlanningAgent(page_state_service)
workflow_plan_validator = WorkflowPlanValidator()
rag_context_service = RagContextService(knowledge_repository, platform_logger)
mcp_repository = McpRepository(BASE_DIR)
mcp_service = McpService(FEATURE_FLAGS.enable_mcp, mcp_repository)


def build_runtime_workflow_context(
    workflow_payload: dict,
    workflow_slug: str,
    attach_stage: str,
    resource_files: list[str] | None = None,
) -> tuple[object | None, dict]:
    if not FEATURE_FLAGS.enable_workflow_contracts:
        return None, dict(workflow_payload)

    runtime_context = dict(workflow_payload)
    derived_context = _derive_structured_workflow_context(runtime_context)
    for key in ("entryPage", "targetPage", "navigationSteps", "targetPageSignals"):
        current_value = runtime_context.get(key)
        if key in ("navigationSteps", "targetPageSignals"):
            if not isinstance(current_value, list) or not current_value:
                runtime_context[key] = derived_context.get(key, [])
        else:
            if not isinstance(current_value, dict) or not current_value:
                runtime_context[key] = derived_context.get(key, {})

    if not isinstance(runtime_context.get("resourceFiles"), list) or not runtime_context.get("resourceFiles"):
        runtime_context["resourceFiles"] = derived_context.get("resourceFiles", [])

    ensure_workflow_contract_artifact(workflow_slug, runtime_context)
    merged_resource_files: list[str] = []
    for item in (resource_files if isinstance(resource_files, list) else runtime_context.get("resourceFiles", [])) or []:
        normalized = clean_text(str(item)).replace("\\", "/")
        if normalized and normalized not in merged_resource_files:
            merged_resource_files.append(normalized)

    contract = WorkflowContractBuilder.build(runtime_context)
    contract.reuse_policy.resource_files = merged_resource_files

    if FEATURE_FLAGS.enable_rag:
        runtime_context["ragContext"] = rag_context_service.build_context(workflow_slug)
        rag_provenance = runtime_context["ragContext"].get("provenance", {}) if isinstance(runtime_context["ragContext"], dict) else {}
        platform_logger.info(
            "rag_context_attached",
            workflow_slug=workflow_slug,
            attach_stage=attach_stage,
            source_preference=rag_provenance.get("sourcePreference", []),
            canonical_freshness=rag_provenance.get("canonicalFreshness", {}),
            resource_bundle_count=rag_provenance.get("resourceBundleCount", 0),
            workflow_knowledge_present=rag_provenance.get("workflowKnowledgePresent", False),
        )

    if FEATURE_FLAGS.enable_mcp:
        runtime_context["mcpContext"] = mcp_service.build_runtime_context()
        platform_logger.info(
            "mcp_context_attached",
            workflow_slug=workflow_slug,
            attach_stage=attach_stage,
            enabled=runtime_context["mcpContext"].get("enabled", False),
            provider=runtime_context["mcpContext"].get("provider", ""),
            transport=runtime_context["mcpContext"].get("transport", ""),
            capability_scope=runtime_context["mcpContext"].get("capabilityScope", []),
            provenance=runtime_context["mcpContext"].get("provenance", {}),
        )

    return contract, runtime_context


def attach_execution_plan_if_enabled(
    workflow_slug: str,
    contract,
    runtime_context: dict,
    attach_stage: str,
) -> dict:
    if not FEATURE_FLAGS.enable_agents or contract is None:
        return runtime_context

    enriched_context = dict(runtime_context)
    enriched_context["executionPlan"] = resolve_execution_plan(
        workflow_slug=workflow_slug,
        contract=contract,
        navigation_steps=enriched_context.get("navigationSteps", []) if isinstance(enriched_context.get("navigationSteps"), list) else [],
        rag_context=enriched_context.get("ragContext", {}) if isinstance(enriched_context.get("ragContext"), dict) else {},
        attach_stage=attach_stage,
        target_signals=enriched_context.get("targetPageSignals", []) if isinstance(enriched_context.get("targetPageSignals"), list) else [],
        mcp_context=enriched_context.get("mcpContext", {}) if isinstance(enriched_context.get("mcpContext"), dict) else {},
    )
    return enriched_context


def build_and_validate_execution_plan(
    workflow_slug: str,
    contract,
    navigation_steps: list[dict] | None = None,
    rag_context: dict | None = None,
    attach_stage: str = "",
    target_signals: list[dict] | None = None,
    mcp_context: dict | None = None,
):
    source_snapshot = execution_plan_repository.get_source_snapshot(workflow_slug)
    resolved_mcp_context = mcp_context if isinstance(mcp_context, dict) else (mcp_service.build_runtime_context() if FEATURE_FLAGS.enable_mcp else {})
    runtime_page_state = page_state_service.build_state_descriptor(contract) if FEATURE_FLAGS.enable_state_merge else {}
    execution_runtime_attachment = mcp_service.build_execution_runtime_attachment(
        runtime_context=resolved_mcp_context,
        page_state=runtime_page_state,
    )
    plan = workflow_planning_agent.build_plan(
        contract,
        navigation_steps,
        rag_context,
        plan_context={
            "navigationSource": "runtime" if navigation_steps else "contract",
            "targetSignalSource": "runtime" if target_signals else "contract",
            "sourceSnapshot": source_snapshot,
            "mcpContext": resolved_mcp_context,
            "executionRuntime": execution_runtime_attachment,
        },
    )
    if isinstance(target_signals, list):
        plan.setdefault("execution", {})["targetSignals"] = [
            dict(item) for item in target_signals if isinstance(item, dict)
        ]
    plan.setdefault("execution", {})["stepCount"] = len(plan.get("execution", {}).get("navigationSteps", []))
    plan_errors = workflow_plan_validator.validate(plan)
    if plan_errors:
        raise HTTPException(status_code=400, detail="Execution plan validation failed: " + "; ".join(plan_errors))

    if FEATURE_FLAGS.enable_execution_plan_persistence:
        execution_plan_repository.save_plan(workflow_slug, plan)

    plan_provenance = plan.get("provenance", {}) if isinstance(plan.get("provenance", {}), dict) else {}
    platform_logger.info(
        "execution_plan_attached",
        workflow_slug=workflow_slug,
        attach_stage=attach_stage,
        step_count=((plan.get("execution", {}) or {}).get("stepCount", 0)),
        navigation_source=plan_provenance.get("navigationSource", ""),
        target_signal_source=plan_provenance.get("targetSignalSource", ""),
        rag_attached=plan_provenance.get("ragAttached", False),
        source_snapshot=plan_provenance.get("sourceSnapshot", {}),
        mcp_adapter=((plan.get("mcp", {}) or {}).get("adapter", {}) if isinstance(plan.get("mcp", {}), dict) else {}),
        mcp_dispatch=((plan.get("mcp", {}) or {}).get("dispatch", {}) if isinstance(plan.get("mcp", {}), dict) else {}),
        execution_runtime=(plan.get("executionRuntime", {}) if isinstance(plan.get("executionRuntime", {}), dict) else {}),
        persisted=FEATURE_FLAGS.enable_execution_plan_persistence,
    )
    return plan


def resolve_execution_plan(
    workflow_slug: str,
    contract,
    navigation_steps: list[dict] | None = None,
    rag_context: dict | None = None,
    attach_stage: str = "",
    target_signals: list[dict] | None = None,
    mcp_context: dict | None = None,
):
    runtime_navigation_steps = [dict(item) for item in (navigation_steps or []) if isinstance(item, dict)]
    runtime_target_signals = [dict(item) for item in (target_signals or []) if isinstance(item, dict)]
    runtime_page_state = page_state_service.build_state_descriptor(contract) if FEATURE_FLAGS.enable_state_merge else {}
    runtime_mcp_context = mcp_context if isinstance(mcp_context, dict) else (mcp_service.build_runtime_context() if FEATURE_FLAGS.enable_mcp else {})
    runtime_mcp_provenance = runtime_mcp_context.get("provenance", {}) if isinstance(runtime_mcp_context.get("provenance", {}), dict) else {}

    persisted_plan = execution_plan_repository.load_plan(workflow_slug) if FEATURE_FLAGS.enable_execution_plan_persistence else None
    if persisted_plan is not None:
        freshness = execution_plan_repository.get_plan_freshness_context(workflow_slug)
        persisted_provenance = persisted_plan.get("provenance", {}) if isinstance(persisted_plan.get("provenance", {}), dict) else {}
        persisted_source_snapshot = persisted_provenance.get("sourceSnapshot", {}) if isinstance(persisted_provenance.get("sourceSnapshot", {}), dict) else {}
        if execution_plan_repository.is_plan_stale(workflow_slug):
            platform_logger.info(
                "execution_plan_persisted_stale",
                workflow_slug=workflow_slug,
                attach_stage=attach_stage,
                freshness=freshness,
                source_snapshot=persisted_source_snapshot,
            )
        elif not execution_plan_repository.snapshots_match(workflow_slug, persisted_source_snapshot):
            platform_logger.info(
                "execution_plan_persisted_snapshot_mismatch",
                workflow_slug=workflow_slug,
                attach_stage=attach_stage,
                source_snapshot=persisted_source_snapshot,
                current_source_snapshot=execution_plan_repository.get_source_snapshot(workflow_slug),
                freshness=freshness,
            )
        else:
            persisted_errors = workflow_plan_validator.validate(persisted_plan)
            if not persisted_errors:
                persisted_execution = persisted_plan.get("execution", {}) if isinstance(persisted_plan.get("execution", {}), dict) else {}
                persisted_navigation_steps = [
                    dict(item) for item in (persisted_execution.get("navigationSteps", []) or []) if isinstance(item, dict)
                ]
                persisted_target_signals = [
                    dict(item) for item in (persisted_execution.get("targetSignals", []) or []) if isinstance(item, dict)
                ]
                page_state_alignment = page_state_service.are_plan_states_aligned(
                    persisted_plan=persisted_plan,
                    runtime_page_state=runtime_page_state,
                )
                persisted_page_state_snapshot = page_state_alignment.get("persistedPageStateSnapshot", {}) if isinstance(page_state_alignment.get("persistedPageStateSnapshot", {}), dict) else {}
                runtime_page_state_snapshot = page_state_alignment.get("runtimePageStateSnapshot", {}) if isinstance(page_state_alignment.get("runtimePageStateSnapshot", {}), dict) else {}
                mcp_alignment = mcp_service.are_plan_contexts_aligned(
                    persisted_plan=persisted_plan,
                    runtime_context=runtime_mcp_context,
                )
                persisted_mcp_provenance = mcp_alignment.get("persistedProvenance", {}) if isinstance(mcp_alignment.get("persistedProvenance", {}), dict) else {}
                runtime_mcp_provenance = mcp_alignment.get("runtimeProvenance", {}) if isinstance(mcp_alignment.get("runtimeProvenance", {}), dict) else {}
                page_state_aligned = bool(page_state_alignment.get("pageStateAligned", False))
                page_state_snapshot_aligned = bool(page_state_alignment.get("pageStateSnapshotAligned", False))
                mcp_provenance_aligned = bool(mcp_alignment.get("provenanceAligned", False))
                mcp_adapter_aligned = bool(mcp_alignment.get("adapterAligned", False))
                mcp_dispatch_aligned = bool(mcp_alignment.get("dispatchAligned", False))
                mcp_execution_aligned = bool(mcp_alignment.get("executionAligned", False))
                if persisted_navigation_steps == runtime_navigation_steps and persisted_target_signals == runtime_target_signals and page_state_aligned and page_state_snapshot_aligned and mcp_provenance_aligned and mcp_adapter_aligned and mcp_dispatch_aligned and mcp_execution_aligned:
                    platform_logger.info(
                        "execution_plan_reused",
                        workflow_slug=workflow_slug,
                        attach_stage=attach_stage,
                        step_count=(persisted_execution.get("stepCount", len(persisted_navigation_steps))),
                        navigation_source=persisted_provenance.get("navigationSource", ""),
                        target_signal_source=persisted_provenance.get("targetSignalSource", ""),
                        rag_attached=persisted_provenance.get("ragAttached", False),
                        source_snapshot=persisted_source_snapshot,
                        page_state_snapshot=persisted_page_state_snapshot,
                        mcp_provenance=persisted_mcp_provenance,
                        mcp_adapter=(mcp_alignment.get("persistedAdapter", {}) if isinstance(mcp_alignment.get("persistedAdapter", {}), dict) else {}),
                        mcp_dispatch=(mcp_alignment.get("persistedDispatch", {}) if isinstance(mcp_alignment.get("persistedDispatch", {}), dict) else {}),
                        mcp_execution=(mcp_alignment.get("persistedExecution", {}) if isinstance(mcp_alignment.get("persistedExecution", {}), dict) else {}),
                        persisted=True,
                        freshness=freshness,
                    )
                    return persisted_plan
                platform_logger.info(
                    "execution_plan_persisted_misaligned",
                    workflow_slug=workflow_slug,
                    attach_stage=attach_stage,
                    persisted_step_count=len(persisted_navigation_steps),
                    runtime_step_count=len(runtime_navigation_steps),
                    persisted_target_signal_count=len(persisted_target_signals),
                    runtime_target_signal_count=len(runtime_target_signals),
                    page_state_aligned=page_state_aligned,
                    page_state_snapshot_aligned=page_state_snapshot_aligned,
                    mcp_provenance_aligned=mcp_provenance_aligned,
                    mcp_adapter_aligned=mcp_adapter_aligned,
                    mcp_dispatch_aligned=mcp_dispatch_aligned,
                    mcp_execution_aligned=mcp_execution_aligned,
                    persisted_page_state_snapshot=persisted_page_state_snapshot,
                    runtime_page_state_snapshot=runtime_page_state_snapshot,
                    persisted_mcp_provenance=persisted_mcp_provenance,
                    runtime_mcp_provenance=runtime_mcp_provenance,
                    persisted_mcp_adapter=(mcp_alignment.get("persistedAdapter", {}) if isinstance(mcp_alignment.get("persistedAdapter", {}), dict) else {}),
                    runtime_mcp_adapter=(mcp_alignment.get("runtimeAdapter", {}) if isinstance(mcp_alignment.get("runtimeAdapter", {}), dict) else {}),
                    persisted_mcp_dispatch=(mcp_alignment.get("persistedDispatch", {}) if isinstance(mcp_alignment.get("persistedDispatch", {}), dict) else {}),
                    runtime_mcp_dispatch=(mcp_alignment.get("runtimeDispatch", {}) if isinstance(mcp_alignment.get("runtimeDispatch", {}), dict) else {}),
                    persisted_mcp_execution=(mcp_alignment.get("persistedExecution", {}) if isinstance(mcp_alignment.get("persistedExecution", {}), dict) else {}),
                    runtime_mcp_execution=(mcp_alignment.get("runtimeExecution", {}) if isinstance(mcp_alignment.get("runtimeExecution", {}), dict) else {}),
                    source_snapshot=persisted_source_snapshot,
                    freshness=freshness,
                )
            else:
                platform_logger.info(
                    "execution_plan_persisted_invalid",
                    workflow_slug=workflow_slug,
                    attach_stage=attach_stage,
                    error_count=len(persisted_errors),
                    source_snapshot=persisted_source_snapshot,
                    freshness=freshness,
                )

    return build_and_validate_execution_plan(
        workflow_slug=workflow_slug,
        contract=contract,
        navigation_steps=runtime_navigation_steps,
        rag_context=rag_context,
        attach_stage=attach_stage,
        target_signals=runtime_target_signals,
        mcp_context=mcp_context,
    )


def ensure_workflow_contract_artifact(workflow_slug: str, workflow_payload: dict | None = None):
    if not FEATURE_FLAGS.enable_workflow_contracts:
        return None

    contract_path = workflow_repository.get_contract_path(workflow_slug)
    if contract_path.exists():
        return read_json(contract_path)

    payload = workflow_payload if isinstance(workflow_payload, dict) else None
    if payload is None:
        workflow_path = WORKFLOW_DIR / f"{workflow_slug}.json"
        if not workflow_path.exists():
            return None
        payload = read_json(workflow_path)

    contract = WorkflowContractBuilder.build(payload)
    contract_errors = WorkflowContractValidator.validate(contract)
    if contract_errors:
        raise HTTPException(status_code=400, detail="Workflow contract validation failed: " + "; ".join(contract_errors))

    workflow_repository.save_contract(workflow_slug, contract)
    platform_logger.info(
        "workflow_contract_ensured",
        workflow_slug=workflow_slug,
        workflow_id=contract.workflow_id,
        page_name=contract.page.name,
        source_type=contract.source_type,
    )
    return contract.to_dict()

# -------------------------------------------------------------------
# Generic helpers
# -------------------------------------------------------------------

def render_template(request: Request, template_name: str, context: dict, status_code: int = 200):
    payload = {"request": request, "success_message": None, "error_message": None}
    payload.update(context)
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=payload,
        status_code=status_code,
    )

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


CONFIG = read_json(CONFIG_PATH) if CONFIG_PATH.exists() else {}
SESSION_DIR = BASE_DIR / "ai_sessions"


def get_session_path(workflow_name: str) -> Path:
    return SESSION_DIR / f"{workflow_name}.json"


def reset_workflow_session(workflow_name: str) -> dict:
    session = {
        "workflow": workflow_name,
        "messages": [],
        "run_active": False,
    }
    save_workflow_session(workflow_name, session)
    return session


def load_workflow_session(workflow_name: str) -> dict:
    session_path = get_session_path(workflow_name)
    if session_path.exists():
        try:
            data = read_json(session_path)
            if isinstance(data, dict) and isinstance(data.get("messages"), list):
                data.setdefault("workflow", workflow_name)
                data.setdefault("run_active", False)
                return data
        except Exception:
            pass
    return reset_workflow_session(workflow_name)


def begin_workflow_run(workflow_name: str) -> dict:
    session = reset_workflow_session(workflow_name)
    session["run_active"] = True
    save_workflow_session(workflow_name, session)
    return session


def ensure_workflow_run(workflow_name: str) -> dict:
    session = load_workflow_session(workflow_name)
    if not session.get("run_active"):
        session = begin_workflow_run(workflow_name)
    return session


def save_workflow_session(workflow_name: str, session: dict):
    session_path = get_session_path(workflow_name)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(session_path, session)


def append_session_message(workflow_name: str, role: str, stage: str, content: str):
    cleaned = (content or "").strip()
    if not cleaned:
        return
    session = ensure_workflow_run(workflow_name)
    session.setdefault("messages", []).append({
        "role": role,
        "stage": stage,
        "content": cleaned,
    })
    session["messages"] = session["messages"][-12:]
    save_workflow_session(workflow_name, session)


def build_session_context(workflow_name: str, stage: str) -> str:
    session = ensure_workflow_run(workflow_name)
    messages = session.get("messages", [])[-8:]
    if not messages:
        return ""

    lines = [
        "Workflow AI session context from earlier stages in the current run. Reuse established decisions where appropriate.",
        "Keep this context subordinate to the current task instructions and current source artifacts.",
    ]
    for entry in messages:
        role = clean_text(str(entry.get("role", "assistant"))).upper() or "ASSISTANT"
        prior_stage = clean_text(str(entry.get("stage", "unknown"))) or "unknown"
        content = str(entry.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"[{role} | {prior_stage}]\n{content}")

    lines.append(f"Current stage: {stage}")
    return "\n\n".join(lines)


def call_ai_with_workflow_session(
    workflow_name: str,
    stage: str,
    endpoint: str,
    token: str,
    prompt: str,
    timeout_seconds: int = 120,
    verify_ssl: bool = False,
) -> str:
    context = build_session_context(workflow_name, stage)
    effective_prompt = prompt if not context else f"{context}\n\n{prompt}"
    append_session_message(workflow_name, "user", stage, prompt)
    response = call_ai_chat(
        endpoint=endpoint,
        token=token,
        prompt=effective_prompt,
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
    )
    append_session_message(workflow_name, "assistant", stage, response)
    return response


def call_manual_ai_with_workflow_session(
    workflow_name: str,
    stage: str,
    endpoint: str,
    token: str,
    prompt: str,
    timeout_seconds: int = 120,
) -> dict:
    context = build_session_context(workflow_name, stage)
    effective_prompt = prompt if not context else f"{context}\n\n{prompt}"
    append_session_message(workflow_name, "user", stage, prompt)
    response = call_devex_ai(
        endpoint=endpoint,
        token=token,
        prompt=effective_prompt,
        timeout_sec=timeout_seconds,
    )
    if not isinstance(response, dict):
        raise HTTPException(status_code=502, detail=f"Manual test AI returned invalid content during {stage}.")
    append_session_message(workflow_name, "assistant", stage, json.dumps(response, indent=2, ensure_ascii=False))
    return response


def migrate_manual_artifacts_to_feature_dir(workflow_name: str):
    feature_dir = get_manual_workflow_dir(workflow_name)
    feature_dir.mkdir(parents=True, exist_ok=True)

    legacy_json = get_manual_legacy_json_path(workflow_name)
    feature_json = get_manual_json_path(workflow_name)
    if legacy_json.exists() and not feature_json.exists():
        shutil.move(str(legacy_json), str(feature_json))

    legacy_excel = get_manual_legacy_excel_path(workflow_name)
    feature_excel = get_manual_excel_path(workflow_name)
    if legacy_excel.exists() and not feature_excel.exists():
        shutil.move(str(legacy_excel), str(feature_excel))


def rename_workflow_slug_artifacts(old_slug: str, new_slug: str):
    old_slug = clean_text(old_slug)
    new_slug = clean_text(new_slug)
    if not old_slug or not new_slug or old_slug == new_slug:
        return

    rename_pairs = [
        (WORKFLOW_DIR / f"{old_slug}.json", WORKFLOW_DIR / f"{new_slug}.json"),
        (get_status_path(old_slug), get_status_path(new_slug)),
        (get_session_path(old_slug), get_session_path(new_slug)),
        (BASE_DIR / "artifacts" / "workflow_knowledge" / f"{old_slug}.json", BASE_DIR / "artifacts" / "workflow_knowledge" / f"{new_slug}.json"),
        (get_manual_json_path(old_slug), get_manual_json_path(new_slug)),
        (get_manual_excel_path(old_slug), get_manual_excel_path(new_slug)),
    ]

    for source, target in rename_pairs:
        if not source.exists() or source == target:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.is_file() and source.is_file():
                source.unlink()
            continue
        shutil.move(str(source), str(target))

    old_manual_dir = get_manual_workflow_dir(old_slug)
    new_manual_dir = get_manual_workflow_dir(new_slug)
    if old_manual_dir.exists() and old_manual_dir != new_manual_dir:
        if not new_manual_dir.exists() or not any(new_manual_dir.iterdir()):
            new_manual_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_manual_dir), str(new_manual_dir))


def export_manual_tests_to_excel(workflow_name: str, workflow: dict | None, manual_data: dict) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Manual Tests"

    headers = [
        "Manual Test ID",
        "Title",
        "Type",
        "Priority",
        "Preconditions",
        "Steps",
        "Expected Result",
    ]
    sheet.append(headers)

    app_code = derive_app_code(workflow, workflow_name)
    feature_code = derive_feature_code(workflow, workflow_name)

    cases = manual_data.get("testCases") or manual_data.get("manualTests") or []
    for index, case in enumerate(cases, start=1):
        case_id = f"{app_code}-{feature_code}{index:02d}"
        preconditions = "\n".join(str(item).strip() for item in case.get("preconditions", []) if str(item).strip())
        steps = "\n".join(str(item).strip() for item in case.get("steps", []) if str(item).strip())
        expected = clean_text(str(case.get("expectedResult", "")))
        sheet.append([
            case_id,
            clean_text(str(case.get("title", f"Test Case {index}"))),
            clean_text(str(case.get("type", ""))),
            clean_text(str(case.get("priority", ""))),
            preconditions,
            steps,
            expected,
        ])

    for column_cells in sheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))
        sheet.column_dimensions[column_letter].width = min(max(max_length + 2, 14), 60)

    output_path = get_manual_excel_path(workflow_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return output_path

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""

def get_workflow_status(workflow_name: str) -> dict:
    workflow = load_workflow_or_404(workflow_name)
    pages = workflow.get("pages", []) if isinstance(workflow, dict) else []
    page_name = ""
    if pages and isinstance(pages[0], dict):
        page_name = clean_text(str(pages[0].get("name", "")))

    page_dir = get_page_dir(page_name) if page_name else None
    metadata_dir = get_page_metadata_dir(page_name) if page_name else None
    elements_path = metadata_dir / f"{page_name}.elements.json" if metadata_dir else None
    resource_path = page_dir / f"{page_name}.resource" if page_dir else None
    keywords_path = metadata_dir / f"{page_name}.keywords.json" if metadata_dir else None
    manual_path = get_manual_json_path(workflow_name)
    automation_path = get_automation_path(workflow_name, workflow)

    page_reviewed = bool(elements_path and elements_path.exists())

    manual_approved = False
    if manual_path.exists():
        try:
            manual_data = read_json(manual_path)
            manual_cases = extract_manual_test_cases(manual_data)
            manual_approved = len(manual_cases) > 0
        except Exception:
            manual_approved = False

    keywords_reviewed = False
    if manual_approved and resource_path and resource_path.exists() and keywords_path and keywords_path.exists():
        try:
            keywords_payload = read_json(keywords_path)
            stored_keywords = keywords_payload.get("keywords", []) if isinstance(keywords_payload, dict) else []
            valid_stored_keywords = [
                item for item in stored_keywords
                if isinstance(item, dict)
                and clean_text(str(item.get("keywordName", "")))
                and bool(item.get("approved", True))
            ]
            resource_context = parse_resource_file(resource_path)
            resource_keywords = [
                kw for kw in resource_context.get("keywords", [])
                if clean_text(str(kw.get("name", "")))
            ]
            keywords_reviewed = bool(valid_stored_keywords and resource_keywords)
        except Exception:
            keywords_reviewed = False

    automation_generated = bool(automation_path.exists() and clean_text(read_text(automation_path)))

    next_action = "Page Review"
    if page_reviewed and not manual_approved:
        next_action = "Manual Tests"
    elif page_reviewed and manual_approved and not keywords_reviewed:
        next_action = "Keywords"
    elif page_reviewed and manual_approved and keywords_reviewed and not automation_generated:
        next_action = "Automation"
    elif page_reviewed and manual_approved and keywords_reviewed and automation_generated:
        next_action = "Review / Regenerate"

    return {
        "page_reviewed": page_reviewed,
        "manual_approved": manual_approved,
        "keywords_reviewed": keywords_reviewed,
        "automation_generated": automation_generated,
        "next_action": next_action,
    }

def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "workflow"

def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def clean_multiline_text(value: str) -> str:
    value = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in value.split("\n")]
    return "\n".join(lines).strip()


def compact_code(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", clean_text(value)).upper()


def derive_app_code(workflow: dict | None, workflow_name: str) -> str:
    workflow = workflow or {}

    config_code = compact_code(str(CONFIG.get("application_code", "")))
    if config_code:
        return config_code

    explicit_code = compact_code(
        workflow.get("applicationCode")
        or workflow.get("appCode")
        or workflow.get("moduleCode")
        or workflow.get("moduleAbbreviation")
    )
    if explicit_code:
        return explicit_code

    module = compact_code(workflow.get("module", ""))
    workflow_code = compact_code(workflow.get("workflowName", workflow_name))
    if module:
        if len(module) <= 4:
            return module
        return module[:2]
    return workflow_code[:2] or "APP"


def derive_feature_code(workflow: dict | None, workflow_name: str) -> str:
    workflow = workflow or {}
    explicit_prefix = compact_code(workflow.get("testIdentifierPrefix", ""))
    feature = compact_code(workflow.get("feature", ""))
    workflow_code = compact_code(workflow.get("workflowName", workflow_name))
    return explicit_prefix or feature or workflow_code or "FLOW"


def derive_workflow_artifact_slug(workflow: dict | None, workflow_name: str) -> str:
    workflow = workflow or {}
    explicit_prefix = slugify(str(workflow.get("testIdentifierPrefix", "")))
    feature_slug = slugify(str(workflow.get("feature", "")))
    workflow_slug = slugify(str(workflow.get("workflowName", workflow_name)))
    page_slug = slugify(str(((workflow.get("pages") or [{}])[0]).get("name", ""))) if isinstance(workflow.get("pages"), list) and workflow.get("pages") else ""
    module_slug = slugify(str(workflow.get("module", "")))
    if explicit_prefix:
        return explicit_prefix
    if feature_slug and len(feature_slug) <= 24:
        return feature_slug
    if page_slug and module_slug:
        combined = f"{page_slug}_{module_slug}"
        if len(combined) <= 24:
            return combined
    if page_slug:
        return page_slug
    if workflow_slug and len(workflow_slug) <= 24:
        return workflow_slug
    short_words = [
        slugify(word)
        for word in re.findall(r"[A-Za-z0-9]+", str(workflow.get("workflowName", workflow_name)))
        if slugify(word)
    ][:3]
    collapsed = "_".join(word for word in short_words if word)
    return collapsed or page_slug or feature_slug or workflow_slug or "workflow"


def derive_canonical_workflow_name(workflow: dict | None, workflow_name: str) -> str:
    return derive_workflow_artifact_slug(workflow, workflow_name)

def to_keyword_title(element_name: str) -> str:
    base = clean_text(element_name).replace("_", " ")
    return " ".join(word.capitalize() for word in base.split())

def to_robot_variable_name(name: str) -> str:
    return slugify(name).upper()

# -------------------------------------------------------------------
# Workflow status
# -------------------------------------------------------------------

def get_status_path(workflow_name: str) -> Path:
    return WORKFLOW_DIR / f"{workflow_name}.status.json"

def load_workflow_status(workflow_name: str) -> dict:
    status_path = get_status_path(workflow_name)
    if status_path.exists():
        try:
            return read_json(status_path)
        except Exception:
            pass
    return {
        "page_reviewed": False,
        "keywords_reviewed": False,
        "manual_approved": False,
        "automation_generated": False
    }

def save_workflow_status(workflow_name: str, status: dict):
    write_json(get_status_path(workflow_name), status)

def update_workflow_status(workflow_name: str, **updates):
    status = load_workflow_status(workflow_name)
    status.update(updates)
    save_workflow_status(workflow_name, status)

# -------------------------------------------------------------------
# Workflow handling
# -------------------------------------------------------------------

def load_workflow_or_404(workflow_name: str) -> dict:
    requested_slug = clean_text(workflow_name)
    workflow_path = WORKFLOW_DIR / f"{requested_slug}.json"
    if not workflow_path.exists():
        requested_normalized = slugify(requested_slug)
        for candidate in WORKFLOW_DIR.glob("*.json"):
            if candidate.name.endswith(".status.json"):
                continue
            try:
                payload = read_json(candidate)
            except Exception:
                continue
            candidate_name = clean_text(str(payload.get("workflowName", "")))
            candidate_slug = derive_workflow_artifact_slug(payload, candidate_name or candidate.stem)
            if requested_slug == candidate_name or requested_normalized == slugify(candidate_name) or requested_slug == candidate_slug:
                workflow_path = candidate
                break
    if not workflow_path.exists():
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_name}")
    migrate_manual_artifacts_to_feature_dir(workflow_path.stem)
    return read_json(workflow_path)

def collect_workflow_expected_outcomes(workflow: dict) -> list[str]:
    outcomes: list[str] = []

    observed_expected = clean_text(str(workflow.get("observedExpectedResult", "")))
    if observed_expected:
        outcomes.append(observed_expected)

    observed_validations = workflow.get("observedValidations", [])
    if isinstance(observed_validations, list):
        for item in observed_validations:
            value = clean_text(str(item))
            if value:
                outcomes.append(value)

    pages = workflow.get("pages", [])
    if isinstance(pages, list):
        for page in pages:
            if not isinstance(page, dict):
                continue
            for key in ("expectedResult", "expectedOutcome", "successCriteria"):
                value = clean_text(str(page.get(key, "")))
                if value:
                    outcomes.append(value)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in outcomes:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(item)
    return deduped


def clean_workflow_for_prompting(workflow: dict) -> dict:
    cleaned = json.loads(json.dumps(workflow))

    rag_context = cleaned.get("ragContext")
    if isinstance(rag_context, dict):
        cleaned["ragContext"] = rag_context

    source = cleaned.get("source")
    if isinstance(source, dict):
        cleaned["source"] = {
            key: clean_text(str(value)) if not isinstance(value, (dict, list)) else value
            for key, value in source.items()
            if value not in (None, "")
        }

    external_context = cleaned.get("externalContext")
    if isinstance(external_context, dict):
        cleaned["externalContext"] = {
            key: value
            for key, value in external_context.items()
            if value not in (None, "", [], {})
        }

    fields = cleaned.get("fields", [])
    if isinstance(fields, list):
        cleaned_fields = []
        for field in fields:
            if not isinstance(field, dict):
                continue
            name = clean_text(str(field.get("name", "")))
            label = clean_text(str(field.get("label", "")))
            field_type = clean_text(str(field.get("type", "")))
            required = bool(field.get("required", False))
            if not any([name, label, field_type, required]):
                continue
            cleaned_fields.append({
                "name": name,
                "label": label,
                "type": field_type,
                "required": required,
            })
        cleaned["fields"] = cleaned_fields

    test_data = cleaned.get("testData", {})
    if isinstance(test_data, dict):
        cleaned["testData"] = {
            key: clean_text(str(value))
            for key, value in test_data.items()
            if clean_text(str(value))
        }

    resource_files = cleaned.get("resourceFiles", [])
    if isinstance(resource_files, list):
        cleaned["resourceFiles"] = [clean_text(str(item)) for item in resource_files if clean_text(str(item))]

    return cleaned


def build_workflow_payload(
    workflow_name: str,
    module: str,
    feature: str,
    page_name: str,
    page_url: str,
    resource_file: str,
    preconditions_text: str,
    steps_text: str,
    expected_result: str,
    fields_text: str,
    validations_text: str,
    scenario_intent_text: str,
    application_code: str = "",
    source: dict | None = None,
    external_context: dict | None = None,
    test_identifier_prefix: str = "",
):
    preconditions = [line.strip() for line in preconditions_text.splitlines() if line.strip()]
    steps = [line.strip() for line in steps_text.splitlines() if line.strip()]
    validations = [line.strip() for line in validations_text.splitlines() if line.strip()]
    scenario_intent = [line.strip() for line in scenario_intent_text.split(",") if line.strip()]

    fields = []
    for line in fields_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        field = {
            "name": parts[0] if len(parts) > 0 else "",
            "label": parts[1] if len(parts) > 1 else parts[0] if parts else "",
            "type": parts[2] if len(parts) > 2 else "textbox",
            "required": (parts[3].lower() == "true") if len(parts) > 3 else False,
        }
        if any([clean_text(field["name"]), clean_text(field["label"]), clean_text(field["type"]), field["required"]]):
            fields.append(field)

    workflow_source = source or {
        "createdBy": "UI user",
        "notes": "Workflow entered from MVP UI."
    }

    page_entry = {
        "name": page_name,
    }
    if page_url:
        page_entry["url"] = page_url

    payload = {
        "inputType": "exploratory_workflow",
        "workflowId": f"{slugify(workflow_name).upper()}_001",
        "workflowName": workflow_name,
        "module": module,
        "feature": feature,
        "applicationCode": application_code.strip(),
        "testIdentifierPrefix": clean_text(test_identifier_prefix).upper(),
        "source": workflow_source,
        "resourceFiles": [resource_file],
        "pages": [page_entry],
        "observedPreconditions": preconditions,
        "observedSteps": steps,
        "observedExpectedResult": expected_result,
        "fields": fields,
        "observedValidations": validations,
        "scenarioIntent": scenario_intent,
    }

    if isinstance(external_context, dict) and external_context:
        payload["externalContext"] = external_context

    return payload

# -------------------------------------------------------------------
# Extraction handling
# -------------------------------------------------------------------

def normalize_navigation_steps(steps: list[dict] | None) -> list[dict]:
    normalized_steps: list[dict] = []
    for step in steps or []:
        if not isinstance(step, dict):
            continue
        normalized_steps.append(dict(step))
    return normalized_steps


def normalize_target_page_signals(signals: list[dict] | None) -> list[dict]:
    normalized_signals: list[dict] = []
    for signal in signals or []:
        if not isinstance(signal, dict):
            continue
        normalized_signal = dict(signal)
        if "value" in normalized_signal:
            normalized_signal["value"] = normalize_url_value(str(normalized_signal.get("value", ""))) or clean_text(str(normalized_signal.get("value", ""))).strip("`")
        normalized_signals.append(normalized_signal)
    return normalized_signals


def _extract_story_lines(value) -> list[str]:
    lines: list[str] = []
    if isinstance(value, list):
        for item in value:
            lines.extend(_extract_story_lines(item))
        return lines
    if isinstance(value, str):
        cleaned = clean_text(value)
        if cleaned:
            lines.append(cleaned)
    return lines


_URL_PATTERN = re.compile(r"https?://[^\s)]+", re.IGNORECASE)


def _extract_heading_sections_from_description(value) -> dict[str, list[str]]:
    if not isinstance(value, str):
        return {}
    sections: dict[str, list[str]] = {}
    current_key = ""
    heading_pattern = re.compile(r"^\s*(\d+[.):-]?\s+)?([A-Za-z][A-Za-z /_-]+):?\s*$")
    for raw_line in value.splitlines():
        stripped = clean_text(raw_line)
        if not stripped:
            continue
        heading_match = heading_pattern.match(stripped)
        if heading_match and len(stripped.split()) <= 8:
            current_key = clean_text(heading_match.group(2)).lower()
            sections.setdefault(current_key, [])
            continue
        if current_key:
            bullet = re.sub(r"^[-*•]+\s*", "", stripped)
            normalized = re.sub(r"^\d+[.):-]?\s*", "", bullet)
            cleaned = clean_text(normalized)
            if cleaned:
                sections.setdefault(current_key, []).append(cleaned)
    return {
        key: [item for index, item in enumerate(values) if item and item not in values[:index]]
        for key, values in sections.items()
        if values
    }


def _extract_urls_from_text_blocks(values: list[str]) -> list[str]:
    urls: list[str] = []
    for value in values:
        for match in _URL_PATTERN.findall(str(value or "")):
            cleaned = clean_text(match).rstrip('.,;:')
            if cleaned and cleaned not in urls:
                urls.append(cleaned)
    return urls


def _derive_structured_workflow_context(workflow: dict) -> dict:
    normalized_workflow = dict(workflow) if isinstance(workflow, dict) else {}
    if not normalized_workflow:
        return {}

    pages = normalized_workflow.get("pages", []) if isinstance(normalized_workflow.get("pages"), list) else []
    first_page = pages[0] if pages and isinstance(pages[0], dict) else {}
    external = normalized_workflow.get("externalContext", {}) if isinstance(normalized_workflow.get("externalContext"), dict) else {}
    test_data = normalized_workflow.get("testData", {}) if isinstance(normalized_workflow.get("testData"), dict) else {}
    description_sections = _extract_heading_sections_from_description(external.get("description"))

    def _parse_labeled_value(lines: list[str], label_fragment: str) -> str:
        for raw_line in lines:
            line = clean_text(raw_line)
            if not line:
                continue
            lowered = line.lower()
            if label_fragment in lowered and ":" in line:
                return normalize_url_value(line.split(":", 1)[-1]) or clean_text(line.split(":", 1)[-1]).strip("`")
        return ""

    def _page_name_to_resource(page_name: str) -> str:
        normalized_name = clean_text(page_name)
        return f"{normalized_name}/{normalized_name}.resource" if normalized_name else ""

    declared_resource_files = normalized_workflow.get("resourceFiles", []) if isinstance(normalized_workflow.get("resourceFiles"), list) else []
    page_resource_files: list[str] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_name = clean_text(str(page.get("name", "")))
        if not page_name:
            continue
        page_resource = f"{page_name}/{page_name}.resource"
        if page_resource not in page_resource_files:
            page_resource_files.append(page_resource)
    merged_resource_files: list[str] = []
    for item in declared_resource_files + page_resource_files:
        normalized_item = clean_text(str(item)).replace('\\', '/')
        if normalized_item and normalized_item not in merged_resource_files:
            merged_resource_files.append(normalized_item)

    story_resource_candidates: list[str] = []
    for line in description_sections.get("resource reuse guidance", []) + description_sections.get("downstream automation guidance", []):
        page_candidate = _parse_labeled_value([line], "reuse the existing")
        if not page_candidate:
            lowered_line = clean_text(line).lower()
            if lowered_line.startswith("reuse the existing ") and lowered_line.endswith(" resource for"):
                page_candidate = clean_text(line[len("Reuse the existing "):].rsplit(" resource", 1)[0]).strip("`")
        if page_candidate:
            candidate_resource = _page_name_to_resource(page_candidate)
            if candidate_resource and candidate_resource not in story_resource_candidates:
                story_resource_candidates.append(candidate_resource)

    for item in story_resource_candidates:
        if item not in merged_resource_files:
            merged_resource_files.append(item)

    application_context_lines = _extract_story_lines(external.get("applicationContext", [])) or description_sections.get("application context", [])
    entry_condition_lines = _extract_story_lines(external.get("entryConditions", [])) or description_sections.get("entry conditions", [])
    transition_lines = _extract_story_lines(external.get("transitionExpectations", [])) or description_sections.get("transition expectations", []) + description_sections.get("primary navigation journey", [])
    validation_lines = _extract_story_lines(external.get("validationExpectations", [])) or description_sections.get("validation expectations", [])
    observed_step_lines = _extract_story_lines(normalized_workflow.get("observedSteps", [])) or description_sections.get("primary navigation journey", [])
    observed_validation_lines = _extract_story_lines(normalized_workflow.get("observedValidations", [])) or description_sections.get("acceptance criteria", [])
    approved_test_data_lines = description_sections.get("approved test data", [])
    resource_reuse_lines = description_sections.get("resource reuse guidance", [])
    all_story_lines = application_context_lines + entry_condition_lines + transition_lines + validation_lines + observed_step_lines + observed_validation_lines + approved_test_data_lines + resource_reuse_lines

    workflow_slug = clean_text(str(normalized_workflow.get("workflowName", ""))) or clean_text(str(normalized_workflow.get("feature", "")))
    workflow_knowledge_payload = knowledge_repository.load_workflow_knowledge_artifact(slugify(workflow_slug)) if workflow_slug else {}
    knowledge_navigation_model = workflow_knowledge_payload.get("navigationModel", {}) if isinstance(workflow_knowledge_payload.get("navigationModel", {}), dict) else {}
    knowledge_entry_point = knowledge_navigation_model.get("entryPoint", {}) if isinstance(knowledge_navigation_model.get("entryPoint", {}), dict) else {}
    knowledge_target = knowledge_navigation_model.get("target", {}) if isinstance(knowledge_navigation_model.get("target", {}), dict) else {}
    knowledge_entry_name = clean_text(str(knowledge_entry_point.get("name", "")))
    knowledge_entry_url = normalize_url_value(str(knowledge_entry_point.get("url", ""))) or clean_text(str(knowledge_entry_point.get("url", ""))).strip("`")
    knowledge_entry_state = clean_text(str(knowledge_entry_point.get("state", ""))).strip("`")

    raw_entry_page = normalized_workflow.get("entryPage") if isinstance(normalized_workflow.get("entryPage"), dict) else {}
    entry_story_name = _parse_labeled_value(application_context_lines, "canonical page name")
    entry_story_state = _parse_labeled_value(application_context_lines + entry_condition_lines, "canonical page state")
    entry_story_url = _parse_labeled_value(approved_test_data_lines + application_context_lines + entry_condition_lines, "exact url match") or _parse_labeled_value(approved_test_data_lines + application_context_lines + entry_condition_lines, "entry url")
    entry_page_name = clean_text(str(first_page.get("name", "")))
    entry_page = {
        "name": clean_text(str(raw_entry_page.get("name", ""))),
        "url": normalize_url_value(str(raw_entry_page.get("url", ""))) or clean_text(str(raw_entry_page.get("url", ""))).strip("`"),
        "state": clean_text(str(raw_entry_page.get("state", ""))).strip("`"),
    } if raw_entry_page else {}
    entry_url = entry_page.get("url", "")
    if not entry_url:
        entry_url = normalize_url_value(str(test_data.get("entryUrl", "")))
    if not entry_url:
        entry_url = entry_story_url
    if not entry_url:
        extracted_urls = _extract_urls_from_text_blocks(application_context_lines + entry_condition_lines + observed_step_lines)
        entry_url = entry_story_url or (extracted_urls[0] if extracted_urls else normalize_url_value(str(first_page.get("url", ""))))
    if not entry_url:
        story_urls = _extract_urls_from_text_blocks(application_context_lines + entry_condition_lines + observed_step_lines + approved_test_data_lines)
        entry_url = story_urls[0] if story_urls else ""
    if not entry_url:
        entry_url = knowledge_entry_url

    entry_state = entry_page.get("state", "")
    if not entry_state:
        entry_state = clean_text(str(first_page.get("state", "")))
    if not entry_state:
        entry_state = entry_story_state or knowledge_entry_state
    if not entry_state:
        state_candidates = [line for line in application_context_lines + entry_condition_lines if clean_text(line)]
        for line in state_candidates:
            lowered = line.lower()
            if ":" in line and "state" in lowered:
                entry_state = clean_text(line.split(":", 1)[-1]).strip("`")
                break

    entry_name = entry_page.get("name", "")
    if entry_story_name:
        entry_name = entry_story_name
    if not entry_name:
        entry_name = knowledge_entry_name
    if not entry_name:
        transition_candidates = application_context_lines + transition_lines + observed_step_lines + observed_validation_lines
        for line in transition_candidates:
            cleaned_line = clean_text(line)
            lowered_line = cleaned_line.lower()
            if " from `" in lowered_line and "` to " in lowered_line:
                entry_name = clean_text(cleaned_line.split(" from ", 1)[1].split(" to ", 1)[0]).strip("`.")
                break
            if lowered_line.startswith("start on `") and "`" in cleaned_line[10:]:
                entry_name = clean_text(cleaned_line.split("`", 2)[1]).strip("`.")
                break
    if not entry_name:
        entry_name = clean_text(str(first_page.get("name", "")))
    if entry_name or entry_url or entry_state:
        entry_page = {"name": entry_name, "url": entry_url, "state": entry_state}

    raw_target_page = normalized_workflow.get("targetPage") if isinstance(normalized_workflow.get("targetPage"), dict) else {}
    target_page = {
        "name": clean_text(str(raw_target_page.get("name", ""))),
        "url": normalize_url_value(str(raw_target_page.get("url", ""))) or clean_text(str(raw_target_page.get("url", ""))).strip("`"),
        "state": clean_text(str(raw_target_page.get("state", ""))).strip("`"),
    } if raw_target_page else {}
    navigation_steps = normalize_navigation_steps(normalized_workflow.get("navigationSteps", []))
    target_page_signals = normalize_target_page_signals(normalized_workflow.get("targetPageSignals", []))
    if not target_page_signals:
        target_page_signals = normalize_target_page_signals(knowledge_navigation_model.get("targetSignals", []))

    if not target_page_signals:
        test_data_values = []
        if isinstance(test_data, dict):
            test_data_values.extend([clean_text(str(value)) for value in test_data.values() if clean_text(str(value))])
        test_data_values.extend(approved_test_data_lines)
        test_data_values.extend(_extract_urls_from_text_blocks(all_story_lines))
        transition_signal_candidates: list[str] = []
        for line in transition_lines + observed_step_lines + observed_validation_lines:
            cleaned_line = clean_text(line)
            lowered_line = cleaned_line.lower()
            if "person/profile" in lowered_line and "login page" in lowered_line:
                exact_login_url = _parse_labeled_value(approved_test_data_lines, "exact url match")
                if exact_login_url:
                    transition_signal_candidates.append(exact_login_url)
        test_data_values.extend(transition_signal_candidates)
        for value in test_data_values:
            cleaned_value = normalize_url_value(str(value)) or clean_text(str(value)).strip("`")
            if not cleaned_value or cleaned_value == normalize_url_value(str(entry_page.get("url", ""))):
                continue
            lowered_value = cleaned_value.lower()
            if lowered_value.endswith(":") or lowered_value.startswith("entry url") or lowered_value.startswith("expected "):
                continue
            if cleaned_value.startswith("/"):
                signal_type = "urlEquals"
            else:
                signal_type = "urlContains" if "/" in cleaned_value or "?" in cleaned_value or "-" in cleaned_value else "pageName"
            marker = json.dumps({"type": signal_type, "value": cleaned_value}, sort_keys=True, ensure_ascii=False)
            if marker in {json.dumps(item, sort_keys=True, ensure_ascii=False) for item in target_page_signals if isinstance(item, dict)}:
                continue
            target_page_signals.append({"type": signal_type, "value": cleaned_value})

    if not navigation_steps:
        reusable_flow_artifacts = workflow_knowledge_payload.get("reusableFlows", []) if isinstance(workflow_knowledge_payload.get("reusableFlows", []), list) else []
        flow_target_markers = [clean_text(str(signal.get("value", ""))).lower() for signal in target_page_signals if isinstance(signal, dict)]
        for line in transition_lines + observed_step_lines + observed_validation_lines:
            cleaned_line = clean_text(line)
            lowered_line = cleaned_line.lower()
            if not cleaned_line:
                continue
            entry_markers = []
            if entry_story_name:
                entry_markers.append(entry_story_name.lower())
            if entry_page_name:
                entry_markers.append(entry_page_name.lower())
            if not any(marker and marker in lowered_line for marker in entry_markers):
                continue
            if "login page" not in lowered_line:
                continue
            if not target_page:
                target_page = {
                    "name": "login_page",
                    "url": "",
                    "state": "",
                }
            if not any(step.get("action") == "reuseApprovedEntryContext" for step in navigation_steps if isinstance(step, dict)):
                navigation_steps.append({"action": "reuseApprovedEntryContext"})
            if not any(step.get("action") == "click" for step in navigation_steps if isinstance(step, dict)):
                navigation_steps.append({
                    "action": "click",
                    "target": {
                        "page": entry_story_name or entry_page_name,
                        "description": cleaned_line,
                    },
                })
            if not any((signal.get("type") == "pageName" and clean_text(str(signal.get("value", ""))).lower() == "login_page") for signal in target_page_signals if isinstance(signal, dict)):
                target_page_signals.append({"type": "pageName", "value": "login_page"})
            break
        flow_target_markers = [clean_text(str(signal.get("value", ""))).lower() for signal in target_page_signals if isinstance(signal, dict)]
        for flow in reusable_flow_artifacts:
            if not isinstance(flow, dict):
                continue
            flow_id = clean_text(str(flow.get("flowId", "")))
            if not flow_id:
                continue
            flow_target = flow.get("targetPage", {}) if isinstance(flow.get("targetPage", {}), dict) else {}
            flow_target_values = [
                clean_text(str(flow_target.get("name", ""))).lower(),
                normalize_url_value(str(flow_target.get("url", ""))).lower(),
            ]
            flow_target_values.extend([clean_text(str(signal.get("value", ""))).lower() for signal in normalize_target_page_signals(flow.get("targetSignals", []))])
            if flow_target_markers and not any(value and value in flow_target_markers for value in flow_target_values):
                continue
            navigation_steps.append({"action": "reuseApprovedEntryContext", "flowId": flow_id})

        bundle_resources = resource_repository.load_bundles(merged_resource_files)
        for bundle in bundle_resources:
            page_name = clean_text(str(bundle.get("pageName", "")))
            reusable_flows = bundle.get("reusableFlows", []) if isinstance(bundle.get("reusableFlows", []), list) else []
            for flow in reusable_flows:
                if not isinstance(flow, dict):
                    continue
                flow_target = flow.get("targetPage", {}) if isinstance(flow.get("targetPage", {}), dict) else {}
                flow_entry = flow.get("entryPage", {}) if isinstance(flow.get("entryPage", {}), dict) else {}
                target_name = clean_text(str(flow_target.get("name", "")))
                target_url = normalize_url_value(str(flow_target.get("url", ""))) or clean_text(str(flow_target.get("url", "")))
                if not target_name and not target_url:
                    continue
                target_markers = [marker.lower() for marker in [target_name, target_url] if marker]
                if not target_markers:
                    continue
                if not any(marker and any(marker in line.lower() for line in all_story_lines) for marker in target_markers):
                    continue
                flow_id = clean_text(str(flow.get("flowId", "")))
                if not flow_id:
                    continue
                navigation_steps.append({"action": "reuseApprovedEntryContext", "flowId": flow_id})
                signal_value = target_url or target_name
                if signal_value:
                    signal_type = "urlContains" if "/" in signal_value or "?" in signal_value else "pageName"
                    target_page_signals.append({"type": signal_type, "value": signal_value})
                if not target_page:
                    target_page = {
                        "name": target_name,
                        "url": target_url,
                        "state": clean_text(str(flow_target.get("state", ""))).strip("`"),
                    }
                if not entry_page:
                    entry_page = {
                        "name": clean_text(str(flow_entry.get("name", page_name))),
                        "url": normalize_url_value(str(flow_entry.get("url", ""))) or clean_text(str(flow_entry.get("url", ""))),
                        "state": clean_text(str(flow_entry.get("state", ""))).strip("`"),
                    }

    if not target_page:
        target_name = clean_text(str(knowledge_target.get("name", "")))
        if not target_name:
            target_name = clean_text(str(first_page.get("name", "")))
            if entry_story_name and target_name and target_name == entry_story_name:
                target_name = ""
        target_url = normalize_url_value(str(knowledge_target.get("url", ""))) or clean_text(str(knowledge_target.get("url", "")))
        if target_name or target_url:
            target_page = {
                "name": target_name,
                "url": target_url,
                "state": clean_text(str(knowledge_target.get("state", ""))).strip("`"),
            }

    deduped_steps: list[dict] = []
    seen_steps: set[str] = set()
    for step in navigation_steps:
        marker = json.dumps(step, sort_keys=True, ensure_ascii=False)
        if marker in seen_steps:
            continue
        seen_steps.add(marker)
        deduped_steps.append(step)

    deduped_signals: list[dict] = []
    seen_signals: set[str] = set()
    for signal in target_page_signals:
        marker = json.dumps(signal, sort_keys=True, ensure_ascii=False)
        if marker in seen_signals:
            continue
        seen_signals.add(marker)
        deduped_signals.append(signal)

    if not entry_page and isinstance(knowledge_entry_point, dict):
        entry_page = {
            "name": clean_text(str(knowledge_entry_point.get("name", ""))),
            "url": normalize_url_value(str(knowledge_entry_point.get("url", ""))) or clean_text(str(knowledge_entry_point.get("url", ""))),
            "state": clean_text(str(knowledge_entry_point.get("state", ""))).strip("`"),
        }

    return {
        "entryPage": entry_page,
        "targetPage": target_page,
        "navigationSteps": deduped_steps,
        "targetPageSignals": deduped_signals,
        "resourceFiles": merged_resource_files,
    }


def run_page_extraction(page_name: str, page_url: str, extraction_context: dict | None = None):
    script_path = BASE_DIR / "scripts" / "extract_page_model.py"
    if not script_path.exists():
        raise HTTPException(status_code=500, detail="Page extraction script not found.")

    command = [
        sys.executable,
        str(script_path),
        "--page-name",
        page_name,
    ]

    extraction_context = extraction_context or {}
    navigation_steps = normalize_navigation_steps(extraction_context.get("navigationSteps", []) if isinstance(extraction_context, dict) else [])
    entry_page = extraction_context.get("entryPage", {}) if isinstance(extraction_context, dict) else {}
    target_page_signals = normalize_target_page_signals(extraction_context.get("targetPageSignals", []) if isinstance(extraction_context, dict) else [])

    if navigation_steps:
        entry_page_url = normalize_url_value(str(entry_page.get("url", ""))) if isinstance(entry_page, dict) else ""
        if not entry_page_url:
            workflow_like = dict(extraction_context) if isinstance(extraction_context, dict) else {}
            workflow_like.setdefault("pageUrl", page_url)
            workflow_like.setdefault("workflowName", page_name)
            try:
                from scripts.extract_page_model import resolve_entry_url as _resolve_entry_url
            except ModuleNotFoundError:
                import sys as _sys
                _sys.path.append(str(BASE_DIR))
                from scripts.extract_page_model import resolve_entry_url as _resolve_entry_url
            entry_page_url = clean_text(_resolve_entry_url(workflow_like))
            if isinstance(extraction_context, dict):
                extraction_context = dict(extraction_context)
                current_entry = extraction_context.get("entryPage", {}) if isinstance(extraction_context.get("entryPage", {}), dict) else {}
                extraction_context["entryPage"] = {
                    "name": clean_text(str(current_entry.get("name", ""))),
                    "url": entry_page_url,
                }
                entry_page = extraction_context["entryPage"]
        if not entry_page_url:
            raise HTTPException(status_code=400, detail="Navigation-based extraction requires an entry page URL.")
        command.extend(["--entry-url", entry_page_url])
        command.extend(["--navigation-json", json.dumps({
            "entryPage": entry_page,
            "targetPage": extraction_context.get("targetPage", {"name": page_name}),
            "navigationSteps": navigation_steps,
            "targetPageSignals": target_page_signals,
            "executionRuntime": extraction_context.get("executionRuntime", {}) if isinstance(extraction_context.get("executionRuntime", {}), dict) else {},
            "workflowName": extraction_context.get("workflowName", page_name),
            "feature": extraction_context.get("feature", ""),
            "testIdentifierPrefix": extraction_context.get("testIdentifierPrefix", ""),
            "applicationCode": extraction_context.get("applicationCode", ""),
            "resourceFiles": extraction_context.get("resourceFiles", []),
            "externalContext": extraction_context.get("externalContext", {}) if isinstance(extraction_context.get("externalContext", {}), dict) else {},
            "pages": extraction_context.get("pages", []) if isinstance(extraction_context.get("pages", []), list) else [],
            "observedSteps": extraction_context.get("observedSteps", []) if isinstance(extraction_context.get("observedSteps", []), list) else [],
            "observedValidations": extraction_context.get("observedValidations", []) if isinstance(extraction_context.get("observedValidations", []), list) else [],
            "acceptanceCriteria": extraction_context.get("acceptanceCriteria", []) if isinstance(extraction_context.get("acceptanceCriteria", []), list) else [],
            "description": extraction_context.get("description", ""),
            "userStory": extraction_context.get("userStory", ""),
        }, ensure_ascii=False)])
    else:
        resolved_url = clean_text(page_url)
        if not resolved_url:
            workflow_like = dict(extraction_context) if isinstance(extraction_context, dict) else {}
            workflow_like.setdefault("pageUrl", page_url)
            workflow_like.setdefault("workflowName", page_name)
            try:
                from scripts.extract_page_model import resolve_entry_url as _resolve_entry_url
            except ModuleNotFoundError:
                import sys as _sys
                _sys.path.append(str(BASE_DIR))
                from scripts.extract_page_model import resolve_entry_url as _resolve_entry_url
            resolved_url = clean_text(_resolve_entry_url(workflow_like))
        if not resolved_url:
            raise HTTPException(status_code=400, detail="Page extraction could not determine an entry URL from the workflow story or existing resources.")
        command.extend(["--url", resolved_url])

    result = subprocess.run(
        command,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True
    )

    stdout_text = (result.stdout or "").strip()
    stderr_text = (result.stderr or "").strip()
    combined_output = "\n".join(part for part in [stdout_text, stderr_text] if part).strip()

    if result.returncode != 0:
        error_message = combined_output or "Unknown extraction error."
        raise HTTPException(status_code=500, detail=f"Page extraction failed: {error_message}")

    if "extraction will be skipped" in combined_output.lower():
        raise HTTPException(status_code=400, detail=combined_output)

    return combined_output

def infer_type_from_raw_item(item: dict) -> str:
    tag = (item.get("tag") or "").lower()
    attrs = item.get("attributes", {}) or {}
    input_type = clean_text(attrs.get("type", "")).lower()

    if tag in {"button", "ion-button", "ion-fab-button", "app-main-button"}:
        return "button"
    if tag == "a":
        return "link"
    if tag in {"select", "ion-select"}:
        return "dropdown"
    if tag == "textarea":
        return "textbox"
    if tag in {"input", "ion-input"}:
        if input_type == "password":
            return "password_textbox"
        return "textbox"
    return "element"

def infer_label_from_raw_item(item: dict) -> str:
    attrs = item.get("attributes", {}) or {}
    candidates = [
        item.get("label", ""),
        item.get("text", ""),
        attrs.get("placeholder", ""),
        attrs.get("aria-label", ""),
        attrs.get("name", ""),
        attrs.get("id", "")
    ]
    for candidate in candidates:
        value = clean_text(candidate)
        if value:
            return value
    return ""

def normalize_ui_element_name(label: str, role: str) -> str:
    base = slugify(label)
    if not base:
        base = role or "element"
    suffix = slugify(role or "element")
    return f"{base}_{suffix}" if suffix and not base.endswith(f"_{suffix}") and base != suffix else (base or suffix or "element")

def infer_name_from_raw_item(item: dict, index: int) -> str:
    role = infer_type_from_raw_item(item)
    label = infer_label_from_raw_item(item)

    if label:
        return normalize_ui_element_name(label, role)
    return f"element_{index+1}"

def build_locator_from_raw_item(item: dict) -> str:
    tag = (item.get("tag") or "").lower()
    attrs = item.get("attributes", {}) or {}
    text = clean_text(item.get("text", ""))
    placeholder = clean_text(attrs.get("placeholder", ""))
    aria = clean_text(attrs.get("aria-label", ""))
    name = clean_text(attrs.get("name", ""))
    el_id = clean_text(attrs.get("id", ""))

    def xpath_literal(value: str) -> str:
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f"\"{value}\""
        parts = value.split("'")
        return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

    if el_id:
        return f"id={el_id}"
    if tag == "ion-fab-button":
        if text:
            return f"xpath=//ion-fab-button[.//ion-icon[@aria-label={xpath_literal(text)}] or normalize-space(.)={xpath_literal(text)}]"
        if aria:
            return f"xpath=//ion-fab-button[@aria-label={xpath_literal(aria)}]"
        return "xpath=//ion-fab-button"
    if placeholder and tag in {"input", "textarea"}:
        return f"xpath=//{tag}[@placeholder={xpath_literal(placeholder)}]"
    if name and tag in {"input", "textarea", "select"}:
        return f"xpath=//{tag}[@name={xpath_literal(name)}]"
    if aria:
        return f"xpath=//{tag}[@aria-label={xpath_literal(aria)}]"
    if text and tag in {"button", "a", "ion-button", "app-main-button"}:
        return f"xpath=//{tag}[normalize-space(.)={xpath_literal(text)}]"
    return f"xpath=//{tag}"

def normalize_extracted_element(item: dict, index: int) -> dict:
    extracted_name = infer_name_from_raw_item(item, index)
    inferred_type = infer_type_from_raw_item(item)
    locator = build_locator_from_raw_item(item)

    display_type = inferred_type
    if display_type == "password_textbox":
        display_type = "textbox"

    return {
        "approvedName": extracted_name,
        "type": display_type,
        "locator": locator,
        "approved": True,
    }

def get_page_reviewed_path(page_name: str) -> Path:
    return get_page_metadata_dir(page_name) / f"{page_name}.elements.reviewed.json"


def get_page_variables_path(page_name: str) -> Path:
    return get_page_metadata_dir(page_name) / f"{page_name}.variables.json"


def get_keywords_reviewed_path(page_name: str) -> Path:
    return get_page_metadata_dir(page_name) / f"{page_name}.keywords.reviewed.json"


def get_manual_legacy_json_path(workflow_name: str) -> Path:
    return MANUAL_DIR / f"{workflow_name}.json"


def get_manual_legacy_excel_path(workflow_name: str) -> Path:
    return MANUAL_DIR / f"{workflow_name}_approved_manual_tests.xlsx"


def get_page_review_data(workflow: dict):
    pages = workflow.get("pages", [])
    page_name = pages[0].get("name") if pages else "page"
    page_url = pages[0].get("url") if pages else ""
    entry_page = workflow.get("entryPage", {}) if isinstance(workflow.get("entryPage"), dict) else {}
    target_page = workflow.get("targetPage", {}) if isinstance(workflow.get("targetPage"), dict) else {}
    navigation_steps = workflow.get("navigationSteps", []) if isinstance(workflow.get("navigationSteps"), list) else []
    target_page_signals = workflow.get("targetPageSignals", []) if isinstance(workflow.get("targetPageSignals"), list) else []

    page_dir = get_page_dir(page_name)
    metadata_dir = get_page_metadata_dir(page_name)
    elements_path = metadata_dir / f"{page_name}.elements.json"
    reviewed_elements_path = get_page_reviewed_path(page_name)
    screenshot_path = metadata_dir / f"{page_name}.png"

    extracted_elements_data = []
    approved_elements_data = []
    refined_elements_data = []
    review_summary = None
    source_artifact = "raw"

    if elements_path.exists():
        try:
            data = read_json(elements_path)
            if isinstance(data, list):
                extracted_elements_data = data
            elif isinstance(data, dict):
                extracted_elements_data = data.get("rawElements", []) or data.get("elements", [])
                approved_elements_data = data.get("elements", [])
        except Exception:
            extracted_elements_data = []
            approved_elements_data = []

    if reviewed_elements_path.exists():
        try:
            reviewed_data = read_json(reviewed_elements_path)
            if isinstance(reviewed_data, dict):
                refined_elements_data = reviewed_data.get("elements", [])
                if reviewed_data.get("reviewSummary"):
                    review_summary = reviewed_data.get("reviewSummary")
                if approved_elements_data and approved_elements_data == refined_elements_data:
                    source_artifact = "approved"
                elif refined_elements_data:
                    source_artifact = "refined"
        except Exception:
            refined_elements_data = []

    elif approved_elements_data:
        source_artifact = "approved"

    display_source_elements = refined_elements_data or approved_elements_data or extracted_elements_data
    display_elements = []
    seen_name_locator: set[tuple[str, str]] = set()
    for idx, item in enumerate(display_source_elements):
        if not isinstance(item, dict):
            continue
        normalized_item = None
        if "approvedName" in item and "locator" in item and "type" in item:
            normalized_item = {
                "approvedName": item.get("approvedName") or f"element_{idx+1}",
                "type": item.get("type", "element"),
                "locator": clean_text(item.get("locator", "")),
                "approved": item.get("approved", True),
                "description": clean_text(str(item.get("description", ""))),
            }
        elif "name" in item and "locator" in item and "type" in item:
            normalized_item = {
                "approvedName": clean_text(str(item.get("name", ""))) or f"element_{idx+1}",
                "type": clean_text(str(item.get("type", "element"))).lower() or "element",
                "locator": clean_text(str(item.get("locator", ""))),
                "approved": True,
                "description": clean_text(str(item.get("description", ""))),
            }
        else:
            normalized_item = normalize_extracted_element(item, idx)
            normalized_item["description"] = clean_text(str(item.get("description", "")))

        approved_name = clean_text(str(normalized_item.get("approvedName", "")))
        locator = clean_text(str(normalized_item.get("locator", "")))
        lowered_name = approved_name.lower()
        key = (lowered_name, locator)
        if not approved_name or not locator or key in seen_name_locator:
            continue
        seen_name_locator.add(key)
        display_elements.append(normalized_item)

    raw_preview_elements = []
    for idx, item in enumerate(extracted_elements_data):
        if not isinstance(item, dict):
            continue
        preview_item = normalize_extracted_element(item, idx)
        preview_item["description"] = clean_text(str(item.get("description", "")))
        raw_preview_elements.append(preview_item)

    screenshot_web_path = None
    if screenshot_path.exists():
        screenshot_web_path = f"/static-artifacts/{page_name}/metadata/{page_name}.png"

    return {
        "page_name": page_name,
        "page_url": page_url,
        "entry_page": entry_page,
        "target_page": target_page,
        "navigation_steps": navigation_steps,
        "target_page_signals": target_page_signals,
        "is_navigation_mode": bool(navigation_steps),
        "elements": display_elements,
        "display_elements_count": len(display_elements),
        "raw_preview_elements": raw_preview_elements,
        "raw_preview_count": len(raw_preview_elements),
        "screenshot_web_path": screenshot_web_path,
        "raw_elements_count": len(raw_preview_elements),
        "elements_path": elements_path,
        "reviewed_elements_path": reviewed_elements_path,
        "raw_elements": extracted_elements_data,
        "approved_elements": approved_elements_data,
        "refined_elements": refined_elements_data,
        "review_summary": review_summary,
        "source_artifact": source_artifact,
    }

# -------------------------------------------------------------------
# Keyword handling
# -------------------------------------------------------------------

def get_keywords_path(page_name: str) -> Path:
    return get_page_metadata_dir(page_name) / f"{page_name}.keywords.json"

def get_resource_path(page_name: str) -> Path:
    return get_page_dir(page_name) / f"{page_name}.resource"


def get_effective_resource_path(page_name: str) -> Path:
    return get_resource_path(page_name)




def get_manual_tests_variable_enrichment_prompt(
    workflow: dict,
    approved_elements: list[dict],
    approved_keywords: list[dict],
    approved_manual_tests: list[dict],
    current_resource_content: str,
) -> str:
    payload = {
        "workflow": clean_workflow_for_prompting(workflow),
        "approved_elements": approved_elements,
        "approved_keywords": approved_keywords,
        "approved_manual_tests": approved_manual_tests,
        "current_page_resource": current_resource_content,
    }
    return (
        "You are AI Layer R2: a Robot Framework page-resource data-abstraction specialist for an AI-first automation framework.\n"
        "Your task is to refine the provided page resource so reusable literal data from approved manual tests is abstracted into the page resource Variables section and not left to be hardcoded in generated test suites.\n\n"
        "Framework intent:\n"
        "- The page resource is the canonical place for reusable page-level variables and page-specific reusable keywords.\n"
        "- Generated .robot suites must stay thin and should reference semantic variables from the page resource instead of embedding reusable URLs, paths, usernames, passwords, expected validation texts, or other stable reusable literals directly.\n"
        "- Use AI judgment from the workflow, approved manual tests, approved elements, approved keywords, and current page resource. Do not rely on hardcoded page assumptions.\n\n"
        "Mandatory rules:\n"
        "- Return only valid Robot Framework resource code.\n"
        "- Do not return markdown fences or explanations.\n"
        "- Preserve useful existing page resource content.\n"
        "- Add or refine reusable semantic variables only when clearly grounded in approved manual tests, workflow context, or existing approved page understanding.\n"
        "- Prefer semantic reusable variables for stable business data such as valid credentials, invalid credentials, page URLs, expected validation text, expected navigation targets, and other reusable test data.\n"
        "- Inspect approved manual tests for semantically meaningful data variants that would otherwise be hardcoded in suites, including credential casing variants, distinct invalid credential classes, reusable long or boundary values, and stable expected validation texts.\n"
        "- Treat uppercase, lowercase, mixed-case, role-specific, invalid, and other semantically meaningful credential variants as reusable business data when approved manual tests depend on them; do not leave such values to be embedded as literals in generated suites.\n"
        "- Do not create unnecessary alias variables for Robot built-ins such as ${EMPTY} or ${SPACE}.\n"
        "- Prefer Robot built-ins and inline composition for blank, whitespace-only, padded, or other trivially derived values. For example, prefer ${EMPTY}, ${SPACE}, ${SPACE}${VALID_USERNAME}, ${VALID_USERNAME}${SPACE}, or ${SPACE}${VALID_USERNAME}${SPACE} instead of creating wrapper aliases like ${WHITESPACE_ONLY_VALUE} or ${USERNAME_WITH_SPACES}.\n"
        "- If a value is a simple derived variation of an existing semantic variable, prefer composition over a new standalone variable. Examples include leading/trailing spaces, repeated spaces, repeated existing usernames, or other formatting-only variations.\n"
        "- Avoid opaque or oversized literal variables for long-value scenarios when the value can be derived from an existing semantic variable through composition. Only keep a dedicated long-value variable when a specific fixed boundary value is clearly reused across multiple approved tests.\n"
        "- Variable names must truthfully match the value. If a name implies spaces, blank input, long text, or invalid credentials, the value must actually reflect that meaning; otherwise repair or omit the variable.\n"
        "- Do not invent unsupported data.\n"
        "- Keep the Variables section concise, semantic, and reusable.\n"
        "- Ensure resulting page keywords remain valid and maintainable.\n"
        "- The output must support downstream robot test generation where tests reference resource variables instead of direct literal values whenever reusable abstraction is possible.\n"
        "- The refined page resource must support zero hardcoded business-data literals in downstream suites except Robot built-ins and trivial inline composition explicitly allowed by framework policy.\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )

def load_approved_elements_for_workflow(workflow: dict) -> list[dict]:
    pages = workflow.get("pages", [])
    page_name = pages[0].get("name") if pages else "page"
    elements_path = get_page_metadata_dir(page_name) / f"{page_name}.elements.json"

    approved = []
    if elements_path.exists():
        try:
            data = read_json(elements_path)
            if isinstance(data, dict):
                approved = data.get("elements", [])
            elif isinstance(data, list):
                approved = data
        except Exception:
            approved = []

    grouped: dict[tuple[str, str], dict] = {}
    locator_priority_patterns = [
        (re.compile(r"^id=", re.IGNORECASE), 1),
        (re.compile(r"@data-testid|@testid", re.IGNORECASE), 2),
        (re.compile(r"@formcontrolname", re.IGNORECASE), 3),
        (re.compile(r"@name=", re.IGNORECASE), 4),
        (re.compile(r"@placeholder=", re.IGNORECASE), 5),
        (re.compile(r"@aria-label=", re.IGNORECASE), 6),
        (re.compile(r"^xpath=", re.IGNORECASE), 7),
    ]

    def locator_rank(locator: str) -> int:
        for pattern, rank in locator_priority_patterns:
            if pattern.search(locator):
                return rank
        return 99

    for item in approved:
        if not isinstance(item, dict):
            continue
        approved_name = clean_text(str(item.get("approvedName", "")))
        locator = clean_text(str(item.get("locator", "")))
        element_type = clean_text(str(item.get("type", "element"))).lower() or "element"
        if not approved_name or not locator or not bool(item.get("approved", True)):
            continue
        key = (approved_name.lower(), element_type)
        candidate = {
            "approvedName": approved_name,
            "type": element_type,
            "locator": locator,
            "approved": True,
        }
        existing = grouped.get(key)
        if not existing or locator_rank(locator) < locator_rank(existing.get("locator", "")):
            grouped[key] = candidate

    return list(grouped.values())


def sync_page_variables_from_approved_elements(workflow: dict, approved_elements: list[dict]) -> dict:
    pages = workflow.get("pages", [])
    page_name = pages[0].get("name") if pages else "page"
    page_url = pages[0].get("url") if pages and isinstance(pages[0], dict) else ""
    page_url = normalize_url_value(str(page_url))
    if not page_url and isinstance(workflow.get("targetPage"), dict):
        page_url = normalize_url_value(str(workflow.get("targetPage", {}).get("url", "")))
    if not page_url and isinstance(workflow.get("entryPage"), dict):
        page_url = normalize_url_value(str(workflow.get("entryPage", {}).get("url", "")))
    metadata_dir = get_page_metadata_dir(page_name)
    navigation_debug_path = metadata_dir / f"{page_name}.navigation.debug.json"
    if navigation_debug_path.exists():
        try:
            navigation_debug_payload = read_json(navigation_debug_path)
            if isinstance(navigation_debug_payload, list):
                for item in reversed(navigation_debug_payload):
                    if not isinstance(item, dict):
                        continue
                    final_url = normalize_url_value(str(item.get("final_url", "")))
                    if final_url:
                        page_url = final_url
                        break
        except Exception:
            pass

    canonical_elements = load_approved_elements_for_workflow(workflow) if workflow else []
    if not canonical_elements:
        canonical_elements = approved_elements

    variables = []
    seen_names: set[str] = set()

    if page_url:
        variables.append({
            "variableName": "PAGE_URL",
            "value": page_url,
            "source": "approved_page",
            "kind": "page_url",
        })
        seen_names.add("PAGE_URL")

    for item in canonical_elements:
        if not isinstance(item, dict):
            continue
        approved_name = clean_text(str(item.get("approvedName", "")))
        locator = clean_text(str(item.get("locator", "")))
        if not approved_name or not locator:
            continue
        variable_name = to_robot_variable_name(approved_name)
        if variable_name in seen_names:
            continue
        seen_names.add(variable_name)
        variables.append({
            "variableName": variable_name,
            "value": locator,
            "source": "approved_element",
            "kind": "locator",
            "approvedName": approved_name,
            "type": clean_text(str(item.get("type", "element"))).lower() or "element",
        })

    payload = {
        "pageName": page_name,
        "pageUrl": page_url,
        "variables": variables,
    }
    write_json(get_page_variables_path(page_name), payload)
    return payload

def build_keywords_from_elements(elements: list[dict]) -> list[dict]:
    del elements
    return []


def sanitize_keyword_name(keyword_name: str, target_element: str = "", action: str = "", approved_element: dict | None = None) -> str:
    del target_element, action, approved_element
    return clean_text(keyword_name)


def normalize_resource_keyword_headers(resource_content: str, approved_keywords: list[dict]) -> str:
    del approved_keywords
    return strip_markdown_fences(resource_content or "")


def get_manual_tests_for_workflow(workflow: dict) -> list[dict]:
    workflow_name = derive_canonical_workflow_name(workflow, str(workflow.get("workflowName", "")))
    if not workflow_name:
        return []
    manual_path = get_manual_json_path(workflow_name)
    if not manual_path.exists():
        return []
    try:
        return extract_manual_test_cases(read_json(manual_path))
    except Exception:
        return []


def build_keyword_generation_prompt(
    workflow: dict,
    approved_elements: list[dict],
    approved_manual_tests: list[dict],
    existing_keywords: list[dict],
    existing_resource_content: str,
    common_resource_context: list[dict] | None = None,
) -> str:
    common_resource_context = common_resource_context or []
    common_keyword_names = sorted({
        clean_text(str(keyword.get("name", "")))
        for resource in common_resource_context
        for keyword in resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    })
    common_variable_names = sorted({
        clean_text(str(variable.get("name", "")))
        for resource in common_resource_context
        for variable in resource.get("variables", [])
        if clean_text(str(variable.get("name", "")))
    })
    page_resource_context = parse_resource_file(get_resource_path(approved_elements[0].get("pageName", "") or workflow.get("pages", [{}])[0].get("name", "page"))) if approved_elements or workflow.get("pages") else None
    approved_keyword_names = sorted({
        clean_text(str(item.get("keywordName", "")))
        for item in existing_keywords
        if clean_text(str(item.get("keywordName", "")))
    })
    approved_element_names = sorted({
        clean_text(str(item.get("approvedName", "")))
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    })
    manual_expected_outcomes = sorted({
        clean_text(str(item.get("expectedResult", "")))
        for item in approved_manual_tests
        if isinstance(item, dict) and clean_text(str(item.get("expectedResult", "")))
    })
    page_name_for_keywords = approved_elements[0].get("pageName", "") or workflow.get("pages", [{}])[0].get("name", "page") if (approved_elements or workflow.get("pages")) else "page"
    keyword_reuse_analysis = analyze_keyword_artifact_reuse(existing_keywords, page_name_for_keywords)
    payload = {
        "workflow": clean_workflow_for_prompting(workflow),
        "approved_elements": approved_elements,
        "approved_element_names": approved_element_names,
        "approved_manual_tests": approved_manual_tests,
        "approved_manual_expected_outcomes": manual_expected_outcomes,
        "existing_keywords": existing_keywords,
        "approved_keyword_names": approved_keyword_names,
        "existing_page_resource": existing_resource_content,
        "existing_page_resource_context": page_resource_context or {},
        "common_resource_context": common_resource_context,
        "retrieved_common_keyword_names": common_keyword_names,
        "retrieved_common_variable_names": common_variable_names,
        "reuse_analysis": keyword_reuse_analysis,
        "keyword_reuse_analysis": keyword_reuse_analysis,
    }
    return (
        "You are AI Layer K1: a Robot Framework page-keyword designer in a staged AI automation framework.\n"
        "Your job is to generate the approved keyword model for a single page after manual tests have already been approved.\n\n"
        "Primary objective:\n"
        "- Produce a compact but complete page-keyword model that supports the approved manual tests.\n"
        "- Use approved elements as the UI source of truth.\n"
        "- Use approved manual tests as the scenario source of truth.\n"
        "- Use retrieved common/shared resource context as the framework source of truth for generic reusable behavior.\n"
        "- Prefer reusable page actions and reusable page validations over scenario-specific one-off keywords.\n"
        "- Include only keywords that are grounded in approved elements and justified by approved manual scenarios.\n\n"
        "Retrieval-grounding rules:\n"
        "- Treat common_resource_context, existing_page_resource_context, approved_elements, and approved_manual_tests as retrieved context, similar to RAG grounding.\n"
        "- Never recreate generic common/shared keywords that already exist in retrieved_common_keyword_names.\n"
        "- Reuse approved keyword names from approved_keyword_names whenever they already express the needed page behavior.\n"
        "- Reuse approved element names from approved_element_names exactly whenever a keyword targets one of those elements.\n"
        "- If a keyword implementation needs waits, clicks, typing, or generic navigation, prefer retrieved common/shared helpers dynamically when those helpers are present in common_resource_context, but do not assume a fixed helper vocabulary.\n"
        "- If existing_page_resource_context already contains a suitable page keyword or page variable, prefer preserving and refining it rather than inventing a parallel one.\n"
        "- Treat reuse_analysis as authoritative duplicate-risk context. If it indicates overlapping ownership or reusable existing capability, minimize net-new keyword creation and preserve reuse.\n"
        "- Keep page keywords page-specific and semantically grounded in approved_elements and approved_manual_tests; use common_resource_context for generic mechanics.\n\n"
        "Mandatory rules:\n"
        "- Return only a valid JSON array.\n"
        "- Each array item must be an object with exactly these keys: keywordId, keywordName, targetElement, action, arguments, implementation, approved.\n"
        "- action should be one of click, input, select, verify, generic.\n"
        "- approved must be true.\n"
        "- targetElement must map to an approved element whenever the keyword directly acts on or validates a specific element.\n"
        "- implementation must be an array of Robot Framework keyword lines only.\n"
        "- For generic interaction steps in implementation, prefer retrieved common/shared keywords over raw SeleniumLibrary calls whenever suitable helpers are discoverable in common_resource_context.\n"
        "- Prefer reusable shared/common helper style when the provided shared context clearly supports it, but do not rely on a fixed list of helper names or hardcoded interaction mappings.\n"
        "- Do not return markdown fences or explanation text.\n"
        "- Do not invent unsupported keywords, locators, fields, messages, or workflows.\n"
        "- Reuse-first rule: identify reusable approved keyword capability first, identify only true gaps second, and keep net-new keywords minimal.\n"
        "- Do not emit duplicate keywordName values or parallel synonyms for the same approved page behavior.\n"
        "- If a candidate implementation would duplicate an existing approved keyword name, normalized implementation, or shared/common helper-backed behavior, reuse/refine the existing capability instead of emitting a parallel keyword.\n\n"
        "Design guidance:\n"
        "- Prefer semantic reusable page-object keywords such as Enter Username, Enter Password, Click Sign In Button, Verify Password Field Is Masked, Verify Login Form Loaded, Verify Login Failed And Still On Login Page, Verify Successful Login Redirect, or similarly grounded page-specific validations.\n"
        "- Avoid generating scenario-wrapper keywords that merely encode one approved manual test case, unless a concise page-level composite action is clearly justified.\n"
        "- Avoid overfitting keywords to one test variation such as blank username, wrong password, or whitespace username when reusable atomic keywords plus resource variables can support those scenarios.\n"
        "- If approved manual tests imply reusable validations for required fields, authentication rejection, redirect success, page readiness, masking, navigation controls, or visible messages, include those validations when grounded in the approved elements or existing resource content.\n"
        "- When approved manual tests expect visible rejection, validation feedback, authentication failure, required-field indication, blocked access, or other observable negative outcomes, prefer dedicated reusable page validation keywords over weak same-page-only checks whenever grounded evidence is available.\n"
        "- Preserve useful existing page keywords when they are still aligned with the approved manual tests.\n"
        "- Keep the keyword set thin, maintainable, and sufficient for downstream resource generation and automation generation.\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )

def build_keyword_review_prompt(
    workflow: dict,
    approved_elements: list[dict],
    approved_manual_tests: list[dict],
    candidate_keywords: list[dict],
    existing_page_resource: str,
    common_resource_context: list[dict] | None = None,
) -> str:
    common_resource_context = common_resource_context or []
    page_name_for_keywords = approved_elements[0].get("pageName", "") or workflow.get("pages", [{}])[0].get("name", "page") if (approved_elements or workflow.get("pages")) else "page"
    keyword_reuse_analysis = analyze_keyword_artifact_reuse(candidate_keywords, page_name_for_keywords)
    payload = {
        "workflow": clean_workflow_for_prompting(workflow),
        "approved_elements": approved_elements,
        "approved_manual_tests": approved_manual_tests,
        "candidate_keywords": candidate_keywords,
        "existing_page_resource": existing_page_resource,
        "common_resource_context": common_resource_context,
        "reuse_analysis": keyword_reuse_analysis,
        "keyword_reuse_analysis": keyword_reuse_analysis,
        "review_goals": [
            "Preserve approved semantic keyword names and target-element grounding.",
            "Improve implementation quality using dynamic common/shared helper discovery rather than hardcoded mappings.",
            "Normalize inconsistent interaction patterns when stronger reusable shared/common helpers are discoverable from the provided resource context.",
            "Keep reviewed keyword artifacts compact, reusable, page-specific, and suitable as the implementation lineage for final resource generation.",
            "Repair duplicate names, technical variable leakage, and keyword-name versus implementation-scope mismatches before the reviewed artifact is saved.",
        ],
    }
    return (
        "You are AI Layer K2: a reviewed-keyword normalization and refinement specialist for an AI-first Robot Framework automation framework.\n"
        "Your task is to review and refine a candidate page-keyword artifact before it becomes the approved reviewed keyword lineage used for final page resource generation.\n\n"
        "Primary objective:\n"
        "- Return a cleaned, normalized, implementation-aware reviewed keyword artifact for one page.\n"
        "- Preserve approved semantic keyword names and approved target-element grounding whenever feasible.\n"
        "- Improve implementation consistency through AI reasoning based on approved artifacts and discovered shared/common helpers.\n"
        "- Do not rely on hardcoded interaction maps or workflow-specific code assumptions.\n\n"
        "Mandatory rules:\n"
        "- Return only a valid JSON array.\n"
        "- Each array item must be an object with exactly these keys: keywordId, keywordName, targetElement, action, arguments, implementation, approved.\n"
        "- Keep keywordName business-readable and aligned with approved element names.\n"
        "- Keep targetElement grounded in approved elements whenever the keyword acts on a specific element.\n"
        "- implementation must be an array of Robot Framework keyword lines only.\n"
        "- approved must be true for retained keywords.\n"
        "- Do not invent unsupported locators, messages, page flows, or framework keywords.\n"
        "- Do not add markdown fences or explanation text.\n"
        "- Treat reuse_analysis as authoritative duplicate-risk context during review. Resolve overlaps by preserving/reusing approved existing capability instead of keeping parallel keywords.\n"
        "- Do not emit duplicate keywordName values in the final reviewed artifact. Each retained keyword must have a unique semantic name. If multiple candidates normalize to the same semantic name, keep one retained keyword with the strongest grounded implementation and merge or drop weaker duplicates.\n"
        "- Do not emit implementation lines that reference non-canonical locator variables when the approved page metadata already establishes a cleaner canonical variable name for the same target element.\n"
        "- Normalize reviewed implementations toward the same canonical semantic variable names that the final page resource is expected to preserve. Avoid leaving extraction-era aliases, technical DOM-id aliases, or mixed naming styles for the same retained control.\n"
        "- When a retained keyword has a grounded targetElement and that targetElement has an approved canonical page variable, ensure the implementation references that canonical variable for the direct page interaction or validation instead of a stale alias.\n"
        "- If a candidate implementation is grounded but uses stale alias variables, refine the implementation to the approved canonical variable names rather than preserving the stale aliases.\n"
        "- When the approved manual outcomes imply absence checks, create page-level absence validations only for controls or indicators that are explicitly grounded in approved elements, approved reviewed keywords, or stable existing page-resource evidence.\n"
        "- Do not invent self-created placeholder indicators, text aliases, synthetic absence-only variables, or speculative element/variable names that are not grounded in approved page artifacts.\n"
        "- If authenticated-state absence is mentioned in manual expectations but there is no approved element or stable page-resource evidence for a specific indicator, keep the reviewed artifact focused on grounded positive page-state validations instead of generating speculative negative keywords.\n"
        "- If a negative validation cannot be grounded in approved elements, approved reviewed keywords, or stable existing page-resource evidence, omit it instead of fabricating placeholder data or synthetic artifact entries.\n\n"
        "Review and normalization rules:\n"
        "- Treat candidate_keywords as the primary semantic lineage, but improve weak implementation choices when approved evidence supports a better reusable abstraction.\n"
        "- Infer reusable interaction preferences dynamically from common_resource_context and existing_page_resource.\n"
        "- When both a low-level framework interaction and a higher-level shared/common helper can satisfy the same intent, prefer the discovered shared/common helper if it is clearly supported by the provided context.\n"
        "- If one candidate keyword already uses a reusable shared/common helper for an interaction pattern and another semantically similar candidate uses lower-level framework steps for the same pattern, normalize toward the reusable helper style when supported by the shared/common context.\n"
        "- Preserve page-specific validations and reusable atomic page actions.\n"
        "- Remove or simplify scenario-wrapper keywords when they are redundant and not useful as stable page-level abstractions.\n"
        "- Avoid duplicate keywords that share the same semantic intent but differ only by argument usage or literal examples.\n"
        "- The implementation scope must match the keyword name. If a keyword name is singular and element-scoped, its implementation should validate or act on that element only. If an implementation validates a group, state, or collection of controls, rename it to a matching group/state-level keyword instead of keeping a misleading singular element name.\n"
        "- Replace technical locator-driven variable references with the best available reviewed semantic variable names inferred from approved elements and existing page resource context.\n"
        "- Where approved manual expected outcomes describe visible guest-state presence, enabled state, absence of authenticated-only controls, or graceful state retention, prefer stable reusable page-level validation keywords that reflect those exact observable outcomes.\n"
        "- Keep implementations concise, maintainable, and suitable for downstream page resource generation.\n"
        "- Prefer reviewed implementations that make downstream resource generation naturally preserve common helper usage.\n"
        "- If the shared/common context does not clearly support a reusable helper, keep a valid low-level implementation rather than inventing one.\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )


def review_and_refine_page_elements(workflow: dict, review_data: dict) -> tuple[list[dict], dict | None]:
    workflow_name = derive_canonical_workflow_name(workflow, review_data["page_name"])
    raw_elements = review_data.get("raw_elements", [])
    if not raw_elements:
        return review_data.get("elements", []), None

    draft_elements = []
    for idx, item in enumerate(raw_elements):
        if not isinstance(item, dict):
            continue
        draft_elements.append(normalize_extracted_element(item, idx))

    approved_element_names = {
        clean_text(str(item.get("approvedName", ""))).lower()
        for item in load_approved_elements_for_workflow(workflow)
        if isinstance(item, dict) and clean_text(str(item.get("approvedName", "")))
    }
    if approved_element_names:
        draft_elements = [
            item for item in draft_elements
            if clean_text(str(item.get("approvedName", ""))).lower() in approved_element_names
        ]

    draft_payload = {
        "pageName": review_data["page_name"],
        "pageUrl": review_data["page_url"],
        "rawElements": raw_elements,
        "elements": draft_elements,
    }
    review_result = None
    refined_elements = draft_elements
    try:
        config = validate_robot_config(load_robot_ai_json(CONFIG_PATH))
        ai_cfg = config.get("ai", {})
        endpoint = ai_cfg.get("endpoint", "").strip()
        token = get_robot_ai_token(ai_cfg)
        if ai_cfg.get("enabled", True) and endpoint and token:
            reviewer_prompt = (
                Path(BASE_DIR / "prompts" / "page_elements_reviewer.md").read_text(encoding="utf-8")
                + "\n\nWorkflow Context:\n"
                + json.dumps(clean_workflow_for_prompting(workflow), indent=2)
                + "\n\nPage Name:\n"
                + review_data["page_name"]
                + "\n\nDraft Page Elements JSON:\n"
                + json.dumps(draft_payload, indent=2)
            )
            review_raw = call_ai_with_workflow_session(
                workflow_name=workflow_name,
                stage="page_elements_review",
                endpoint=endpoint,
                token=token,
                prompt=reviewer_prompt,
                timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                verify_ssl=ai_cfg.get("verify_ssl", False),
            )
            review_result = json.loads(strip_markdown_fences(review_raw))

            refiner_prompt = (
                Path(BASE_DIR / "prompts" / "page_elements_refiner.md").read_text(encoding="utf-8")
                + "\n\nWorkflow Context:\n"
                + json.dumps(clean_workflow_for_prompting(workflow), indent=2)
                + "\n\nDraft Page Elements JSON:\n"
                + json.dumps(draft_payload, indent=2)
                + "\n\nReview Findings:\n"
                + json.dumps(review_result, indent=2)
            )
            refined_raw = call_ai_with_workflow_session(
                workflow_name=workflow_name,
                stage="page_elements_refine",
                endpoint=endpoint,
                token=token,
                prompt=refiner_prompt,
                timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                verify_ssl=ai_cfg.get("verify_ssl", False),
            )
            refined_payload = json.loads(strip_markdown_fences(refined_raw))
            candidate_elements = refined_payload.get("elements", []) if isinstance(refined_payload, dict) else []
            normalized = []
            for idx, item in enumerate(candidate_elements, start=1):
                if not isinstance(item, dict):
                    continue
                name = clean_text(str(item.get("name", "")))
                locator = clean_text(str(item.get("locator", "")))
                if not name or not locator:
                    continue
                normalized.append({
                    "approvedName": name,
                    "type": clean_text(str(item.get("type", "element"))).lower() or "element",
                    "locator": locator,
                    "approved": True,
                    "description": clean_text(str(item.get("description", ""))),
                })
            if approved_element_names:
                normalized = [
                    item for item in normalized
                    if clean_text(str(item.get("approvedName", ""))).lower() in approved_element_names
                ]
            if normalized:
                refined_elements = normalized
                refined_payload_to_store = {
                    "pageName": review_data["page_name"],
                    "pageUrl": review_data["page_url"],
                    "rawElements": raw_elements,
                    "elements": refined_elements,
                    "reviewSummary": review_result,
                }
                write_json(get_page_reviewed_path(review_data["page_name"]), refined_payload_to_store)
    except Exception as exc:
        review_result = {
            "overall_quality": "low",
            "summary": f"AI refinement failed: {str(exc)}",
            "issues": [],
        }
        draft_payload["reviewSummary"] = review_result
        write_json(get_page_reviewed_path(review_data["page_name"]), draft_payload)

    return refined_elements, review_result


def validate_reviewed_keywords_against_existing_resources(keywords: list[dict], page_name: str) -> tuple[bool, str]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_names: set[str] = set()
    seen_signatures: set[str] = set()

    approved_elements = load_approved_elements_for_workflow({"pages": [{"name": page_name}]})
    canonical_variables_by_element = {
        clean_text(str(item.get("approvedName", ""))): to_robot_variable_name(clean_text(str(item.get("approvedName", ""))))
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    }
    approved_locator_variables = {name.upper() for name in canonical_variables_by_element.values() if name}

    resource_path = get_resource_path(page_name)
    existing_resource_variables: set[str] = set()
    if resource_path.exists():
        try:
            parsed_resource = parse_resource_file(resource_path)
            existing_resource_variables = {
                clean_text(str(item.get("name", ""))).upper()
                for item in parsed_resource.get("variables", [])
                if clean_text(str(item.get("name", "")))
            }
        except Exception:
            existing_resource_variables = set()

    allowed_argument_names = {"TEXT", "PASSWORD", "VALUE", "URL", "TIMEOUT", "EXPECTED", "MESSAGE"}

    for keyword in keywords:
        name = clean_text(str(keyword.get("keywordName", "")))
        if not name:
            continue
        lowered = name.lower()
        if lowered in seen_names:
            continue
        seen_names.add(lowered)

        normalized_signature = normalize_name_tokens(name) + "::" + "|".join(
            clean_text(line).lower() for line in (keyword.get("implementation", []) or []) if clean_text(line)
        )
        if normalized_signature in seen_signatures:
            errors.append(f"Duplicate reviewed keyword implementation signature inside artifact: {name}")
        seen_signatures.add(normalized_signature)

        target_element = clean_text(str(keyword.get("targetElement", "")))
        expected_target_variable = canonical_variables_by_element.get(target_element, "")
        arguments = {
            clean_text(str(arg)).replace("${", "").replace("}", "").upper()
            for arg in (keyword.get("arguments", []) or [])
            if clean_text(str(arg))
        }
        implementation_lines = [clean_text(str(line)) for line in (keyword.get("implementation", []) or []) if clean_text(str(line))]
        referenced_variables = {
            ref.upper()
            for line in implementation_lines
            for ref in re.findall(r"\$\{([A-Z0-9_]+)\}", line)
        }

        for ref in sorted(referenced_variables):
            if ref in arguments or ref in allowed_argument_names:
                continue
            if ref in approved_locator_variables or ref in existing_resource_variables:
                continue
            errors.append(f"Reviewed keyword '{name}' references unknown variable '${{{ref}}}' in its implementation")

        if expected_target_variable and referenced_variables and expected_target_variable not in referenced_variables:
            warnings.append(
                f"Reviewed keyword '{name}' targets '{target_element}' but its implementation does not reference canonical variable '${{{expected_target_variable}}}'"
            )

    if errors:
        messages = [f"- {error}" for error in errors] + [f"- {warning}" for warning in warnings]
        return False, "\n".join(messages)
    return True, "\n".join(f"- {warning}" for warning in warnings)


def get_keyword_review_data(workflow: dict):
    pages = workflow.get("pages", [])
    page_name = pages[0].get("name") if pages else "page"
    keywords_path = get_keywords_path(page_name)
    reviewed_keywords_path = get_keywords_reviewed_path(page_name)
    resource_path = get_resource_path(page_name)

    review_summary = None
    source_artifact = "raw"
    source_keywords_path = reviewed_keywords_path if reviewed_keywords_path.exists() else keywords_path
    if reviewed_keywords_path.exists():
        source_artifact = "refined"
    elif keywords_path.exists():
        source_artifact = "approved"

    approved_elements = load_approved_elements_for_workflow(workflow)
    approved_manual_tests = get_manual_tests_for_workflow(workflow)
    common_resource_context = []
    resources_dir = BASE_DIR / "resources"
    if resources_dir.exists():
        for common_resource_path in sorted(resources_dir.glob("*.resource")):
            try:
                common_resource_context.append(parse_resource_file(common_resource_path))
            except Exception:
                continue
    approved_elements_by_name = {
        clean_text(str(item.get("approvedName", ""))): item
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    }
    disallowed_resource_keywords = {
        "open page",
        "open browser to page",
    }

    keywords = []
    if source_keywords_path.exists() and approved_elements_by_name:
        try:
            payload = read_json(source_keywords_path)
            raw_keywords = payload.get("keywords", [])
            filtered_keywords = []
            for item in raw_keywords:
                keyword_name = clean_text(str(item.get("keywordName", "")))
                if not keyword_name or keyword_name.lower() in disallowed_resource_keywords:
                    continue
                target_element = clean_text(str(item.get("targetElement", "")))
                implementation = item.get("implementation", [])
                if isinstance(implementation, str):
                    implementation = [line.rstrip() for line in implementation.splitlines() if clean_text(line)]
                implementation = [str(line).rstrip() for line in implementation if clean_text(str(line))]
                arguments = item.get("arguments", [])
                if isinstance(arguments, str):
                    arguments = [arg.strip() for arg in arguments.split(",") if arg.strip()]
                arguments = [str(arg).replace("${", "").replace("}", "").strip() for arg in arguments if clean_text(str(arg))]
                filtered_keywords.append({
                    "keywordId": clean_text(str(item.get("keywordId", ""))) or f"KW_{len(filtered_keywords)+1:03d}",
                    "keywordName": keyword_name,
                    "targetElement": target_element,
                    "action": clean_text(str(item.get("action", ""))) or "generic",
                    "arguments": arguments,
                    "implementation": implementation,
                    "approved": bool(item.get("approved", True)),
                })
            keywords = filtered_keywords
        except Exception:
            keywords = []

    if not keywords and resource_path.exists() and approved_elements_by_name:
        try:
            resource_context = parse_resource_file(resource_path)
            for idx, keyword in enumerate(resource_context.get("keywords", []), start=1):
                keyword_name = clean_text(str(keyword.get("name", "")))
                lowered_name = keyword_name.lower()
                if not keyword_name or lowered_name in disallowed_resource_keywords:
                    continue

                target_element = ""
                action = "generic"
                if lowered_name.startswith("click "):
                    action = "click"
                elif lowered_name.startswith("enter ") or lowered_name.startswith("input "):
                    action = "input"
                elif lowered_name.startswith("select "):
                    action = "select"
                elif lowered_name.startswith("verify "):
                    action = "verify"

                implementation_lines = [line.rstrip() for line in keyword.get("body", []) if clean_text(str(line))]
                keywords.append({
                    "keywordId": f"KW_{idx:03d}",
                    "keywordName": keyword_name,
                    "targetElement": target_element,
                    "action": action,
                    "arguments": [arg.replace("${", "").replace("}", "") for arg in keyword.get("args", [])],
                    "implementation": implementation_lines,
                    "approved": True,
                })
        except Exception:
            keywords = []

    if not keywords:
        keywords = build_keywords_from_elements(approved_elements)

    if approved_elements and approved_manual_tests:
        try:
            workflow_name = derive_canonical_workflow_name(workflow, page_name)
            config = validate_robot_config(load_robot_ai_json(CONFIG_PATH))
            ai_cfg = config.get("ai", {})
            if ai_cfg.get("enabled", True):
                endpoint = ai_cfg.get("endpoint", "").strip()
                token = get_robot_ai_token(ai_cfg)
                if endpoint and token:
                    reviewed_keywords_raw = call_ai_with_workflow_session(
                        workflow_name=workflow_name,
                        stage="keyword_ui_review",
                        endpoint=endpoint,
                        token=token,
                        prompt=build_keyword_generation_prompt(
                            workflow,
                            approved_elements,
                            approved_manual_tests,
                            keywords,
                            read_text(resource_path),
                            common_resource_context,
                        ),
                        timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                        verify_ssl=ai_cfg.get("verify_ssl", False),
                    )
                    reviewed_keywords = json.loads(strip_markdown_fences(reviewed_keywords_raw))
                    if isinstance(reviewed_keywords, list):
                        keyword_review_prompt = build_keyword_review_prompt(
                            workflow,
                            approved_elements,
                            approved_manual_tests,
                            reviewed_keywords,
                            read_text(resource_path),
                            common_resource_context,
                        )
                        reviewed_keywords_refined_raw = call_ai_with_workflow_session(
                            workflow_name=workflow_name,
                            stage="keyword_artifact_refine",
                            endpoint=endpoint,
                            token=token,
                            prompt=keyword_review_prompt,
                            timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                            verify_ssl=ai_cfg.get("verify_ssl", False),
                        )
                        refined_reviewed_keywords = json.loads(strip_markdown_fences(reviewed_keywords_refined_raw))
                        if isinstance(refined_reviewed_keywords, list) and refined_reviewed_keywords:
                            reviewed_keywords = refined_reviewed_keywords
                        normalized_reviewed = []
                        source_artifact = "refined"
                        for idx, item in enumerate(reviewed_keywords, start=1):
                            if not isinstance(item, dict):
                                continue
                            keyword_name = clean_text(str(item.get("keywordName", "")))
                            if not keyword_name or keyword_name.lower() in disallowed_resource_keywords:
                                continue
                            target_element = clean_text(str(item.get("targetElement", "")))
                            if target_element and target_element not in approved_elements_by_name:
                                continue
                            keyword_name = sanitize_keyword_name(keyword_name, target_element, clean_text(str(item.get("action", ""))) or "generic")
                            implementation = item.get("implementation", [])
                            if isinstance(implementation, str):
                                implementation = [line.rstrip() for line in implementation.splitlines() if clean_text(line)]
                            implementation = [str(line).rstrip() for line in implementation if clean_text(str(line))]
                            if not implementation:
                                continue
                            arguments = item.get("arguments", [])
                            if isinstance(arguments, str):
                                arguments = [arg.strip() for arg in arguments.split(",") if arg.strip()]
                            arguments = [str(arg).replace("${", "").replace("}", "").strip() for arg in arguments if clean_text(str(arg))]
                            normalized_reviewed.append({
                                "keywordId": clean_text(str(item.get("keywordId", ""))) or f"KW_{idx:03d}",
                                "keywordName": keyword_name,
                                "targetElement": target_element,
                                "action": clean_text(str(item.get("action", ""))) or "generic",
                                "arguments": arguments,
                                "implementation": implementation,
                                "approved": bool(item.get("approved", True)),
                            })
                        if normalized_reviewed:
                            reviewed_valid, reviewed_message = validate_reviewed_keywords_against_existing_resources(normalized_reviewed, page_name)
                            if not reviewed_valid:
                                keyword_review_prompt_with_failures = (
                                    keyword_review_prompt
                                    + "\n\nAdditional validation failures that must be resolved before saving reviewed keywords:\n"
                                    + reviewed_message
                                    + "\n\nReturn only a corrected valid JSON array of reviewed keywords that reuses approved existing capability instead of duplicating it."
                                )
                                reviewed_keywords_refined_raw = call_ai_with_workflow_session(
                                    workflow_name=workflow_name,
                                    stage="keyword_artifact_refine_conflicts",
                                    endpoint=endpoint,
                                    token=token,
                                    prompt=keyword_review_prompt_with_failures,
                                    timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                                    verify_ssl=ai_cfg.get("verify_ssl", False),
                                )
                                refined_reviewed_keywords = json.loads(strip_markdown_fences(reviewed_keywords_refined_raw))
                                if isinstance(refined_reviewed_keywords, list) and refined_reviewed_keywords:
                                    retry_normalized_reviewed = []
                                    for idx, item in enumerate(refined_reviewed_keywords, start=1):
                                        if not isinstance(item, dict):
                                            continue
                                        keyword_name = clean_text(str(item.get("keywordName", "")))
                                        if not keyword_name or keyword_name.lower() in disallowed_resource_keywords:
                                            continue
                                        target_element = clean_text(str(item.get("targetElement", "")))
                                        if target_element and target_element not in approved_elements_by_name:
                                            continue
                                        keyword_name = sanitize_keyword_name(keyword_name, target_element, clean_text(str(item.get("action", ""))) or "generic")
                                        implementation = item.get("implementation", [])
                                        if isinstance(implementation, str):
                                            implementation = [line.rstrip() for line in implementation.splitlines() if clean_text(line)]
                                        implementation = [str(line).rstrip() for line in implementation if clean_text(str(line))]
                                        if not implementation:
                                            continue
                                        arguments = item.get("arguments", [])
                                        if isinstance(arguments, str):
                                            arguments = [arg.strip() for arg in arguments.split(",") if arg.strip()]
                                        arguments = [str(arg).replace("${", "").replace("}", "").strip() for arg in arguments if clean_text(str(arg))]
                                        retry_normalized_reviewed.append({
                                            "keywordId": clean_text(str(item.get("keywordId", ""))) or f"KW_{idx:03d}",
                                            "keywordName": keyword_name,
                                            "targetElement": target_element,
                                            "action": clean_text(str(item.get("action", ""))) or "generic",
                                            "arguments": arguments,
                                            "implementation": implementation,
                                            "approved": bool(item.get("approved", True)),
                                        })
                                    retry_valid, retry_message = validate_reviewed_keywords_against_existing_resources(retry_normalized_reviewed, page_name)
                                    if retry_normalized_reviewed and retry_valid:
                                        normalized_reviewed = retry_normalized_reviewed
                            if normalized_reviewed:
                                keywords = normalized_reviewed
                                write_json(reviewed_keywords_path, {
                                    "pageName": page_name,
                                    "keywords": normalized_reviewed,
                                })
        except Exception:
            pass

    return {
        "page_name": page_name,
        "keywords_path": keywords_path,
        "reviewed_keywords_path": reviewed_keywords_path,
        "resource_path": resource_path,
        "keywords": keywords,
        "approved_elements": approved_elements,
        "review_summary": review_summary,
        "source_artifact": source_artifact,
    }

def review_and_refine_resource_artifact(workflow: dict, page_name: str, elements: list[dict], draft_resource: str):
    workflow_name = derive_canonical_workflow_name(workflow, page_name)

    review_result = None
    refined_resource = draft_resource
    try:
        config = validate_robot_config(load_robot_ai_json(CONFIG_PATH))
        ai_cfg = config.get("ai", {})
        endpoint = ai_cfg.get("endpoint", "").strip()
        token = get_robot_ai_token(ai_cfg)
        common_resource = read_text(BASE_DIR / "resources" / "common_keywords.resource")
        if ai_cfg.get("enabled", True) and endpoint and token and draft_resource.strip():
            reviewer_prompt = (
                Path(BASE_DIR / "prompts" / "resource_reviewer.md").read_text(encoding="utf-8")
                + "\n\nWorkflow Context:\n"
                + json.dumps(clean_workflow_for_prompting(workflow), indent=2)
                + "\n\nPage Elements Artifact:\n"
                + json.dumps(elements, indent=2)
                + "\n\nCommon Shared Resource Content:\n"
                + common_resource
                + "\n\nGenerated Page Resource Draft:\n"
                + draft_resource
            )
            review_raw = call_ai_with_workflow_session(
                workflow_name=workflow_name,
                stage="resource_review",
                endpoint=endpoint,
                token=token,
                prompt=reviewer_prompt,
                timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                verify_ssl=ai_cfg.get("verify_ssl", False),
            )
            review_result = json.loads(strip_markdown_fences(review_raw))

            approved_keywords_payload = {}
            approved_keywords_path = get_keywords_reviewed_path(page_name)
            if approved_keywords_path.exists():
                try:
                    approved_keywords_payload = read_json(approved_keywords_path)
                except Exception:
                    approved_keywords_payload = {}

            refiner_prompt = (
                Path(BASE_DIR / "prompts" / "resource_refiner.md").read_text(encoding="utf-8")
                + "\n\nWorkflow Context:\n"
                + json.dumps(clean_workflow_for_prompting(workflow), indent=2)
                + "\n\nApproved Artifact Lineage:\n"
                + json.dumps({
                    "elements_source": str(get_page_reviewed_path(page_name).relative_to(BASE_DIR)).replace("\\", "/"),
                    "keywords_source": str(approved_keywords_path.relative_to(BASE_DIR)).replace("\\", "/") if approved_keywords_path.exists() else "",
                    "resource_target": str(get_resource_path(page_name).relative_to(BASE_DIR)).replace("\\", "/"),
                    "lineage_rule": "Approved reviewed artifacts are the semantic source of truth. Preserve approved names exactly whenever feasible.",
                }, indent=2)
                + "\n\nPage Elements Artifact:\n"
                + json.dumps(elements, indent=2)
                + "\n\nApproved Reviewed Keywords Artifact:\n"
                + json.dumps(approved_keywords_payload, indent=2)
                + "\n\nCommon Shared Resource Content:\n"
                + common_resource
                + "\n\nReviewer Findings:\n"
                + json.dumps(review_result, indent=2)
                + "\n\nOriginal Draft Resource:\n"
                + draft_resource
            )
            refined_raw = call_ai_with_workflow_session(
                workflow_name=workflow_name,
                stage="resource_refine",
                endpoint=endpoint,
                token=token,
                prompt=refiner_prompt,
                timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                verify_ssl=ai_cfg.get("verify_ssl", False),
            )
            candidate = strip_markdown_fences(refined_raw).strip()
            if candidate and "*** Keywords ***" in candidate and "*** Variables ***" in candidate and "*** Settings ***" in candidate:
                refined_resource = candidate
    except Exception as exc:
        review_result = {
            "overall_quality": "low",
            "summary": f"AI refinement failed: {str(exc)}",
            "issues": [],
            "recommended_additions": [],
        }

    write_text_file(get_resource_path(page_name), refined_resource)
    return refined_resource, review_result


def enrich_resource_with_manual_test_variables(workflow: dict, approved_keywords: list[dict]) -> str:
    pages = workflow.get("pages", [])
    page_name = pages[0].get("name") if pages else "page"
    resource_path = get_resource_path(page_name)
    if not resource_path.exists():
        return ""

    workflow_name = derive_canonical_workflow_name(workflow, page_name)
    manual_path = get_manual_json_path(workflow_name)
    if not manual_path.exists():
        return read_text(resource_path)

    approved_manual_tests = extract_manual_test_cases(read_json(manual_path))
    if not approved_manual_tests:
        return read_text(resource_path)

    approved_elements = load_approved_elements_for_workflow(workflow)
    current_resource = read_text(resource_path)

    try:
        config = validate_robot_config(load_robot_ai_json(CONFIG_PATH))
        ai_cfg = config.get("ai", {})
        endpoint = ai_cfg.get("endpoint", "").strip()
        token = get_robot_ai_token(ai_cfg)
        if not ai_cfg.get("enabled", True) or not endpoint or not token:
            return current_resource

        enrichment_prompt = get_manual_tests_variable_enrichment_prompt(
            workflow,
            approved_elements,
            approved_keywords,
            approved_manual_tests,
            current_resource,
        )
        enriched_raw = call_ai_with_workflow_session(
            workflow_name=workflow_name,
            stage="resource_variable_enrichment",
            endpoint=endpoint,
            token=token,
            prompt=enrichment_prompt,
            timeout_seconds=ai_cfg.get("timeout_seconds", 120),
            verify_ssl=ai_cfg.get("verify_ssl", False),
        )
        candidate = normalize_resource_content(strip_markdown_fences(enriched_raw).strip())
        if candidate and "*** Keywords ***" in candidate and "*** Variables ***" in candidate and "*** Settings ***" in candidate:
            validation_ok, validation_message = validate_resource_content(candidate, [])
            if validation_message:
                append_session_message(workflow_name, "assistant", "resource_variable_enrichment_validation", validation_message)
            write_text_file(resource_path, candidate)
            return candidate
    except Exception:
        pass

    return current_resource


def validate_keyword_grounding(workflow: dict, keywords: list[dict]) -> tuple[bool, list[str], list[dict]]:
    pages = workflow.get("pages", [])
    page_name = pages[0].get("name") if pages else "page"
    warnings: list[str] = []

    approved_elements = load_approved_elements_for_workflow(workflow)
    approved_element_names = {
        clean_text(str(item.get("approvedName", "")))
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    }

    normalized_keywords: list[dict] = []
    for keyword in keywords:
        if not isinstance(keyword, dict):
            continue
        item = dict(keyword)
        keyword_name = clean_text(str(item.get("keywordName", "")))
        implementation = item.get("implementation", [])
        if isinstance(implementation, str):
            implementation = [line.rstrip() for line in implementation.splitlines() if clean_text(line)]
        implementation = [str(line).rstrip() for line in implementation if clean_text(str(line))]
        item["implementation"] = implementation

        target_element = clean_text(str(item.get("targetElement", "")))
        if target_element and target_element not in approved_element_names:
            warnings.append(f"Keyword '{clean_text(str(item.get('keywordName', '')))}' references non-approved target element '{target_element}'")

        normalized_keywords.append(item)

    return len([w for w in warnings if "non-approved target element" in w]) == 0, warnings, normalized_keywords


def save_keywords_for_workflow(workflow: dict, keywords: list[dict]):
    pages = workflow.get("pages", [])
    page_name = pages[0].get("name") if pages else "page"
    keywords_path = get_keywords_path(page_name)
    reviewed_keywords_path = get_keywords_reviewed_path(page_name)

    approved_elements = load_approved_elements_for_workflow(workflow)
    approved_elements_by_name = {
        clean_text(str(item.get("approvedName", ""))): item
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    }
    approved_titles_to_name = {
        to_keyword_title(name).lower(): name
        for name in approved_elements_by_name
    }
    canonical_variable_by_target = {
        clean_text(str(item.get("approvedName", ""))): to_robot_variable_name(clean_text(str(item.get("approvedName", ""))))
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    }
    approved_variable_names = set(canonical_variable_by_target.values())

    disallowed_resource_keywords = {
        "open page",
        "open browser to page",
    }

    def resolve_target_element(keyword_name: str, provided_target: str = "") -> str:
        target = clean_text(provided_target)
        if target in approved_elements_by_name:
            return target
        lowered_name = clean_text(keyword_name).lower()
        for candidate_title, element_name in approved_titles_to_name.items():
            if candidate_title and candidate_title in lowered_name:
                return element_name
        return ""

    def normalize_implementation_variables(lines: list[str], target_element: str) -> list[str]:
        normalized_lines: list[str] = []
        canonical_variable = canonical_variable_by_target.get(target_element, "")
        for line in lines:
            updated_line = str(line).rstrip()
            tokens = re.findall(r"\$\{([A-Z0-9_]+)\}", updated_line)
            if canonical_variable and any(token.startswith("AUTO_") for token in tokens):
                auto_tokens = [token for token in tokens if token.startswith("AUTO_")]
                if len(set(auto_tokens)) == 1:
                    updated_line = re.sub(r"\$\{AUTO_[A-Z0-9_]+\}", f"${{{canonical_variable}}}", updated_line)
            normalized_lines.append(updated_line)
        return normalized_lines

    normalized_keywords = []
    seen_keyword_names: set[str] = set()
    for idx, keyword in enumerate(keywords, start=1):
        keyword_name = clean_text(str(keyword.get("keywordName", "")))
        if not keyword_name or keyword_name.lower() in disallowed_resource_keywords:
            continue

        target_element = clean_text(str(keyword.get("targetElement", "")))
        keyword_name = sanitize_keyword_name(keyword_name, target_element, clean_text(str(keyword.get("action", ""))) or "generic")
        implementation = keyword.get("implementation", [])
        if isinstance(implementation, str):
            implementation = [line.rstrip() for line in implementation.splitlines() if line.strip()]
        implementation = [str(line).rstrip() for line in implementation if clean_text(str(line))]
        implementation = normalize_implementation_variables(implementation, target_element)
        if not implementation:
            continue

        normalized_keyword_name = keyword_name.lower()
        if normalized_keyword_name in seen_keyword_names:
            continue
        seen_keyword_names.add(normalized_keyword_name)

        arguments = keyword.get("arguments", [])
        if isinstance(arguments, str):
            arguments = [arg.strip() for arg in arguments.split(",") if arg.strip()]
        arguments = [str(arg).replace("${", "").replace("}", "").strip() for arg in arguments if clean_text(str(arg))]

        normalized_keywords.append({
            "keywordId": clean_text(str(keyword.get("keywordId", ""))) or f"KW_{idx:03d}",
            "keywordName": keyword_name,
            "targetElement": target_element,
            "action": clean_text(str(keyword.get("action", ""))) or "generic",
            "arguments": arguments,
            "implementation": implementation,
            "approved": bool(keyword.get("approved", True)),
        })

    payload = {
        "pageName": page_name,
        "keywords": normalized_keywords,
    }
    write_json(keywords_path, payload)
    write_json(reviewed_keywords_path, payload)

# -------------------------------------------------------------------
# AI-driven resource generation
# -------------------------------------------------------------------

def build_resource_generation_prompt(
    workflow: dict,
    approved_elements: list[dict],
    approved_keywords: list[dict],
    approved_manual_tests: list[dict] | None = None,
    common_resource_context: list[dict] | None = None,
    existing_page_resource: str = "",
) -> str:
    prompt_ready_workflow = clean_workflow_for_prompting(workflow)
    pages = workflow.get("pages", []) if isinstance(workflow, dict) else []
    page_name = clean_text(str(pages[0].get("name", ""))) if pages and isinstance(pages[0], dict) else "page"
    reviewed_keywords_path = get_keywords_reviewed_path(page_name)
    approved_keywords_path = get_keywords_path(page_name)
    approved_artifact_lineage = {
        "elements_source": f"pom_pages/{page_name}/metadata/{page_name}.elements.reviewed.json",
        "keywords_source": str(reviewed_keywords_path.relative_to(BASE_DIR)).replace("\\", "/") if reviewed_keywords_path.exists() else str(approved_keywords_path.relative_to(BASE_DIR)).replace("\\", "/") if approved_keywords_path.exists() else "",
        "resource_target": str(get_resource_path(page_name).relative_to(BASE_DIR)).replace("\\", "/"),
        "lineage_rule": "Approved reviewed artifacts are the semantic source of truth. Preserve approved variable names, but structurally normalize element-backed keyword names from approved targetElement and action before final save.",
    }
    workflow_expected_outcomes = collect_workflow_expected_outcomes(workflow)
    current_workflow_knowledge = build_workflow_knowledge_context(workflow)
    relevant_workflow_knowledge = discover_relevant_workflow_knowledge(workflow)
    payload = {
        "workflow": prompt_ready_workflow,
        "approved_elements": approved_elements,
        "approved_keywords": approved_keywords,
        "approved_manual_tests": approved_manual_tests or [],
        "common_resource_context": common_resource_context or [],
        "existing_page_resource": existing_page_resource,
        "approved_artifact_lineage": approved_artifact_lineage,
        "current_workflow_knowledge": current_workflow_knowledge,
        "relevant_workflow_knowledge": relevant_workflow_knowledge,
        "workflow_expected_outcomes": workflow_expected_outcomes,
        "generation_focus": [
            "Use approved reviewed artifacts as the semantic source of truth.",
            "Preserve approved variable names and structurally normalize element-backed keyword names from approved targetElement and action.",
            "Improve abstraction and naming quality through AI reasoning, not hardcoded workflow-specific logic.",
            "Prefer shared/common keywords for generic behavior and page-resource keywords for page semantics.",
            "Keep the page resource expressive enough that downstream suites can stay thin and business-readable.",
            "Create stronger page validations only when supported by workflow inputs, approved manual tests, or approved page evidence.",
            "Prefer evidence-based page validations grounded in workflow expected outcomes and approved page artifacts.",
            "Do not invent unsupported assertions; strengthen validations only when supported by approved evidence."
        ],
    }

    return (
        "You are an expert Robot Framework resource-file designer working on a maintainable enterprise UI automation framework.\n"
        "Generate exactly one valid page-specific Robot Framework .resource file.\n\n"
        "Primary objective:\n"
        "- Build a reusable page resource file that contains only page-specific locators, page-specific action keywords, page-specific validation keywords, and page-specific test-data variables inferred from approved workflow and approved manual tests.\n"
        "- You are also given common/shared resource context. Reuse that knowledge and avoid duplicating common keywords, browser lifecycle keywords, generic navigation keywords, and generic variables already suitable for shared resources.\n"
        "- If an existing page resource is provided, treat this as a review-and-repair task as well: preserve good page-specific content, remove duplicated common concerns, tighten formatting, and improve Robot syntax and maintainability.\n\n"
        "Mandatory output rules:\n"
        "- Return only Robot Framework resource code.\n"
        "- Do not include markdown fences.\n"
        "- Include only these sections if needed: *** Settings ***, *** Variables ***, *** Keywords ***.\n"
        "- Use SeleniumLibrary in Settings only if truly needed in this page resource.\n"
        "- Use only the approved elements to create locator variables. Remove or avoid any locator variable or locator-backed step that is not grounded in the current approved elements.\n"
        "- If metadata variable context is present, treat it as the primary canonical source for locator-variable names and page-url variable naming. Preserve those names in the generated resource whenever feasible.\n"
        "- Preserve human-reviewed semantic naming. Variable names and page keyword names should stay business-readable and aligned with approved element names, not raw DOM ids.\n"
        "- Remove technical locator/id noise from naming when it is not semantically meaningful, including prefixes or fragments such as auto, btn, ctl, component, generated hashes, or framework-internal tokens. Keep only domain-meaningful words in final variable and keyword names.\n"
        "- If an underlying locator uses a technical id such as auto_person_btn, the locator value may keep that id, but the resource variable name should reflect the reviewed semantic name such as PERSON_NAVIGATION_BUTTON.\n"
        "- Use the approved keywords as the canonical source for implementation ownership and target grounding. For single-element element-backed keywords, structurally normalize the final keyword name from approved targetElement and action rather than preserving stale extraction-era wording.\n"
        "- Approved keyword names must remain business-readable and aligned to the approved target element names. Remove technical DOM/id noise such as Auto, Btn, Ctl, Component, generated numeric fragments, or raw id wording from final page keyword names. For example, prefer Click Person Navigation Button over Click Auto Person Btn Button.\n"
        "- Use the approved keywords as the foundation for reusable keyword implementations.\n"
        "- Treat the approved reviewed keyword implementations as the primary implementation lineage whenever they are valid and supported. Do not replace them with raw framework-level alternatives unless the approved implementation is invalid, unsupported, or clearly inferior based on the shared/common resource context.\n"
        "- Infer reusable interaction preferences dynamically from the provided common_resource_context. If the shared/common resource exposes a higher-level reusable helper for an interaction pattern, prefer that helper over assembling the same behavior with lower-level SeleniumLibrary steps.\n"
        "- Do not rely on hardcoded mappings or workflow-specific assumptions; reason from the approved artifacts and the discovered shared/common keyword surface.\n"
        "- Enforce workflow knowledge → authoritative upstream resources → approved entry journey → approved destination-state validation as a mandatory reasoning chain when the page/resource behavior depends on upstream workflow context or post-action destination state.\n"
        "- If current_workflow_knowledge or relevant_workflow_knowledge identifies authoritative upstream resources for entry flow, return-path validation, or destination-state validation, preserve that ownership boundary and reuse intent instead of duplicating those concerns locally.\n"
        "- If workflow knowledge defines that the page is reached through an upstream journey, do not design the page resource as if target-page availability is unexplained or directly reachable by unsupported shortcuts.\n"
        "- If workflow knowledge defines a success destination or return destination, prefer page-resource validations that support downstream destination-state verification and ownership boundaries rather than only local disappearance checks.\n"
        "- Treat empty placeholder rows in workflow.fields as noise and ignore them.\n"
        "- Create reusable test-data variables based on approved manual tests, not just workflow.testData.\n"
        "- Valid business data should come from workflow.testData if present.\n"
        "- Use AI judgment to keep the Variables section minimal, semantic, and maintainable rather than exhaustively materializing every test-data variation.\n"
        "- Create explicit page-resource variables only for true reusable business data or semantically distinct data sets, such as ${VALID_USERNAME}, ${VALID_PASSWORD}, ${INVALID_USERNAME}, ${INVALID_PASSWORD}, locked-user credentials, role-specific credentials, or other clearly distinct business cases justified by approved manual tests.\n"
        "- Use AI judgment to avoid semantically duplicate credential variables, redundant literal aliases, and weak generic container abstractions. Prefer the minimal set of reusable variables that keeps downstream suites grounded and maintainable.\n"
        "- When locator-backed validations and page verification keywords already express a message, label, or page state clearly, avoid creating extra literal-alias variables unless they materially improve reuse across multiple unrelated assertions.\n"
        "- Prefer page-specific evidence over generic shell/container abstractions when designing reusable variables and validations.\n"
        "- Do NOT create unnecessary wrapper or alias variables for Robot built-ins or simple compositions. For blank input use ${EMPTY} directly in test/keyword usage, and for whitespace use ${SPACE} directly or inline composition such as ${SPACE}${SPACE}${VALID_USERNAME}${SPACE}.\n"
        "- Do NOT define explicit variables such as ${BLANK_USERNAME}, ${BLANK_PASSWORD}, ${SPACE_USERNAME}, ${SPACE_PASSWORD}, ${USERNAME_WITH_SPACES}, ${PASSWORD_WITH_SPACES}, or similar derived aliases when the same intent can be expressed directly with built-ins and existing semantic variables.\n"
        "- Avoid duplicate semantic variables. If one ${INVALID_USERNAME} and one ${INVALID_PASSWORD} are sufficient for negative authentication scenarios, reuse them across those scenarios instead of inventing variants such as _ALT, _SECONDARY, _NEGATIVE, or other duplicates unless the approved manual tests clearly require truly different invalid data classes.\n"
        "- Prefer inline composition over new variables for derived forms of existing data. Examples: use ${SPACE}${VALID_USERNAME}${SPACE} instead of creating ${USERNAME_WITH_SPACES}; use repeated semantic variables or built-ins inline rather than storing one-off composed aliases.\n"
        "- Avoid hardcoding dedicated LONG variables when the long input is only a derived repetition of an existing semantic value. If a long-value scenario can be represented by composing or repeating an existing semantic variable at usage time, prefer that over adding a separate page variable, unless a fixed boundary test value must be reused across multiple tests.\n"
        "- Do NOT define Robot Framework built-in variables like ${EMPTY}, ${SPACE}, ${True}, ${False}, or ${None}; reference them directly only where needed.\n"
        "- Keep naming clean and maintainable.\n"
        "- Prefer reusable validation keywords when expected results mention UI messages, masking, redirection, visibility, enabled/disabled state, or validation behavior.\n"
        "- Do not invent unnecessary variables or keywords.\n"
        "- Preserve a clean resource file structure with compact formatting: no blank lines between consecutive variable definitions, at most one blank line between major sections, and at most one blank line between keyword blocks.\n"
        "- Use modern Robot Framework syntax only. Do NOT use deprecated loop syntax such as ': FOR' or backslash-prefixed loop bodies. Use 'FOR ... END' syntax if a loop is truly necessary.\n"
        "- Use AI intelligence instead of hardcoded assumptions.\n\n"
        "Shared-vs-page resource rules:\n"
        "- Generic or common variables belong in resources/common_keywords.resource, not in the page resource. Examples include browser selection such as ${BROWSER}, generic timeout variables, generic environment/base-url variables, shared credential defaults used across suites, and other cross-page defaults.\n"
        "- Generic or common keywords belong in resources/common_keywords.resource, not in the page resource. Examples include Open Browser To Url, Go To Url, Open Login Page, Open Browser Session, Close Browser Session, Wait For Element To Be Ready, Click When Ready, Input Text When Ready, generic click/input wrappers, and other cross-page/browser lifecycle helpers.\n"
        "- If a common/shared keyword already exists or is strongly implied by common_resource_context, do not recreate it in the page resource. Instead, design the page resource to rely on the shared/common resource layer.\n"
        "- The page resource should contain only page-specific behavior such as entering credentials into this page, clicking page-specific buttons, and validating page-specific messages or field behavior.\n"
        "- The page resource must import ../../resources/common_keywords.resource in its *** Settings *** section whenever it uses shared/common helpers.\n"
        "- Page-specific action keywords should prefer the highest-value shared/common helpers discovered in common_resource_context whenever those helpers fit the action. Avoid reconstructing the same interaction behavior with lower-level SeleniumLibrary calls when a reusable shared/common abstraction already exists.\n"
        "- The page resource must import ../../resources/common_keywords.resource in *** Settings ***. Treat this import as mandatory for generated page resources in this framework.\n"
        "- If a page keyword uses a common helper or depends on a common variable, the page resource must reuse that helper or variable through the common resource import instead of inlining raw SeleniumLibrary behavior.\n"
        "- Insert exactly one blank line between major sections such as *** Settings ***, *** Variables ***, and *** Keywords ***. Do not leave extra blank lines inside the Settings section. There must be no blank line immediately before *** Keywords *** when it directly follows *** Variables ***; only a single section-separator blank line is allowed.\n"
        "- Do not leave blank lines between consecutive variable definitions.\n"
        "- Prefer atomic page-object keywords over workflow/business-flow orchestration. Good examples are Enter Username, Enter Password, Click Sign In Button, Verify Login Error Message, Verify Password Field Is Masked, Verify Login Page Loaded.\n"
        "- Avoid business-flow keywords that merely orchestrate a whole login scenario when they are not truly page-specific. Avoid keywords such as Login With Valid Credentials, Login With Credentials, Submit Login, Perform Successful Login, or other scenario wrappers unless there is a compelling page-specific reason.\n"
        "- Do not duplicate keywords that already exist in common/shared resources.\n\n"
        "Resource quality requirements:\n"
        "- The Variables section should centralize reusable page-level test data so generated .robot test suites do not hardcode those values.\n"
        "- Create reusable page-resource variables only for semantically distinct edge-case or business data that must remain stable and reusable across multiple tests. For blank values, whitespace-only values, padded values, and other simple derived forms, prefer Robot built-ins and inline composition instead of creating dedicated page variables unless a fixed reusable boundary value is genuinely required.\n"
        "- Keep the Variables section semantically clean: variable names must accurately match the actual values. For example, a variable named WITH_SPACES must really contain spaces; otherwise do not create it.\n"
        "- Remove unnecessary, duplicate, or weak variables if they are not clearly supported by approved manual tests.\n"
        "- Do not leave reusable edge-case or credential-like values inline in test suites; define them as page-resource variables so they are easier to maintain later.\n"
        "- The Keywords section should contain reusable business-friendly page actions and validations rather than low-level one-off steps only.\n"
        "- If approved manual tests mention password masking, create a reusable page-specific keyword to verify password masking behavior if feasible in the framework.\n"
        "- If approved manual tests mention validation messages, incorrect credentials, blocked login, rejection behavior, required-field behavior, whitespace handling, case sensitivity, duplicate submission behavior, copy-paste behavior, or successful navigation, create reusable page-specific validation/assertion keywords where feasible instead of relying only on page-loaded checks.\n"
        "- Prefer creating page validation keywords such as Verify Authentication Error Message, Verify Username Required Validation, Verify Password Required Validation, Verify Login Rejected, Verify Successful Login Redirect, Verify Duplicate Submission Prevented, or other grounded page-specific assertions when approved manual tests justify them.\n"
        "- Do not create placeholder absence validations or text-alias variables for indicators that are not grounded in approved elements, approved reviewed keywords, or stable existing page-resource evidence. Avoid speculative keywords such as verifying made-up logout/sign-out indicators unless those indicators are explicitly supported by approved artifacts.\n"
        "- Do not create generic browser open/close keywords here if those belong in common/shared resources.\n"
        "- Keep formatting compact with no excessive blank lines and use modern Robot syntax only.\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )

def sanitize_existing_resource_against_approved_elements(existing_resource: str, approved_elements: list[dict]) -> str:
    resource_text = strip_markdown_fences(existing_resource or "")
    if not resource_text.strip():
        return ""

    approved_locators = {
        clean_text(str(item.get("locator", "")))
        for item in approved_elements
        if isinstance(item, dict) and clean_text(str(item.get("locator", "")))
    }
    if not approved_locators:
        return resource_text

    lines = resource_text.splitlines()
    sanitized_lines: list[str] = []
    in_variables = False

    variable_pattern = re.compile(r"^(\$\{[^}]+\})\s{2,}(.*)$")
    keyword_step_locator_patterns = [
        re.compile(r"^\s*(?:Click Element|Input Text|Wait Until Element Is Visible|Wait Until Page Contains Element|Element Should Be Visible|Element Should Not Be Visible|Page Should Contain Element|Scroll Element Into View)\s{2,}(.+)$", re.IGNORECASE),
        re.compile(r"^\s*(?:Click When Ready|Input Text When Ready|Wait For Element To Be Ready)\s{2,}(.+?)(?:\s{2,}.*)?$", re.IGNORECASE),
    ]

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if stripped.startswith("***"):
            in_variables = lower == "*** variables ***"
            sanitized_lines.append(line)
            continue

        if in_variables:
            match = variable_pattern.match(stripped)
            if match:
                variable_value = clean_text(match.group(2))
                if variable_value and (
                    variable_value.startswith(("xpath=", "css=", "id=", "name=", "//", "(", "#", "."))
                    or "@" in variable_value
                ):
                    if variable_value not in approved_locators:
                        continue
            sanitized_lines.append(line)
            continue

        should_drop_line = False
        for pattern in keyword_step_locator_patterns:
            match = pattern.match(line)
            if match:
                locator_candidate = clean_text(match.group(1))
                if locator_candidate and locator_candidate not in approved_locators:
                    should_drop_line = True
                    break
        if not should_drop_line:
            sanitized_lines.append(line)

    sanitized_text = "\n".join(sanitized_lines).strip()
    return sanitized_text + ("\n" if sanitized_text else "")


def normalize_resource_content(content: str) -> str:
    content = strip_markdown_fences(content)
    lines = content.splitlines()

    cleaned: list[str] = []
    blank_count = 0
    in_variables_section = False
    previous_was_variable = False

    for line in lines:
        normalized_line = line.rstrip()
        stripped = normalized_line.strip()
        lower = stripped.lower()

        if stripped.startswith("***"):
            while cleaned and cleaned[-1] == "":
                cleaned.pop()
            in_variables_section = lower == "*** variables ***"
            previous_was_variable = False
            blank_count = 0
            if cleaned:
                cleaned.append("")
            cleaned.append(stripped)
            continue

        if stripped == "":
            if in_variables_section:
                continue
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
            continue

        blank_count = 0
        if in_variables_section:
            previous_was_variable = bool(re.match(r"^\$\{[^}]+\}\s{2,}.+", stripped))
        else:
            previous_was_variable = False
        cleaned.append(normalized_line)

    content = "\n".join(cleaned).strip() + "\n"
    content = re.sub(r"(?m)^\s*: FOR\b", "FOR", content)
    content = re.sub(r"(?m)^\s*\\\s+", "    ", content)

    if re.search(r"(?im)^\s*\*\*\*\s*settings\s*\*\*\*", content):
        if re.search(r"(?im)^\s*Resource\s+\.\./\.\./resources/common_keywords\.resource\s*$", content) is None:
            settings_match = re.search(r"(?is)(^\*\*\*\s*settings\s*\*\*\*\s*\n)(.*?)(?=^\*\*\*|\Z)", content, re.MULTILINE)
            if settings_match:
                settings_body = settings_match.group(2)
                new_settings_body = "Resource    ../../resources/common_keywords.resource\n" + settings_body.lstrip("\n")
                content = content[:settings_match.start(2)] + new_settings_body + content[settings_match.end(2):]
    else:
        content = "*** Settings ***\nResource    ../../resources/common_keywords.resource\n\n" + content

    return content


def build_resource_review_prompt(
    workflow: dict,
    approved_elements: list[dict],
    approved_keywords: list[dict],
    approved_manual_tests: list[dict],
    common_resource_context: list[dict],
    generated_resource: str,
) -> str:
    prompt_ready_workflow = clean_workflow_for_prompting(workflow)
    reuse_analysis = analyze_reuse_conflicts(generated_resource, "")
    payload = {
        "workflow": prompt_ready_workflow,
        "approved_elements": approved_elements,
        "approved_keywords": approved_keywords,
        "approved_manual_tests": approved_manual_tests,
        "common_resource_context": common_resource_context,
        "current_workflow_knowledge": build_workflow_knowledge_context(workflow),
        "relevant_workflow_knowledge": discover_relevant_workflow_knowledge(workflow),
        "reuse_analysis": reuse_analysis,
        "generated_page_resource": generated_resource,
    }

    return (
        "You are a senior Robot Framework resource-file reviewer and repair specialist.\n"
        "Your task is to review an already generated page-specific .resource file and return a corrected version of the same file.\n\n"
        "Review objectives:\n"
        "- Keep only page-specific locators, page-specific actions, page-specific validations, and page-specific test-data variables.\n"
        "- Remove or avoid duplicated common/shared variables and keywords that belong in resources/common_keywords.resource.\n"
        "- Improve formatting, Robot syntax quality, and maintainability.\n"
        "- Preserve useful page-specific content grounded in approved elements, approved keywords, and approved manual tests.\n"
        "- Remove any locator variable, locator-backed step, or page-specific keyword step that relies on a locator not present in the current approved elements.\n"
        "- Review naming quality explicitly. Replace technical or DOM-derived naming noise such as auto, btn, ctl, generated numeric fragments, or framework-specific prefixes in variable and keyword names with business-readable names grounded in the approved reviewed element names and approved keyword names.\n"
        "- Keep locator values intact when technically required, but do not let locator ids leak into final variable names if cleaner reviewed names already exist.\n\n"
        "Mandatory repair rules:\n"
        "- Return only Robot Framework resource code with no markdown fences and no explanation.\n"
        "- Keep the file page-specific. Generic browser lifecycle, generic navigation, generic waits, generic click/input wrappers, ${BROWSER}, ${DEFAULT_TIMEOUT}, and other cross-page concerns belong in resources/common_keywords.resource, not here.\n"
        "- Page action keywords should reuse the best available shared/common helpers discoverable in common_resource_context when applicable instead of directly repeating lower-level SeleniumLibrary interaction patterns.\n"
        "- Treat approved reviewed keyword implementations as authoritative implementation lineage whenever they are valid and supported. If the approved implementation already uses a reusable shared/common helper, preserve that choice. If it uses raw framework steps but the shared/common resource clearly exposes a reusable helper for the same interaction pattern, intelligently refine toward the shared/common helper without introducing unsupported behavior.\n"
        "- Infer helper preference from the provided shared/common resource content and approved artifacts rather than from hardcoded interaction maps.\n"
        "- Treat reuse_analysis as authoritative conflict guidance. If it shows duplicate variables, duplicate keywords, or ownership conflicts, repair the resource by reusing existing approved names/ownership rather than keeping parallel definitions.\n"
        "- Before returning the final resource, internally perform a retrieval-first decision sequence: identify reusable approved variables/keywords first, identify only the true gaps second, and keep net-new additions minimal and justified.\n"
        "- If a candidate variable points to a locator already owned elsewhere, do not preserve that duplicate local ownership unless the provided context proves a truly distinct page-specific semantic need.\n"
        "- If a candidate keyword duplicates an approved keyword name or normalized implementation already present in approved resource context, reuse that existing capability rather than preserving a parallel keyword.\n"
        "- Enforce workflow knowledge → authoritative upstream resources → approved entry journey → approved destination-state validation as a mandatory review chain when the page/resource behavior depends on upstream workflow context or post-action destination state.\n"
        "- If workflow knowledge identifies authoritative upstream resources for entry, return, or destination-state validation, keep those ownership boundaries explicit and do not duplicate them as local page-resource behavior.\n"
        "- Reject or repair page-resource behavior that assumes unsupported direct access when workflow knowledge says the page is reached through an upstream journey.\n"
        "- Reject or repair page-resource validations that stop at local disappearance when workflow knowledge and approved artifacts support a stronger destination-state validation chain.\n"
        "- If a common/shared keyword already exists or is implied by common_resource_context, do not recreate it here.\n"
        "- Remove business-flow keywords that are too generic or duplicate shared/common behavior.\n"
        "- Keep reusable page-specific actions and page-specific validations.\n"
        "- Prefer atomic page-object keywords and validations. Remove or simplify scenario-wrapper keywords such as Login With Credentials, Login With Valid Credentials, Submit Login, Perform Login Flow, or other business-flow orchestration if they are not clearly necessary as page-level abstractions.\n"
        "- Keep page-specific test-data variables only when they are clearly useful, reusable, and semantically accurate.\n"
        "- Remove unused, duplicate, overly noisy, or weak one-off variables when they are not justified by approved manual tests. Merge similar variables where appropriate.\n"
        "- Use AI judgment to simplify semantically duplicate variables and keep only the minimal reusable set needed by downstream suites.\n"
        "- Prefer locator-backed validations and page verification keywords over redundant literal aliases when that keeps the resource clearer and more maintainable.\n"
        "- Prefer page-specific evidence over weak generic shell/container abstractions unless the approved artifacts genuinely justify them.\n"
        "- Eliminate unnecessary alias variables for Robot built-ins and simple compositions. Replace variables such as ${BLANK_*} that only equal ${EMPTY}, ${SPACE_*} that only equal whitespace, ${*_WITH_SPACES}, and similar wrapper aliases with direct built-in usage or inline composition whenever possible.\n"
        "- Collapse duplicate negative data into a single semantic variable when the intent is the same. For example, keep one ${INVALID_USERNAME} and one ${INVALID_PASSWORD} unless the approved manual tests clearly require distinct invalid classes. Remove suffix variants such as _ALT or other duplicates when they do not add meaning.\n"
        "- Prefer inline composition over dedicated derived variables. If a value can be expressed by combining ${SPACE}, ${EMPTY}, and existing semantic variables such as ${VALID_USERNAME} or ${VALID_PASSWORD}, do that instead of keeping a separate page variable.\n"
        "- Avoid dedicated long-value aliases when they are just repeated forms of existing semantic variables unless a stable reusable boundary value is genuinely needed across multiple tests.\n"
        "- If a variable name implies spaces, blanks, long text, invalid credentials, or another property, ensure the value really matches that meaning; otherwise repair or remove it.\n"
        "- Ensure the page resource imports ../../resources/common_keywords.resource in *** Settings ***. Treat this import as mandatory for generated page resources in this framework.\n"
        "- Use compact formatting with minimal blank lines and no blank lines between consecutive variable definitions.\n"
        "- Keep exactly one blank line between major sections. Do not leave extra blank lines inside *** Settings ***. There must be no extra blank line immediately before *** Keywords *** beyond the single section separator.\n"
        "- Use modern Robot Framework syntax only. Do not use deprecated ': FOR' syntax or backslash-prefixed loop bodies.\n"
        "- Prefer page-specific validation keywords for incorrect credentials, validation messages, blocked login, and password masking when approved manual tests imply them.\n"
        "- Do not allow the page resource to stop at only generic validations such as Verify Login Failed or Verify Page Loaded if approved manual tests imply richer assertions. Add more specific page validation keywords for authentication error messages, required-field validation, successful login redirect, duplicate submission prevention, or other grounded outcomes whenever feasible.\n"
        "- Do not create generic browser open/close keywords here.\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )


def validate_review_artifact_consistency(workflow: dict, approved_keywords: list[dict]) -> tuple[bool, str]:
    review_data = get_page_review_data(workflow)
    approved_elements = load_approved_elements_for_workflow(workflow)

    if not approved_elements:
        return False, "Approved page elements are required before resource generation."
    if not approved_keywords:
        return False, "Approved keywords are required before resource generation."

    approved_element_names = {
        clean_text(str(item.get("approvedName", "")))
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    }
    missing_targets = []
    for item in approved_keywords:
        if not isinstance(item, dict) or not bool(item.get("approved", True)):
            continue
        target = clean_text(str(item.get("targetElement", "")))
        if target and target not in approved_element_names:
            missing_targets.append(f"{clean_text(str(item.get('keywordName', 'Unnamed Keyword')))} -> {target}")

    if missing_targets:
        return False, "Approved keyword target elements do not match approved reviewed elements: " + "; ".join(missing_targets)

    if review_data.get("source_artifact") == "raw":
        return False, "Resource generation requires reviewed or approved page elements. Run extraction/refinement and approve the refined artifact first."

    return True, ""


def is_resource_level_keyword_name(name: str) -> bool:
    return bool(clean_text(name))



def validate_generated_resource_against_approved_artifacts(
    workflow: dict,
    approved_keywords: list[dict],
    resource_content: str,
    common_resource_context: list[dict] | None = None,
    candidate_file: str = "",
) -> tuple[bool, str]:
    approved_elements = load_approved_elements_for_workflow(workflow)
    approved_variable_names = {
        to_robot_variable_name(clean_text(str(item.get("approvedName", ""))))
        for item in approved_elements
        if clean_text(str(item.get("approvedName", "")))
    }
    approved_keyword_names = {
        clean_text(str(item.get("keywordName", ""))).lower()
        for item in approved_keywords
        if isinstance(item, dict)
        and clean_text(str(item.get("keywordName", "")))
        and bool(item.get("approved", True))
        and is_resource_level_keyword_name(str(item.get("keywordName", "")))
    }
    non_resource_keyword_names = sorted(
        {
            clean_text(str(item.get("keywordName", "")))
            for item in approved_keywords
            if isinstance(item, dict)
            and clean_text(str(item.get("keywordName", "")))
            and bool(item.get("approved", True))
            and not is_resource_level_keyword_name(str(item.get("keywordName", "")))
        }
    )

    parsed_keywords = extract_keywords_from_resource(resource_content)
    parsed_variables = extract_variables_from_resource(resource_content)
    resource_keyword_names = {
        clean_text(str(item.get("name", ""))).lower()
        for item in parsed_keywords
        if clean_text(str(item.get("name", "")))
    }
    resource_variable_names = {
        clean_text(str(item.get("name", ""))).upper()
        for item in parsed_variables
        if clean_text(str(item.get("name", "")))
    }

    common_keyword_names = {
        clean_text(str(keyword.get("name", ""))).lower()
        for resource in (common_resource_context or [])
        for keyword in resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    }

    missing_keywords = sorted(name for name in approved_keyword_names if name not in resource_keyword_names)
    missing_variables = sorted(name for name in approved_variable_names if name and name not in resource_variable_names)
    matched_keywords = sorted(name for name in approved_keyword_names if name in resource_keyword_names)

    errors = []
    warnings = []
    technical_name_pattern = re.compile(r"\b(auto|btn|ctl|component)\b", re.IGNORECASE)
    if approved_keyword_names and not matched_keywords:
        errors.append(
            "Generated page resource did not preserve any approved reusable keywords from the reviewed artifact."
        )
    elif missing_keywords:
        warnings.append(
            "Generated page resource is missing some approved reusable keywords: "
            + ", ".join(missing_keywords)
        )
    if missing_variables:
        warnings.append(
            "Generated page resource is missing approved locator variables: "
            + ", ".join(missing_variables)
        )

    noisy_resource_variables = sorted(
        name for name in resource_variable_names
        if name and technical_name_pattern.search(name)
    )
    if noisy_resource_variables:
        warnings.append(
            "Generated page resource still contains technical locator-driven variable names. Prefer approved semantic names instead: "
            + ", ".join(noisy_resource_variables)
        )
    non_resource_keywords_present_in_resource = sorted(
        name for name in non_resource_keyword_names if name.lower() in resource_keyword_names
    )
    non_resource_keywords_missing_from_resource = sorted(
        name for name in non_resource_keyword_names if name.lower() not in resource_keyword_names
    )
    if non_resource_keywords_missing_from_resource:
        warnings.append(
            "Approved composite/scenario keywords were not enforced as page-resource keywords: "
            + ", ".join(non_resource_keywords_missing_from_resource)
        )

    direct_low_level_calls = [
        "wait until element is visible",
        "wait until element is enabled",
        "click element",
        "input text",
        "input password",
        "go to",
        "open browser",
    ]
    forbidden_builtin_assertion_keywords = [
        "location should not contain",
        "location should be",
        "wait until location contains",
    ]
    common_usage_patterns = [
        "click when ready",
        "input text when ready",
        "wait for element to be ready",
        "open browser session",
        "close browser session",
        "open browser to url",
        "go to url",
    ]
    if common_keyword_names:
        low_level_hits = sum(len(re.findall(rf"(?im)^\s*{re.escape(name)}\b", resource_content)) for name in direct_low_level_calls)
        common_hits = sum(len(re.findall(rf"(?im)^\s*{re.escape(name)}\b", resource_content)) for name in common_usage_patterns if name in common_keyword_names)
        if low_level_hits >= 3 and common_hits == 0:
            errors.append(
                "Generated page resource does not reuse retrieved common/shared keywords even though common resource context is available; prefer common wrappers over raw SeleniumLibrary calls."
            )

        approved_implementation_tokens = set()
        approved_low_level_tokens = set()
        for item in approved_keywords:
            if not isinstance(item, dict) or not bool(item.get("approved", True)):
                continue
            for line in item.get("implementation", []) or []:
                token = clean_text(str(line).split("    ")[0]).lower()
                if not token:
                    continue
                approved_implementation_tokens.add(token)
                if token in direct_low_level_calls:
                    approved_low_level_tokens.add(token)

        resource_low_level_tokens = {
            name for name in direct_low_level_calls
            if re.search(rf"(?im)^\s*{re.escape(name)}\b", resource_content)
        }
        if resource_low_level_tokens and approved_implementation_tokens and not (resource_low_level_tokens & approved_implementation_tokens):
            warnings.append(
                "Generated page resource fell back to raw low-level interaction keywords that are not reflected in the approved reviewed keyword implementations. Prefer preserving approved reviewed implementations and use shared/common helpers when the common resource context indicates a reusable abstraction."
            )

        if approved_low_level_tokens and common_hits > 0 and resource_low_level_tokens:
            warnings.append(
                "Approved reviewed keywords still contain some raw low-level interaction steps while shared/common helpers are also available. Consider improving the reviewed keyword generation/review prompts so approved implementations converge on shared helper usage before final resource generation."
            )

    forbidden_builtin_hits = [
        keyword_name for keyword_name in forbidden_builtin_assertion_keywords
        if re.search(rf"(?im)^\s*{re.escape(keyword_name)}\b", resource_content)
    ]
    if forbidden_builtin_hits:
        warnings.append(
            "Generated page resource uses raw Selenium/Browser assertion keywords instead of approved/common abstractions: "
            + ", ".join(sorted(set(forbidden_builtin_hits)))
        )

    reuse_analysis = analyze_reuse_conflicts(resource_content, candidate_file)
    if reuse_analysis.get("summary", {}).get("duplicateVariableCount", 0) > 0:
        errors.append(
            "Generated page resource introduces locator ownership duplication against approved resources. Reuse existing approved variables/owners instead of creating parallel locator variables."
        )
    if reuse_analysis.get("summary", {}).get("duplicateKeywordCount", 0) > 0:
        errors.append(
            "Generated page resource introduces duplicate keyword capability against approved resources. Reuse existing approved keywords instead of creating parallel keyword definitions."
        )
    if reuse_analysis.get("summary", {}).get("ownershipConflictCount", 0) > 0:
        warnings.append(
            "Ownership conflicts detected in reuse analysis; keep ownership conservative and prefer upstream/shared/page-authoritative reuse over duplicate local ownership."
        )

    is_valid = len(errors) == 0
    message_parts = []
    if errors:
        message_parts.append("\n".join(errors))
    if warnings:
        message_parts.append("Warnings:\n" + "\n".join(warnings))
    return is_valid, "\n\n".join(part for part in message_parts if part)


def generate_resource_for_workflow(workflow: dict, approved_keywords: list[dict]):
    review_data = get_page_review_data(workflow)
    page_name = review_data["page_name"]
    approved_elements = load_approved_elements_for_workflow(workflow)
    is_consistent, consistency_message = validate_review_artifact_consistency(workflow, approved_keywords)
    if not is_consistent:
        raise HTTPException(status_code=400, detail=consistency_message)
    variables_payload = sync_page_variables_from_approved_elements(workflow, approved_elements)

    def build_deterministic_resource() -> str:
        try:
            from scripts.extract_page_model import generate_resource as generate_page_resource
        except ModuleNotFoundError:
            import sys
            sys.path.append(str(BASE_DIR))
            from scripts.extract_page_model import generate_resource as generate_page_resource

        metadata_dir = get_page_metadata_dir(page_name)
        entry_url = ""
        pages = workflow.get("pages", []) if isinstance(workflow, dict) else []
        if pages and isinstance(pages[0], dict):
            entry_url = clean_text(str(pages[0].get("url", "")))
        return normalize_resource_content(
            generate_page_resource(
                entry_url,
                approved_elements,
                page_name=page_name,
                metadata_dir=metadata_dir,
            )
        )

    approved_manual_tests = []
    workflow_name = derive_canonical_workflow_name(workflow, page_name)
    manual_path = get_manual_json_path(workflow_name)
    if manual_path.exists():
        try:
            approved_manual_tests = extract_manual_test_cases(read_json(manual_path))
        except Exception:
            approved_manual_tests = []

    common_resource_context = []
    resources_dir = BASE_DIR / "resources"
    if resources_dir.exists():
        for common_resource_path in sorted(resources_dir.glob("*.resource")):
            try:
                common_resource_context.append(parse_resource_file(common_resource_path))
            except Exception:
                continue

    config = validate_robot_config(load_robot_ai_json(CONFIG_PATH))
    ai_cfg = config["ai"]

    if not ai_cfg.get("enabled", True):
        raise HTTPException(status_code=400, detail="AI is disabled in configuration.")

    endpoint = ai_cfg.get("endpoint", "").strip()
    token = get_robot_ai_token(ai_cfg)
    if not endpoint or not token:
        raise HTTPException(status_code=400, detail="AI endpoint/token missing for resource generation.")

    resource_path = get_resource_path(page_name)
    existing_page_resource = sanitize_existing_resource_against_approved_elements(
        read_text(resource_path),
        approved_elements,
    )

    metadata_variable_context = variables_payload.get("variables", []) if isinstance(variables_payload, dict) else []
    prompt = build_resource_generation_prompt(
        workflow,
        approved_elements,
        approved_keywords,
        approved_manual_tests,
        common_resource_context,
        existing_page_resource + ("\n\n# METADATA_VARIABLE_CONTEXT\n" + json.dumps(metadata_variable_context, indent=2) if metadata_variable_context else ""),
    )
    try:
        resource_content = call_ai_with_workflow_session(
            workflow_name=page_name,
            stage="resource_generation",
            endpoint=endpoint,
            token=token,
            prompt=prompt,
            timeout_seconds=ai_cfg.get("timeout_seconds", 120),
            verify_ssl=ai_cfg.get("verify_ssl", False),
        )
        resource_content = normalize_resource_content(resource_content)

        review_prompt = build_resource_review_prompt(
            workflow,
            approved_elements,
            approved_keywords,
            approved_manual_tests,
            common_resource_context,
            resource_content,
        )
        reviewed_resource_content = call_ai_with_workflow_session(
            workflow_name=page_name,
            stage="resource_review",
            endpoint=endpoint,
            token=token,
            prompt=review_prompt,
            timeout_seconds=ai_cfg.get("timeout_seconds", 120),
            verify_ssl=ai_cfg.get("verify_ssl", False),
        )
        reviewed_resource_content = normalize_resource_content(reviewed_resource_content)
        if reviewed_resource_content:
            resource_content = reviewed_resource_content
    except requests.HTTPError as exc:
        logger.warning("AI resource generation/review failed for %s; falling back to deterministic approved-artifact generation. Error: %s", page_name, exc)
        append_session_message(page_name, "assistant", "resource_generation_warning", f"AI resource generation failed; using deterministic approved-artifact generation instead. Details: {exc}")
        resource_content = build_deterministic_resource()

    is_valid, validation_message = validate_resource_content(resource_content, common_resource_context)
    artifact_valid, artifact_message = validate_generated_resource_against_approved_artifacts(
        workflow,
        approved_keywords,
        resource_content,
        common_resource_context,
        str(resource_path.relative_to(BASE_DIR)).replace("\\", "/"),
    )
    if validation_message:
        append_session_message(page_name, "assistant", "resource_validation", validation_message)
    if artifact_message:
        append_session_message(page_name, "assistant", "resource_artifact_validation", artifact_message)

    blocking_generation_failure = (not is_valid) or (not artifact_valid and artifact_message and "Warnings:" not in artifact_message)
    if blocking_generation_failure:
        refinement_prompt = (
            build_resource_review_prompt(
                workflow,
                approved_elements,
                approved_keywords,
                approved_manual_tests,
                common_resource_context,
                resource_content,
            )
            + "\n\nAdditional validation findings that should be repaired before finalizing when possible:\n"
            + (artifact_message or validation_message or "")
            + "\n\nReturn only corrected Robot Framework resource content. Reuse approved existing variables/keywords/resources where conflicts were identified. If some findings remain warning-level only, still return the best corrected non-empty resource content instead of failing."
        )
        try:
            refined_resource_content = call_ai_with_workflow_session(
                workflow_name=page_name,
                stage="resource_conflict_refinement",
                endpoint=endpoint,
                token=token,
                prompt=refinement_prompt,
                timeout_seconds=ai_cfg.get("timeout_seconds", 120),
                verify_ssl=ai_cfg.get("verify_ssl", False),
            )
            refined_resource_content = normalize_resource_content(refined_resource_content)
        except requests.HTTPError as exc:
            logger.warning("AI resource refinement failed for %s; falling back to deterministic approved-artifact generation. Error: %s", page_name, exc)
            append_session_message(page_name, "assistant", "resource_conflict_refinement_warning", f"AI resource refinement failed; using deterministic approved-artifact generation instead. Details: {exc}")
            refined_resource_content = build_deterministic_resource()
        refined_valid, refined_validation_message = validate_resource_content(refined_resource_content, common_resource_context)
        refined_artifact_valid, refined_artifact_message = validate_generated_resource_against_approved_artifacts(
            workflow,
            approved_keywords,
            refined_resource_content,
            common_resource_context,
            str(resource_path.relative_to(BASE_DIR)).replace("\\", "/"),
        )
        if refined_validation_message:
            append_session_message(page_name, "assistant", "resource_conflict_refinement_validation", refined_validation_message)
        if refined_artifact_message:
            append_session_message(page_name, "assistant", "resource_conflict_refinement_artifact_validation", refined_artifact_message)
        if refined_resource_content.strip():
            resource_content = refined_resource_content
            is_valid = refined_valid
            artifact_valid = refined_artifact_valid
            validation_message = refined_validation_message
            artifact_message = refined_artifact_message
        elif not refined_valid and not refined_artifact_valid:
            raise HTTPException(status_code=400, detail=refined_artifact_message or refined_validation_message or artifact_message or validation_message)

    if validation_message:
        append_session_message(page_name, "assistant", "resource_final_validation", validation_message)
    if artifact_message:
        append_session_message(page_name, "assistant", "resource_final_artifact_validation", artifact_message)

    resource_content = normalize_resource_keyword_headers(resource_content, approved_keywords)
    resource_path.write_text(resource_content, encoding="utf-8")
    enrich_resource_with_manual_test_variables(workflow, approved_keywords)

# -------------------------------------------------------------------
# Manual tests handling
# -------------------------------------------------------------------

def generate_manual_tests_for_workflow(workflow_name: str) -> dict:
    begin_workflow_run(workflow_name)
    workflow_input = load_workflow_or_404(workflow_name)
    approved_elements = load_approved_elements_for_workflow(workflow_input)
    if not approved_elements:
        raise HTTPException(status_code=400, detail="Approved page elements are required before generating manual tests.")

    workflow_with_elements = json.loads(json.dumps(workflow_input))
    workflow_with_elements["approvedElements"] = approved_elements
    if FEATURE_FLAGS.enable_rag:
        workflow_slug = derive_workflow_artifact_slug(workflow_input, workflow_name)
        workflow_with_elements["ragContext"] = rag_context_service.build_context(workflow_slug)

    config = validate_manual_config(load_manual_config())
    ai_cfg = config["ai"]

    if not ai_cfg.get("enabled", False):
        raise HTTPException(status_code=400, detail="AI is disabled in configuration.")

    endpoint = ai_cfg.get("endpoint", "").strip()
    token = get_manual_ai_token(ai_cfg)
    if not endpoint or not token:
        raise HTTPException(status_code=400, detail="Manual test AI endpoint/token missing in configuration.")

    timeout_seconds = int(ai_cfg.get("timeout_seconds", 120) or 120)
    prompt = build_manual_prompt(workflow_with_elements)
    generated = call_manual_ai_with_workflow_session(
        workflow_name=workflow_name,
        stage="manual_generation",
        endpoint=endpoint,
        token=token,
        prompt=prompt,
        timeout_seconds=timeout_seconds,
    )
    if not generated:
        raise HTTPException(status_code=502, detail="Manual test AI returned no content for generation stage.")

    final_json = normalize_manual_test(generated, workflow_input)
    is_valid, validation_message = validate_manual_content(final_json)

    if not is_valid:
        reviewed_manual = call_manual_ai_with_workflow_session(
            workflow_name=workflow_name,
            stage="manual_review",
            endpoint=endpoint,
            token=token,
            prompt=build_manual_review_prompt(generated, workflow_with_elements),
            timeout_seconds=timeout_seconds,
        )
        refined_manual = call_manual_ai_with_workflow_session(
            workflow_name=workflow_name,
            stage="manual_refinement",
            endpoint=endpoint,
            token=token,
            prompt=(
                build_manual_refiner_prompt(generated, reviewed_manual or generated, workflow_with_elements)
                + (f"\n\nValidation findings that must be resolved before approval:\n{validation_message}" if validation_message else "")
            ),
            timeout_seconds=timeout_seconds,
        )
        final_json = normalize_manual_test(refined_manual or reviewed_manual or generated, workflow_input)
        is_valid, validation_message = validate_manual_content(final_json)

        if is_valid and validation_message and (
            "fewer than 6 test cases" in validation_message.lower()
            or "missing scenario category" in validation_message.lower()
        ):
            expansion_prompt = (
                build_manual_prompt(workflow_with_elements)
                + "\n\nExpansion instruction:\n"
                + "The previous manual-test result was too thin or missed scenario categories. Expand the suite while staying grounded in approved elements and workflow context.\n"
                + "Preserve existing good cases and add missing positive, negative, UI, validation, navigation, blank-input, and edge/boundary scenarios where applicable.\n"
                + "Do not return a minimal representative subset. Return a broader but still non-redundant suite."
            )
            expanded = call_manual_ai_with_workflow_session(
                workflow_name=workflow_name,
                stage="manual_expansion",
                endpoint=endpoint,
                token=token,
                prompt=expansion_prompt,
                timeout_seconds=timeout_seconds,
            )
            expanded_reviewed = call_manual_ai_with_workflow_session(
                workflow_name=workflow_name,
                stage="manual_expansion_review",
                endpoint=endpoint,
                token=token,
                prompt=build_manual_review_prompt(expanded, workflow_with_elements),
                timeout_seconds=timeout_seconds,
            )
            expanded_refined = call_manual_ai_with_workflow_session(
                workflow_name=workflow_name,
                stage="manual_expansion_refinement",
                endpoint=endpoint,
                token=token,
                prompt=build_manual_refiner_prompt(expanded, expanded_reviewed or expanded, workflow_with_elements),
                timeout_seconds=timeout_seconds,
            )
            expanded_json = normalize_manual_test(expanded_refined or expanded_reviewed or expanded, workflow_input)
            expanded_valid, expanded_message = validate_manual_content(expanded_json)
            if expanded_valid and len(extract_manual_test_cases(expanded_json)) >= len(extract_manual_test_cases(final_json)):
                final_json = expanded_json
                validation_message = expanded_message
                is_valid = expanded_valid

    if not is_valid:
        raise HTTPException(status_code=400, detail=validation_message)
    write_json(get_manual_json_path(workflow_name), final_json)
    return final_json

def infer_manual_intent(title: str, steps: list[str], expected_result: str) -> dict:
    del title, steps, expected_result
    return {}


def extract_manual_test_cases(manual: dict) -> list[dict]:
    if not manual:
        return []

    candidates = []
    for key in ("manualTests", "testCases", "tests", "cases"):
        value = manual.get(key)
        if isinstance(value, list):
            candidates = value
            break

    normalized = []
    for idx, case in enumerate(candidates, start=1):
        if not isinstance(case, dict):
            continue

        preconditions = case.get("preconditions", [])
        if isinstance(preconditions, str):
            preconditions = [preconditions]

        steps = case.get("steps", [])
        if isinstance(steps, list):
            step_lines = []
            for step in steps:
                if isinstance(step, dict):
                    text = step.get("step") or step.get("action") or step.get("description") or ""
                    if text:
                        step_lines.append(str(text))
                else:
                    step_lines.append(str(step))
            steps = step_lines
        elif isinstance(steps, str):
            steps = [steps]
        else:
            steps = []

        expected_result = (
            case.get("expectedResult")
            or case.get("expected")
            or case.get("expectedOutcome")
            or ""
        )
        title = case.get("title") or case.get("name") or f"Test Case {idx}"

        normalized.append({
            "id": case.get("id") or case.get("testCaseId") or f"TC_{idx:03d}",
            "title": title,
            "type": case.get("type") or case.get("scenarioType") or "General",
            "priority": case.get("priority") or "Medium",
            "preconditions": preconditions,
            "steps": steps,
            "expectedResult": expected_result,
            "interactionIntent": infer_manual_intent(title, steps, expected_result),
            "approved": True,
        })
    return normalized

def update_manual_with_ui_cases(original: dict, cases: list[dict]) -> dict:
    target_key = None
    for key in ("manualTests", "testCases", "tests", "cases"):
        if isinstance(original.get(key), list):
            target_key = key
            break

    if target_key is None:
        target_key = "manualTests"

    original[target_key] = [
        {
            "id": case["id"],
            "title": case["title"],
            "type": case["type"],
            "priority": case["priority"],
            "preconditions": case["preconditions"],
            "steps": case["steps"],
            "expectedResult": case["expectedResult"],
        }
        for case in cases
    ]
    return original

# -------------------------------------------------------------------
# Automation handling
# -------------------------------------------------------------------

def strip_markdown_fences(content: str) -> str:
    content = content.strip()

    fenced_pattern = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n(.*?)\n```$", re.DOTALL)
    match = fenced_pattern.match(content)
    if match:
        return match.group(1).strip()

    content = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"\n```$", "", content, flags=re.MULTILINE)
    return content.strip()

def normalize_robot_content_spacing(content: str) -> str:
    lines = content.splitlines()

    cleaned: list[str] = []
    blank_count = 0
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line.rstrip())

    result: list[str] = []
    in_settings = False
    in_test_cases = False
    first_test_case_seen = False

    for line in cleaned:
        stripped = line.strip()
        lower = stripped.lower()

        if stripped.startswith("***"):
            while result and result[-1] == "":
                result.pop()
            if result:
                result.append("")
            result.append(stripped)
            in_settings = lower == "*** settings ***"
            in_test_cases = lower == "*** test cases ***"
            first_test_case_seen = False if in_test_cases else first_test_case_seen
            continue

        if in_settings and stripped == "":
            continue

        if in_test_cases:
            is_test_name = bool(stripped) and not line.startswith((" ", "\t"))
            if is_test_name:
                while result and result[-1] == "":
                    result.pop()
                if first_test_case_seen:
                    result.append("")
                result.append(stripped)
                first_test_case_seen = True
                continue

        if stripped == "":
            if result and result[-1] == "":
                continue
            result.append("")
            continue

        result.append(line.rstrip())

    normalized = "\n".join(result).strip() + "\n"
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r"(?im)(\*\*\* test cases \*\*\*\n)(\n+)", r"\1\n", normalized)
    normalized = re.sub(r"(?m)^\*\*\* Variables \*\*\*\n(\$\{.*?\}\s{2,}.*\n)(\*\*\* Keywords \*\*\*)", r"*** Variables ***\n\1\n\2", normalized)
    return normalized

def normalize_robot_blank_and_space_arguments(content: str) -> str:
    lines = content.splitlines()
    normalized = []

    keyword_patterns = [
        r"^\s*Enter\s+.*",
        r"^\s*Input\s+.*",
        r"^\s*Type\s+.*"
    ]

    blank_case_patterns = [
        r"(\s{2,})''(\s*)$",
        r'(\s{2,})""(\s*)$',
        r"(\s{2,})blank(\s*)$",
        r"(\s{2,})none(\s*)$"
    ]

    space_case_patterns = [
        r"(\s{2,})space(\s*)$",
        r"(\s{2,})whitespace(\s*)$",
        r"(\s{2,})whitespace_only(\s*)$",
        r"(\s{2,})' '(\s*)$",
        r'(\s{2,})" "(\s*)$'
    ]

    for line in lines:
        line = line.replace("${Empty}", "${EMPTY}").replace("${Space}", "${SPACE}")

        if any(re.match(pattern, line) for pattern in keyword_patterns):
            if re.search(r"\s{2,}$", line):
                line = re.sub(r"\s{2,}$", "    ${EMPTY}", line)
            for pattern in blank_case_patterns:
                line = re.sub(pattern, r"\1${EMPTY}\2", line, flags=re.IGNORECASE)
            for pattern in space_case_patterns:
                line = re.sub(pattern, r"\1${SPACE}\2", line, flags=re.IGNORECASE)

        normalized.append(line)

    return "\n".join(normalized)

def apply_robot_test_naming_and_tags(content: str, workflow: dict | None, workflow_name: str) -> str:
    app_code = derive_app_code(workflow, workflow_name)
    feature_code = derive_feature_code(workflow, workflow_name)

    lines = content.splitlines()
    result: list[str] = []
    in_test_cases = False
    current_index = 0

    def build_codes(existing_name: str, sequence: int) -> tuple[str, str]:
        match = re.search(r"([A-Z]+)_TC_(\d+)", existing_name.upper())
        if match:
            number = int(match.group(2))
        else:
            match = re.search(r"(\d+)", existing_name)
            number = int(match.group(1)) if match else sequence
        nn = f"{number:02d}"
        testcase_id = f"{app_code}-{feature_code}{nn}"
        return testcase_id, testcase_id

    def detect_scenario_type(title: str, existing_tags: list[str]) -> str:
        del title, existing_tags
        return "generic"

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        lower = stripped.lower()

        if stripped.startswith("***"):
            in_test_cases = lower == "*** test cases ***"
            result.append(stripped)
            i += 1
            continue

        if in_test_cases and stripped and not line.startswith((" ", "\t")):
            current_index += 1
            testcase_id, primary_tag = build_codes(stripped, current_index)
            title = stripped
            title = re.sub(r"^[A-Z]+_TC_\d+\s*", "", title)
            title = re.sub(r"^AUT-[A-Z0-9]+-[A-Z0-9]+\s*:\s*", "", title)
            title = re.sub(r"^AUT-[A-Z0-9]+\s*:\s*", "", title)
            title = re.sub(r"^[A-Z0-9]+-[A-Z0-9]+\s*:\s*", "", title)
            title = clean_text(title)

            existing_tags: list[str] = []
            if i + 1 < len(lines) and lines[i + 1].strip().startswith("[Tags]"):
                existing_tags_line = lines[i + 1].strip()
                tag_tokens = re.split(r"\s{2,}|\t+", existing_tags_line)
                existing_tags = [t for t in tag_tokens[1:] if t.strip()]

            scenario_type = detect_scenario_type(title, existing_tags)
            result.append(f"AUT-{testcase_id}: {title}")
            result.append(f"    [Tags]    {primary_tag}    {scenario_type}")

            if existing_tags:
                i += 2
                continue

            i += 1
            continue

        result.append(line.rstrip())
        i += 1

    return "\n".join(result)


def compact_robot_tests_after_setup(content: str) -> str:
    lines = content.splitlines()

    settings_section: list[str] = []
    test_section: list[str] = []
    other_section: list[str] = []
    section = None
    for line in lines:
        lowered = line.strip().lower()
        if lowered == "*** settings ***":
            section = "settings"
            settings_section.append(line)
            continue
        if lowered == "*** test cases ***":
            section = "tests"
            test_section.append(line)
            continue
        if lowered.startswith("***"):
            section = "other"
            other_section.append(line)
            continue
        if section == "settings":
            settings_section.append(line)
        elif section == "tests":
            test_section.append(line)
        else:
            other_section.append(line)

    if not test_section:
        return content

    setup_lines: list[str] = []
    for line in settings_section:
        match = re.match(r"(?im)^\s*Test Setup\s{2,}(.+)$", line)
        if not match:
            continue
        rhs = match.group(1).strip()
        if rhs.lower().startswith("run keywords"):
            parts = [part.strip() for part in re.split(r"\s{2,}|\t+", rhs) if part.strip()]
            current: list[str] = []
            for token in parts[1:]:
                lowered = clean_text(token).lower()
                if lowered == "and":
                    if current:
                        setup_lines.append("    " + "    ".join(current))
                        current = []
                    continue
                current.append(token)
            if current:
                setup_lines.append("    " + "    ".join(current))
        else:
            setup_lines.append("    " + rhs)
        break

    normalized_setup_steps = {clean_text(line).lower() for line in setup_lines if clean_text(line)}
    if not normalized_setup_steps:
        return content

    def parse_tests(test_lines: list[str]) -> tuple[list[str], list[dict]]:
        header: list[str] = []
        tests: list[dict] = []
        current = None
        seen_first_test = False
        for line in test_lines:
            stripped = line.strip()
            if not seen_first_test:
                header.append(line)
                if stripped.lower() == "*** test cases ***":
                    continue
                if stripped and not line.startswith((" ", "\t")) and not stripped.startswith("***"):
                    seen_first_test = True
                    current = {"name": line, "body": []}
                    tests.append(current)
                    header.pop()
                continue
            if stripped and not line.startswith((" ", "\t")) and not stripped.startswith("***"):
                current = {"name": line, "body": []}
                tests.append(current)
                continue
            if current is not None:
                current["body"].append(line)
        return header, tests

    header_lines, tests = parse_tests(test_section)
    if not tests:
        return content

    changed = False
    for test in tests:
        new_body: list[str] = []
        seen_non_metadata_step = False
        for line in test["body"]:
            stripped = line.strip()
            normalized = clean_text(stripped).lower()
            if not stripped:
                if new_body and new_body[-1].strip():
                    new_body.append(line)
                continue
            if stripped.startswith("["):
                new_body.append(line)
                continue
            if not line.startswith((" ", "\t")):
                new_body.append(line)
                continue

            if normalized in normalized_setup_steps:
                changed = True
                continue

            new_body.append(line)
            seen_non_metadata_step = True

        while new_body and not new_body[-1].strip():
            new_body.pop()
        test["body"] = new_body

    if not changed:
        return content

    rebuilt: list[str] = []
    if settings_section:
        rebuilt.extend(settings_section)
        if rebuilt and rebuilt[-1].strip():
            rebuilt.append("")
    rebuilt.extend(header_lines)
    for index, test in enumerate(tests):
        if index > 0 and rebuilt and rebuilt[-1].strip():
            rebuilt.append("")
        rebuilt.append(test["name"])
        rebuilt.extend(test["body"])
    if other_section:
        if rebuilt and rebuilt[-1].strip():
            rebuilt.append("")
        rebuilt.extend(other_section)
    return "\n".join(rebuilt) + ("\n" if content.endswith("\n") else "")


def normalize_robot_content(content: str, workflow: dict | None = None, workflow_name: str = "") -> str:
    content = strip_markdown_fences(content)
    content = normalize_robot_blank_and_space_arguments(content)
    content = compact_robot_tests_after_setup(content)
    content = normalize_robot_content_spacing(content)
    if workflow_name:
        content = apply_robot_test_naming_and_tags(content, workflow, workflow_name)
        content = compact_robot_tests_after_setup(content)
        content = normalize_robot_content_spacing(content)
    return content


def generate_automation_for_workflow(workflow_name: str) -> str:
    manual_path = get_manual_json_path(workflow_name)
    if not manual_path.exists():
        raise HTTPException(status_code=404, detail=f"Manual tests not found for workflow: {workflow_name}")

    config = validate_robot_config(load_robot_ai_json(CONFIG_PATH))
    ai_cfg = config["ai"]
    if not ai_cfg.get("enabled", True):
        raise HTTPException(status_code=400, detail="AI is disabled in configuration.")

    endpoint = ai_cfg.get("endpoint", "").strip()
    token = get_robot_ai_token(ai_cfg)
    if not endpoint or not token:
        raise HTTPException(status_code=400, detail="Automation AI endpoint/token missing in configuration.")

    manual_data = load_robot_ai_json(manual_path)
    if FEATURE_FLAGS.enable_rag:
        workflow_slug = derive_workflow_artifact_slug(load_workflow_or_404(workflow_name), workflow_name)
        manual_data["ragContext"] = rag_context_service.build_context(workflow_slug)
    resource_files = manual_data.get("resourceFiles", [])
    if not isinstance(resource_files, list) or not resource_files:
        raise HTTPException(status_code=400, detail="Manual tests do not contain valid resourceFiles.")

    pom_root = BASE_DIR / config["pom_output_dir"]
    resource_context = []
    for rel_path in resource_files:
        resource_path = pom_root / str(rel_path).replace("\\", "/")
        if not resource_path.exists():
            raise HTTPException(status_code=400, detail=f"Resource file not found: {resource_path}")
        resource_context.append(parse_resource_file(resource_path))

    resources_dir = BASE_DIR / "resources"
    if resources_dir.exists():
        for common_resource_path in sorted(resources_dir.glob("*.resource")):
            try:
                resource_context.append(parse_resource_file(common_resource_path))
            except Exception:
                continue

    prompt = build_robot_prompt(manual_data, resource_context)
    robot_content = call_ai_with_workflow_session(
        workflow_name=workflow_name,
        stage="robot_generation",
        endpoint=endpoint,
        token=token,
        prompt=prompt,
        timeout_seconds=ai_cfg.get("timeout_seconds", 120),
        verify_ssl=ai_cfg.get("verify_ssl", False),
    )

    workflow = load_workflow_or_404(workflow_name)
    robot_content = normalize_robot_content(robot_content, workflow, workflow_name)

    review_prompt = build_review_prompt(manual_data, resource_context, robot_content)
    reviewed_robot_content = call_ai_with_workflow_session(
        workflow_name=workflow_name,
        stage="robot_review",
        endpoint=endpoint,
        token=token,
        prompt=review_prompt,
        timeout_seconds=ai_cfg.get("timeout_seconds", 120),
        verify_ssl=ai_cfg.get("verify_ssl", False),
    )
    reviewed_robot_content = normalize_robot_content(reviewed_robot_content, workflow, workflow_name)
    if reviewed_robot_content:
        robot_content = reviewed_robot_content

    validation_review_prompt = build_validation_review_prompt(manual_data, resource_context, robot_content)
    validated_robot_content = call_ai_with_workflow_session(
        workflow_name=workflow_name,
        stage="robot_validation_review",
        endpoint=endpoint,
        token=token,
        prompt=validation_review_prompt,
        timeout_seconds=ai_cfg.get("timeout_seconds", 120),
        verify_ssl=ai_cfg.get("verify_ssl", False),
    )
    validated_robot_content = normalize_robot_content(validated_robot_content, workflow, workflow_name)
    if validated_robot_content:
        robot_content = validated_robot_content

    is_valid, validation_message = validate_robot_content(robot_content, resource_files)
    if validation_message:
        repair_prompt = (
            build_validation_review_prompt(manual_data, resource_context, robot_content)
            + "\n\nAdditional validation findings to repair with highest priority:\n"
            + validation_message
            + "\n\nWarnings are non-blocking, but you must still repair them when approved workflow knowledge, approved manual expectations, or imported resources provide enough evidence to do so. In particular, do not keep guest-state destination checks after successful authentication, do not keep repeated entry-journey steps in test bodies when setup can absorb them, do not leave any test without a final observable verification, and do not weaken password-masking scenarios into generic field-readiness checks. If approved resources do not yet expose a strong enough destination or masking validation keyword, preserve the strongest supported observable assertion and make the behavior-specific validation as explicit as the imported resources allow. Return only corrected Robot Framework code. Preserve approved scenario intent."
        )
        repaired_robot_content = call_ai_with_workflow_session(
            workflow_name=workflow_name,
            stage="robot_signature_repair",
            endpoint=endpoint,
            token=token,
            prompt=repair_prompt,
            timeout_seconds=ai_cfg.get("timeout_seconds", 120),
            verify_ssl=ai_cfg.get("verify_ssl", False),
        )
        repaired_robot_content = normalize_robot_content(repaired_robot_content, workflow, workflow_name)
        if repaired_robot_content:
            robot_content = repaired_robot_content
        is_valid, validation_message = validate_robot_content(robot_content, resource_files)
    if not is_valid:
        raise HTTPException(status_code=400, detail=validation_message)

    target = get_automation_path(workflow_name, workflow)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(robot_content, encoding="utf-8")
    save_workflow_knowledge(workflow_name)
    return robot_content

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.get("/")
def home(request: Request):
    workflows = sorted([
        p.stem
        for p in WORKFLOW_DIR.glob("*.json")
        if not p.name.endswith(".status.json") and not p.name.endswith(".contract.json")
    ])

    workflow_rows = []
    for workflow_name in workflows:
        workflow_rows.append({
            "name": workflow_name,
            "status": get_workflow_status(workflow_name)
        })

    return render_template(request, "index.html", {
        "workflow_rows": workflow_rows,
    })


@app.get("/story")
def story_generator_page(request: Request):
    return render_template(request, "story_generator.html", {
        "story_raw_input": "",
        "story_output": "",
    })


@app.post("/story/generate")
async def generate_workflow_story_route(request: Request, raw_input: str = Form("")):
    raw_value = clean_multiline_text(raw_input)
    try:
        story_output = generate_workflow_story_from_raw_input(raw_value)
        return render_template(request, "story_generator.html", {
            "story_raw_input": raw_value,
            "story_output": story_output,
            "success_message": "Workflow story generated successfully. Review and copy it into Azure DevOps if needed.",
        })
    except HTTPException as exc:
        return render_template(request, "story_generator.html", {
            "story_raw_input": raw_value,
            "story_output": "",
            "error_message": exc.detail,
        }, status_code=exc.status_code)
    except Exception as exc:
        return render_template(request, "story_generator.html", {
            "story_raw_input": raw_value,
            "story_output": "",
            "error_message": f"Workflow story generation failed: {str(exc)}",
        }, status_code=400)

@app.post("/workflow/delete/{workflow_name}")
def delete_workflow(workflow_name: str):
    workflow = load_workflow_or_404(workflow_name)

    workflow_path = WORKFLOW_DIR / f"{workflow_name}.json"
    if workflow_path.exists():
        workflow_path.unlink()

    status_path = get_status_path(workflow_name)
    if status_path.exists():
        status_path.unlink()

    session_path = get_session_path(workflow_name)
    if session_path.exists():
        session_path.unlink()

    manual_json_path = get_manual_json_path(workflow_name)
    if manual_json_path.exists():
        manual_json_path.unlink()
    legacy_manual_json_path = get_manual_legacy_json_path(workflow_name)
    if legacy_manual_json_path.exists():
        legacy_manual_json_path.unlink()

    manual_excel_path = get_manual_excel_path(workflow_name)
    if manual_excel_path.exists():
        manual_excel_path.unlink()
    legacy_manual_excel_path = get_manual_legacy_excel_path(workflow_name)
    if legacy_manual_excel_path.exists():
        legacy_manual_excel_path.unlink()

    automation_path = get_automation_path(workflow_name, workflow)
    if automation_path.exists():
        automation_path.unlink()

    page_name = ""
    pages = workflow.get("pages", []) if isinstance(workflow, dict) else []
    if pages and isinstance(pages[0], dict):
        page_name = clean_text(str(pages[0].get("name", "")))

    if page_name:
        page_dir = get_page_dir(page_name)
        if page_dir.exists() and page_dir.is_dir():
            shutil.rmtree(page_dir, ignore_errors=True)

    manual_dir = get_manual_workflow_dir(workflow_name)
    if manual_dir.exists() and manual_dir.is_dir():
        shutil.rmtree(manual_dir, ignore_errors=True)

    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)

def load_workflow_story_normalizer_prompt() -> str:
    prompt = read_text_file(WORKFLOW_STORY_NORMALIZER_PROMPT_PATH).strip()
    if not prompt:
        raise HTTPException(status_code=500, detail="Workflow story normalizer prompt is not configured.")
    return prompt


def call_devex_ai_text_fallback(endpoint: str, token: str, prompt: str, timeout_sec: int = 120) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(
            endpoint,
            headers=headers,
            data={"query": prompt},
            files=[],
            timeout=timeout_sec,
            verify=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Story generation request failed: {exc}") from exc

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Devex AI request failed ({resp.status_code}): {resp.text[:500]}",
        )

    raw_text = (resp.text or "").strip()
    if not raw_text:
        raise HTTPException(status_code=502, detail="Story generator returned empty content.")

    try:
        parsed = resp.json()
    except ValueError:
        return clean_multiline_text(raw_text)

    if isinstance(parsed, dict):
        candidate_keys = ["response", "content", "result", "answer", "text", "output"]
        for key in candidate_keys:
            value = parsed.get(key)
            if isinstance(value, str) and clean_multiline_text(value):
                return clean_multiline_text(value)
        if len(parsed) == 1:
            only_value = next(iter(parsed.values()))
            if isinstance(only_value, str) and clean_multiline_text(only_value):
                return clean_multiline_text(only_value)
        return clean_multiline_text(raw_text)

    if isinstance(parsed, str) and clean_multiline_text(parsed):
        return clean_multiline_text(parsed)

    return clean_multiline_text(raw_text)


def generate_workflow_story_from_raw_input(raw_input: str) -> str:
    cleaned_input = clean_multiline_text(raw_input)
    if not cleaned_input:
        raise HTTPException(status_code=400, detail="Raw input is required to generate a workflow story.")
    if len(cleaned_input) < 30:
        raise HTTPException(status_code=400, detail="Please provide more workflow details before generating the user story.")

    config = validate_manual_config(load_manual_config())
    ai_cfg = config.get("ai", {})
    if not ai_cfg.get("enabled"):
        raise HTTPException(status_code=400, detail="AI story generation is disabled in configuration.")

    endpoint = clean_text(str(ai_cfg.get("endpoint", "")))
    token = get_manual_ai_token(ai_cfg)
    if not endpoint or not token:
        raise HTTPException(status_code=400, detail="Devex AI endpoint or token is not configured for story generation.")

    timeout_seconds = int(ai_cfg.get("timeout_seconds", 120) or 120)
    instruction_prompt = load_workflow_story_normalizer_prompt()
    final_prompt = f"{instruction_prompt}\n\nRaw Input:\n{cleaned_input}\n"
    return call_devex_ai_text_fallback(
        endpoint=endpoint,
        token=token,
        prompt=final_prompt,
        timeout_sec=timeout_seconds,
    )


@app.get("/workflow/new")
def workflow_form(request: Request):
    existing = WORKFLOW_DIR / "login.json"
    data = read_json(existing) if existing.exists() else {}
    azure_defaults = {
        "base_url": os.getenv("AZURE_DEVOPS_BASE_URL", "https://devtfs.dover-global.net"),
        "collection": os.getenv("AZURE_DEVOPS_COLLECTION", "QA"),
        "project": os.getenv("AZURE_DEVOPS_PROJECT", "AutomationProject"),
    }
    return render_template(request, "workflow_form.html", {
        "data": data,
        "edit_mode": False,
        "workflow_slug": "",
        "azure_defaults": azure_defaults,
    })

@app.get("/workflow/edit/{workflow_name}")
def edit_workflow(request: Request, workflow_name: str):
    workflow = load_workflow_or_404(workflow_name)
    azure_defaults = {
        "base_url": os.getenv("AZURE_DEVOPS_BASE_URL", "https://devtfs.dover-global.net"),
        "collection": os.getenv("AZURE_DEVOPS_COLLECTION", "QA"),
        "project": os.getenv("AZURE_DEVOPS_PROJECT", "AutomationProject"),
    }
    return render_template(request, "workflow_form.html", {
        "data": workflow,
        "edit_mode": True,
        "workflow_slug": workflow_name,
        "azure_defaults": azure_defaults,
    })

def normalize_resource_file_path(page_name: str, resource_file: str) -> str:
    page_name = clean_text(page_name)
    if not page_name:
        return clean_text(resource_file)
    expected = f"{page_name}/{page_name}.resource"
    raw = clean_text(resource_file).replace("\\", "/")
    if not raw:
        return expected
    if raw.endswith(f"/{page_name}.resource"):
        return raw
    if raw.endswith(".resource") and "/" in raw:
        return raw
    return expected


def normalize_url_value(value: str) -> str:
    value = clean_text(value).strip().strip('`').rstrip('.,;:')
    if not value:
        return ""
    value = value.replace("%60", "")
    value = value.strip().strip('`').rstrip('.,;:')
    if value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    return value


def strip_html_tags(value: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\n+", "\n", re.sub(r"[ \t]+", " ", text)).strip()


def split_story_lines(value: str) -> list[str]:
    cleaned = strip_html_tags(value)
    lines = []
    for part in re.split(r"\n+|(?:^|\s)[\-*•]\s+|\d+[\.)]\s+", cleaned):
        item = clean_text(part)
        if item:
            lines.append(item)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in lines:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(item)
    return deduped


def build_azure_devops_auth_headers(pat: str) -> dict:
    token = base64.b64encode(f":{pat}".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def parse_azure_project_url(project_url: str) -> dict:
    raw = clean_text(project_url)
    if not raw:
        return {"base_url": "", "collection": "", "project": ""}
    parsed = urlparse(raw)
    path_parts = [part for part in parsed.path.split("/") if part]
    collection = path_parts[0] if len(path_parts) >= 1 else ""
    project = path_parts[1] if len(path_parts) >= 2 else ""
    base_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else raw.rstrip("/")
    return {
        "base_url": base_url.rstrip("/"),
        "collection": collection,
        "project": project,
    }


def resolve_azure_connection_details(base_url: str, collection: str, project: str) -> tuple[str, str, str]:
    parsed = parse_azure_project_url(base_url)
    resolved_base = clean_text(base_url) or parsed.get("base_url", "")
    resolved_collection = clean_text(collection) or parsed.get("collection", "")
    resolved_project = clean_text(project) or parsed.get("project", "")
    return resolved_base.rstrip("/"), resolved_collection.strip("/"), resolved_project.strip("/")


def fetch_azure_work_item(base_url: str, collection: str, project: str, work_item_id: str, pat: str) -> dict:
    base, collection, project = resolve_azure_connection_details(base_url, collection, project)
    work_item_id = clean_text(str(work_item_id))
    if not all([base, collection, project, work_item_id, pat]):
        raise HTTPException(status_code=400, detail="Azure DevOps connection details are incomplete. Provide a project URL or base URL plus collection/project, and ensure AZURE_DEVOPS_PAT is configured.")

    url = f"{base}/{collection}/{project}/_apis/wit/workitems/{work_item_id}?$expand=relations&api-version=5.1"
    try:
        response = requests.get(url, headers=build_azure_devops_auth_headers(pat), timeout=45, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        detail = exc.response.text.strip() if exc.response is not None and exc.response.text else str(exc)
        raise HTTPException(status_code=400, detail=f"Azure DevOps work item fetch failed: {detail}") from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Azure DevOps work item fetch failed: {exc}") from exc


def normalize_azure_work_item(base_url: str, collection: str, project: str, work_item: dict) -> dict:
    base_url, collection, project = resolve_azure_connection_details(base_url, collection, project)
    fields = work_item.get("fields", {}) if isinstance(work_item, dict) else {}
    title = clean_text(str(fields.get("System.Title", ""))) or f"Work Item {work_item.get('id', '')}"
    description = strip_html_tags(str(fields.get("System.Description", "")))
    acceptance_raw = str(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", ""))
    acceptance_criteria = split_story_lines(acceptance_raw)
    if not acceptance_criteria and description:
        acceptance_criteria = split_story_lines(description)

    relations = work_item.get("relations", []) if isinstance(work_item, dict) else []
    attachments = []
    for relation in relations:
        if not isinstance(relation, dict):
            continue
        rel = clean_text(str(relation.get("rel", ""))).lower()
        url = clean_text(str(relation.get("url", "")))
        if rel == "attachedfile" and url:
            attachments.append(url)

    return {
        "source": "azure_devops",
        "sourceId": str(work_item.get("id", "")),
        "sourceUrl": f"{base_url.rstrip('/')}/{collection.strip('/')}/{project.strip('/')}/_workitems/edit/{work_item.get('id', '')}",
        "title": title,
        "description": description,
        "acceptanceCriteria": acceptance_criteria,
        "attachments": attachments,
        "workItemType": clean_text(str(fields.get("System.WorkItemType", ""))),
        "state": clean_text(str(fields.get("System.State", ""))),
        "areaPath": clean_text(str(fields.get("System.AreaPath", ""))),
        "iterationPath": clean_text(str(fields.get("System.IterationPath", ""))),
        "assignedTo": clean_text(str(fields.get("System.AssignedTo", ""))),
        "tags": split_story_lines(str(fields.get("System.Tags", "")).replace(";", "\n")),
        "rawFields": {
            "System.Title": title,
            "System.Description": description,
            "Microsoft.VSTS.Common.AcceptanceCriteria": strip_html_tags(acceptance_raw),
        },
    }


def derive_test_identifier_prefix(source_context: dict | None) -> str:
    if not isinstance(source_context, dict):
        return ""
    source_id = clean_text(str(source_context.get("sourceId", "")))
    title = clean_text(str(source_context.get("title", "")))
    basis = source_id or title
    return compact_code(basis)[:20] if basis else ""


def build_workflow_payload_from_azure_story(
    azure_context: dict,
    page_name: str,
    page_url: str,
    resource_file: str,
    test_identifier_prefix: str = "",
) -> dict:
    workflow_name = clean_text(str(azure_context.get("title", ""))) or "Imported Workflow"
    description = clean_text(str(azure_context.get("description", "")))
    acceptance_criteria = azure_context.get("acceptanceCriteria", []) if isinstance(azure_context.get("acceptanceCriteria"), list) else []
    observed_steps = acceptance_criteria if acceptance_criteria else ([description] if description else [])
    expected_result = acceptance_criteria[0] if acceptance_criteria else description

    source = {
        "createdBy": "Azure DevOps import",
        "notes": f"Imported from Azure DevOps work item {azure_context.get('sourceId', '')}",
        "provider": "azure_devops",
        "sourceId": str(azure_context.get("sourceId", "")),
        "sourceUrl": clean_text(str(azure_context.get("sourceUrl", ""))),
    }

    return build_workflow_payload(
        workflow_name=workflow_name,
        module="Imported",
        feature=workflow_name,
        page_name=page_name,
        page_url=page_url,
        resource_file=resource_file,
        preconditions_text="",
        steps_text="\n".join(observed_steps),
        expected_result=expected_result,
        fields_text="",
        validations_text="\n".join(acceptance_criteria),
        scenario_intent_text="positive,negative,edge,ui",
        application_code=str(CONFIG.get("application_code", "")),
        source=source,
        external_context=azure_context,
        test_identifier_prefix=clean_text(test_identifier_prefix).upper() or derive_test_identifier_prefix(azure_context),
    )


@app.post("/workflow/save")
async def save_workflow(
    request: Request,
    workflow_name: str = Form(""),
    module: str = Form("Authentication"),
    feature: str = Form("Login"),
    page_name: str = Form(...),
    page_url: str = Form(""),
    resource_file: str = Form(...),
    preconditions_text: str = Form(""),
    steps_text: str = Form(""),
    expected_result: str = Form(""),
    fields_text: str = Form(""),
    validations_text: str = Form(""),
    scenario_intent_text: str = Form("positive,negative,edge,ui"),
    existing_workflow_slug: str = Form(""),
    input_source: str = Form("manual"),
    azure_base_url: str = Form(""),
    azure_collection: str = Form(""),
    azure_project: str = Form(""),
    azure_work_item_id: str = Form(""),
    test_identifier_prefix: str = Form(""),
):
    await request.form()
    page_url = normalize_url_value(page_url)
    input_source = clean_text(input_source).lower() or "manual"

    if input_source == "azure_devops":
        pat = os.getenv("AZURE_DEVOPS_PAT", "").strip()
        if not pat:
            raise HTTPException(status_code=400, detail="AZURE_DEVOPS_PAT environment variable is not configured.")
        work_item = fetch_azure_work_item(
            azure_base_url,
            azure_collection,
            azure_project,
            azure_work_item_id,
            pat,
        )
        azure_context = normalize_azure_work_item(azure_base_url, azure_collection, azure_project, work_item)
        payload = clean_workflow_for_prompting(build_workflow_payload_from_azure_story(
            azure_context=azure_context,
            page_name=page_name,
            page_url=page_url,
            resource_file=resource_file,
            test_identifier_prefix=test_identifier_prefix,
        ))
        workflow_name = clean_text(str(payload.get("workflowName", workflow_name)))
    else:
        payload = clean_workflow_for_prompting(build_workflow_payload(
            workflow_name,
            module,
            feature,
            page_name,
            page_url,
            resource_file,
            preconditions_text,
            steps_text,
            expected_result,
            fields_text,
            validations_text,
            scenario_intent_text,
            str(CONFIG.get("application_code", "")),
        ))

    canonical_workflow_name = derive_canonical_workflow_name(payload, workflow_name)
    if canonical_workflow_name:
        payload["workflowName"] = canonical_workflow_name

    existing_slug = clean_text(existing_workflow_slug)
    target_slug = derive_workflow_artifact_slug(payload, canonical_workflow_name or workflow_name)
    if existing_slug and existing_slug != target_slug:
        rename_workflow_slug_artifacts(existing_slug, target_slug)
    elif existing_slug and not (WORKFLOW_DIR / f"{target_slug}.json").exists() and (WORKFLOW_DIR / f"{existing_slug}.json").exists():
        target_slug = existing_slug

    target = WORKFLOW_DIR / f"{target_slug}.json"
    write_json(target, payload)

    if FEATURE_FLAGS.enable_workflow_contracts:
        planned_contract, payload = build_runtime_workflow_context(
            workflow_payload=payload,
            workflow_slug=target_slug,
            attach_stage="workflow_save",
        )
        payload = attach_execution_plan_if_enabled(
            workflow_slug=target_slug,
            contract=planned_contract,
            runtime_context=payload,
            attach_stage="workflow_save",
        )
        write_json(target, payload)
        if planned_contract is not None:
            platform_logger.info(
                "workflow_contract_saved",
                workflow_slug=target_slug,
                workflow_id=planned_contract.workflow_id,
                page_name=planned_contract.page.name,
                source_type=planned_contract.source_type,
            )

    normalized_page_name = clean_text(page_name)
    normalized_resource = normalize_resource_file_path(normalized_page_name, resource_file)
    if normalized_page_name:
        metadata_dir = get_page_metadata_dir(normalized_page_name)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        if isinstance(payload.get("resourceFiles"), list):
            payload["resourceFiles"] = [normalized_resource]
            write_json(target, payload)

    return RedirectResponse(url=f"/page-review/{target_slug}", status_code=303)

@app.get("/page-review/{workflow_name}")
def page_review(request: Request, workflow_name: str):
    workflow = load_workflow_or_404(workflow_name)
    review_data = get_page_review_data(workflow)
    return render_template(request, "page_review.html", {
        "workflow_name": derive_canonical_workflow_name(workflow, workflow_name),
        "workflow": workflow,
        "page_name": review_data["page_name"],
        "page_url": review_data["page_url"],
        "entry_page": review_data.get("entry_page", {}),
        "target_page": review_data.get("target_page", {}),
        "navigation_steps": review_data.get("navigation_steps", []),
        "target_page_signals": review_data.get("target_page_signals", []),
        "is_navigation_mode": review_data.get("is_navigation_mode", False),
        "elements": review_data["elements"],
        "screenshot_web_path": review_data["screenshot_web_path"],
        "raw_elements_count": review_data["raw_elements_count"],
        "display_elements_count": review_data["display_elements_count"],
        "raw_preview_elements": review_data.get("raw_preview_elements", []),
        "review_summary": review_data.get("review_summary"),
        "source_artifact": review_data.get("source_artifact", "raw"),
    })

@app.post("/page-review/{workflow_name}/extract")
def run_page_review_extraction(request: Request, workflow_name: str):
    workflow = load_workflow_or_404(workflow_name)
    review_data = get_page_review_data(workflow)
    resource_files = workflow.get("resourceFiles", []) if isinstance(workflow.get("resourceFiles"), list) else []
    merged_resource_files = []
    for item in resource_files:
        normalized = clean_text(str(item)).replace("\\", "/")
        if normalized and normalized not in merged_resource_files:
            merged_resource_files.append(normalized)
    resource_files = merged_resource_files

    navigation_steps = review_data.get("navigation_steps", [])
    target_page_signals = review_data.get("target_page_signals", [])
    extraction_context = {
        "entryPage": review_data.get("entry_page", {}),
        "targetPage": review_data.get("target_page", {}) or {"name": review_data["page_name"]},
        "navigationSteps": navigation_steps,
        "targetPageSignals": target_page_signals,
        "workflowName": clean_text(str(workflow.get("workflowName", workflow_name))),
        "feature": clean_text(str(workflow.get("feature", ""))),
        "testIdentifierPrefix": clean_text(str(workflow.get("testIdentifierPrefix", ""))),
        "applicationCode": clean_text(str(workflow.get("applicationCode", ""))),
        "resourceFiles": resource_files,
        "externalContext": workflow.get("externalContext", {}) if isinstance(workflow.get("externalContext"), dict) else {},
        "pages": workflow.get("pages", []) if isinstance(workflow.get("pages"), list) else [],
        "pageUrl": review_data.get("page_url", ""),
        "description": clean_text(str(workflow.get("description", workflow.get("userStory", "")))),
        "userStory": clean_text(str(workflow.get("userStory", ""))),
        "observedSteps": workflow.get("observedSteps", []) if isinstance(workflow.get("observedSteps"), list) else [],
        "observedValidations": workflow.get("observedValidations", []) if isinstance(workflow.get("observedValidations"), list) else [],
        "acceptanceCriteria": workflow.get("acceptanceCriteria", []) if isinstance(workflow.get("acceptanceCriteria"), list) else [],
        "ragContext": workflow.get("ragContext", {}) if isinstance(workflow.get("ragContext"), dict) else {},
    }
    if FEATURE_FLAGS.enable_workflow_contracts and FEATURE_FLAGS.enable_resource_reuse_agent:
        contract, extraction_context = build_runtime_workflow_context(
            workflow_payload=extraction_context,
            workflow_slug=workflow_name,
            attach_stage="page_extraction",
            resource_files=resource_files,
        )
        if contract is not None:
            platform_logger.info(
                "workflow_contract_available",
                workflow_slug=workflow_name,
                workflow_id=contract.workflow_id,
                page_name=contract.page.name,
                source_type=contract.source_type,
            )
        try:
            extraction_context["navigationSteps"] = resource_reuse_agent.resolve_navigation_steps(contract) or extraction_context["navigationSteps"]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        extraction_context = attach_execution_plan_if_enabled(
            workflow_slug=workflow_name,
            contract=contract,
            runtime_context=extraction_context,
            attach_stage="page_extraction",
        )
        execution_plan = extraction_context.get("executionPlan", {}) if isinstance(extraction_context.get("executionPlan", {}), dict) else {}
        execution_plan_execution = execution_plan.get("execution", {}) if isinstance(execution_plan.get("execution", {}), dict) else {}
        execution_runtime = execution_plan.get("executionRuntime", {}) if isinstance(execution_plan.get("executionRuntime", {}), dict) else {}
        extraction_runtime_payload = mcp_service.build_extraction_runtime_payload(execution_runtime)
        extraction_context["navigationSteps"] = execution_plan_execution.get("navigationSteps", extraction_context.get("navigationSteps", []))
        extraction_context["targetPageSignals"] = execution_plan_execution.get("targetSignals", extraction_context.get("targetPageSignals", []))
        extraction_context.update(extraction_runtime_payload)
        platform_logger.info(
            "execution_runtime_attached_for_extraction",
            workflow_slug=workflow_name,
            page_state=extraction_context.get("pageState", {}),
            mcp_execution=extraction_context.get("mcpExecution", {}),
            mcp_dispatch=extraction_context.get("mcpDispatch", {}),
            mcp_adapter=extraction_context.get("mcpAdapter", {}),
            mcp_enabled=extraction_context.get("mcpEnabled", False),
        )
    try:
        run_page_extraction(review_data["page_name"], review_data["page_url"], extraction_context)
        updated_review_data = get_page_review_data(workflow)
        refined_elements, review_summary = review_and_refine_page_elements(workflow, updated_review_data)
        updated_review_data = get_page_review_data(workflow)
        return render_template(request, "page_review.html", {
            "workflow_name": derive_canonical_workflow_name(workflow, workflow_name),
            "workflow": workflow,
            "page_name": updated_review_data["page_name"],
            "page_url": updated_review_data["page_url"],
            "entry_page": updated_review_data.get("entry_page", {}),
            "target_page": updated_review_data.get("target_page", {}),
            "navigation_steps": updated_review_data.get("navigation_steps", []),
            "target_page_signals": updated_review_data.get("target_page_signals", []),
            "is_navigation_mode": updated_review_data.get("is_navigation_mode", False),
            "elements": refined_elements or updated_review_data["elements"],
            "screenshot_web_path": updated_review_data["screenshot_web_path"],
            "raw_elements_count": updated_review_data["raw_elements_count"],
            "display_elements_count": len(refined_elements or updated_review_data["elements"]),
            "raw_preview_elements": updated_review_data.get("raw_preview_elements", []),
            "review_summary": review_summary,
            "source_artifact": "refined",
            "success_message": "Page extraction completed and AI review/refinement has been applied. Review the refined elements below.",
        })
    except Exception as exc:
        updated_review_data = get_page_review_data(workflow)
        return render_template(request, "page_review.html", {
            "workflow_name": derive_canonical_workflow_name(workflow, workflow_name),
            "workflow": workflow,
            "page_name": updated_review_data["page_name"],
            "page_url": updated_review_data["page_url"],
            "entry_page": updated_review_data.get("entry_page", {}),
            "target_page": updated_review_data.get("target_page", {}),
            "navigation_steps": updated_review_data.get("navigation_steps", []),
            "target_page_signals": updated_review_data.get("target_page_signals", []),
            "is_navigation_mode": updated_review_data.get("is_navigation_mode", False),
            "elements": updated_review_data["elements"],
            "screenshot_web_path": updated_review_data["screenshot_web_path"],
            "raw_elements_count": updated_review_data["raw_elements_count"],
            "display_elements_count": updated_review_data["display_elements_count"],
            "raw_preview_elements": updated_review_data.get("raw_preview_elements", []),
            "review_summary": updated_review_data.get("review_summary"),
            "source_artifact": updated_review_data.get("source_artifact", "raw"),
            "error_message": f"Page extraction failed: {str(exc)}",
        }, status_code=400)

@app.post("/page-review/{workflow_name}/save")
async def save_page_review(request: Request, workflow_name: str):
    workflow = load_workflow_or_404(workflow_name)
    review_data = get_page_review_data(workflow)
    form = await request.form()

    count = int(form.get("element_count", "0"))
    manual_count = int(form.get("manual_count", "0"))

    approved_elements = []

    for i in range(count):
        approved = form.get(f"element_{i}_approved") == "on"
        if not approved:
            continue

        approved_name = str(form.get(f"element_{i}_approved_name", "")).strip()
        element_type = str(form.get(f"element_{i}_type", "")).strip()
        locator = str(form.get(f"element_{i}_locator", "")).strip()

        if approved_name and locator:
            approved_elements.append({
                "approvedName": approved_name,
                "type": element_type,
                "locator": locator,
                "approved": True,
            })

    for i in range(manual_count):
        approved = form.get(f"manual_{i}_approved") == "on"
        if not approved:
            continue

        approved_name = str(form.get(f"manual_{i}_approved_name", "")).strip()
        element_type = str(form.get(f"manual_{i}_type", "")).strip()
        locator = str(form.get(f"manual_{i}_locator", "")).strip()

        if approved_name and locator:
            approved_elements.append({
                "approvedName": approved_name,
                "type": element_type,
                "locator": locator,
                "approved": True,
            })

    payload = {
        "pageName": review_data["page_name"],
        "pageUrl": review_data["page_url"],
        "rawElements": review_data.get("raw_elements", []),
        "elements": approved_elements,
        "reviewSummary": review_data.get("review_summary"),
    }
    write_json(review_data["elements_path"], payload)
    write_json(review_data["reviewed_elements_path"], payload)
    sync_page_variables_from_approved_elements(workflow, approved_elements)

    return RedirectResponse(url=f"/manual-tests/{workflow_name}", status_code=HTTP_303_SEE_OTHER)

@app.get("/keywords/{workflow_name}")
def keyword_review(request: Request, workflow_name: str):
    workflow = load_workflow_or_404(workflow_name)
    keyword_data = get_keyword_review_data(workflow)
    return render_template(request, "keyword_review.html", {
        "workflow_name": workflow_name,
        "page_name": keyword_data["page_name"],
        "keywords": keyword_data["keywords"],
        "review_summary": keyword_data.get("review_summary"),
        "source_artifact": keyword_data.get("source_artifact", "raw"),
    })

@app.post("/keywords/{workflow_name}/save")
async def save_keyword_review(request: Request, workflow_name: str):
    workflow = load_workflow_or_404(workflow_name)
    form = await request.form()
    count = int(form.get("keyword_count", "0"))
    approved_keywords = []

    for i in range(count):
        approved = form.get(f"keyword_{i}_approved") == "on"
        if not approved:
            continue

        implementation_text = str(form.get(f"keyword_{i}_implementation", "")).strip()
        implementation_lines = [line.rstrip() for line in implementation_text.splitlines() if line.strip()]
        arguments_text = str(form.get(f"keyword_{i}_arguments", "")).strip()
        arguments = [arg.strip() for arg in arguments_text.split(",") if arg.strip()]

        approved_keywords.append({
            "keywordId": str(form.get(f"keyword_{i}_id", "")).strip() or f"KW_{i+1:03d}",
            "keywordName": str(form.get(f"keyword_{i}_name", "")).strip(),
            "targetElement": str(form.get(f"keyword_{i}_target", "")).strip(),
            "action": str(form.get(f"keyword_{i}_action", "")).strip(),
            "arguments": arguments,
            "implementation": implementation_lines,
            "approved": True,
        })

    manual_path = get_manual_json_path(workflow_name)
    if not manual_path.exists():
        return render_template(request, "keyword_review.html", {
            "workflow_name": workflow_name,
            "page_name": get_keyword_review_data(workflow)["page_name"],
            "keywords": get_keyword_review_data(workflow)["keywords"],
            "review_summary": None,
            "error_message": "Approved manual tests are required before keyword approval and resource generation.",
        }, status_code=400)

    approved_manual_tests = extract_manual_test_cases(read_json(manual_path))
    if not approved_manual_tests:
        return render_template(request, "keyword_review.html", {
            "workflow_name": workflow_name,
            "page_name": get_keyword_review_data(workflow)["page_name"],
            "keywords": get_keyword_review_data(workflow)["keywords"],
            "review_summary": None,
            "error_message": "Approve at least one manual test before generating the page resource and keywords.",
        }, status_code=400)

    keywords_valid, keyword_warnings, normalized_keywords = validate_keyword_grounding(workflow, approved_keywords)
    keyword_reuse_validation_ok, keyword_reuse_validation_message = validate_reviewed_keywords_against_existing_resources(normalized_keywords, get_keyword_review_data(workflow)["page_name"])
    keyword_data = get_keyword_review_data(workflow)
    combined_warnings = list(keyword_warnings)
    if keyword_reuse_validation_message:
        combined_warnings.extend([line.lstrip("- ").strip() for line in keyword_reuse_validation_message.splitlines() if clean_text(line)])
    blocking_keyword_warnings = [
        warning for warning in combined_warnings
        if any(token in warning.lower() for token in (
            "duplicate reviewed keyword implementation signature",
            "references unknown variable",
            "non-approved target element",
        ))
    ]
    if not keywords_valid or blocking_keyword_warnings:
        return render_template(request, "keyword_review.html", {
            "workflow_name": workflow_name,
            "page_name": keyword_data["page_name"],
            "keywords": normalized_keywords or keyword_data["keywords"],
            "review_summary": keyword_data.get("review_summary"),
            "source_artifact": keyword_data.get("source_artifact", "raw"),
            "error_message": "Keyword review contains blocking validation issues that must be resolved before continuing.",
            "grounding_warnings": combined_warnings,
        }, status_code=400)

    save_keywords_for_workflow(workflow, normalized_keywords)
    generate_resource_for_workflow(workflow, normalized_keywords)
    save_workflow_knowledge(workflow_name)

    return RedirectResponse(url=f"/automation/{workflow_name}", status_code=HTTP_303_SEE_OTHER)

@app.get("/manual-tests/{workflow_name}")
def manual_tests_page(request: Request, workflow_name: str):
    workflow_path = WORKFLOW_DIR / f"{workflow_name}.json"
    manual_path = get_manual_json_path(workflow_name)
    workflow = read_json(workflow_path) if workflow_path.exists() else None
    manual = read_json(manual_path) if manual_path.exists() else None
    test_cases = extract_manual_test_cases(manual) if manual else []

    return render_template(request, "manual_tests.html", {
        "workflow_name": workflow_name,
        "workflow": workflow,
        "manual": manual,
        "test_cases": test_cases,
    })

@app.post("/manual-tests/{workflow_name}/generate")
def generate_manual_tests_route(request: Request, workflow_name: str):
    workflow_path = WORKFLOW_DIR / f"{workflow_name}.json"
    manual_path = get_manual_json_path(workflow_name)
    workflow = read_json(workflow_path) if workflow_path.exists() else None
    try:
        generated = generate_manual_tests_for_workflow(workflow_name)
        test_cases = extract_manual_test_cases(generated)
        return render_template(request, "manual_tests.html", {
            "workflow_name": workflow_name,
            "workflow": workflow,
            "manual": generated,
            "test_cases": test_cases,
            "success_message": "Manual tests generated successfully. Review and approve the relevant tests.",
        })
    except Exception as exc:
        existing_manual = read_json(manual_path) if manual_path.exists() else None
        return render_template(request, "manual_tests.html", {
            "workflow_name": workflow_name,
            "workflow": workflow,
            "manual": existing_manual,
            "test_cases": extract_manual_test_cases(existing_manual) if existing_manual else [],
            "error_message": f"Manual test generation failed: {str(exc)}",
        }, status_code=400)

@app.post("/manual-tests/{workflow_name}/save")
async def save_manual_tests(request: Request, workflow_name: str):
    workflow_path = WORKFLOW_DIR / f"{workflow_name}.json"
    workflow = read_json(workflow_path) if workflow_path.exists() else None
    manual_path = get_manual_json_path(workflow_name)

    try:
        form = await request.form()

        original = read_json(manual_path) if manual_path.exists() else {
            "workflowName": workflow_name,
            "resourceFiles": workflow.get("resourceFiles", []) if workflow else [],
            "manualTests": [],
        }

        count = int(form.get("case_count", "0"))
        cases = []

        for i in range(count):
            approved = form.get(f"case_{i}_approved") == "on"
            if not approved:
                continue

            case_id = str(form.get(f"case_{i}_id", "")).strip()
            title = str(form.get(f"case_{i}_title", "")).strip()
            case_type = str(form.get(f"case_{i}_type", "General")).strip()
            priority = str(form.get(f"case_{i}_priority", "Medium")).strip()
            preconditions_text = str(form.get(f"case_{i}_preconditions", "")).strip()
            steps_text = str(form.get(f"case_{i}_steps", "")).strip()
            expected_result = str(form.get(f"case_{i}_expected", "")).strip()

            preconditions = [line.strip().removeprefix("- ").strip() for line in preconditions_text.splitlines() if line.strip()]
            steps = []
            for line in steps_text.splitlines():
                value = line.strip()
                if not value:
                    continue
                value = re.sub(r"^\d+\.\s*", "", value)
                steps.append(value)

            cases.append({
                "id": case_id or f"TC_{i+1:03d}",
                "title": title or f"Test Case {i+1}",
                "type": case_type.title() or "General",
                "priority": priority or "Medium",
                "preconditions": preconditions,
                "steps": steps,
                "expectedResult": expected_result,
            })

        if not cases:
            existing_manual = read_json(manual_path) if manual_path.exists() else None
            return render_template(request, "manual_tests.html", {
                "workflow_name": workflow_name,
                "workflow": workflow,
                "manual": existing_manual,
                "test_cases": extract_manual_test_cases(existing_manual) if existing_manual else [],
                "error_message": "Please select at least one test case to approve.",
            }, status_code=400)

        updated = update_manual_with_ui_cases(original, cases)
        write_json(manual_path, updated)
        export_manual_tests_to_excel(workflow_name, workflow, updated)
        save_workflow_knowledge(workflow_name)

        page_name = ""
        pages = workflow.get("pages", []) if isinstance(workflow, dict) else []
        if pages and isinstance(pages[0], dict):
            page_name = clean_text(str(pages[0].get("name", "")))
        if page_name:
            keywords_path = get_keywords_path(page_name)
            approved_keywords = []
            if keywords_path.exists():
                try:
                    payload = read_json(keywords_path)
                    approved_keywords = payload.get("keywords", []) if isinstance(payload, dict) else []
                except Exception:
                    approved_keywords = []
            enrich_resource_with_manual_test_variables(workflow, approved_keywords)

        return RedirectResponse(url=f"/keywords/{workflow_name}", status_code=HTTP_303_SEE_OTHER)

    except Exception as exc:
        existing_manual = read_json(manual_path) if manual_path.exists() else None
        return render_template(request, "manual_tests.html", {
            "workflow_name": workflow_name,
            "workflow": workflow,
            "manual": existing_manual,
            "test_cases": extract_manual_test_cases(existing_manual) if existing_manual else [],
            "error_message": f"Failed to approve manual tests: {str(exc)}",
        }, status_code=400)

@app.get("/automation/{workflow_name}")
def automation_page(request: Request, workflow_name: str):
    workflow = read_json(WORKFLOW_DIR / f"{workflow_name}.json") if (WORKFLOW_DIR / f"{workflow_name}.json").exists() else None
    robot_path = get_automation_path(workflow_name, workflow)
    robot_content = read_text(robot_path)
    return render_template(request, "automation.html", {
        "workflow_name": workflow_name,
        "robot_content": robot_content,
    })

@app.post("/automation/{workflow_name}/generate")
def generate_automation_route(request: Request, workflow_name: str):
    workflow = read_json(WORKFLOW_DIR / f"{workflow_name}.json") if (WORKFLOW_DIR / f"{workflow_name}.json").exists() else None
    automation_path = get_automation_path(workflow_name, workflow)
    existing_content = read_text(automation_path) if automation_path.exists() else ""
    ensure_workflow_run(workflow_name)
    try:
        robot_content = generate_automation_for_workflow(workflow_name)
        return render_template(request, "automation.html", {
            "workflow_name": workflow_name,
            "robot_content": robot_content,
            "success_message": "Automation script generated successfully. Review and save the approved version.",
        })
    except Exception as exc:
        return render_template(request, "automation.html", {
            "workflow_name": workflow_name,
            "robot_content": existing_content,
            "error_message": f"Automation generation failed: {str(exc)}",
        }, status_code=400)

@app.post("/automation/{workflow_name}/save")
def save_automation(request: Request, workflow_name: str, robot_content: str = Form(...)):
    try:
        workflow = read_json(WORKFLOW_DIR / f"{workflow_name}.json") if (WORKFLOW_DIR / f"{workflow_name}.json").exists() else None
        target = get_automation_path(workflow_name, workflow)
        target.parent.mkdir(parents=True, exist_ok=True)
        robot_content = normalize_robot_content(robot_content, workflow, workflow_name)
        target.write_text(robot_content, encoding="utf-8")
        return render_template(request, "automation.html", {
            "workflow_name": workflow_name,
            "robot_content": robot_content,
            "success_message": "Automation script saved successfully.",
        })
    except Exception as exc:
        return render_template(request, "automation.html", {
            "workflow_name": workflow_name,
            "robot_content": robot_content,
            "error_message": f"Failed to save automation script: {str(exc)}",
        }, status_code=400)

@app.get("/static-artifacts/{page_name}/{file_name}")
def static_artifact(page_name: str, file_name: str):
    from fastapi.responses import FileResponse
    target = get_page_metadata_dir(page_name) / file_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(target)