#!/usr/bin/env python3
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from scripts.generate_robot_from_manual import build_manual_review_prompt, validate_manual_content
    from scripts.workflow_context import infer_workflow_reuse_context
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from scripts.generate_robot_from_manual import build_manual_review_prompt, validate_manual_content
    from scripts.workflow_context import infer_workflow_reuse_context

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


def build_prompt(workflow_input: Dict[str, Any]) -> str:
    reuse_context = infer_workflow_reuse_context(workflow_input)
    acceptance_criteria = parse_acceptance_criteria(workflow_input)
    mandatory_scenarios = []
    for idx, criterion in enumerate(acceptance_criteria, start=1):
        mandatory_scenarios.append({
            "id": f"AC{idx}",
            "criterion": criterion,
            "mustGenerateAtLeastOneTest": True,
        })
    return f"""
You are AI Layer 1: a senior QA test designer operating inside a multi-layer AI-assisted automation framework.
Your output is a reviewable manual-test artifact that will feed downstream keyword/resource generation, Robot generation, and additional AI review and governance layers.

Your goal is not just to list tests, but to produce high-signal manual tests with explicit observable outcomes so later AI layers can generate strong assertions and the exact reusable page keywords needed for approved scenarios.

Analyze the workflow input and generate a practical manual test suite JSON.

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
3. Use approved elements to infer realistic UI actions, visible validations, control-state checks, navigation checks, and field-level scenarios.
4. Use user-supplied testData and workflow context to infer positive, negative, and edge data combinations.
5. Use expected observations and validations to derive concrete observable expectedResult values.
6. Do not limit generation to only explicitly listed workflow steps if the approved page elements clearly support additional meaningful scenarios.
7. Never generate a manual test, step, field reference, validation, or expected result around an element that is not present in approvedElements unless that behavior is explicitly stated in the workflow input itself (for example in observedSteps, observedValidations, preconditions, fields, or user story text).
8. If an element was not approved, treat it as out of scope and do not infer new tests from it.

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
12. Acceptance criteria involving shared or upstream controls must still generate tests even when those controls are not newly extracted on the current page.
13. For navigation criteria such as Back button or Home button returning to a previous page, generate explicit navigation tests instead of replacing them with generic exploratory cases.
14. Prioritize mandatory acceptance-criteria coverage before adding additional exploratory edge cases.

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
- For positive authentication/navigation cases, expectedResult should explicitly mention authenticated state, landing page, redirect, dashboard/home visibility, URL change, or equivalent observable outcome.
- For negative authentication or validation cases, expectedResult should explicitly mention observable rejection, validation messaging, no navigation, protected-area denial, disabled submission, or continued presence of the login/form state where applicable.
- For edge interaction scenarios such as Enter key, repeated clicking, whitespace handling, copy-paste, and long input, expectedResult should describe the exact observable behavior that automation must verify.
- Avoid producing shallow variants that differ only in wording but not in observable intent.
- Prefer tests whose expectedResult can be validated by visible UI state, message, field behavior, redirect behavior, enabled/disabled state, masking behavior, or other observable outcomes.
- Do not write weak expected results like 'system works correctly', 'login should happen', or 'validation should appear' without specifying what exactly must be observed.
- When generating authentication tests, ensure at least one positive case explicitly expects successful login state and at least one negative case explicitly expects failed login state with an observable rejection condition.

Mandatory Acceptance Criteria Coverage Map:
{pretty_json(mandatory_scenarios)}

Additional generation instructions for acceptance criteria:
- Generate at least one explicit test case for each mandatory acceptance criterion above.
- If a criterion mentions Back button, Home button, Forgot Password, or other shared/upstream controls, still generate the scenario even if that control is reused from another approved resource.
- Do not omit explicit navigation scenarios because of missing local extraction.
- Do not treat URLs, headings, or descriptive labels as standalone test cases.
- expectedResult must be a single clear string, not a serialized list.

Workflow Input:
{pretty_json(workflow_input)}

Inferred Existing Resource Reuse Context:
{pretty_json(reuse_context)}
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
    elif has_any("error message", "validation message", "invalid credentials", "authentication failed", "rejected", "denied"):
        validation_type = "error_message"
    elif has_any("redirect", "dashboard", "home page", "landing page", "successful login", "logged in"):
        validation_type = "navigation_success"
    elif has_any("masked", "masking", "password hidden"):
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

    normalized = {
        "id": tc_id,
        "title": title,
        "type": tc_type,
        "steps": steps,
        "expectedResult": expected,
        "fields": fields,
    }
    normalized["interactionIntent"] = infer_interaction_intent(title, steps, expected)
    return normalized


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
        "login",
        "home page",
        "back",
        "forgot password",
        "username",
        "password",
        "validation",
        "authenticate",
        "return to",
        "open",
        "click",
    ]
    return any(token in lowered for token in behavior_tokens)



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

    seen = set()
    normalized: List[str] = []
    for criterion in raw_candidates:
        criterion = re.sub(r"^\d+[\.)]\s*", "", criterion).strip()
        if not looks_like_acceptance_criterion(criterion):
            continue
        key = criterion.lower()
        if key not in seen:
            seen.add(key)
            normalized.append(criterion)
    return normalized


def criterion_signature(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


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

    lowered = criterion.lower()
    special_patterns = []
    if "back button" in lowered and "home page" in lowered:
        special_patterns.append({"back", "button", "home", "page"})
    if "home button" in lowered and "home page" in lowered:
        special_patterns.append({"home", "button", "page"})
    if "forgot password" in lowered:
        special_patterns.append({"forgot", "password"})

    for tc in test_cases:
        candidate_key = test_case_signature(tc)
        candidate_tokens = set(candidate_key.split())
        if criterion_key and criterion_key in candidate_key:
            return True
        overlap = criterion_tokens & candidate_tokens
        if len(overlap) >= max(2, min(len(criterion_tokens), 4)):
            return True
        for pattern in special_patterns:
            if pattern.issubset(candidate_tokens):
                return True
    return False


def build_required_case_from_criterion(
    criterion: str,
    idx: int,
    id_prefix: str,
    fallback_fields: List[str],
) -> Dict[str, Any]:
    text = clean_text(criterion)
    lowered = text.lower()
    fields = list(fallback_fields)
    steps = ["Open the relevant page or workflow context", text]
    expected = text
    tc_type = "positive"
    title = text

    if "back button" in lowered and "home page" in lowered:
        fields = sorted(set(fields + ["back_button"]))
        title = "Verify Back button on Login page returns user to Home page"
        steps = [
            "Open the Login page from the Home page",
            "Click the Back button on the Login page",
        ]
        expected = "The user is returned to the Home page in guest state and the Login page is no longer active."
        tc_type = "positive"
    elif "home button" in lowered and "home page" in lowered:
        fields = sorted(set(fields + ["home_button"]))
        title = "Verify Home button on Login page returns user to Home page"
        steps = [
            "Open the Login page from the Home page",
            "Click the Home button on the Login page",
        ]
        expected = "The user is returned to the Home page in guest state and the Login page is no longer active."
        tc_type = "positive"
    elif "forgot password" in lowered:
        fields = sorted(set(fields + ["forgot_password_link"]))
        title = "Verify Forgot Password navigation opens recovery flow from Login page"
        steps = [
            "Open the Login page from the Home page",
            "Click Forgot Password on the Login page",
        ]
        expected = "The supported password recovery destination or recovery workflow opens successfully."
        tc_type = "positive"
    elif any(token in lowered for token in ["invalid", "fail", "error", "remain unauthenticated", "should not proceed"]):
        tc_type = "negative"
    elif any(token in lowered for token in ["masked", "validation", "required", "blank", "empty"]):
        tc_type = "negative" if any(token in lowered for token in ["required", "blank", "empty"]) else "positive"

    return normalize_test_case(
        test_case={
            "id": f"{id_prefix}_{idx:03d}",
            "title": title,
            "type": tc_type,
            "steps": steps,
            "expectedResult": expected,
            "fields": fields,
        },
        idx=idx,
        id_prefix=id_prefix,
        fallback_fields=fallback_fields,
        fallback_steps=steps,
        fallback_expected=expected,
        forced_title=title,
        forced_type=tc_type,
    )


def normalize_manual_test(generated: Dict[str, Any], workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    workflow_name = str(
        workflow_input.get("workflowName")
        or generated.get("workflowName")
        or "Workflow"
    ).strip()

    resource_files = generated.get("resourceFiles")
    if not isinstance(resource_files, list) or not resource_files:
        resource_files = workflow_input.get("resourceFiles", [])

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

    acceptance_criteria = parse_acceptance_criteria(workflow_input)
    missing_required_cases: List[Dict[str, Any]] = []
    next_idx = len(normalized_cases) + 1
    for criterion in acceptance_criteria:
        if not criterion_is_covered(criterion, normalized_cases + missing_required_cases):
            missing_required_cases.append(
                build_required_case_from_criterion(
                    criterion=criterion,
                    idx=next_idx,
                    id_prefix=id_prefix,
                    fallback_fields=fallback_fields,
                )
            )
            next_idx += 1

    if missing_required_cases:
        logger.info(
            "Added %d acceptance-criteria coverage test case(s) for workflow %s",
            len(missing_required_cases),
            workflow_name,
        )
        normalized_cases.extend(missing_required_cases)

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
            tuple(sorted((tc.get("interactionIntent") or {}).items())),
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
                "interactionIntent": case.get("interactionIntent", infer_interaction_intent(case["title"], case["steps"], case["expectedResult"])),
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

    prompt = build_prompt(workflow_input)
    generated = call_devex_ai(
        endpoint=endpoint,
        token=token,
        prompt=prompt,
    )
    reviewed = call_devex_ai(
        endpoint=endpoint,
        token=token,
        prompt=build_manual_review_prompt(generated),
    )
    final_json = normalize_manual_test(reviewed or generated, workflow_input)
    is_valid, validation_message = validate_manual_content(final_json)
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