import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Set

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

import requests
import urllib3

try:
    from scripts.workflow_knowledge import build_workflow_knowledge_context, discover_relevant_workflow_knowledge
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from scripts.workflow_knowledge import build_workflow_knowledge_context, discover_relevant_workflow_knowledge

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "page_model_config.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("generate_robot_from_manual")

def load_prompt_markdown(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def slugify(text: str) -> str:
    text = clean_text(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "module"


def compact_code(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", clean_text(text)).upper()


def normalize_feature_code(text: str) -> str:
    cleaned = clean_text(text).upper()
    cleaned = re.sub(r"[^A-Z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def derive_fallback_feature_code(manual_data: dict) -> str:
    raw_prefix = compact_code(str(manual_data.get("testIdentifierPrefix", "")))
    if raw_prefix:
        return raw_prefix[:16]

    for candidate in [
        str(manual_data.get("feature", "")),
        str(manual_data.get("workflowName", "")),
        str(manual_data.get("module", "")),
    ]:
        code = compact_code(candidate)
        if code:
            return code[:16]
    return "FLOW"


def resolve_test_identifier_policy(manual_data: dict) -> dict:
    app_code = compact_code(str(manual_data.get("applicationCode", "")))[:8] or "APP"
    raw_prefix = clean_text(str(manual_data.get("testIdentifierPrefix", "")))
    normalized_prefix = normalize_feature_code(raw_prefix)
    feature_code = normalized_prefix[:20] if normalized_prefix else derive_fallback_feature_code(manual_data)
    family_prefix = f"{app_code}-{feature_code}"
    return {
        "app_code": app_code,
        "feature_code": feature_code,
        "family_prefix": family_prefix,
        "example_test_id": f"{family_prefix}01",
        "example_test_name": f"AUT-{family_prefix}01: Verify workflow behavior",
    }


def derive_standard_test_identifier(manual_data: dict) -> dict:
    return resolve_test_identifier_policy(manual_data)

def get_ai_token(ai_cfg: dict) -> str:
    token = str(ai_cfg.get("token", "")).strip()
    if token:
        return token

    token_env_var = str(ai_cfg.get("token_env_var", "")).strip()
    if token_env_var:
        return os.getenv(token_env_var, "").strip()

    return ""


def validate_config(config: dict) -> dict:
    config["pom_output_dir"] = str(config.get("pom_output_dir", "pom_pages"))
    config["manual_tests_output_dir"] = str(config.get("manual_tests_output_dir", "manual_tests"))
    config["robot_tests_output_dir"] = str(config.get("robot_tests_output_dir", "tests"))

    if "generation_control" not in config:
        config["generation_control"] = {}

    gc = config["generation_control"]
    gc["overwrite_robot_tests"] = bool(gc.get("overwrite_robot_tests", False))
    gc["excluded_modules"] = [slugify(x) for x in gc.get("excluded_modules", []) if str(x).strip()]
    gc["excluded_manual_files"] = [str(x).strip().lower() for x in gc.get("excluded_manual_files", []) if str(x).strip()]

    if "ai" not in config:
        config["ai"] = {}

    ai = config["ai"]
    ai["enabled"] = bool(ai.get("enabled", True))
    ai["endpoint"] = str(ai.get("endpoint", "")).strip()
    ai["temperature"] = float(ai.get("temperature", 0.2))
    ai["timeout_seconds"] = int(ai.get("timeout_seconds", 120))
    ai["verify_ssl"] = bool(ai.get("verify_ssl", False))

    return config

def extract_keywords_from_resource(resource_text: str) -> List[Dict]:
    lines = resource_text.splitlines()
    in_keywords = False
    keywords = []
    current = None

    for line in lines:
        stripped = line.strip()

        if stripped.lower() == "*** keywords ***":
            in_keywords = True
            current = None
            continue

        if stripped.startswith("***") and stripped.lower() != "*** keywords ***":
            in_keywords = False
            current = None
            continue

        if not in_keywords:
            continue

        if not stripped:
            if current and current.get("body"):
                current["body"].append("")
            continue

        if not line.startswith((" ", "\t")):
            current = {"name": stripped, "args": [], "body": []}
            keywords.append(current)
            continue

        if not current:
            continue

        if stripped.startswith("[Arguments]"):
            parts = re.split(r"\s{2,}|\t+", stripped)
            current["args"] = parts[1:] if len(parts) > 1 else []
            continue

        current["body"].append(line.rstrip())

    while keywords and keywords[-1].get("body") == [""]:
        keywords[-1]["body"] = []

    for keyword in keywords:
        body = keyword.get("body", [])
        while body and body[-1] == "":
            body.pop()
        keyword["body"] = body

    return keywords

def extract_variables_from_resource(resource_text: str) -> List[Dict]:
    lines = resource_text.splitlines()
    in_variables = False
    variables = []

    for line in lines:
        stripped = line.strip()

        if stripped.lower() == "*** variables ***":
            in_variables = True
            continue

        if stripped.startswith("***") and stripped.lower() != "*** variables ***":
            in_variables = False
            continue

        if not in_variables or not stripped:
            continue

        parts = re.split(r"\s{2,}|\t+", stripped, maxsplit=1)
        if len(parts) == 2 and parts[0].startswith("${") and parts[0].endswith("}"):
            variables.append({
                "name": parts[0][2:-1].strip(),
                "value": parts[1].strip(),
            })

    return variables


def parse_resource_file(resource_path: Path) -> Dict:
    text = resource_path.read_text(encoding="utf-8")
    rel_path = str(resource_path.relative_to(BASE_DIR)).replace("\\", "/")
    resource_type = "common" if rel_path.startswith("resources/") else "page"
    return {
        "file": rel_path,
        "type": resource_type,
        "variables": extract_variables_from_resource(text),
        "keywords": extract_keywords_from_resource(text),
        "retrieved_keyword_names": [clean_text(str(item.get("name", ""))) for item in extract_keywords_from_resource(text) if clean_text(str(item.get("name", "")))],
        "retrieved_variable_names": [clean_text(str(item.get("name", ""))) for item in extract_variables_from_resource(text) if clean_text(str(item.get("name", "")))],
        "source": text[:12000]
    }

def build_prompt(manual_data: dict, resource_context: List[Dict]) -> str:
    prompt_manual_data = json.loads(json.dumps(manual_data))
    rag_context = prompt_manual_data.get("ragContext", {}) if isinstance(prompt_manual_data.get("ragContext"), dict) else {}
    current_workflow_knowledge = build_workflow_knowledge_context(prompt_manual_data)
    relevant_workflow_knowledge = discover_relevant_workflow_knowledge(prompt_manual_data)
    if isinstance(prompt_manual_data.get("fields"), list):
        prompt_manual_data["fields"] = [
            field for field in prompt_manual_data["fields"]
            if isinstance(field, dict) and any(clean_text(str(field.get(k, ""))) for k in ("name", "label", "type"))
        ]

    retrieved_common_keywords = sorted({
        clean_text(str(keyword.get("name", "")))
        for resource in resource_context
        if resource.get("type") == "common"
        for keyword in resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    })
    retrieved_page_keywords = sorted({
        clean_text(str(keyword.get("name", "")))
        for resource in resource_context
        if resource.get("type") == "page"
        for keyword in resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    })
    retrieved_page_variables = sorted({
        clean_text(str(variable.get("name", "")))
        for resource in resource_context
        if resource.get("type") == "page"
        for variable in resource.get("variables", [])
        if clean_text(str(variable.get("name", "")))
    })

    identifier_policy = derive_standard_test_identifier(prompt_manual_data)
    allowed_builtin_keywords, allowed_selenium_keywords = get_framework_keyword_catalog()

    payload = {
        "manual_test": prompt_manual_data,
        "resource_context": resource_context,
        "retrieved_common_keywords": retrieved_common_keywords,
        "retrieved_page_keywords": retrieved_page_keywords,
        "retrieved_page_variables": retrieved_page_variables,
        "allowed_builtin_keywords": sorted(allowed_builtin_keywords),
        "allowed_selenium_keywords": sorted(allowed_selenium_keywords),
        "resource_import_prefix": "../pom_pages/",
        "common_resource_hint": "../resources/common_keywords.resource",
        "identifier_policy": identifier_policy,
        "current_workflow_knowledge": current_workflow_knowledge,
        "relevant_workflow_knowledge": relevant_workflow_knowledge,
        "rag_context": rag_context,
    }

    return (
        "You are AI Layer 3: an expert Robot Framework automation engineer working in a strict POM-based framework.\n"
        "Generate exactly one valid Robot Framework .robot test suite file.\n\n"
        "Framework architecture rules:\n"
        "- Page object resource files are the single source of truth for locators, reusable UI action keywords, page-open keywords, setup/teardown keywords, validation keywords, and reusable test data variables.\n"
        "- Shared framework behavior belongs in common resources such as ../resources/common_keywords.resource. This includes browser lifecycle, generic navigation, generic waits, and generic interaction wrappers.\n"
        "- The generated .robot suite must remain thin and contain only suite-level settings and executable test cases.\n"
        "- Any navigation/open-page/wait-for-page-ready keyword already belongs in the resource layer and must be reused from there.\n"
        "- Any reusable test data such as usernames, passwords, URLs, paths, expected validation text, long strings, invalid variants, SQL injection payloads, whitespace variants, and boundary values belongs in the resource layer, not in the test suite.\n"
        "- Every generated test must align with the manual test title, steps, and expectedResult; do not skip the expected validation.\n"
        "- Prefer resource validation keywords and resource variables whenever the resource file suggests they exist or should be reused.\n\n"
        "Mandatory output rules:\n"
        "- Use only the provided resource files and the shared common resource hint.\n"
        "- Always import ../resources/common_keywords.resource in the suite Settings section.\n"
        "- Also import the page resource files listed in manual_test.resourceFiles.\n"
        "- Use provided keyword names and variable names from resource_context wherever possible.\n"
        "- Treat the final approved page resource files in resource_context as the authoritative source of truth for page variables and page keywords. Prefer those exact approved names over inferred, legacy, metadata-derived, or paraphrased alternatives.\n"
        "- Prefer existing keywords from resource_context over inventing new ones.\n"
        "- Never invent or define new custom keywords in the generated test suite. User-created/custom wrapper intelligence belongs to approved upstream resource files, not to AI-generated suite code.\n"
        "- If a needed behavior is not already available through imported resource_context or approved framework keywords, compose the test only from existing approved keywords; do not create a new abstraction name.\n"
        "- Treat resource_context as including both page-specific resources and shared/common resources. Use common/shared keywords for generic browser lifecycle, navigation, waiting, clicking, and text entry behaviors, and avoid duplicating them in suite logic.\n"
        "- Treat retrieved_common_keywords, retrieved_page_keywords, retrieved_page_variables, current_workflow_knowledge, relevant_workflow_knowledge, and rag_context as retrieved context. Reuse them explicitly instead of free-form invention.\n"
        "- current_workflow_knowledge is the concise approved-memory draft for the current workflow assembled from current workflow context plus approved artifacts already available. Use it to keep the suite aligned with the workflow's business journey, ownership boundaries, and approved test intent.\n"
        "- relevant_workflow_knowledge is approved cumulative workflow memory created from approved user story context, approved element extraction, approved manual tests, approved resource keywords, and approved automation from prior workflows. Consult it before creating navigation/setup assumptions for the current suite.\n"
        "- If relevant_workflow_knowledge shows that an upstream workflow already owns navigation, page opening, state validation, or reusable controls needed by this workflow, reuse that approved upstream knowledge and imported upstream resources instead of inventing new suite abstractions.\n"
        "- Shared/common resource keywords take priority over raw SeleniumLibrary keywords for generic interactions. If a shared helper such as Open Browser Session, Close Browser Session, Open Browser To Url, Go To Url, Wait For Element To Be Ready, Click When Ready, or Input Text When Ready exists in retrieved_common_keywords, use that helper rather than direct SeleniumLibrary calls.\n"
        "- If a page keyword or page variable already exists in retrieved_page_keywords or retrieved_page_variables, preserve and reuse it instead of creating a parallel name.\n"
        "- Prefer common/shared wrapper keywords for text and password entry. If no explicit password-specific shared helper exists, use the common/shared text-entry wrapper that already exists rather than raw SeleniumLibrary Input Password.\n"
        "- Include *** Settings *** and *** Test Cases *** sections.\n"
        "- Do NOT include a *** Variables *** section in the generated .robot file.\n"
        "- Use compact formatting: no blank lines inside the Settings section, no blank line after *** Test Cases *** (the first test case must start immediately on the next line), exactly one blank line between major sections, and exactly one blank line between test cases.\n"
        "- Every generated test case name must start with AUT- and follow the pattern AUT-<APPCODE>-<FEATURECODE><NN>: <Title>.\n"
        "- Use identifier_policy from the input JSON as the authoritative naming guide for <APPCODE>, <FEATURECODE>, and example formats.\n"
        "- Follow a concise enterprise-style identifier standard: short stable application code, short stable feature code, then a two-digit sequence. Keep identifiers readable and bounded in length.\n"
        "- <FEATURECODE> must be a compact semantic code, typically one or two meaningful tokens, uppercase alphanumeric with optional underscores only when needed for readability. Do not derive it by concatenating the full workflow or story title.\n"
        "- Every generated test case must include a [Tags] line immediately after the test case name. Keep tags minimal: only the testcase id tag and the scenario type tag, for example [Tags]    WT-LOGIN01    positive.\n"
        "- If the workflow input does not explicitly provide a short feature tag, derive a concise semantic feature code/tag from the workflow feature or workflow intent. Never use the full user-story sentence or full workflow title as a tag-like feature code.\n"
        "- <APPCODE> should be the uppercase abbreviated application code from the input. Use a short stable abbreviation.\n"
        "- Do not add extra tags such as AUT, ui, validation, security, accessibility, or feature-name tags.\n"
        "- Do NOT include a *** Keywords *** section in the generated .robot file. The suite must not define AI-created helper keywords.\n"
        "- Do NOT define ad hoc page-open, page-ready, navigation, authentication, or wrapper keywords in the suite if the resource layer already provides page-open/navigation capability.\n"
        "- Prefer shared/common resource keywords exposed in resource_context for browser lifecycle, navigation, waiting, clicking, and text entry whenever they fit the intent. Raw SeleniumLibrary keywords in the suite should be a last resort, not the default.\n"
        "- If the resource layer provides browser/page setup or teardown keywords, use them as Test Setup, Suite Setup, Test Teardown, or Suite Teardown as appropriate.\n"
        "- When the suite imports common/browser lifecycle helpers and the workflow has a known entry page or page URL context, include an explicit setup strategy for opening the browser and navigating to the starting page. Do not leave the suite with only teardown unless the tests are intentionally API-only, which this framework is not.\n"
        "- Preserve approved manual navigation intent. If the manual scenario describes browser/application return navigation and imported approved resources support that path, keep that path explicit instead of silently substituting a direct URL reset. If approved resources do not support the stronger path, preserve the strongest grounded behavior without inventing a shortcut abstraction.\n"
        "- Respect the exact keyword signatures from the imported resource files. Never call a resource keyword without all mandatory arguments defined in its [Arguments] section.\n"
        "- When a page-specific open/navigation keyword is available and a page URL variable exists in the page resource, prefer a no-argument page keyword design or pass the required page URL variable explicitly if the keyword still requires an argument.\n"
        "- Prefer reusable setup/teardown from shared/common resources for opening and closing browser or preparing generic page state.\n"
        "- If the resource layer appears to provide page-open, page-ready, browser-open, browser-close, or cleanup keywords, use them intelligently in suite/test setup and teardown rather than repeating those actions inside every test. Repeated startup actions such as opening the page, opening the browser, navigating to the feature URL, or waiting for the page to be ready should be promoted into Test Setup or Suite Setup whenever that preserves test independence and intent.\n"
        "- If test data is reused across test cases, reference a variable from the resource file rather than declaring suite variables.\n"
        "- Use resource variables only for semantically meaningful reusable data such as valid credentials, one canonical invalid credential set, role-specific users, locked users, or other clearly distinct business data supported by the resource context.\n"
        "- Do not create or rely on unnecessary wrapper variables for blank, whitespace-only, padded, or trivially derived values when Robot built-ins and inline composition are sufficient.\n"
        "- For intentionally blank input use Robot built-in ${EMPTY}; for a single blank space use ${SPACE}; do not leave argument positions visually empty.\n"
        "- For values with leading/trailing spaces or other simple compositions, prefer inline expressions such as ${SPACE}${VALID_USERNAME}${SPACE} instead of expecting separate resource aliases like ${USERNAME_WITH_SPACES}.\n"
        "- Reuse canonical semantic variables consistently. If one ${INVALID_USERNAME} or ${INVALID_PASSWORD} already captures the invalid-login intent, reuse it across negative scenarios instead of expecting duplicate variants.\n"
        "- Never hardcode reusable credential, URL, path, expected-text, and negative or edge data values directly in tests when a meaningful resource variable is available or clearly implied by the resource context. If the approved manual tests clearly require an edge-case value, prefer a semantic resource variable or built-in composition over ad hoc literals in the suite.\n"
        "- Any semantically meaningful credential or business-data variant required by an approved manual test, including uppercase, lowercase, mixed-case, role-specific, invalid, boundary, or other reusable edge-case data, must be referenced through a semantic page-resource variable and must never appear as a literal in the suite.\n"
        "- If an approved manual test requires reusable or semantically meaningful edge-case input and the resource context does not explicitly expose that variable yet, still structure the suite to reference a semantic page-resource variable rather than embedding a literal.\n"
        "- If the resource context contains variables such as ${PAGE_URL}, ${LOGIN_PAGE_URL}, ${VALID_USERNAME}, ${VALID_PASSWORD}, ${INVALID_USERNAME}, ${INVALID_PASSWORD}, or other approved semantic data variables, you must use those variables in the suite instead of literal values.\n"
        "- Hardcoded URLs like http://..., hardcoded credentials, and hardcoded special-character strings are not allowed in the suite when equivalent approved resource variables exist or are clearly implied by the approved manual tests and resource context.\n"
        "- Literal usernames, passwords, URLs, expected messages, and reusable edge-case strings are forbidden in the suite except for Robot built-ins such as ${EMPTY} and ${SPACE} and trivial inline composition explicitly allowed by policy.\n"
        "- For masking, visibility, error message, disabled state, enabled state, page navigation, redirection, and UI behavior expectations, include explicit assertion/verification steps that satisfy expectedResult.\n"
        "- Keep the suite focused on calling resource keywords and assertions only.\n"
        "- Do not include markdown fences.\n"
        "- Return only Robot Framework code.\n"
        "- Use resource import paths with prefix ../pom_pages/ for page resources and import ../resources/common_keywords.resource explicitly for shared resources.\n"
        "- Do not add explanation text before or after the Robot code.\n\n"
        "Robot quality requirements:\n"
        "- Use valid Robot Framework syntax with two-or-more-space separation between keyword and arguments.\n"
        "- Use built-in variables correctly: ${EMPTY}, ${SPACE}, ${True}, ${False}, ${None} only when semantically correct.\n"
        "- Do not leave missing data arguments blank in a keyword call; use an explicit built-in or resource variable.\n"
        "- Each test case should have a clear final verification aligned to its expectedResult.\n"
        "- If a manual test is about password masking, generate an explicit verification for masking behavior instead of only entering data.\n"
        "- If a manual test expects an error message, validation message, rejection, blocked transition, or failed protected action, generate an explicit verification for that result, not only a generic page-loaded check. Prefer dedicated page validation keywords from resource_context when they are supported or clearly implied.\n"
        "- For negative protected-flow scenarios, do not rely solely on a same-page-loaded check. Include at least one stronger observable assertion such as an error message check, validation message check, no-navigation check, protected-area-not-visible check, or another resource-backed visible rejection check.\n"
        "- If the approved manual expectedResult describes visible failure, validation feedback, rejection, required indication, blocked access, or another observable negative outcome, a same-page-only or URL-only assertion is insufficient unless the resource context genuinely provides no stronger supported validation.\n"
        "- If a manual test expects successful navigation or successful login, generate an explicit verification for landing page, URL change, success state, dashboard/home visibility, or another observable post-condition. Prefer page validation keywords such as Verify Successful Login Redirect when available.\n"
        "- If a manual test expects field-level behavior such as required validation, character masking, disabled state, visibility, duplicate submission prevention, copy-paste behavior, keyboard submission behavior, or no duplicate request behavior, include a corresponding verification step and do not stop at action steps only.\n"
        "- Preserve specialized manual intent. If the approved manual test is specifically about copy-paste, Enter key submission, repeated clicking, whitespace handling, case sensitivity, or duplicate prevention, the generated automation should reflect that interaction intent instead of collapsing it into a generic login flow.\n"
        "- Prefer business-readable test cases that call reusable resource keywords over low-level keyword chains when the resource context supports that style.\n"
        "- Use only valid, existing Robot Framework/SeleniumLibrary/BuiltIn keywords or keywords provided by the imported resources. Never invent unsupported keywords. If a negative URL assertion is needed, prefer a valid built-in assertion or a valid page/resource verification keyword for no-navigation behavior.\n"
        "- Prefer wait-oriented verification patterns over immediate absence checks. When verifying UI state, favor visible-state waits such as Wait Until Element Is Visible or Wait Until Element Is Not Visible, or equivalent approved resource keywords, instead of direct page/DOM absence checks whenever visibility is the real user-observable outcome.\n"
        "- For negative UI assertions about an element not appearing, not remaining visible, being dismissed, or being hidden, prefer Wait Until Element Is Not Visible or an equivalent approved resource/page validation keyword. Avoid direct reliance on Page Should Not Contain Element when the user expectation is about visibility in the UI.\n"
        "- Do not add speculative negative assertions for controls, labels, or indicators that are not grounded in approved page-resource elements or approved page-resource validation keywords. If the resource context does not provide a grounded absence validation, do not invent placeholder text checks.\n"
        "- For positive UI assertions about an element appearing or becoming usable, prefer Wait Until Element Is Visible or an equivalent approved resource/page validation keyword before or as part of the assertion.\n"
        "- Before finalizing the suite, review whether repeated opening/navigation/waiting steps are duplicated at the start of many tests. If so, move those repeated startup actions into Test Setup or Suite Setup unless a specific test intentionally requires a different startup sequence.\n"
        "- Before finalizing the suite, self-review every keyword call and remove or replace any keyword that is not part of Robot built-ins, SeleniumLibrary, or the imported resource context.\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )

def extract_response_text(resp: requests.Response) -> str:
    content_type = resp.headers.get("Content-Type", "").lower()

    if "application/json" in content_type:
        data = resp.json()

        if isinstance(data, dict):
            if data.get("choices"):
                return str(data["choices"][0]["message"]["content"]).strip()
            if "content" in data:
                return str(data["content"]).strip()
            if "response" in data:
                return str(data["response"]).strip()
            if "answer" in data:
                return str(data["answer"]).strip()
            if "detail" in data:
                return str(data["detail"]).strip()

        return json.dumps(data, indent=2)

    return resp.text.strip()


def build_manual_review_prompt(manual_data: dict, workflow_input: dict | None = None) -> str:
    reviewer_md = load_prompt_markdown("manual_tests_reviewer.md")
    prompt_manual_data = json.loads(json.dumps(manual_data))
    workflow_context_source = workflow_input if isinstance(workflow_input, dict) else prompt_manual_data
    current_workflow_knowledge = build_workflow_knowledge_context(workflow_context_source)
    relevant_workflow_knowledge = discover_relevant_workflow_knowledge(workflow_context_source)
    payload = {
        "manual_test": prompt_manual_data,
        "current_workflow_knowledge": current_workflow_knowledge,
        "relevant_workflow_knowledge": relevant_workflow_knowledge,
        "review_focus": [
            "Preserve approved workflow/business journey and navigation expectations.",
            "Use workflow knowledge as approved memory for upstream reuse, ownership boundaries, and observable outcome expectations.",
            "Do not weaken approved business data, transition evidence, or validation evidence during review."
        ],
    }
    if reviewer_md:
        return f"{reviewer_md}\n\nInput JSON:\n{json.dumps(payload, indent=2)}"
    return (
        "You are AI Layer 2: a senior QA review architect performing a strict review of a generated manual-test JSON artifact.\n"
        "Return only valid JSON with the same top-level structure.\n\n"
        "Review and repair goals:\n"
        "- preserve approved workflow intent while improving test quality\n"
        "- preserve breadth of scenario coverage, not just a minimal representative subset\n"
        "- remove only true duplicates or low-signal cases that do not add distinct observable coverage\n"
        "- strengthen expectedResult values so downstream automation can create observable assertions\n"
        "- ensure positive cases have explicit success outcomes\n"
        "- ensure negative cases have explicit rejection/validation outcomes\n"
        "- ensure edge cases describe exact observable behavior\n"
        "- keep the artifact practical for Robot Framework generation\n\n"
        "Coverage preservation rules:\n"
        "- preserve all meaningful scenario categories already present in the generated artifact\n"
        "- do not collapse broad scenario coverage into only a few representative tests\n"
        "- retain distinct positive, negative, UI, validation, and edge scenarios whenever they differ in observable intent\n"
        "- retain distinct field-level validation scenarios such as blank input, invalid input, whitespace handling, boundary input, special characters, and navigation behavior when they are materially different\n"
        "- if the generated artifact is missing obvious scenario categories for a form workflow, expand it rather than shrinking it\n"
        "- prefer breadth with low redundancy over aggressive minimization\n"
        "- preserve workflow-mandated scenarios such as explicit navigation controls, approved data usage, entry flows, transition validations, and state-change evidence before optional exploratory edge cases\n"
        "- if the manual artifact uses generic placeholders for business data, destination state, or expected transition while the source workflow provides concrete approved data or observable state evidence, refine the manual tests so that requirement-grounded lineage and observable outcomes remain explicit in title, steps, or expectedResult\n"
        "- if workflow acceptance criteria or transition expectations mention observable destination-state evidence, state-change evidence, newly available capabilities, or context-specific outcome signals, ensure those become explicit manual test coverage rather than remaining implied inside a generic success case\n"
        "- treat current_workflow_knowledge and relevant_workflow_knowledge as mandatory approved-memory context during manual review; preserve upstream reuse guidance, ownership boundaries, navigation journey, and business-visible outcomes\n\n"
        "Rules:\n"
        "- return only JSON\n"
        "- keep resourceFiles intact\n"
        "- keep testCases non-empty\n"
        "- do not add extra top-level keys\n"
        "- each test case must still contain only id, title, type, steps, expectedResult, fields\n"
        "- remove shallow duplicates that differ only in wording but not observable intent\n"
        "- repair vague expected results into observable outcomes\n"
        "- preserve or improve overall coverage breadth\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )


def build_manual_refiner_prompt(original_manual_data: dict, reviewed_manual_data: dict, workflow_input: dict | None = None) -> str:
    refiner_md = load_prompt_markdown("manual_tests_refiner.md")
    workflow_context_source = workflow_input if isinstance(workflow_input, dict) else reviewed_manual_data if isinstance(reviewed_manual_data, dict) else original_manual_data
    payload = {
        "original_manual": original_manual_data,
        "reviewed_manual": reviewed_manual_data,
        "current_workflow_knowledge": build_workflow_knowledge_context(workflow_context_source),
        "relevant_workflow_knowledge": discover_relevant_workflow_knowledge(workflow_context_source),
        "refinement_focus": [
            "Preserve action intent and behavioral nuance from the source artifact.",
            "Strengthen expectedResult into observable evidence without inventing unsupported behavior.",
            "Keep scenario breadth high and avoid collapsing distinct interaction patterns into generic flows.",
            "Stay aligned with approved workflow knowledge, upstream reuse context, and business-visible outcomes."
        ],
    }
    if refiner_md:
        return f"{refiner_md}\n\nInput JSON:\n{json.dumps(payload, indent=2)}"
    return (
        "You are AI Layer 2B: a senior QA manual-test refinement specialist.\n"
        "Return only valid JSON with the same top-level manual-test structure.\n\n"
        "Your task is to refine the reviewed manual-test artifact without shrinking meaningful coverage.\n"
        "Preserve workflow intent, preserve distinct scenario categories, improve wording and observability, and repair any weak expected results.\n"
        "Do not reduce the suite to a small representative subset.\n"
        "Keep resourceFiles intact and keep testCases non-empty.\n"
        "Each test case must still contain only id, title, type, steps, expectedResult, fields.\n"
        "Remove only true duplicates that do not add distinct observable behavior.\n"
        "If obvious category gaps remain for a form workflow, expand the suite while staying grounded in the original_manual context.\n"
        "Treat current_workflow_knowledge and relevant_workflow_knowledge as mandatory approved-memory context during refinement so that navigation journey, upstream reuse boundaries, approved business data, and observable outcomes remain aligned.\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )


def build_review_prompt(manual_data: dict, resource_context: List[Dict], generated_robot: str) -> str:
    prompt_manual_data = json.loads(json.dumps(manual_data))
    reviewer_md = load_prompt_markdown("robot_tests_reviewer.md")
    current_workflow_knowledge = build_workflow_knowledge_context(prompt_manual_data)
    relevant_workflow_knowledge = discover_relevant_workflow_knowledge(prompt_manual_data)
    if isinstance(prompt_manual_data.get("fields"), list):
        prompt_manual_data["fields"] = [
            field for field in prompt_manual_data["fields"]
            if isinstance(field, dict) and any(clean_text(str(field.get(k, ""))) for k in ("name", "label", "type"))
        ]

    page_resources = [resource.get("file", "") for resource in resource_context if "/pom_pages/" in f"/{resource.get('file', '')}" or str(resource.get("file", "")).startswith("pom_pages/")]
    allowed_builtin_keywords, allowed_selenium_keywords = get_framework_keyword_catalog()
    payload = {
        "manual_test": prompt_manual_data,
        "resource_context": resource_context,
        "current_workflow_knowledge": current_workflow_knowledge,
        "relevant_workflow_knowledge": relevant_workflow_knowledge,
        "generated_robot": generated_robot,
        "resource_import_prefix": "../pom_pages/",
        "common_resource_hint": "../resources/common_keywords.resource",
        "approved_artifact_lineage": {
            "page_resources": page_resources,
            "suite_target": "tests/<workflow>_tests.robot",
        },
        "allowed_builtin_keywords": sorted(allowed_builtin_keywords),
        "allowed_selenium_keywords": sorted(allowed_selenium_keywords),
    }

    if reviewer_md:
        return f"{reviewer_md}\n\nInput JSON:\n{json.dumps(payload, indent=2)}"

    return (
        "You are AI Layer 4: a senior Robot Framework reviewer and repair specialist.\n"
        "Your task is to review an already generated Robot Framework test suite and return a corrected version of the same suite.\n\n"
        "Review objectives:\n"
        "- Preserve the intent and coverage of the approved manual tests.\n"
        "- Correct Robot Framework syntax and framework alignment issues.\n"
        "- Improve reuse of resource keywords, resource variables, setup/teardown, and validation steps.\n"
        "- Ensure the output remains a thin suite that relies on the provided page resource files and the shared common resource layer.\n"
        "- Use the input keyword inventory as the allowed universe for non-resource keywords: prefer allowed_builtin_keywords and allowed_selenium_keywords, and otherwise reuse imported resource keywords from resource_context.\n\n"
        "Mandatory repair rules:\n"
        "- Return only Robot Framework code, with no markdown fences and no explanation.\n"
        "- Preserve compact formatting: no blank lines inside the Settings section, no blank line after *** Test Cases *** (the first test case must start immediately on the next line), exactly one blank line between major sections, and exactly one blank line between test cases.\n"
        "- Ensure every test case name starts with AUT- and follows the pattern AUT-<APPCODE>-<FEATURECODE><NN>: <Title>. Use identifier_policy from the input JSON as the authoritative naming guide.\n"
        "- Ensure every test case includes a [Tags] line immediately after the test case name. Keep tags minimal: only the testcase id tag and the scenario type tag, for example [Tags]    WT-LOGIN01    positive.\n"
        "- Ensure generated IDs stay concise and stable; never concatenate the full workflow or user-story title into <FEATURECODE>.\n"
        "- Preserve or repair the numbering so it is stable and aligned to the approved manual test order or id when possible.\n"
        "- The final approved page resource files are authoritative. Reuse exact approved page keyword names and exact approved page variable names from resource_context instead of paraphrasing, renaming, or reverting to metadata-derived naming.\n"
        "- Treat current_workflow_knowledge and relevant_workflow_knowledge as mandatory approved-memory context during review and repair. Use them to preserve business journey, entry flow, upstream ownership, state-transition expectations, and approved downstream reuse boundaries.\n"
        "- Never return a suite that introduces a custom keyword name not present in imported resource_context or approved framework keyword inventories. Repair such usage by replacing it with existing upstream resource keywords.\n"
        "- Do not add extra tags such as AUT, ui, validation, security, accessibility, or feature-name tags.\n"
        "- Keep only the suite file; do not generate resource content.\n"
        "- Use only the provided resource files from manual_test.resourceFiles plus ../resources/common_keywords.resource as the shared common layer.\n"
        "- Ensure ../resources/common_keywords.resource is imported in the suite Settings section.\n"
        "- Do not add a *** Variables *** section.\n"
        "- Do not add a *** Keywords *** section unless a tiny test-specific helper is absolutely unavoidable; prefer resource keywords instead.\n"
        "- Replace bad blank handling with ${EMPTY} and single-space handling with ${SPACE}. Never leave input arguments visually empty.\n"
        "- Replace hardcoded reusable test data with semantic resource variables whenever the resource context supports it or clearly implies it. Do not leave reusable usernames, passwords, URLs, paths, expected texts, role-specific credentials, or other meaningful business data inline in the suite when a page-resource variable should be used instead.\n"
        "- Treat uppercase, lowercase, mixed-case, role-specific, invalid, boundary, and other semantically meaningful credential variants as reusable business data, not harmless one-off literals. These must be represented through page-resource variables rather than inline suite values.\n"
        "- If page-resource variables for page URL, valid credentials, invalid credentials, or reusable edge data exist in resource_context, use them and remove corresponding literals from the suite.\n"
        "- Eliminate unnecessary dependence on noisy derived variables. If the suite uses aliases that merely duplicate ${EMPTY}, ${SPACE}, padded forms of valid credentials, duplicate invalid credential variants, or other simple compositions, rewrite the suite to use built-ins, canonical semantic variables, and inline composition instead.\n"
        "- Reuse one canonical invalid username/password pair across similar negative scenarios unless the approved manual tests clearly require distinct invalid data classes.\n"
        "- Prefer common/shared resource keywords for generic browser lifecycle, page opening, navigation, waiting, clicking, and text entry when suitable. Raw SeleniumLibrary keywords in the suite should be replaced by shared/common resource keywords whenever a suitable helper exists.\n"
        "- For generic field entry, including password fields, prefer common/shared wrapper keywords over low-level SeleniumLibrary entry keywords whenever the wrapper can satisfy the intent. If the shared/common layer already exposes Input Text When Ready or an equivalent reusable text-entry helper, use it instead of direct Input Password unless a dedicated shared password helper exists and is more appropriate.\n"
        "- If resource keywords suggest page lifecycle operations, use Suite/Test Setup and Teardown intelligently. Repeated startup actions such as open-page, navigate, and page-ready waits should normally be lifted into setup instead of being duplicated in every test.\n"
        "- If the reviewed suite contains Test Teardown or Suite Teardown for browser cleanup, it should normally also contain a corresponding Test Setup or Suite Setup for browser opening and initial navigation whenever the tests are UI/browser-based. Repair missing setup instead of returning a teardown-only browser suite.\n"
        "- Every test must contain explicit validation aligned to expectedResult.\n"
        "- Prefer page-resource validation keywords over generic visibility checks when the expected result mentions authentication errors, validation messages, redirect behavior, blocked login, duplicate submission prevention, or success outcomes.\n"
        "- If a test is about password masking, ensure there is an explicit masking verification.\n"
        "- If a test is about validation messages, blocked login, rejection behavior, or failed authentication, ensure there is an explicit assertion for that behavior and not only a page-loaded check. For negative authentication scenarios, include at least one stronger observable assertion such as an error message check, validation message check, no-navigation check, protected-area-not-visible check, or another resource-backed visible rejection check.\n"
        "- Flag and repair any test whose final negative assertion weakens an approved manual expectedResult into only a same-page or URL-presence check when stronger approved validation intent exists in the manual artifact or resource context.\n"
        "- If a test is about successful login or navigation, ensure there is an explicit post-condition verification such as dashboard/home visibility, URL change, success state, or a dedicated page validation keyword.\n"
        "- Preserve specialized interaction intent such as copy-paste, Enter key submission, repeated clicking, whitespace handling, or duplicate submission prevention; do not simplify these into a generic login-only sequence.\n"
        "- Prefer business-readable resource keyword calls over low-level one-off steps.\n"
        "- Prefer wait-based visibility assertions over immediate DOM-absence assertions. When validating that an element appears, disappears, remains hidden, or is dismissed in the UI, use Wait Until Element Is Visible or Wait Until Element Is Not Visible, or equivalent approved resource keywords, instead of Page Should Not Contain Element when visibility is the true intent.\n"
        "- Do not preserve or introduce speculative absence checks backed only by invented text variables or placeholder strings. Negative UI validations must be grounded in approved page-resource elements or approved page-resource validation keywords.\n"
        "- Replace any unsupported or invented keyword with a valid existing Robot built-in, SeleniumLibrary keyword, or imported resource keyword.\n"
        "- Treat allowed_builtin_keywords and allowed_selenium_keywords from the input JSON as the approved non-resource keyword inventory. If a keyword is not in those lists or in imported resource_context, replace it instead of returning it.\n"
        "- Self-audit the final suite for keyword existence: every called keyword must come from Robot built-ins, SeleniumLibrary, or the imported resource files.\n"
        "- Self-audit every imported resource keyword call against its required [Arguments] signature and fix any missing mandatory arguments before returning the suite.\n"
        "- Review the final suite for repetitive startup sequences. If multiple tests begin with the same open-page, navigate, or page-ready steps, refactor those repeated actions into Test Setup or Suite Setup unless a specific test intentionally requires a different startup flow.\n"
        "- Do not compensate for duplicated common/page keywords by creating additional duplicates; prefer the shared/common resource keyword when the intent is generic.\n\n"
        "Repair focus areas:\n"
        "- common resource import and reuse\n"
        "- built-in variables (${EMPTY}, ${SPACE})\n"
        "- resource variable reuse instead of hardcoded inline data\n"
        "- setup and teardown usage\n"
        "- validation/assertion coverage from expectedResult\n"
        "- Robot syntax correctness and maintainability\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )

def build_validation_review_prompt(manual_data: dict, resource_context: List[Dict], generated_robot: str) -> str:
    prompt_manual_data = json.loads(json.dumps(manual_data))
    refiner_md = load_prompt_markdown("robot_tests_refiner.md")
    current_workflow_knowledge = build_workflow_knowledge_context(prompt_manual_data)
    relevant_workflow_knowledge = discover_relevant_workflow_knowledge(prompt_manual_data)
    if isinstance(prompt_manual_data.get("fields"), list):
        prompt_manual_data["fields"] = [
            field for field in prompt_manual_data["fields"]
            if isinstance(field, dict) and any(clean_text(str(field.get(k, ""))) for k in ("name", "label", "type"))
        ]

    page_resources = [resource.get("file", "") for resource in resource_context if "/pom_pages/" in f"/{resource.get('file', '')}" or str(resource.get("file", "")).startswith("pom_pages/")]
    allowed_builtin_keywords, allowed_selenium_keywords = get_framework_keyword_catalog()
    manual_expected_outcomes = collect_manual_expected_outcomes(prompt_manual_data)
    resource_validation_keywords = collect_resource_validation_keywords(resource_context)
    payload = {
        "manual_test": prompt_manual_data,
        "resource_context": resource_context,
        "current_workflow_knowledge": current_workflow_knowledge,
        "relevant_workflow_knowledge": relevant_workflow_knowledge,
        "generated_robot": generated_robot,
        "allowed_builtin_keywords": sorted(allowed_builtin_keywords),
        "allowed_selenium_keywords": sorted(allowed_selenium_keywords),
        "resource_import_prefix": "../pom_pages/",
        "common_resource_hint": "../resources/common_keywords.resource",
        "approved_artifact_lineage": {
            "page_resources": page_resources,
            "suite_target": "tests/<workflow>_tests.robot",
        },
        "assertion_guidance": {
            "manual_expected_outcomes": manual_expected_outcomes,
            "resource_validation_keywords": resource_validation_keywords,
        }
    }

    if refiner_md:
        return f"{refiner_md}\n\nInput JSON:\n{json.dumps(payload, indent=2)}"

    return (
        "You are AI Layer 5: a principal QA automation governance reviewer acting as a final AI validation gate.\n"
        "Your job is to perform a strict policy-and-quality review of an already reviewed Robot Framework suite and return the best corrected final suite.\n\n"
        "Final-gate objectives:\n"
        "- Preserve approved manual intent and scenario coverage.\n"
        "- Reject weak or action-only tests by repairing them into assertion-complete tests when the resource context supports it.\n"
        "- Prefer framework-safe, reusable, maintainable suite structure over ad hoc literal-driven test steps.\n"
        "- Keep generated page resources untouched; operate only on the suite.\n"
        "- Use the input keyword inventory as a guardrail: allowed_builtin_keywords and allowed_selenium_keywords define the approved non-resource keyword universe, and imported resource_context defines the approved resource keyword universe.\n\n"
        "Final-gate enforcement rules:\n"
        "- Return only Robot Framework code. No markdown fences. No explanation text.\n"
        "- Keep the suite thin: only *** Settings *** and *** Test Cases *** unless a tiny local helper is absolutely unavoidable.\n"
        "- Do not add or modify page-resource content.\n"
        "- Use only imported resources from manual_test.resourceFiles plus ../resources/common_keywords.resource.\n"
        "- Ensure the shared common resource is imported.\n"
        "- The final approved page resource files are authoritative. Reuse exact approved page keyword names and exact approved page variable names from resource_context instead of paraphrasing, renaming, or reverting to metadata-derived naming.\n"
        "- Treat current_workflow_knowledge and relevant_workflow_knowledge as mandatory approved-memory context during final validation and repair. Use them to preserve approved entry flow, upstream ownership, resource reuse boundaries, state transitions, and business-visible outcomes.\n"
        "- Never return a suite that introduces a custom keyword name not present in imported resource_context or approved framework keyword inventories. Replace invented suite actions with existing upstream resource keywords or valid framework keywords only.\n"
        "- Preserve compact formatting and one blank line between test cases.\n"
        "- Use Test Setup / Test Teardown when repeated startup and cleanup behavior exists.\n"
        "- A UI/browser suite must not end up teardown-only. If browser cleanup exists, ensure an appropriate setup exists for browser opening and initial navigation using approved shared/common helpers or approved page-open keywords.\n"
        "- Every test must end with an observable validation aligned to expectedResult.\n"
        "- Positive navigation or state-transition tests must include an observable destination-state verification when such a keyword exists in resource_context. If such a success keyword does not exist, preserve the test but do not invent unsupported keywords.\n"
        "- Negative validation or failed-transition tests must include stronger rejection assertions when supported by resource_context; do not rely only on page-ready checks unless that is the only available resource validation.\n"
        "- For UI visibility assertions, prefer wait-based visibility semantics such as Wait Until Element Is Visible and Wait Until Element Is Not Visible, or equivalent approved resource validation keywords. Avoid immediate absence checks like Page Should Not Contain Element when the user-observable intent is hidden/not visible.\n"
        "- Only keep negative visibility assertions when the page-resource context grounds them in approved elements or approved validation keywords. Remove speculative text-only absence checks for indicators that are not part of the approved artifact lineage.\n"
        "- For generic clicking, waiting, navigation, and text/password entry, prefer approved shared/common resource helpers over direct SeleniumLibrary calls whenever the shared/common helper already exists in resource_context.\n"
        "- Preserve specialized interaction intent such as Enter key submission and repeated clicking.\n"
        "- Reuse semantic resource variables over inline literals whenever available in resource_context, especially for reusable usernames, passwords, URLs, paths, expected validation texts, and semantically meaningful credential variants such as uppercase, lowercase, mixed-case, or other reusable edge-case data.\n"
        "- Reject suites that preserve hardcoded credential literals or weaken approved negative expected outcomes into only same-page checks when stronger approved resource semantics or manual expectations exist.\n"
        "- Avoid inventing unsupported keywords, unsupported assertions, or unsupported library APIs.\n"
        "- If validation warnings indicate an unknown keyword, repair it by reusing imported resource keywords or by choosing only from allowed_builtin_keywords and allowed_selenium_keywords in the input JSON.\n"
        "- Self-audit the final suite against the imported keyword inventory before returning it.\n\n"
        "Special review focus for this framework maturity stage:\n"
        "- detect false-positive positive-path tests\n"
        "- detect weak duplicate-submission scenarios\n"
        "- detect hardcoded edge-case literals that should be resource-driven when supported\n"
        "- detect mismatch between manual expectedResult and final assertion strength\n"
        "- detect repeated open/navigate/wait steps that belong in setup\n\n"
        f"Input JSON:\n{json.dumps(payload, indent=2)}"
    )


def call_ai_chat(
    endpoint: str,
    token: str,
    prompt: str,
    timeout_seconds: int = 120,
    verify_ssl: bool = False
) -> str:
    headers = {
        "Authorization": f"Bearer {token}",
    }

    resp = requests.post(
        endpoint,
        headers=headers,
        data={"query": prompt},
        files=[],
        timeout=timeout_seconds,
        verify=verify_ssl,
    )

    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        error_body = ""
        try:
            error_body = extract_response_text(resp)
        except Exception:
            error_body = resp.text.strip()
        raise requests.HTTPError(
            f"{exc}. Response body: {error_body}",
            response=resp
        ) from exc

    return extract_response_text(resp)

def get_framework_keyword_catalog() -> tuple[set[str], set[str]]:
    builtin_keywords = {
        "should be equal", "should not be equal", "should contain", "should not contain",
        "should be true", "should be false", "should be empty", "should not be empty",
        "should match", "should not match", "should match regexp", "should not match regexp",
        "length should be", "log", "sleep", "set test variable", "set suite variable",
        "set global variable", "run keyword if", "run keywords", "repeat keyword",
        "wait until keyword succeeds", "create list", "create dictionary", "get length",
        "evaluate", "set variable", "should start with", "should end with"
    }
    selenium_keywords = {
        "open browser", "close browser", "close all browsers", "go to", "reload page",
        "get location", "location should be", "title should be", "element should be visible",
        "element should not be visible", "element should be enabled", "element should be focused",
        "page should contain", "page should not contain", "page should contain element", "page should not contain element",
        "wait until element is visible", "wait until element is not visible", "wait until element is enabled",
        "wait until page contains", "wait until page contains element", "wait until page does not contain",
        "wait until page does not contain element", "wait until location is", "wait until location contains",
        "click element", "input text", "input password", "clear element text", "press keys",
        "get text", "get value", "get element attribute", "element text should be",
        "textfield value should be", "capture page screenshot", "select checkbox", "unselect checkbox",
        "select from list by label", "select from list by value", "select radio button",
        "handle alert", "alert should be present", "get title"
    }
    return builtin_keywords, selenium_keywords


def validate_resource_content(content: str, common_resource_context: List[Dict] | None = None) -> tuple[bool, str]:
    errors: list[str] = []
    warnings: list[str] = []

    def normalize_keyword_token(value: str) -> str:
        return clean_text(value).lower()

    def scan_keyword_invocation(raw_text: str) -> tuple[str, list[str]]:
        stripped = raw_text.strip()
        parts = [part.strip() for part in re.split(r"\s{2,}|\t+", stripped) if part.strip()]
        if not parts:
            return "", []
        if parts[0].startswith("${") and parts[0].endswith("}="):
            if len(parts) >= 2:
                return parts[1], parts[2:]
            return "", []
        return parts[0], parts[1:]

    builtin_keywords, selenium_keywords = get_framework_keyword_catalog()

    if "*** Keywords ***" not in content:
        warnings.append("Generated resource does not include a *** Keywords *** section")

    if re.search(r"(?im)^\s*: FOR\b", content):
        errors.append("Generated resource uses deprecated ': FOR' syntax; use modern FOR/END syntax")

    if re.search(r"(?im)^\s*\\\s+", content):
        errors.append("Generated resource uses deprecated backslash loop-body syntax; use modern FOR/END syntax")

    if re.search(r"\n{3,}", content):
        warnings.append("Generated resource contains excessive blank lines; keep formatting compact")

    variables_match = re.search(r"(?is)\*\*\*\s*variables\s*\*\*\*(.*?)(?:\n\*\*\*|\Z)", content)
    if variables_match and re.search(r"\n\s*\n\s*\$\{", variables_match.group(1)):
        errors.append("Generated resource contains blank lines between consecutive variable definitions; keep variable blocks compact")

    if re.search(r"(?im)^\s*Resource\s+\.\./\.\./resources/common_keywords\.resource\s*$", content) is None:
        errors.append("Generated page resource must import ../../resources/common_keywords.resource")

    common_keyword_names = set()
    for item in common_resource_context or []:
        for kw in item.get("keywords", []):
            name = clean_text(str(kw.get("name", "")))
            if name:
                common_keyword_names.add(name.lower())

    for common_name in sorted(common_keyword_names):
        if re.search(rf"(?im)^\s*{re.escape(common_name)}\s*$", content):
            warnings.append(f"Generated resource appears to duplicate shared/common keyword: {common_name}")

    parsed_resource = {"variables": extract_variables_from_resource(content), "keywords": extract_keywords_from_resource(content)}
    local_keyword_names = {
        normalize_keyword_token(str(keyword.get("name", "")))
        for keyword in parsed_resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    }
    allowed_keyword_names = builtin_keywords | selenium_keywords | common_keyword_names | local_keyword_names

    control_tokens = {"for", "end", "if", "else", "else if", "try", "except", "finally", "return from keyword", "continue for loop", "exit for loop"}
    setting_tokens = {"[documentation]", "[arguments]", "[return]", "[tags]", "[timeout]", "[setup]", "[teardown]"}

    for keyword in parsed_resource.get("keywords", []):
        keyword_name = clean_text(str(keyword.get("name", "")))
        for body_line in keyword.get("body", []):
            stripped = body_line.strip()
            if not stripped:
                continue
            lowered = stripped.lower()
            if lowered.startswith("..."):
                continue
            token, _arguments = scan_keyword_invocation(body_line)
            normalized_token = normalize_keyword_token(token)
            if not normalized_token or normalized_token in control_tokens or normalized_token in setting_tokens:
                continue
            if normalized_token not in allowed_keyword_names:
                errors.append(
                    f"Generated resource uses an unknown or unsupported keyword '{token}' in resource keyword '{keyword_name}'"
                )

    variable_names = re.findall(r"(?im)^\s*\$\{([A-Z0-9_]+)\}\s{2,}(.+?)\s*$", content)
    all_variable_refs = re.findall(r"\$\{([A-Z0-9_]+)\}", content)
    variable_ref_counts: dict[str, int] = {}
    for ref_name in all_variable_refs:
        key = ref_name.upper()
        variable_ref_counts[key] = variable_ref_counts.get(key, 0) + 1

    for var_name, _var_value in variable_names:
        upper_name = var_name.upper()
        if variable_ref_counts.get(upper_name, 0) <= 1:
            warnings.append(f"Variable ${{{var_name}}} appears unused outside its own definition; remove low-value unused variables")

    is_valid = len(errors) == 0
    message_parts = []
    if errors:
        message_parts.append("\n".join(errors))
    if warnings:
        message_parts.append("Warnings:\n" + "\n".join(warnings))
    return is_valid, "\n\n".join(part for part in message_parts if part)


def build_keyword_signature_map(allowed_resources: list[str]) -> dict[str, dict]:
    signature_map: dict[str, dict] = {}

    def add_keywords_from_resource(resource_path: Path):
        if not resource_path.exists():
            return
        try:
            parsed = parse_resource_file(resource_path)
        except Exception:
            return
        for kw in parsed.get("keywords", []):
            name = clean_text(str(kw.get("name", "")))
            if not name:
                continue
            args = [clean_text(str(arg)) for arg in kw.get("args", []) if clean_text(str(arg))]
            required_args = [arg for arg in args if "=" not in arg]
            signature_map[name.lower()] = {
                "name": name,
                "args": args,
                "required_args": required_args,
                "source": str(resource_path.relative_to(BASE_DIR)).replace("\\", "/"),
            }

    for resource in allowed_resources:
        resource_path = BASE_DIR / "pom_pages" / resource
        add_keywords_from_resource(resource_path)

    common_resource_path = BASE_DIR / "resources" / "common_keywords.resource"
    add_keywords_from_resource(common_resource_path)
    return signature_map


def validate_robot_alignment_with_resource_context(content: str, resource_context: list[dict]) -> tuple[bool, str]:
    errors: list[str] = []
    warnings: list[str] = []

    approved_resource_keyword_names = {
        clean_text(str(keyword.get("name", ""))).lower()
        for resource in resource_context
        for keyword in resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    }

    suite_called_keywords: list[str] = []
    test_step_sequences: list[list[str]] = []
    current_sequence: list[str] = []
    in_test_cases = False
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        lowered = stripped.lower()
        if lowered == "*** test cases ***":
            in_test_cases = True
            current_sequence = []
            continue
        if lowered.startswith("***") and lowered != "*** test cases ***":
            if current_sequence:
                test_step_sequences.append(current_sequence)
            in_test_cases = False
            current_sequence = []
            continue
        if not in_test_cases:
            continue
        if stripped and not raw_line.startswith((" ", "\t")):
            if current_sequence:
                test_step_sequences.append(current_sequence)
            current_sequence = []
            continue
        if raw_line.startswith((" ", "\t")) and stripped and not stripped.startswith("["):
            parts = [part.strip() for part in re.split(r"\s{2,}|\t+", stripped) if part.strip()]
            if parts:
                keyword_name = clean_text(parts[0]).lower()
                suite_called_keywords.append(keyword_name)
                current_sequence.append(keyword_name)
    if current_sequence:
        test_step_sequences.append(current_sequence)

    common_helper_names = {
        clean_text(str(keyword.get("name", ""))).lower()
        for resource in resource_context
        if resource.get("type") == "common"
        for keyword in resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    }
    page_keyword_names = {
        clean_text(str(keyword.get("name", ""))).lower()
        for resource in resource_context
        if resource.get("type") != "common"
        for keyword in resource.get("keywords", [])
        if clean_text(str(keyword.get("name", "")))
    }
    suite_keyword_counts: dict[str, int] = {}
    for name in suite_called_keywords:
        suite_keyword_counts[name] = suite_keyword_counts.get(name, 0) + 1

    if approved_resource_keyword_names:
        called_approved_keywords = [name for name in suite_called_keywords if name in approved_resource_keyword_names]
        if not called_approved_keywords:
            warnings.append("Generated suite does not appear to reuse approved page/common resource keywords from the provided resource context")
        invented_keywords = [
            name for name in suite_called_keywords
            if name not in approved_resource_keyword_names and name not in get_framework_keyword_catalog()[0] and name not in get_framework_keyword_catalog()[1]
        ]
        if invented_keywords:
            deduped_invented: list[str] = []
            seen_invented: set[str] = set()
            for name in invented_keywords:
                if name in seen_invented:
                    continue
                seen_invented.add(name)
                deduped_invented.append(name)
            warnings.append(
                "AI-invented suite keyword(s) detected that are not present in approved upstream resources or approved framework libraries: "
                + ", ".join(deduped_invented[:8])
            )

    if common_helper_names:
        called_common_helpers = [name for name in suite_called_keywords if name in common_helper_names]
        if not called_common_helpers:
            warnings.append("Generated suite does not appear to call retrieved common/shared helper keywords")
        if "input text when ready" in common_helper_names and any(name in {"input text", "input password"} for name in suite_called_keywords):
            warnings.append(
                "Wrapper-priority violation: shared/common text-entry wrapper 'Input Text When Ready' exists, but the suite still uses direct SeleniumLibrary Input Text/Input Password calls. Shared wrapper keywords must take precedence for field entry."
            )

    has_setup = bool(re.search(r"(?im)^\s*(?:Suite Setup|Test Setup)\s+.+$", content))
    has_teardown = bool(re.search(r"(?im)^\s*(?:Suite Teardown|Test Teardown)\s+.+$", content))
    if has_teardown and not has_setup:
        repeated_start_candidates = []
        for steps in test_step_sequences:
            if steps:
                repeated_start_candidates.append(steps[0])
            if len(steps) >= 2:
                repeated_start_candidates.append(" > ".join(steps[:2]))
        if repeated_start_candidates:
            top_pattern = max(set(repeated_start_candidates), key=repeated_start_candidates.count)
            if repeated_start_candidates.count(top_pattern) >= max(2, len(test_step_sequences) // 2):
                warnings.append(
                    "Generated suite includes teardown but missed promoting the repeated startup pattern into Test Setup or Suite Setup. Prefer using the repeated page-open/page-ready keyword sequence as setup when it is shared by most tests."
                )

    setup_match = re.search(r"(?im)^\s*(Suite Setup|Test Setup)\s{2,}(.+)$", content)
    setup_keyword_name = ""
    if setup_match:
        setup_keyword_name, _setup_args = scan_keyword_invocation(setup_match.group(2))
        setup_keyword_name = clean_text(setup_keyword_name).lower()

    if has_setup and test_step_sequences:
        opener_like_keywords = [
            name for name in page_keyword_names
            if any(token in name for token in ["open ", "launch ", "guest state", "page is loaded", "page loaded"])
        ]
        repeated_opener_counts = {name: suite_keyword_counts.get(name, 0) for name in opener_like_keywords if suite_keyword_counts.get(name, 0)}
        if repeated_opener_counts:
            best_repeated_opener = max(repeated_opener_counts, key=repeated_opener_counts.get)
            best_count = repeated_opener_counts[best_repeated_opener]
            if best_count >= max(2, len(test_step_sequences) // 2):
                if setup_keyword_name and setup_keyword_name != best_repeated_opener:
                    warnings.append(
                        f"Generated suite uses setup '{setup_keyword_name}' but repeatedly invokes higher-level page startup keyword '{best_repeated_opener}' inside test bodies. Prefer the strongest reusable semantic setup abstraction instead of a lower-level opener."
                    )
                elif not setup_keyword_name:
                    warnings.append(
                        "Generated suite appears to have setup configured, but the repeated highest-level page startup abstraction is still being invoked inside test bodies. Prefer moving that semantic opener into setup."
                    )

    repeated_open_keywords = {
        name for name in page_keyword_names
        if any(token in name for token in ["open ", "launch ", "guest state", "page is loaded", "page loaded"])
    }
    if not has_setup and repeated_open_keywords:
        repeated_opener_usage = sum(suite_keyword_counts.get(name, 0) for name in repeated_open_keywords)
        if repeated_opener_usage >= 2:
            warnings.append(
                "Generated suite repeatedly invokes a page-opening/page-readiness keyword inside test bodies instead of lifting it into Test Setup or Suite Setup."
            )

    return len(errors) == 0, ("Warnings:\n" + "\n".join(warnings)) if warnings else ""


def collect_manual_expected_outcomes(manual_data: dict) -> list[str]:
    outcomes: list[str] = []
    cases = manual_data.get("testCases") or manual_data.get("manualTests") or []
    if isinstance(cases, list):
        for case in cases:
            if not isinstance(case, dict):
                continue
            value = clean_text(str(case.get("expectedResult") or case.get("expected") or case.get("expectedOutcome") or ""))
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


def collect_resource_validation_keywords(resource_context: list[dict]) -> list[str]:
    validation_keywords: list[str] = []
    for resource in resource_context:
        for keyword in resource.get("keywords", []):
            name = clean_text(str(keyword.get("name", "")))
            if not name:
                continue
            validation_keywords.append(name)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in validation_keywords:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(item)
    return deduped


def warn_on_assertion_quality(manual_expected_outcomes: list[str], robot_content: str, resource_validation_keywords: list[str]) -> str:
    del manual_expected_outcomes, robot_content, resource_validation_keywords
    return ""


def normalize_generated_robot_identifiers(content: str, identifier_policy: dict) -> str:
    family_prefix = clean_text(str(identifier_policy.get("family_prefix", "")))
    if not family_prefix:
        return content

    lines = content.splitlines()
    normalized_lines: list[str] = []
    current_test_id = ""
    sequence = 1
    pending_tag_for_current_test = False

    def is_test_case_header(raw_line: str) -> bool:
        stripped_line = raw_line.strip()
        if not stripped_line or raw_line.startswith((" ", "\t")):
            return False
        if stripped_line.startswith("***"):
            return False
        upper = stripped_line.upper()
        if upper.startswith(("LIBRARY", "RESOURCE", "SUITE SETUP", "SUITE TEARDOWN", "TEST SETUP", "TEST TEARDOWN", "DOCUMENTATION", "METADATA", "FORCE TAGS", "DEFAULT TAGS")):
            return False
        return ":" in stripped_line

    for line in lines:
        stripped = line.strip()
        test_name_match = re.match(r"^(AUT-)([A-Z0-9]+)-([A-Z0-9_]+?)(\d{2})(:\s+.*)$", stripped)
        if stripped and not line.startswith((" ", "\t")) and test_name_match:
            current_test_id = f"{family_prefix}{sequence:02d}"
            normalized_lines.append(f"AUT-{current_test_id}{test_name_match.group(5)}")
            pending_tag_for_current_test = True
            sequence += 1
            continue

        if stripped and is_test_case_header(line):
            current_test_id = f"{family_prefix}{sequence:02d}"
            title_suffix = stripped[stripped.find(":"):] if ":" in stripped else f": Test Case {sequence:02d}"
            normalized_lines.append(f"AUT-{current_test_id}{title_suffix}")
            pending_tag_for_current_test = True
            sequence += 1
            continue

        if current_test_id and pending_tag_for_current_test and line.startswith((" ", "\t")):
            lower_stripped = stripped.lower()
            if stripped.startswith("["):
                if lower_stripped.startswith("[tags]"):
                    normalized_lines.append(f"    [Tags]    {current_test_id}")
                    pending_tag_for_current_test = False
                    continue
                normalized_lines.append(line)
                continue

            normalized_lines.append(f"    [Tags]    {current_test_id}")
            pending_tag_for_current_test = False

        if current_test_id and line.startswith((" ", "\t")) and stripped and not stripped.startswith("[") and compact_code(stripped) == compact_code(str(identifier_policy.get("feature_code", ""))):
            continue

        normalized_lines.append(line)

    return "\n".join(normalized_lines) + ("\n" if content.endswith("\n") else "")


def validate_robot_content(content: str, allowed_resources: list[str]) -> tuple[bool, str]:
    errors: list[str] = []
    warnings: list[str] = []

    low_level_usage = len(re.findall(r"(?im)^\s*(Input Text|Press Keys|Click Element|Wait Until Element Is Visible|Wait Until Page Contains Element)\b", content))
    if low_level_usage >= 6:
        warnings.append("Generated suite appears to rely heavily on low-level interaction keywords; prefer approved page/common abstractions when available")

    if re.search(r"(?im)^\s*Page Should Not Contain Element\b", content):
        warnings.append(
            "Generated suite uses Page Should Not Contain Element. For UI-hidden/dismissed/absent-in-view expectations, prefer wait-based visibility semantics such as Wait Until Element Is Not Visible or an equivalent approved resource validation keyword."
        )
    if re.search(r"(?im)^\s*(?:Page Should Not Contain|Wait Until Element Is Not Visible)\b.*\$\{(?:[A-Z0-9_]*TEXT|[A-Z0-9_]*LABEL|[A-Z0-9_]*MESSAGE|[A-Z0-9_]*INDICATOR|[A-Z0-9_]*STATUS)\}", content):
        warnings.append(
            "Generated suite contains speculative negative assertions backed by text/indicator variables. Prefer only grounded page-resource absence validations tied to approved elements or approved resource keywords."
        )

    def normalize_keyword_token(value: str) -> str:
        return clean_text(value).lower()

    def scan_keyword_invocation(raw_text: str) -> tuple[str, list[str]]:
        stripped = raw_text.strip()
        parts = [part.strip() for part in re.split(r"\s{2,}|\t+", stripped) if part.strip()]
        if not parts:
            return "", []
        return parts[0], parts[1:]

    def validate_keyword_call(keyword_name: str, arguments: list[str], source_label: str):
        normalized_keyword = normalize_keyword_token(keyword_name)
        if not normalized_keyword:
            return
        if normalized_keyword not in builtin_keywords and normalized_keyword not in selenium_keywords and normalized_keyword not in resource_keyword_names:
            warnings.append(
                f"Generated suite uses an unknown or unsupported keyword '{keyword_name}' in {source_label}. "
                "Review and replace it with an imported resource keyword or a valid Robot Framework/SeleniumLibrary/BuiltIn keyword."
            )
            return
        signature = keyword_signature_map.get(normalized_keyword)
        if signature:
            required_count = len(signature.get("required_args", []))
            total_count = len(signature.get("args", []))
            actual_count = len(arguments)
            if actual_count < required_count:
                errors.append(
                    f"Keyword '{signature.get('name', keyword_name)}' requires {required_count} argument(s) but was called with {actual_count} in {source_label}. Source: {signature.get('source', 'unknown')}"
                )
            elif actual_count > total_count:
                errors.append(
                    f"Keyword '{signature.get('name', keyword_name)}' accepts {total_count} argument(s) but was called with {actual_count} in {source_label}. Source: {signature.get('source', 'unknown')}"
                )

    builtin_keywords, selenium_keywords = get_framework_keyword_catalog()

    if "*** Settings ***" not in content:
        errors.append("Missing *** Settings *** section")
    if "*** Test Cases ***" not in content:
        errors.append("Missing *** Test Cases *** section")

    if "*** Variables ***" in content:
        errors.append("Suite-level *** Variables *** section is not allowed; move reusable test data into the POM resource file")
    if "*** Keywords ***" in content:
        errors.append("Suite-level *** Keywords *** section is not allowed for generated automation; use POM resource keywords instead")

    resource_lines = re.findall(r"(?im)^\s*Resource\s+(.+?)\s*$", content)
    normalized_allowed = {f"../pom_pages/{name}" for name in allowed_resources}
    normalized_allowed.add("../resources/common_keywords.resource")

    for resource in resource_lines:
        cleaned = resource.strip()
        if cleaned not in normalized_allowed:
            errors.append(f"Unauthorized resource import: {cleaned}")

    if "../resources/common_keywords.resource" not in {line.strip() for line in resource_lines}:
        warnings.append("Generated suite does not import ../resources/common_keywords.resource; prefer the shared common layer for browser lifecycle and generic helpers")

    forbidden_keyword_patterns = [
        r"(?im)^\s*Open Browser To Login Page\s*$",
        r"(?im)^\s*Open Browser To Page\s*$",
        r"(?im)^\s*Open Page\s*$",
        r"(?im)^\s*Wait Until .* (?:Page|Textbox|Field) .*Visible\s*$",
    ]
    for pattern in forbidden_keyword_patterns:
        if re.search(pattern, content):
            errors.append("Generated suite contains navigation/wait helper definitions that should live in the POM resource file")
            break

    if re.search(r"(?im)^\s*(?:Input|Enter|Type)\b.*\s{2,}$", content):
        errors.append("Generated suite contains an input keyword call with an empty trailing argument; use ${EMPTY} or ${SPACE} explicitly")

    if re.search(r"\$\{Empty\}", content):
        errors.append("Use Robot built-in ${EMPTY} instead of ${Empty}")

    if re.search(r"\$\{Space\}", content):
        errors.append("Use Robot built-in ${SPACE} instead of ${Space}")

    has_setup = bool(re.search(r"(?im)^\s*(?:Suite Setup|Test Setup)\s+.+$", content))
    has_teardown = bool(re.search(r"(?im)^\s*(?:Suite Teardown|Test Teardown)\s+.+$", content))

    if not has_setup:
        warnings.append("Generated suite does not include Suite Setup or Test Setup; prefer reusable setup keywords when resource context supports them")

    if not has_teardown:
        warnings.append("Generated suite does not include Suite Teardown or Test Teardown; prefer reusable teardown keywords when resource context supports them")

    if has_teardown and not has_setup:
        warnings.append("Generated suite includes teardown but no setup; repair the suite to include setup for browser opening and initial navigation using approved shared/common or page resource helpers")

    startup_sequences: list[list[str]] = []
    current_steps: list[str] = []
    in_test_cases_for_setup_review = False
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        lowered = stripped.lower()
        if lowered == "*** test cases ***":
            in_test_cases_for_setup_review = True
            current_steps = []
            continue
        if lowered.startswith("***") and lowered != "*** test cases ***":
            if current_steps:
                startup_sequences.append(current_steps)
            in_test_cases_for_setup_review = False
            current_steps = []
            continue
        if not in_test_cases_for_setup_review:
            continue
        if stripped and not raw_line.startswith((" ", "\t")):
            if current_steps:
                startup_sequences.append(current_steps)
            current_steps = []
            continue
        if raw_line.startswith((" ", "\t")) and stripped and not stripped.startswith("["):
            keyword_name, _arguments = scan_keyword_invocation(stripped)
            if keyword_name:
                current_steps.append(clean_text(keyword_name).lower())
    if current_steps:
        startup_sequences.append(current_steps)

    if not has_setup and startup_sequences:
        startup_prefixes: dict[str, int] = {}
        for steps in startup_sequences:
            for prefix_length in (1, 2):
                if len(steps) >= prefix_length:
                    prefix = " > ".join(steps[:prefix_length])
                    startup_prefixes[prefix] = startup_prefixes.get(prefix, 0) + 1
        repeated_prefixes = [
            prefix for prefix, count in startup_prefixes.items()
            if count >= max(2, len(startup_sequences) // 2)
        ]
        if repeated_prefixes:
            warnings.append(
                "Generated suite repeats the same startup pattern across most tests but does not use Test Setup or Suite Setup; prefer promoting the repeated page-open/page-ready sequence into setup."
            )

    if re.search(r"(?is)\*\*\*\s*settings\s*\*\*\*.*?\n\s*\n\s*(?:Test Setup|Suite Setup|Test Teardown|Suite Teardown|Resource)", content):
        warnings.append("Generated suite contains unnecessary blank lines inside the Settings section; keep Settings compact")

    if re.search(r"(?im)^\*\*\* Test Cases \*\*\*\n\s*\n", content):
        errors.append("Generated suite contains a blank line after *** Test Cases ***; the first test case must start immediately on the next line")

    keyword_signature_map = build_keyword_signature_map(allowed_resources)
    resource_keyword_names = set(keyword_signature_map.keys())

    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        setup_match = re.match(r"(?im)^\s*(Suite Setup|Test Setup|Suite Teardown|Test Teardown)\s{2,}(.+)$", raw_line)
        if setup_match:
            keyword_name, arguments = scan_keyword_invocation(setup_match.group(2))
            validate_keyword_call(keyword_name, arguments, setup_match.group(1))

    in_test_cases = False
    current_test_steps: list[str] = []
    all_test_steps: list[list[str]] = []
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        lowered = stripped.lower()
        if lowered == "*** test cases ***":
            in_test_cases = True
            current_test_steps = []
            continue
        if lowered.startswith("***") and lowered != "*** test cases ***":
            if current_test_steps:
                all_test_steps.append(current_test_steps)
            in_test_cases = False
            current_test_steps = []
            continue
        if not in_test_cases:
            continue
        if stripped and not raw_line.startswith((" ", "\t")):
            if current_test_steps:
                all_test_steps.append(current_test_steps)
            current_test_steps = []
            continue
        if raw_line.startswith((" ", "\t")) and stripped and not stripped.startswith("["):
            keyword_name, arguments = scan_keyword_invocation(stripped)
            if keyword_name:
                current_test_steps.append(keyword_name)
                validate_keyword_call(keyword_name, arguments, "the suite")
    if current_test_steps:
        all_test_steps.append(current_test_steps)

    common_prefix: list[str] = []
    if len(all_test_steps) >= 2 and all_test_steps[0]:
        common_prefix = list(all_test_steps[0])
        for steps in all_test_steps[1:]:
            prefix_len = 0
            for left, right in zip(common_prefix, steps):
                if clean_text(left).lower() == clean_text(right).lower():
                    prefix_len += 1
                else:
                    break
            common_prefix = common_prefix[:prefix_len]
            if not common_prefix:
                break

    if len(common_prefix) >= 2:
        warnings.append("Generated suite repeats the same startup steps across tests; prefer moving repeated opening/navigation/wait steps into Test Setup or Suite Setup")

    if has_setup and all_test_steps:
        page_startup_keywords = {
            clean_text(name).lower()
            for name in resource_keyword_names
            if any(token in clean_text(name).lower() for token in ["open ", "launch ", "guest state", "page is loaded", "page loaded"])
        }
        repeated_page_startup = {
            name: sum(1 for steps in all_test_steps if steps and clean_text(steps[0]).lower() == name)
            for name in page_startup_keywords
        }
        repeated_page_startup = {name: count for name, count in repeated_page_startup.items() if count >= max(2, len(all_test_steps) // 2)}
        setup_lines = re.findall(r"(?im)^\s*(?:Suite Setup|Test Setup)\s{2,}(.+)$", content)
        configured_setup_keywords = set()
        for line in setup_lines:
            kw_name, _args = scan_keyword_invocation(line)
            if kw_name:
                configured_setup_keywords.add(clean_text(kw_name).lower())
        if repeated_page_startup:
            strongest_startup = max(repeated_page_startup, key=repeated_page_startup.get)
            if strongest_startup not in configured_setup_keywords:
                warnings.append(
                    f"Generated suite has setup configured but still repeats semantic page startup keyword '{strongest_startup}' at the beginning of most tests. Prefer promoting that higher-level page setup abstraction into Test Setup or Suite Setup."
                )

    if not re.search(r"(?im)^AUT-[A-Z0-9]{2,8}-[A-Z0-9_]{3,20}\d{2}:\s+.+$", content):
        warnings.append("Generated suite test case names should follow the concise format AUT-<APPCODE>-<FEATURECODE><NN>: <Title>")

    verbose_identifier_matches = re.findall(r"(?im)^AUT-[A-Z0-9]{2,8}-([A-Z0-9_]{21,})\d{2}:", content)
    if verbose_identifier_matches:
        warnings.append("Generated suite test identifiers appear too verbose; use a concise stable feature code instead of a full workflow-title concatenation")

    if re.search(r"(?im)^(AUT.*)\n(?!\s+\[Tags\])", content):
        warnings.append("Each generated test case should include a [Tags] line immediately after the test case name")

    if not re.search(r"\$\{[A-Z0-9_]+\}", content):
        warnings.append("Generated suite does not appear to use reusable resource variables; prefer resource-file test data over hardcoded inline data")

    inline_business_data_warning_patterns = [
        (
            r"(?im)^\s{4,}(?:Enter Username|Input Username|Type Username)\b.*\s{2,}(?!\$\{)(?!xpath=)(?!css=)(?!id=)(?!name=)(?!//)([^\n]+)$",
            "Policy warning: generated suite contains an inline username literal; semantic business data should come from page-resource variables, not direct values in test cases"
        ),
        (
            r"(?im)^\s{4,}(?:Enter Password|Input Password|Type Password)\b.*\s{2,}(?!\$\{)(?!xpath=)(?!css=)(?!id=)(?!name=)(?!//)([^\n]+)$",
            "Policy warning: generated suite contains an inline password literal; semantic business data should come from page-resource variables, not direct values in test cases"
        ),
        (
            r"(?im)^\s{4,}.*https?://[^\s]+.*$",
            "Policy warning: generated suite contains an inline URL literal; reusable environment or page data should come from page-resource variables, not direct values in test cases"
        ),
    ]
    specific_inline_policy_warning_found = False
    for pattern, message in inline_business_data_warning_patterns:
        if re.search(pattern, content):
            warnings.append(message)
            specific_inline_policy_warning_found = True

    likely_inline_literals = [
        r"(?im)^\s{4,}(?:Enter|Input|Type)\b.*\s{2,}(?!\$\{)(?!xpath=)(?!css=)(?!id=)(?!name=)(?!//)([^\n]+)$",
    ]
    if not specific_inline_policy_warning_found:
        for pattern in likely_inline_literals:
            if re.search(pattern, content):
                warnings.append("Generated suite appears to contain inline literal test data; prefer page-resource variables instead of direct values in test cases")
                break

    if re.search(r"(?im)^\s*Wait Until Element Is Not Visible\s{2,}(?:xpath=|css=|id=|name=)", content):
        warnings.append(
            "Generated suite contains raw negative visibility checks in test bodies. Prefer reusable page-resource validation keywords for guest-state or authenticated-only absence expectations when the manual outcomes imply a stable page-level assertion."
        )
    if re.search(r"(?im)^\s*(?:Page Should Not Contain|Wait Until Element Is Not Visible)\b.*\$\{(?:[A-Z0-9_]*TEXT|[A-Z0-9_]*LABEL|[A-Z0-9_]*MESSAGE|[A-Z0-9_]*INDICATOR|[A-Z0-9_]*STATUS)\}", content):
        warnings.append(
            "Generated suite contains negative assertions backed by speculative text or indicator variables rather than grounded page-resource validations. Prefer approved page-state validations and avoid placeholder-style absence checks."
        )

    is_valid = len(errors) == 0
    message_parts = []
    if errors:
        message_parts.append("\n".join(errors))
    if warnings:
        message_parts.append("Warnings:\n" + "\n".join(warnings))
    return is_valid, "\n\n".join(part for part in message_parts if part)


def validate_manual_content(manual_data: dict) -> tuple[bool, str]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(manual_data, dict):
        return False, "Manual artifact must be a JSON object"

    test_cases = manual_data.get("testCases")
    if not isinstance(test_cases, list) or not test_cases:
        errors.append("Manual artifact must contain a non-empty testCases array")
        return False, "\n".join(errors)

    seen_signatures = set()

    for idx, case in enumerate(test_cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"Test case #{idx} is not an object")
            continue

        title = clean_text(str(case.get("title", "")))
        expected = clean_text(str(case.get("expectedResult", "")))
        case_type = clean_text(str(case.get("type", ""))).lower()
        steps = case.get("steps", [])
        fields = case.get("fields", [])

        if not title:
            errors.append(f"Test case #{idx} is missing title")
        if case_type not in {"positive", "negative", "edge"}:
            errors.append(f"Test case '{title or idx}' has unsupported type '{case_type}'")
        if not isinstance(steps, list) or not steps:
            errors.append(f"Test case '{title or idx}' must contain non-empty steps")
        if not expected:
            errors.append(f"Test case '{title or idx}' must contain expectedResult")
        if not isinstance(fields, list):
            errors.append(f"Test case '{title or idx}' must contain fields as a list")

        signature = (
            title.lower(),
            case_type,
            tuple(clean_text(str(step)).lower() for step in steps if clean_text(str(step))),
            expected.lower(),
        )
        if signature in seen_signatures:
            warnings.append(f"Potential duplicate manual test detected: {title or idx}")
        seen_signatures.add(signature)

    if len(test_cases) < 6:
        warnings.append("Manual test coverage appears thin: fewer than 6 test cases were generated")

    is_valid = len(errors) == 0
    message_parts = []
    if errors:
        message_parts.append("\n".join(errors))
    if warnings:
        message_parts.append("Warnings:\n" + "\n".join(warnings))
    return is_valid, "\n\n".join(part for part in message_parts if part)

def derive_module_name(manual_data: dict, manual_json_path: Path) -> str:
    explicit_prefix = normalize_feature_code(str(manual_data.get("testIdentifierPrefix", "")))
    if explicit_prefix:
        return slugify(explicit_prefix)

    feature_code = normalize_feature_code(str(manual_data.get("feature", "")))
    if feature_code:
        return slugify(feature_code)

    if manual_data.get("workflowName"):
        return slugify(manual_data["workflowName"])
    return slugify(manual_json_path.stem)

def should_exclude_manual(
    manual_json_path: Path,
    manual_data: dict,
    excluded_modules: Set[str],
    excluded_files: Set[str]
) -> bool:
    if manual_json_path.name.lower() in excluded_files:
        return True

    keys = {slugify(manual_json_path.stem)}
    if manual_data.get("workflowName"):
        keys.add(slugify(manual_data["workflowName"]))

    return any(k in excluded_modules for k in keys)

def process_manual_file(config: dict, manual_json_path: Path):
    gc = config["generation_control"]
    ai = config["ai"]

    manual_data = load_json(manual_json_path)

    excluded_modules = set(gc.get("excluded_modules", []))
    excluded_files = set(gc.get("excluded_manual_files", []))
    if should_exclude_manual(manual_json_path, manual_data, excluded_modules, excluded_files):
        logger.info("Excluded manual file: %s", manual_json_path.name)
        return

    resource_files = manual_data.get("resourceFiles", [])
    if not isinstance(resource_files, list) or not resource_files:
        raise ValueError(f"{manual_json_path.name}: 'resourceFiles' must be a non-empty list")

    resource_files = [str(x).replace("\\", "/").strip() for x in resource_files if str(x).strip()]
    if not resource_files:
        raise ValueError(f"{manual_json_path.name}: 'resourceFiles' must contain valid entries")

    module_name = derive_module_name(manual_data, manual_json_path)
    tests_output_dir = BASE_DIR / config["robot_tests_output_dir"]
    output_path = tests_output_dir / f"{module_name}_tests.robot"

    if output_path.exists() and not gc.get("overwrite_robot_tests", False):
        logger.info("Skipped existing robot test (overwrite disabled): %s", output_path.name)
        return

    pom_root = BASE_DIR / config["pom_output_dir"]
    resource_context = []
    for rel_path in resource_files:
        resource_path = pom_root / rel_path
        if not resource_path.exists():
            raise FileNotFoundError(f"{manual_json_path.name}: resource not found -> {resource_path}")
        resource_context.append(parse_resource_file(resource_path))

    resources_dir = BASE_DIR / "resources"
    if resources_dir.exists():
        for common_resource_path in sorted(resources_dir.glob("*.resource")):
            try:
                resource_context.append(parse_resource_file(common_resource_path))
            except Exception:
                continue

    if not ai.get("enabled", True):
        raise ValueError("AI is disabled in config.")

    endpoint = ai.get("endpoint", "")
    token = get_ai_token(ai)
    if not endpoint or not token:
        raise ValueError("AI endpoint/token missing in config.")

    identifier_policy = resolve_test_identifier_policy(manual_data)

    prompt = build_prompt(manual_data, resource_context)
    robot_content = call_ai_chat(
        endpoint=endpoint,
        token=token,
        prompt=prompt,
        timeout_seconds=ai.get("timeout_seconds", 120),
        verify_ssl=ai.get("verify_ssl", False),
    )

    robot_content = robot_content.strip()
    robot_content = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", robot_content)
    robot_content = re.sub(r"\n```$", "", robot_content)
    robot_content = normalize_generated_robot_identifiers(robot_content, identifier_policy)

    review_prompt = build_review_prompt(manual_data, resource_context, robot_content)
    reviewed_robot_content = call_ai_chat(
        endpoint=endpoint,
        token=token,
        prompt=review_prompt,
        timeout_seconds=ai.get("timeout_seconds", 120),
        verify_ssl=ai.get("verify_ssl", False),
    )
    reviewed_robot_content = reviewed_robot_content.strip()
    reviewed_robot_content = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", reviewed_robot_content)
    reviewed_robot_content = re.sub(r"\n```$", "", reviewed_robot_content)
    robot_content = normalize_generated_robot_identifiers(reviewed_robot_content or robot_content, identifier_policy)

    validation_review_prompt = build_validation_review_prompt(manual_data, resource_context, robot_content)
    validated_robot_content = call_ai_chat(
        endpoint=endpoint,
        token=token,
        prompt=validation_review_prompt,
        timeout_seconds=ai.get("timeout_seconds", 120),
        verify_ssl=ai.get("verify_ssl", False),
    )
    validated_robot_content = validated_robot_content.strip()
    validated_robot_content = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", validated_robot_content)
    validated_robot_content = re.sub(r"\n```$", "", validated_robot_content)
    robot_content = normalize_generated_robot_identifiers(validated_robot_content or robot_content, identifier_policy)

    is_valid, validation_message = validate_robot_content(robot_content, resource_files)
    if validation_message and re.search(r"unknown or unsupported keyword", validation_message, flags=re.IGNORECASE):
        keyword_repair_prompt = (
            build_validation_review_prompt(manual_data, resource_context, robot_content)
            + "\n\nValidation findings to repair before returning the suite:\n"
            + validation_message
            + "\n\nRepair instruction:\n"
            + "Replace any unknown keyword by reusing imported resource keywords or by choosing only from allowed_builtin_keywords and allowed_selenium_keywords already provided in the input JSON. "
            + "Focus on imported libraries, imported resources, existing keyword signatures, and approved keyword inventories. "
            + "Do not invent replacement keywords. If a needed behavior is missing, compose it using only valid existing keywords from the provided inventories. "
            + "Do not explain. Return only corrected Robot Framework code."
        )
        repaired_robot_content = call_ai_chat(
            endpoint=endpoint,
            token=token,
            prompt=keyword_repair_prompt,
            timeout_seconds=ai.get("timeout_seconds", 120),
            verify_ssl=ai.get("verify_ssl", False),
        )
        repaired_robot_content = repaired_robot_content.strip()
        repaired_robot_content = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", repaired_robot_content)
        repaired_robot_content = re.sub(r"\n```$", "", repaired_robot_content)
        robot_content = normalize_generated_robot_identifiers(repaired_robot_content or robot_content, identifier_policy)
        is_valid, validation_message = validate_robot_content(robot_content, resource_files)

    if validation_message:
        followup_review_prompt = (
            build_validation_review_prompt(manual_data, resource_context, robot_content)
            + "\n\nValidation and quality findings to improve:\n"
            + validation_message
            + "\n\nFollow-up repair instructions:\n"
            + "Use the provided imported resource context and allowed keyword inventories as guardrails. "
            + "Reduce hallucination risk by preferring existing imported resource keywords, exact supported library keywords, and valid keyword signatures. "
            + "When a shared/common helper exists for generic waiting, clicking, navigation, or text/password entry, prefer that helper over direct SeleniumLibrary usage. "
            + "Do not block the workflow. Return the best corrected Robot Framework suite possible using only valid framework-aligned keywords."
        )
        followup_robot_content = call_ai_chat(
            endpoint=endpoint,
            token=token,
            prompt=followup_review_prompt,
            timeout_seconds=ai.get("timeout_seconds", 120),
            verify_ssl=ai.get("verify_ssl", False),
        )
        followup_robot_content = followup_robot_content.strip()
        followup_robot_content = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", followup_robot_content)
        followup_robot_content = re.sub(r"\n```$", "", followup_robot_content)
        robot_content = normalize_generated_robot_identifiers(followup_robot_content or robot_content, identifier_policy)
        is_valid, validation_message = validate_robot_content(robot_content, resource_files)
    alignment_valid, alignment_message = validate_robot_alignment_with_resource_context(robot_content, resource_context)
    manual_expected_outcomes = collect_manual_expected_outcomes(manual_data)
    resource_validation_keywords = collect_resource_validation_keywords(resource_context)
    assertion_warning = warn_on_assertion_quality(manual_expected_outcomes, robot_content, resource_validation_keywords)
    if not is_valid:
        logger.warning(
            "Generated robot content for %s did not fully validate after repair: %s",
            manual_json_path.name,
            validation_message,
        )
    if alignment_message:
        logger.warning("Robot alignment review for %s: %s", manual_json_path.name, alignment_message)
    if assertion_warning:
        logger.warning("Assertion quality review for %s: %s", manual_json_path.name, assertion_warning)
    
    ensure_dir(tests_output_dir)
    output_path.write_text(robot_content, encoding="utf-8")
    logger.info("Generated robot test: %s", output_path)

def main():
    config = validate_config(load_json(CONFIG_PATH))

    manual_tests_dir = BASE_DIR / config["manual_tests_output_dir"]
    if not manual_tests_dir.exists():
        raise FileNotFoundError(f"manual_tests directory not found: {manual_tests_dir}")

    manual_files = sorted(manual_tests_dir.rglob("*.json"))
    if not manual_files:
        logger.info("No manual test JSON files found in: %s", manual_tests_dir)
        return

    logger.info("Found %d manual files", len(manual_files))
    for mf in manual_files:
        try:
            process_manual_file(config, mf)
        except Exception as exc:
            logger.error("Failed for %s: %s", mf.name, exc)

if __name__ == "__main__":
    main()