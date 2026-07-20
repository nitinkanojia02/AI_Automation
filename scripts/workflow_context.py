import json
import re
from pathlib import Path
from typing import Any, Dict, List

try:
    from scripts.workflow_knowledge import discover_relevant_workflow_knowledge
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from scripts.workflow_knowledge import discover_relevant_workflow_knowledge

try:
    from scripts.artifact_reuse import collect_existing_resource_context, normalize_name_tokens
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from scripts.artifact_reuse import collect_existing_resource_context, normalize_name_tokens

BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_INPUT_DIR = BASE_DIR / "workflow_inputs"
POM_DIR = BASE_DIR / "pom_pages"
MANUAL_DIR = BASE_DIR / "manual_tests"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def slugify(text: str) -> str:
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "workflow"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_load_json(path: Path) -> Dict[str, Any] | None:
    try:
        if path.exists():
            return load_json(path)
    except Exception:
        return None
    return None


def collect_story_text(workflow_input: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for key in [
        "description",
        "userStory",
        "observedExpectedResult",
        "acceptanceCriteria",
        "acceptance_criteria",
        "generationGuidance",
    ]:
        value = workflow_input.get(key)
        if isinstance(value, str) and clean_text(value):
            chunks.append(clean_text(value))
        elif isinstance(value, list):
            chunks.extend(clean_text(str(item)) for item in value if clean_text(str(item)))
    for key in ["observedPreconditions", "observedSteps", "observedValidations", "scenarioIntent", "preconditions", "steps"]:
        value = workflow_input.get(key)
        if isinstance(value, list):
            chunks.extend(clean_text(str(item)) for item in value if clean_text(str(item)))
    for key in ["entryPage", "targetPage"]:
        value = workflow_input.get(key)
        if isinstance(value, dict):
            chunks.extend(clean_text(str(v)) for v in value.values() if clean_text(str(v)))
    if isinstance(workflow_input.get("navigationSteps"), list):
        for step in workflow_input["navigationSteps"]:
            if isinstance(step, dict):
                chunks.extend(clean_text(str(v)) for v in step.values() if clean_text(str(v)))
    external_context = workflow_input.get("externalContext")
    if isinstance(external_context, dict):
        for key in [
            "description",
            "userStory",
            "acceptanceCriteria",
            "acceptance_criteria",
            "generationGuidance",
            "validationExpectations",
            "behaviorRules",
            "transitionExpectations",
            "pomReuseGuidance",
            "approvedTestDataGuidance",
            "applicationContext",
            "loginPageElements",
        ]:
            value = external_context.get(key)
            if isinstance(value, str) and clean_text(value):
                chunks.append(clean_text(value))
            elif isinstance(value, list):
                chunks.extend(clean_text(str(item)) for item in value if clean_text(str(item)))
    return " ".join(chunk for chunk in chunks if chunk)


def resource_summary(resource_file: str) -> Dict[str, Any]:
    rel = str(resource_file).replace("\\", "/").strip()
    page_key = Path(rel).stem
    resource_path = POM_DIR / rel
    summary: Dict[str, Any] = {
        "resourceFile": rel,
        "pageKey": page_key,
        "exists": resource_path.exists(),
    }
    if resource_path.exists():
        try:
            text = resource_path.read_text(encoding="utf-8")
            keywords = re.findall(r"(?m)^([^\s*].+)$", text)
            summary["keywordNames"] = [clean_text(k) for k in keywords if clean_text(k) and not clean_text(k).startswith("Resource")]
            summary["ownsUrlVariables"] = sorted(set(re.findall(r"\$\{([A-Z0-9_]*URL[A-Z0-9_]*)\}", text)))
        except Exception:
            pass
    return summary


def find_relevant_existing_resources(workflow_input: Dict[str, Any]) -> List[str]:
    story = collect_story_text(workflow_input).lower()
    external_context = workflow_input.get("externalContext", {}) if isinstance(workflow_input.get("externalContext"), dict) else {}
    external_story = collect_story_text(external_context).lower() if external_context else ""
    combined_story = f"{story} {external_story}".strip()
    current = {str(x).replace('\\', '/').strip() for x in workflow_input.get("resourceFiles", []) if str(x).strip()}

    story_tokens = set(normalize_name_tokens(combined_story).split())
    resources = collect_existing_resource_context(include_common=False)
    scored: List[tuple[int, str]] = []
    relevant_knowledge = discover_relevant_workflow_knowledge(workflow_input)
    knowledge_resource_signals: set[str] = set()
    knowledge_text_tokens: set[str] = set()

    for item in relevant_knowledge if isinstance(relevant_knowledge, list) else []:
        knowledge = item.get("knowledge") if isinstance(item, dict) else {}
        if not isinstance(knowledge, dict):
            continue
        resource_knowledge = knowledge.get("resourceKnowledge") if isinstance(knowledge.get("resourceKnowledge"), dict) else {}
        for path in resource_knowledge.get("authoritativeResources") or []:
            normalized = str(path).replace("\\", "/").strip()
            if normalized:
                knowledge_resource_signals.add(normalized)
        knowledge_blob = json.dumps(knowledge, ensure_ascii=False)
        knowledge_text_tokens.update(normalize_name_tokens(knowledge_blob).split())

    for resource in resources:
        rel = str(resource.get("file", "")).replace("pom_pages/", "").strip()
        if not rel:
            continue
        page_dir_name = Path(rel).parent.name
        page_name = page_dir_name.replace("_page", "")
        if rel in current and page_name not in {"home", "logout"}:
            continue

        resource_tokens = set()
        resource_tokens.update(normalize_name_tokens(page_name).split())
        resource_tokens.update(normalize_name_tokens(page_dir_name).split())
        for keyword in resource.get("keywords", []):
            resource_tokens.update(normalize_name_tokens(keyword.get("name", "")).split())
        for variable in resource.get("variables", []):
            resource_tokens.update(normalize_name_tokens(variable.get("name", "")).split())

        token_overlap = len({token for token in resource_tokens if token and token in story_tokens})
        knowledge_overlap = len({token for token in resource_tokens if token and token in knowledge_text_tokens})
        direct_page_hit = 1 if any(token and token in combined_story for token in {page_name, page_dir_name, page_name.replace("_", " ")}) else 0
        knowledge_resource_hit = 1 if rel in knowledge_resource_signals else 0
        current_overlap_penalty = -2 if rel in current else 0
        score = token_overlap * 3 + knowledge_overlap * 2 + direct_page_hit * 5 + knowledge_resource_hit * 6 + current_overlap_penalty

        if score > 0:
            scored.append((score, rel))

    scored.sort(key=lambda item: (-item[0], item[1]))
    deduped: List[str] = []
    seen = set()
    for _, item in scored:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped[:10]


def infer_workflow_reuse_context(workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    workflow_name = str(workflow_input.get("workflowName", "")).strip() or "workflow"
    story = collect_story_text(workflow_input)
    current_resources = [str(x).replace("\\", "/").strip() for x in workflow_input.get("resourceFiles", []) if str(x).strip()]
    inferred_resources = find_relevant_existing_resources(workflow_input)
    entry_page = workflow_input.get("entryPage") if isinstance(workflow_input.get("entryPage"), dict) else {}
    target_page = workflow_input.get("targetPage") if isinstance(workflow_input.get("targetPage"), dict) else {}

    classification = "standalone_page_or_workflow"
    lowered = story.lower()
    if "single page application" in lowered or "spa" in lowered:
        classification = "spa_stateful_workflow"
    if entry_page or workflow_input.get("navigationSteps"):
        classification = "dependent_navigation_workflow"
    if any(token in lowered for token in ["logout", "sign out", "authenticated state", "account menu"]):
        classification = "authenticated_state_behavior"

    authoritative = current_resources + [item for item in inferred_resources if item not in current_resources]
    return {
        "workflowName": workflow_name,
        "workflowType": classification,
        "storySummary": story,
        "entryPage": entry_page,
        "targetPage": target_page,
        "currentResourceFiles": current_resources,
        "inferredRelevantResourceFiles": inferred_resources,
        "authoritativeResourceFiles": authoritative,
        "resourceSummaries": [resource_summary(item) for item in authoritative],
        "reuseGuidance": [
            "Infer dependencies from the workflow story and existing approved resources; do not assume direct URL access unless the story states it.",
            "Prefer approved existing page resources for navigation, setup, and post-condition validation when the story implies those relationships.",
            "Treat SPA state changes as potential states of an existing page resource instead of automatically creating a new unrelated page model.",
            "Prefer reusing authoritative approved resources over duplicating ownership of controls or keywords in a new workflow.",
        ],
    }
