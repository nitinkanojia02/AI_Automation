#!/usr/bin/env python3
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from scripts.generate_robot_from_manual import build_manual_refiner_prompt, build_manual_review_prompt, validate_manual_content
    from scripts.workflow_context import infer_workflow_reuse_context
    from scripts.workflow_knowledge import build_workflow_knowledge_context, discover_relevant_workflow_knowledge
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from scripts.generate_robot_from_manual import build_manual_refiner_prompt, build_manual_review_prompt, validate_manual_content
    from scripts.workflow_context import infer_workflow_reuse_context
    from scripts.workflow_knowledge import build_workflow_knowledge_context, discover_relevant_workflow_knowledge

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "page_model_config.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("generate_manual_tests_json")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "workflow"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def pretty_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_list_of_strings(v: Any) -> List[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str) and v.strip():
        return [v.strip()]
    return []


def extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None
    return None


def get_ai_token(ai_cfg: dict) -> str:
    token = str(ai_cfg.get("token", "")).strip()
    if token:
        return token

    token_env_var = str(ai_cfg.get("token_env_var", "")).strip()
    if token_env_var:
        return os.getenv(token_env_var, "").strip()

    return ""


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    return load_json(CONFIG_PATH)



def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    config["workflow_input_dir"] = str(config.get("workflow_input_dir", "workflow_inputs"))
    config["manual_tests_output_dir"] = str(config.get("manual_tests_output_dir", "manual_tests"))

    if "generation_control" not in config:
        config["generation_control"] = {}

    gc = config["generation_control"]
    gc["overwrite_manual_tests"] = bool(gc.get("overwrite_manual_tests", False))
    gc["excluded_workflows"] = [slugify(x) for x in gc.get("excluded_workflows", []) if str(x).strip()]

    if "ai" not in config:
        config["ai"] = {}

    ai = config["ai"]
    ai["enabled"] = bool(ai.get("enabled", False))
    ai["endpoint"] = str(ai.get("endpoint", "")).strip()

    return config


def make_test_id_prefix(workflow_name: str) -> str:
    letters = re.findall(r"[A-Za-z0-9]+", workflow_name.upper())
    if not letters:
        return "TST"
    if len(letters) == 1:
        token = letters[0]
        return (token[:3] if len(token) >= 3 else token.ljust(3, "X"))
    prefix = "".join(x[0] for x in letters[:3])
    return prefix[:3].ljust(3, "X")


def build_compact_story_context(workflow_input: Dict[str, Any], max_chars: int = 6000) -> Dict[str, Any]:
    keys_to_keep = [
        "workflowName",
        "module",
        "feature",
        "scenarioIntent",
        "resourceFiles",
        "fields",
        "testData",
        "approvedElements",
        "observedPreconditions",
        "observedSteps",
        "observedExpectedResult",
        "observedValidations",
    ]
    compact: Dict[str, Any] = {}
    for key in keys_to_keep:
        value = workflow_input.get(key)
        if value in (None, "", [], {}):
            continue
        compact[key] = value

    external_context = workflow_input.get("externalContext")
    if isinstance(external_context, dict):
        reduced_context = {}
        for key in ["description", "acceptanceCriteria", "notes", "references"]:
            value = external_context.get(key)
            if value in (None, "", [], {}):
                continue
            reduced_context[key] = value
        if reduced_context:
            compact["externalContext"] = reduced_context

    serialized = pretty_json(compact)
    if len(serialized) <= max_chars:
        return compact

    for key in ["approvedElements", "observedSteps", "observedValidations", "externalContext", "testData", "fields"]:
        if key not in compact:
            continue
        candidate = dict(compact)
        candidate.pop(key, None)
        serialized_candidate = pretty_json(candidate)
        if len(serialized_candidate) <= max_chars:
            return candidate
        compact = candidate

    serialized = pretty_json(compact)
    if len(serialized) > max_chars:
        compact["_truncated"] = True
    return compact


def build_prompt(workflow_input: Dict[str, Any]) -> str:
    current_workflow_knowledge = build_workflow_knowledge_context(workflow_input)
    reuse_context = infer_workflow_reuse_context(workflow_input)
    relevant_workflow_knowledge = discover_relevant_workflow_knowledge(workflow_input)
    requirement_units = extract_requirement_units(workflow_input)
    mandatory_scenarios = []
    for item in requirement_units:
        mandatory_scenarios.append({
            "id": item["id"],
            "source": item["source"],
            "requirement": item["text"],
        })
    compact_workflow_input = build_compact_story_context(workflow_input)
    return f"""
You are AI Layer 1: a senior QA test designer operating inside a multi-layer AI-assisted automation framework.
Your output is a reviewable manual-test artifact that will feed downstream keyword/resource generation, Robot generation, and additional AI review and governance layers.

Your goal is not just to list tests, but to produce high-signal manual tests with explicit observable outcomes so later AI layers can generate strong assertions and the exact reusable page keywords needed for approved scenarios.

Analyze the workflow input and generate a practical manual test suite JSON.
Prioritize full coverage of the imported user story structure: user story, entry conditions, behavior rules, validation expectations, transition expectations, approved test data guidance, acceptance criteria, and generation guidance. Treat those sections as mandatory scenario sources before adding optional exploratory cases.

Return ONLY a valid JSON object with exactly these top-level keys:
- workflowName
- resourceFiles
- preconditions
- testCases

Return ONLY test cases in JSON form. Do not include commentary, markdown, notes, headings, or explanations.

Behavior-faithfulness requirement:
- Even though the output schema stays minimal, preserve interaction nuance in the wording of title, steps, and expectedResult so downstream AI layers can infer intent without hardcoded mapping.
- Keep distinctions such as paste, keyboard submit, repeated click, whitespace handling, masking, navigation-specific behavior, and validation-specific behavior explicit in the artifact wording whenever they are materially different.

Context usage requirements:
1. Treat approvedElements as the approved UI ground truth for this workflow.
2. Use observedPreconditions, observedSteps, observedExpectedResult, observedValidations, testData, scenarioIntent, fields, resourceFiles, and approvedElements together.
3. Before generating tests, consult the supplied relevant workflow knowledge artifacts and reuse approved upstream application knowledge, navigation knowledge, resource ownership knowledge, and validation knowledge when the current workflow depends on prior approved workflows.
4. Use approved elements to infer realistic UI actions, visible validations, control-state checks, navigation checks, and field-level scenarios.
5. Use user-supplied testData and workflow context to infer positive, negative, and edge data combinations.
6. Use expected observations and validations to derive concrete observable expectedResult values.
7. Do not limit generation to only explicitly listed workflow steps if the approved page elements clearly support additional meaningful scenarios.
8. Never generate a manual test, step, field reference, validation, or expected result around an element that is not present in approvedElements unless that behavior is explicitly stated in the workflow input itself (for example in observedSteps, observedValidations, preconditions, fields, or user story text).
9. If an element was not approved, treat it as out of scope and do not infer new tests from it.
10. Treat workflow knowledge artifacts as approved application memory. They summarize approved user-story knowledge, approved element knowledge, approved manual coverage, approved keyword/resource knowledge, and approved automation knowledge from prior workflows. Reuse them before inventing any new page ownership or navigation assumptions.
11. Also use the supplied current workflow knowledge draft as the concise approved-memory view of the current workflow input. Keep generation aligned with that draft so downstream stages preserve application and workflow intelligence consistently.
12. Use workflow knowledge → authoritative upstream resources → approved entry journey → approved destination-state validation as a mandatory reasoning chain for scenario design whenever the workflow depends on upstream navigation or post-action state transitions.
13. If workflow knowledge indicates the target page is not directly accessed by URL, do not design manual scenarios as if the target page is the unexplained starting point; model the approved upstream entry journey explicitly.
14. If workflow knowledge defines a success destination or return destination, generate explicit manual coverage for those destination states instead of validating only local-page disappearance or remaining on the origin page.
15. If workflow knowledge identifies authoritative upstream resources for entry flow, return-path validation, or destination-state validation, preserve that reuse intent explicitly in scenario steps and expected results.

Mandatory coverage requirements:
1. testCases must be a non-empty array.
2. Generate as many meaningful and distinct test cases as reasonably possible for the workflow.
3. Do not artificially limit the number of test cases.
4. Cover all relevant scenarios you can infer from the workflow input.
5. The generated suite must include all of the following categories wherever applicable:
   - Positive test cases
   - Negative test cases
   - UI test cases
   - Field validation test cases
   - Suggested additional edge test cases
6. Use workflow steps, approvedElements, fields, observedValidations, preconditions, resourceFiles, testData, and observedExpectedResult to infer additional scenarios.
7. Convert every explicit validation into one or more concrete test cases.
8. If approved elements or fields imply likely validations, generate those test cases too even if not explicitly listed.
9. Prefer high coverage and realistic manual execution scenarios over minimal output.
10. Avoid duplicate or redundant test cases.
11. Every mandatory acceptance criterion must be covered by at least one generated test case.
12. Acceptance criteria involving shared, upstream, reused, or cross-page controls must still generate tests even when those controls are not newly extracted on the current page.
13. For workflow-defined navigation, return, redirect, or transition criteria, generate explicit scenario coverage instead of replacing them with generic exploratory cases.
14. Prioritize mandatory acceptance-criteria coverage before adding additional exploratory edge cases.
15. If the workflow includes explicit approved business data, required controls, transition expectations, state changes, observable outcome signals, or reusable resource guidance, generate tests that reflect those exact story details before adding extra generic exploratory scenarios.
16. Do not let optional edge or accessibility-style tests displace mandatory user-story scenarios such as required navigation, transition validation, state-change validation, observable outcome validation, or approved business-data usage.

Schema rules:
1. Every test case object must contain exactly these keys:
   - id
   - title
   - type
   - steps
   - expectedResult
   - fields
2. Do not add extra keys for intent metadata in the output; instead preserve intent clearly in natural-language wording so downstream refinement layers can infer it.
2. type must be one of:
   - positive
   - negative
   - edge
3. Preserve resourceFiles exactly if provided in input.
4. Keep steps actionable, UI-focused, and executable manually.
5. Do not include any extra keys.
6. Do not group test cases under separate headings. Place all cases inside testCases.

Coverage guidance:
- Positive cases:
  - valid end-to-end flow
  - valid alternate user actions
  - valid combinations of input
- Negative cases:
  - invalid input
  - incorrect values
  - missing values
  - invalid sequence
  - rejection/error handling
- UI cases:
  - page or form element visibility
  - labels, placeholders, buttons, links, controls
  - control state such as enabled/disabled
  - navigation behavior
  - messages shown on screen
  - focus behavior where relevant
- Field validation cases:
  - required field validation
  - invalid format
  - min length
  - max length
  - boundary values
  - whitespace-only input
  - leading/trailing whitespace
  - special characters
  - unsupported characters
  - numeric/alphanumeric constraints
  - field-specific business validation
- Additional edge cases:
  - unusual but valid input
  - repeated clicks/submissions
  - very long input
  - empty state behavior
  - case sensitivity
  - copy-paste behavior where relevant
  - browser/UI interaction anomalies inferable from workflow
  - alternate but valid navigation path

Important behavior:
- Generate all practical tests the workflow supports on its own.
- Do not stop after a minimum number of cases.
- Infer as many useful UI, validation, negative, and edge scenarios as possible.
- If the workflow is form-based, expand test cases heavily around each field and approved control.
- If multiple fields exist, include combination-based validation scenarios where useful.
- If approvedElements expose navigation controls, action buttons, messages, masked fields, or other meaningful UI states, generate grounded manual tests for them where relevant.
- If observedValidations exist, transform them into concrete manual test cases, not summary text.
- Write expectedResult values so downstream automation and keyword generation can create observable assertions and reusable validations, not vague outcomes.
- For positive transition or navigation cases, expectedResult should explicitly mention the destination state, landing view/page, redirect, visible state change, role-specific UI change, URL change, or another equivalent observable outcome.
- If approved business data is provided in the workflow story, reflect that approved data in the relevant positive scenario wording instead of replacing it with generic placeholder phrasing everywhere.
- For negative validation or failed-transition cases, expectedResult should explicitly mention observable rejection, validation messaging, lack of navigation, denial of protected access, disabled submission, or continued presence of the current state where applicable.
- If the story requires transition validation such as identity changes, role/state-specific UI changes, newly available capabilities, or destination-state evidence, create explicit manual tests for those outcomes instead of leaving them implied inside a generic successful flow test.
- For edge interaction scenarios such as Enter key, repeated clicking, whitespace handling, copy-paste, and long input, expectedResult should describe the exact observable behavior that automation must verify.
- Avoid producing shallow variants that differ only in wording but not in observable intent.
- Prefer tests whose expectedResult can be validated by visible UI state, message, field behavior, redirect behavior, enabled/disabled state, masking behavior, or other observable outcomes.
- Do not write weak expected results like 'system works correctly', 'login should happen', or 'validation should appear' without specifying what exactly must be observed.
- When generating authentication tests, ensure at least one positive case explicitly expects successful login state and at least one negative case explicitly expects failed login state with an observable rejection condition.

Mandatory Acceptance Criteria Coverage Map:
{pretty_json(mandatory_scenarios)}

Additional generation instructions for acceptance criteria:
- Cover the requirement units above with explicit, observable manual scenarios.
- Treat extracted story sections as requirement sources, not as background-only prose.
- Preserve concrete business data and observable outcomes from the workflow wherever they are explicitly provided.
- Turn explicit transitions, state changes, validations, and control behaviors into dedicated scenarios instead of leaving them implied inside generic success cases.
- Do not treat URLs, headings, or descriptive labels as standalone test cases.
- expectedResult must be a single clear string, not a serialized list.

Workflow Input:
{pretty_json(compact_workflow_input)}

Inferred Existing Resource Reuse Context:
{pretty_json(reuse_context)}

Current Workflow Knowledge Draft:
{pretty_json(current_workflow_knowledge)}

Relevant Approved Workflow Knowledge Artifacts:
{pretty_json(relevant_workflow_knowledge)}
""".strip()


def call_devex_ai(
    endpoint: str,
    token: str,
    prompt: str,
    timeout_sec: int = 120,
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = requests.post(
        endpoint,
        headers=headers,
        data={"query": prompt},
        files=[],
        timeout=timeout_sec,
        verify=False,
    )

    if resp.status_code >= 400:
        raise RuntimeError(f"Devex AI request failed ({resp.status_code}): {resp.text[:500]}")

    content = resp.text.strip()
    parsed = extract_json_block(content)
    if not parsed:
        raise ValueError(f"Devex AI returned non-JSON content: {content[:500]}")

    return parsed


def map_test_type(title: str, expected_result: str, raw_type: str) -> str:
    raw = str(raw_type).strip().lower()
    if raw in {"positive", "negative", "edge"}:
        return raw

    combined = f"{title} {expected_result} {raw}".lower()

    edge_keywords = {
        "edge", "boundary", "limit", "max", "min", "length", "special character",
        "whitespace", "trim", "case sensitivity", "repeated", "duplicate click",
        "copy paste", "long input"
    }
    negative_keywords = {
        "invalid", "error", "reject", "required", "blank", "missing", "incorrect",
        "fail", "not allowed", "unsupported", "validation", "disabled", "warning"
    }

    if any(keyword in combined for keyword in edge_keywords):
        return "edge"
    if any(keyword in combined for keyword in negative_keywords):
        return "negative"
    return "positive"


def infer_interaction_intent(title: str, steps: List[str], expected_result: str) -> Dict[str, str]:
    combined = " ".join([title or "", expected_result or "", *steps]).lower()

    def has_any(*tokens: str) -> bool:
        return any(token in combined for token in tokens)

    input_method = "type"
    if has_any("paste", "copy paste", "copy-paste", "clipboard"):
        input_method = "paste"

    submission_method = "click"
    if has_any("press enter", "hit enter", "enter key", "keyboard submit", "submit using enter"):
        submission_method = "keyboard_enter"

    interaction_pattern = "standard"
    if has_any("multiple rapid click", "multiple clicks", "click multiple times", "repeated click", "duplicate click", "double click"):
        interaction_pattern = "repeat_click"
    elif has_any("whitespace", "leading spaces", "trailing spaces", "with spaces"):
        interaction_pattern = "whitespace"
    elif has_any("special character", "special characters", "symbols"):
        interaction_pattern = "special_characters"

    validation_type = "generic"
    if has_any("required", "mandatory", "empty", "blank"):
        validation_type = "required_field"
    elif has_any("error message", "validation message", "rejected", "denied", "failed"):
        validation_type = "error_message"
    elif has_any("redirect", "landing page", "destination page", "state change", "success state", "navigated"):
        validation_type = "navigation_success"
    elif has_any("masked", "masking", "hidden"):
        validation_type = "masking"

    return {
        "inputMethod": input_method,
        "submissionMethod": submission_method,
        "interactionPattern": interaction_pattern,
        "validationType": validation_type,
    }


def normalize_test_case(
    test_case: Dict[str, Any],
    idx: int,
    id_prefix: str,
    fallback_fields: List[str],
    fallback_steps: List[str],
    fallback_expected: str,
    forced_title: Optional[str] = None,
    forced_type: Optional[str] = None,
) -> Dict[str, Any]:
    title = forced_title or str(test_case.get("title", "")).strip() or f"Test Case {idx}"
    raw_expected = test_case.get("expectedResult", fallback_expected)
    if isinstance(raw_expected, list):
        expected = " ".join(clean_text(x) for x in raw_expected if clean_text(x))
    else:
        expected = str(raw_expected).strip()
    tc_type = forced_type or map_test_type(title, expected, str(test_case.get("type", "")))

    tc_id = str(test_case.get("id", "")).strip() or f"{id_prefix}-{idx:03d}"
    steps = ensure_list_of_strings(test_case.get("steps", fallback_steps))
    fields = ensure_list_of_strings(test_case.get("fields", fallback_fields))

    if not steps:
        steps = ["Open the relevant page", "Perform the workflow action"]
    if not expected:
        expected = "System behaves as expected"

    return {
        "id": tc_id,
        "title": title,
        "type": tc_type,
        "steps": steps,
        "expectedResult": expected,
        "fields": fields,
    }


def generate_fallback_test_cases(workflow_input: Dict[str, Any], workflow_name: str) -> List[Dict[str, Any]]:
    fields = ensure_list_of_strings(workflow_input.get("fields", []))
    steps = ensure_list_of_strings(workflow_input.get("steps", []))
    expected = str(workflow_input.get("expectedResult", "")).strip()
    validations = ensure_list_of_strings(workflow_input.get("observedValidations", []))
    id_prefix = make_test_id_prefix(workflow_name)

    base_steps = steps or ["Open the relevant page", "Perform the workflow action"]
    base_expected = expected or "Workflow completes successfully"

    fallback_cases: List[Dict[str, Any]] = [
        {
            "id": f"{id_prefix}-001",
            "title": f"Verify {workflow_name} with valid input",
            "type": "positive",
            "steps": base_steps,
            "expectedResult": base_expected,
            "fields": fields,
        },
        {
            "id": f"{id_prefix}-002",
            "title": f"Verify UI elements are visible and usable for {workflow_name}",
            "type": "positive",
            "steps": ["Open the relevant page", "Observe all relevant UI elements for the workflow"],
            "expectedResult": "All expected UI elements, labels, fields, and action controls are visible and usable",
            "fields": fields,
        },
        {
            "id": f"{id_prefix}-003",
            "title": f"Verify required field validation for {workflow_name}",
            "type": "negative",
            "steps": ["Open the relevant page", "Leave required fields blank", "Attempt to submit the workflow"],
            "expectedResult": "System shows appropriate validation messages for required fields",
            "fields": fields,
        },
        {
            "id": f"{id_prefix}-004",
            "title": f"Verify invalid field input handling for {workflow_name}",
            "type": "negative",
            "steps": base_steps,
            "expectedResult": "System rejects invalid field values and shows appropriate validation or error messages",
            "fields": fields,
        },
        {
            "id": f"{id_prefix}-005",
            "title": f"Verify edge input behavior for {workflow_name}",
            "type": "edge",
            "steps": base_steps,
            "expectedResult": "System handles boundary and unusual inputs correctly without crashing or allowing invalid behavior",
            "fields": fields,
        },
    ]

    next_idx = 6
    for validation in validations:
        fallback_cases.append(
            {
                "id": f"{id_prefix}-{next_idx:03d}",
                "title": f"Verify validation scenario for {workflow_name} - {next_idx - 5}",
                "type": "negative",
                "steps": base_steps,
                "expectedResult": validation,
                "fields": fields,
            }
        )
        next_idx += 1

    return fallback_cases


def looks_like_acceptance_criterion(text: str) -> bool:
    cleaned = clean_text(text)
    if not cleaned:
        return False
    if re.fullmatch(r"https?://\S+", cleaned, flags=re.IGNORECASE):
        return False
    lowered = cleaned.lower()
    if lowered in {
        "acceptance criteria",
        "application context",
        "entry conditions",
        "generation guidance",
        "prefer",
        "validate",
    }:
        return False
    if lowered.startswith("given "):
        return True
    if lowered.startswith("when ") or lowered.startswith("then "):
        return False
    behavior_tokens = [
        "button",
        "field",
        "form",
        "validation",
        "authenticate",
        "submit",
        "return to",
        "navigate",
        "redirect",
        "open",
        "click",
        "visible",
        "enabled",
        "disabled",
    ]
    return any(token in lowered for token in behavior_tokens)



def _collect_text_blocks(value: Any) -> List[str]:
    blocks: List[str] = []
    if isinstance(value, str) and clean_text(value):
        blocks.append(clean_text(value))
    elif isinstance(value, list):
        blocks.extend(clean_text(str(item)) for item in value if clean_text(str(item)))
    return blocks


def extract_story_sections(workflow_input: Dict[str, Any]) -> Dict[str, List[str]]:
    section_names = [
        "user story",
        "application context",
        "entry conditions",
        "test credentials",
        "approved test data guidance",
        "page elements",
        "screen elements",
        "view elements",
        "behavior rules",
        "validation expectations",
        "transition expectations",
        "pom reuse guidance",
        "acceptance criteria",
        "generation guidance",
        "prefer",
    ]
    raw_blocks: List[str] = []
    for key in (
        "description",
        "userStory",
        "observedExpectedResult",
        "observedPreconditions",
        "observedSteps",
        "observedValidations",
        "acceptanceCriteria",
        "acceptance_criteria",
        "generationGuidance",
    ):
        raw_blocks.extend(_collect_text_blocks(workflow_input.get(key)))
    for parent_key in ("externalContext", "metadata"):
        parent = workflow_input.get(parent_key)
        if not isinstance(parent, dict):
            continue
        for key in (
            "description",
            "userStory",
            "acceptanceCriteria",
            "acceptance_criteria",
            "generationGuidance",
            "validationExpectations",
            "transitionExpectations",
            "behaviorRules",
            "pomReuseGuidance",
            "approvedTestDataGuidance",
            "applicationContext",
            "loginPageElements",
            "entryConditions",
            "testCredentials",
        ):
            raw_blocks.extend(_collect_text_blocks(parent.get(key)))

    combined_text = "\n".join(block for block in raw_blocks if clean_text(block))
    combined_text = re.sub(r"\s*\n\s*", "\n", combined_text)
    combined_text = re.sub(r"[ \t]+", " ", combined_text).strip()

    sections: Dict[str, List[str]] = {name: [] for name in section_names}
    if not combined_text:
        return sections

    escaped_names = [re.escape(name) for name in section_names]
    header_pattern = re.compile(rf"(?i)({'|'.join(escaped_names)})\b")
    matches = list(header_pattern.finditer(combined_text))

    for idx, match in enumerate(matches):
        name = match.group(1).lower()
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(combined_text)
        fragment = combined_text[start:end].strip(" :-\n\t")
        if fragment:
            sections[name].append(clean_text(fragment))

    deduped_sections: Dict[str, List[str]] = {}
    for name, values in sections.items():
        seen = set()
        deduped: List[str] = []
        for value in values:
            key = value.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(value)
        deduped_sections[name] = deduped
    return deduped_sections


def parse_acceptance_criteria(workflow_input: Dict[str, Any]) -> List[str]:
    raw_candidates: List[str] = []

    for key in ("acceptanceCriteria", "acceptance_criteria", "criteria"):
        value = workflow_input.get(key)
        if isinstance(value, list):
            raw_candidates.extend(str(x).strip() for x in value if str(x).strip())
        elif isinstance(value, str) and value.strip():
            raw_candidates.extend(line.strip(" -\t") for line in re.split(r"\n+", value) if line.strip())

    for parent_key in ("externalContext", "metadata"):
        parent = workflow_input.get(parent_key)
        if not isinstance(parent, dict):
            continue
        for key in ("acceptanceCriteria", "acceptance_criteria", "criteria"):
            value = parent.get(key)
            if isinstance(value, list):
                raw_candidates.extend(str(x).strip() for x in value if str(x).strip())
            elif isinstance(value, str) and value.strip():
                raw_candidates.extend(line.strip(" -\t") for line in re.split(r"\n+", value) if line.strip())

    story_sections = extract_story_sections(workflow_input)
    for section_value in story_sections.get("acceptance criteria", []):
        cleaned_section = clean_text(re.sub(r"^acceptance criteria\s*", "", section_value, flags=re.IGNORECASE))
        if cleaned_section:
            parts = re.split(r"(?=Given\s)", cleaned_section, flags=re.IGNORECASE)
            raw_candidates.extend(part.strip() for part in parts if part.strip())

    seen = set()
    normalized: List[str] = []
    pending_when_then = False
    for criterion in raw_candidates:
        criterion = re.sub(r"^\d+[\.)]\s*", "", criterion).strip()
        if "acceptance criteria" in criterion.lower():
            parts = re.split(r"(?=Given\s)", criterion, flags=re.IGNORECASE)
            for part in parts:
                part = clean_text(re.sub(r"^acceptance criteria\s*", "", part, flags=re.IGNORECASE))
                if part:
                    raw_candidates.append(part)
            continue
        lowered = criterion.lower()
        if lowered.startswith("when ") or lowered.startswith("then "):
            pending_when_then = True
            continue
        if lowered.startswith("given "):
            pending_when_then = False
        if pending_when_then and not lowered.startswith("given "):
            continue
        if not looks_like_acceptance_criterion(criterion):
            continue
        key = criterion.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(criterion)
    return normalized


def criterion_signature(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def extract_requirement_units(workflow_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    requirements: List[Dict[str, Any]] = []

    acceptance_criteria = parse_acceptance_criteria(workflow_input)
    for idx, criterion in enumerate(acceptance_criteria, start=1):
        requirements.append({
            "id": f"AC{idx}",
            "source": "acceptance_criteria",
            "text": criterion,
            "signature": criterion_signature(criterion),
        })

    generic_sections = [
        "validation expectations",
        "transition expectations",
        "generation guidance",
        "behavior rules",
        "entry conditions",
        "test credentials",
        "approved test data guidance",
        "page elements",
        "screen elements",
        "view elements",
        "pom reuse guidance",
        "application context",
        "user story",
    ]
    story_sections = extract_story_sections(workflow_input)
    next_idx = len(requirements) + 1
    seen_signatures = {item["signature"] for item in requirements}

    for section_name in generic_sections:
        for item in story_sections.get(section_name, []):
            cleaned_item = clean_text(re.sub(rf"^{re.escape(section_name)}\s*", "", item, flags=re.IGNORECASE))
            if not cleaned_item:
                continue
            sig = criterion_signature(cleaned_item)
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            requirements.append({
                "id": f"REQ{next_idx}",
                "source": section_name.replace(" ", "_"),
                "text": cleaned_item,
                "signature": sig,
            })
            next_idx += 1
    return requirements



def test_case_signature(tc: Dict[str, Any]) -> str:
    combined = " ".join(
        [
            str(tc.get("title", "")),
            str(tc.get("expectedResult", "")),
            " ".join(ensure_list_of_strings(tc.get("steps", []))),
            " ".join(ensure_list_of_strings(tc.get("fields", []))),
        ]
    )
    return criterion_signature(combined)


def criterion_is_covered(criterion: str, test_cases: List[Dict[str, Any]]) -> bool:
    criterion_key = criterion_signature(criterion)
    criterion_tokens = {token for token in criterion_key.split() if len(token) > 2}
    if not criterion_tokens:
        return False

    for tc in test_cases:
        candidate_key = test_case_signature(tc)
        candidate_tokens = set(candidate_key.split())
        if criterion_key and criterion_key in candidate_key:
            return True
        overlap = criterion_tokens & candidate_tokens
        if len(overlap) >= max(2, min(len(criterion_tokens), 4)):
            return True
    return False


def normalize_manual_test(generated: Dict[str, Any], workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    workflow_name = str(
        workflow_input.get("workflowName")
        or generated.get("workflowName")
        or "Workflow"
    ).strip()

    resource_files = generated.get("resourceFiles")
    if not isinstance(resource_files, list) or not resource_files:
        resource_files = workflow_input.get("resourceFiles", [])

    inferred_reuse = workflow_input.get("inferredReuseContext") or infer_workflow_reuse_context(workflow_input)
    if isinstance(inferred_reuse, dict):
        authoritative_files = inferred_reuse.get("authoritativeResourceFiles") or inferred_reuse.get("inferredRelevantResourceFiles") or []
        if isinstance(authoritative_files, list):
            existing = {str(x).replace("\\", "/").strip() for x in resource_files if str(x).strip()}
            for rel_path in authoritative_files:
                normalized_path = str(rel_path).replace("\\", "/").strip()
                if normalized_path and normalized_path not in existing:
                    resource_files.append(normalized_path)
                    existing.add(normalized_path)

    preconditions = ensure_list_of_strings(
        generated.get("preconditions", workflow_input.get("preconditions", []))
    )

    fallback_fields = ensure_list_of_strings(workflow_input.get("fields", []))
    fallback_steps = ensure_list_of_strings(workflow_input.get("steps", []))
    fallback_expected = str(workflow_input.get("expectedResult", "")).strip()
    id_prefix = make_test_id_prefix(workflow_name)

    raw_cases = generated.get("testCases")
    normalized_cases: List[Dict[str, Any]] = []

    if isinstance(raw_cases, list):
        for idx, tc in enumerate(raw_cases, start=1):
            if not isinstance(tc, dict):
                continue
            normalized_cases.append(
                normalize_test_case(
                    test_case=tc,
                    idx=idx,
                    id_prefix=id_prefix,
                    fallback_fields=fallback_fields,
                    fallback_steps=fallback_steps,
                    fallback_expected=fallback_expected,
                )
            )

    if not normalized_cases:
        normalized_cases = generate_fallback_test_cases(workflow_input, workflow_name)

    requirement_units = extract_requirement_units(workflow_input)
    missing_requirements = [
        requirement["text"]
        for requirement in requirement_units
        if not criterion_is_covered(requirement["text"], normalized_cases)
    ]
    if missing_requirements:
        logger.warning(
            "Manual tests for %s do not clearly cover %d extracted requirement(s): %s",
            workflow_name,
            len(missing_requirements),
            "; ".join(missing_requirements[:10]),
        )

    seen_ids = set()
    deduped_cases: List[Dict[str, Any]] = []
    seen_signatures = set()

    normalized_id_prefix = clean_text(str(workflow_input.get("testIdentifierPrefix") or generated.get("testIdentifierPrefix") or workflow_input.get("feature") or workflow_name)).upper()
    normalized_id_prefix = re.sub(r"[^A-Z0-9]+", "_", normalized_id_prefix).strip("_") or id_prefix

    for idx, tc in enumerate(normalized_cases, start=1):
        tc_id = str(tc.get("id", "")).strip()
        if not tc_id or tc_id in seen_ids:
            tc["id"] = f"{normalized_id_prefix}_{idx:03d}"
        seen_ids.add(tc["id"])

        signature = (
            tc["title"].strip().lower(),
            tc["type"].strip().lower(),
            tuple(s.strip().lower() for s in tc["steps"]),
            tc["expectedResult"].strip().lower(),
            tuple(f.strip().lower() for f in tc["fields"]),
        )

        if signature not in seen_signatures:
            seen_signatures.add(signature)
            deduped_cases.append(tc)

    explicit_prefix = clean_text(str(workflow_input.get("testIdentifierPrefix") or generated.get("testIdentifierPrefix", "")))
    explicit_feature = clean_text(str(workflow_input.get("feature") or generated.get("feature", "")))
    if explicit_prefix:
        resolved_feature = explicit_prefix
    elif explicit_feature and len(re.findall(r"[A-Za-z0-9]+", explicit_feature)) <= 3:
        resolved_feature = explicit_feature
    else:
        resolved_feature = workflow_name

    return {
        "workflowName": workflow_name,
        "feature": resolved_feature,
        "applicationCode": workflow_input.get("applicationCode") or generated.get("applicationCode", ""),
        "testIdentifierPrefix": explicit_prefix,
        "resourceFiles": [str(x).strip() for x in resource_files if str(x).strip()],
        "preconditions": preconditions,
        "testCases": [
            {
                "id": case["id"],
                "title": case["title"],
                "type": case["type"],
                "steps": case["steps"],
                "expectedResult": case["expectedResult"],
                "fields": case["fields"],
            }
            for case in deduped_cases
        ],
    }


def process_workflow_file(config: Dict[str, Any], input_path: Path) -> None:
    workflow_input = load_json(input_path)
    workflow_input["inferredReuseContext"] = infer_workflow_reuse_context(workflow_input)
    gc = config["generation_control"]
    ai_cfg = config["ai"]

    wf_name = str(workflow_input.get("workflowName", input_path.stem))
    wf_slug = slugify(wf_name)

    if wf_slug in set(gc.get("excluded_workflows", [])):
        logger.info("Skipped excluded workflow: %s", wf_name)
        return

    output_dir = BASE_DIR / config["manual_tests_output_dir"]
    output_path = output_dir / f"{wf_slug}.json"

    if output_path.exists() and not gc.get("overwrite_manual_tests", False):
        logger.info("Manual test already exists (overwrite=false): %s", output_path)
        return

    if not ai_cfg.get("enabled", False):
        raise RuntimeError("AI is disabled in page_model_config.json.")

    endpoint = ai_cfg.get("endpoint", "").strip()
    token = get_ai_token(ai_cfg)

    if not endpoint or not token:
        raise RuntimeError("Missing ai.endpoint or AI token.")

    workflow_context = {
        "reuse_context": workflow_input.get("inferredReuseContext") or infer_workflow_reuse_context(workflow_input),
        "current_workflow_knowledge": build_workflow_knowledge_context(workflow_input),
        "relevant_workflow_knowledge": discover_relevant_workflow_knowledge(workflow_input),
    }

    prompt = build_prompt(workflow_input)
    generated = call_devex_ai(
        endpoint=endpoint,
        token=token,
        prompt=prompt,
    )
    reviewed = call_devex_ai(
        endpoint=endpoint,
        token=token,
        prompt=build_manual_review_prompt(generated, workflow_context),
    )
    final_json = normalize_manual_test(reviewed or generated, workflow_input)
    is_valid, validation_message = validate_manual_content(final_json, workflow_context)
    if validation_message:
        refinement_prompt = build_manual_refiner_prompt(generated, final_json, workflow_context)
        refined = call_devex_ai(
            endpoint=endpoint,
            token=token,
            prompt=refinement_prompt,
        )
        final_json = normalize_manual_test(refined or final_json, workflow_input)
        is_valid, validation_message = validate_manual_content(final_json, workflow_context)
    if not is_valid:
        raise ValueError(f"Generated invalid manual content for {input_path.name}: {validation_message}")
    if validation_message:
        logger.warning("Manual content review warnings for %s: %s", input_path.name, validation_message)
    save_json(output_path, final_json)

    logger.info("Manual test JSON generated: %s", output_path)


def main():
    config = validate_config(load_config())

    workflow_input_dir = BASE_DIR / config["workflow_input_dir"]
    if not workflow_input_dir.exists():
        raise FileNotFoundError(f"workflow_inputs directory not found: {workflow_input_dir}")

    workflow_files = sorted(workflow_input_dir.glob("*.json"))
    if not workflow_files:
        logger.info("No workflow input JSON files found in: %s", workflow_input_dir)
        return

    logger.info("Found %d workflow input files", len(workflow_files))
    for wf in workflow_files:
        try:
            process_workflow_file(config, wf)
        except Exception as exc:
            logger.error("Failed for %s: %s", wf.name, exc)


if __name__ == "__main__":
    main()