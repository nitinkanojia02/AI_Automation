import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from scripts.artifact_reuse import normalize_name_tokens

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from scripts.artifact_reuse import analyze_reuse_conflicts
except ModuleNotFoundError:
    import sys
    sys.path.append(str(BASE_DIR))
    from scripts.artifact_reuse import analyze_reuse_conflicts

WORKFLOW_INPUT_DIR = BASE_DIR / "workflow_inputs"
MANUAL_DIR = BASE_DIR / "manual_tests"
TESTS_DIR = BASE_DIR / "tests"
POM_DIR = BASE_DIR / "pom_pages"
RESOURCES_DIR = BASE_DIR / "resources"
WORKFLOW_KNOWLEDGE_DIR = BASE_DIR / "artifacts" / "workflow_knowledge"
POM_METADATA_DIR = BASE_DIR / "pom_pages"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slugify(value: str) -> str:
    text = clean_text(value).lower()
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


def ensure_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def unique_strings(values: List[Any], limit: int | None = None) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in values:
        cleaned = clean_text(item)
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(cleaned)
        if limit and len(result) >= limit:
            break
    return result


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract_variables_from_resource(resource_text: str) -> List[Dict[str, str]]:
    lines = resource_text.splitlines()
    in_variables = False
    variables: List[Dict[str, str]] = []
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
            variables.append({"name": parts[0][2:-1].strip(), "value": parts[1].strip()})
    return variables


def extract_keywords_from_resource(resource_text: str) -> List[Dict[str, Any]]:
    lines = resource_text.splitlines()
    in_keywords = False
    keywords: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
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
    return keywords


def extract_manual_test_cases(manual_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("testCases", "manualTests", "tests", "cases"):
        value = manual_data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def normalize_heading_label(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    text = re.sub(r"^\d+[.):-]?\s*", "", text)
    return clean_text(text).lower()


def normalize_text_blocks(value: Any) -> List[str]:
    if isinstance(value, list):
        flattened: List[str] = []
        for item in value:
            flattened.extend(normalize_text_blocks(item))
        return unique_strings(flattened)
    if isinstance(value, dict):
        flattened: List[str] = []
        heading = clean_text(value.get("heading") or value.get("title") or value.get("section"))
        body = value.get("body") if isinstance(value.get("body"), list) else value.get("content")
        if heading:
            flattened.append(heading)
        flattened.extend(normalize_text_blocks(body))
        for key in ("items", "bullets", "lines", "children", "sections"):
            flattened.extend(normalize_text_blocks(value.get(key)))
        return unique_strings(flattened)
    if isinstance(value, str):
        cleaned = clean_text(value)
        return [cleaned] if cleaned else []
    return []


def select_relevant_lines(values: List[str], keywords: List[str], limit: int = 12) -> List[str]:
    del keywords
    if not values:
        return []
    return unique_strings(values, limit=limit)


def compact_story_lines(values: List[str], limit: int = 12) -> List[str]:
    return unique_strings(values, limit=limit)


def extract_story_urls(story_sections: Dict[str, List[str]]) -> List[str]:
    urls: List[str] = []
    for section_values in story_sections.values():
        for item in ensure_list(section_values):
            for match in re.findall(r"https?://[^\s)]+", str(item or "")):
                cleaned = clean_text(match)
                if cleaned:
                    urls.append(cleaned)
    return unique_strings(urls, limit=10)


def extract_story_fragments(story_sections: Dict[str, List[str]]) -> List[str]:
    fragments: List[str] = []
    fragment_pattern = re.compile(r"(?<!https:)(?<!http:)(/[A-Za-z0-9_?=&\-/.]+)")
    token_pattern = re.compile(r"^[A-Za-z0-9_?=&\-/.]+$")
    for section_values in story_sections.values():
        for item in ensure_list(section_values):
            text = str(item or "")
            for match in fragment_pattern.findall(text):
                cleaned = clean_text(match).rstrip(".,;:")
                if not cleaned or cleaned.startswith("//"):
                    continue
                if cleaned.startswith("/localhost/") or cleaned.startswith("/127.0.0.1/"):
                    continue
                fragments.append(cleaned)
            cleaned_text = clean_text(text).rstrip(".,;:")
            if not cleaned_text or cleaned_text.startswith("http://") or cleaned_text.startswith("https://"):
                continue
            if " " in cleaned_text:
                continue
            if token_pattern.fullmatch(cleaned_text) and any(token in cleaned_text for token in ("-", "?", "/")):
                if cleaned_text.startswith("/localhost/") or cleaned_text.startswith("/127.0.0.1/"):
                    continue
                fragments.append(cleaned_text)
    return unique_strings(fragments, limit=20)


def collect_sectioned_description_lines(description: Any) -> Dict[str, List[str]]:
    if not isinstance(description, str):
        return {}
    lines = [line.rstrip() for line in description.splitlines()]
    sections: Dict[str, List[str]] = {}
    current_key = ""
    heading_pattern = re.compile(r"^\s*(\d+[.):-]?\s+)?([A-Za-z][A-Za-z /_-]+):?\s*$")
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        heading_match = heading_pattern.match(stripped)
        if heading_match and len(stripped.split()) <= 8:
            current_key = normalize_heading_label(heading_match.group(2))
            sections.setdefault(current_key, [])
            continue
        if current_key:
            bullet = re.sub(r"^[-*•]+\s*", "", stripped)
            numbered = re.sub(r"^\d+[.):-]?\s*", "", bullet)
            cleaned = clean_text(numbered)
            if cleaned:
                sections.setdefault(current_key, []).append(cleaned)
    return {key: unique_strings(value) for key, value in sections.items() if value}


def _pick_story_section(external: Dict[str, Any], description_sections: Dict[str, List[str]], external_keys: List[str], section_aliases: List[str], fallback: Any = None, limit: int = 10) -> List[str]:
    values: List[str] = []
    for key in external_keys:
        values.extend(normalize_text_blocks(external.get(key)))
    for alias in section_aliases:
        values.extend(description_sections.get(normalize_heading_label(alias), []))
    if not values and fallback is not None:
        values.extend(normalize_text_blocks(fallback))
    return compact_story_lines(values, limit=limit)


def collect_workflow_story_lines(workflow_input: Dict[str, Any]) -> Dict[str, List[str]]:
    external = workflow_input.get("externalContext") if isinstance(workflow_input.get("externalContext"), dict) else {}
    user_story = workflow_input.get("userStory") if isinstance(workflow_input.get("userStory"), str) else ""
    description_sections = collect_sectioned_description_lines(external.get("description"))
    acceptance = workflow_input.get("acceptanceCriteria") if isinstance(workflow_input.get("acceptanceCriteria"), list) else external.get("acceptanceCriteria")
    validations = external.get("validationExpectations") if isinstance(external.get("validationExpectations"), list) else workflow_input.get("observedValidations")
    application_context = external.get("applicationContext")
    entry_conditions = external.get("entryConditions") if external.get("entryConditions") not in (None, [], "") else workflow_input.get("observedPreconditions")
    behavior_rules = external.get("behaviorRules")
    transition_expectations = external.get("transitionExpectations")
    reuse_guidance = external.get("pomReuseGuidance")
    approved_test_data_guidance = external.get("approvedTestDataGuidance")

    return {
        "userStory": unique_strings(([clean_text(user_story)] if clean_text(user_story) else []) or description_sections.get("user story", []), limit=1),
        "applicationContext": _pick_story_section(external, description_sections, ["applicationContext"], ["application context"], application_context, limit=8),
        "entryConditions": _pick_story_section(external, description_sections, ["entryConditions"], ["entry conditions"], entry_conditions, limit=12),
        "acceptanceCriteria": _pick_story_section(external, description_sections, ["acceptanceCriteria"], ["acceptance criteria"], acceptance, limit=14),
        "behaviorRules": _pick_story_section(external, description_sections, ["behaviorRules"], ["business rules"], behavior_rules, limit=12),
        "validationExpectations": _pick_story_section(external, description_sections, ["validationExpectations"], ["validation expectations"], validations, limit=12),
        "transitionExpectations": _pick_story_section(external, description_sections, ["transitionExpectations"], ["transition expectations", "primary navigation journey"], transition_expectations, limit=16),
        "reuseGuidance": _pick_story_section(external, description_sections, ["pomReuseGuidance"], ["resource reuse guidance", "downstream automation guidance"], reuse_guidance, limit=10),
        "approvedTestDataGuidance": _pick_story_section(external, description_sections, ["approvedTestDataGuidance"], ["approved test data"], approved_test_data_guidance, limit=10),
    }


def derive_navigation_model(workflow_input: Dict[str, Any], story_sections: Dict[str, List[str]]) -> Dict[str, Any]:
    entry_page = workflow_input.get("entryPage") if isinstance(workflow_input.get("entryPage"), dict) else {}
    target_page = workflow_input.get("targetPage") if isinstance(workflow_input.get("targetPage"), dict) else {}
    pages = workflow_input.get("pages") if isinstance(workflow_input.get("pages"), list) else []
    primary_page = pages[0] if pages and isinstance(pages[0], dict) else {}

    inferred_target_name = clean_text(target_page.get("name") or primary_page.get("name"))
    inferred_target_url = clean_text(target_page.get("url"))
    inferred_entry_name = clean_text(entry_page.get("name"))
    inferred_entry_url = clean_text(entry_page.get("url"))

    if not inferred_entry_name:
        inferred_entry_name = clean_text(primary_page.get("name"))

    if inferred_entry_name and inferred_target_name and inferred_entry_name.lower() == inferred_target_name.lower():
        for step in ensure_list(workflow_input.get("navigationSteps")):
            if not isinstance(step, dict):
                continue
            candidate_page = clean_text(step.get("page"))
            if candidate_page and candidate_page.lower() != inferred_target_name.lower():
                inferred_entry_name = candidate_page
                break

    story_urls = extract_story_urls(story_sections)
    story_fragments = extract_story_fragments(story_sections)
    if not inferred_entry_url and story_urls:
        inferred_entry_url = story_urls[0]
    if not inferred_target_url and story_urls:
        inferred_target_url = story_urls[0]

    raw_target_signals = [item for item in ensure_list(workflow_input.get("targetPageSignals")) if isinstance(item, dict)]
    if not raw_target_signals:
        for value in story_fragments:
            signal_type = "urlContains" if any(token in value for token in ("/", "?", "-")) else "pageName"
            raw_target_signals.append({"type": signal_type, "value": value})

    target_signals: List[Dict[str, Any]] = []
    seen_signal_keys: set[str] = set()
    for item in raw_target_signals:
        signal_type = clean_text(item.get("type"))
        signal_value = clean_text(item.get("value"))
        if not signal_type or not signal_value:
            continue
        marker = f"{signal_type.lower()}::{signal_value.lower()}"
        if marker in seen_signal_keys:
            continue
        seen_signal_keys.add(marker)
        target_signals.append({"type": signal_type, "value": signal_value})

    journey: List[Dict[str, str]] = []
    for step in ensure_list(workflow_input.get("navigationSteps")):
        if not isinstance(step, dict):
            continue
        action = clean_text(step.get("action"))
        page = clean_text(step.get("page"))
        element = clean_text(step.get("element"))
        if not any([action, page, element]):
            continue
        journey.append({
            "page": page,
            "action": action,
            "element": element,
        })

    return {
        "entryPoint": {
            "name": inferred_entry_name,
            "url": inferred_entry_url,
            "state": clean_text(entry_page.get("state")),
        },
        "target": {
            "name": inferred_target_name,
            "url": inferred_target_url,
        },
        "journey": journey[:10],
        "targetSignals": target_signals[:20],
    }


def load_approved_elements_for_workflow(workflow_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    approved: List[Dict[str, Any]] = []
    for page in ensure_list(workflow_input.get("pages")):
        if not isinstance(page, dict):
            continue
        page_name = clean_text(page.get("name"))
        if not page_name:
            continue
        page_approved: List[Dict[str, Any]] = []
        candidates = [
            POM_DIR / page_name / "metadata" / f"{page_name}.elements.reviewed.json",
            POM_DIR / page_name / "metadata" / f"{page_name}.elements.json",
        ]
        for path in candidates:
            payload = safe_load_json(path)
            if not payload:
                continue
            elements = payload.get("elements") if isinstance(payload, dict) else payload if isinstance(payload, list) else []
            for item in ensure_list(elements):
                if not isinstance(item, dict):
                    continue
                name = clean_text(item.get("approvedName") or item.get("name"))
                locator = clean_text(item.get("locator"))
                if not name or not locator:
                    continue
                page_approved.append({
                    "page": page_name,
                    "name": name,
                    "type": clean_text(item.get("type") or "element").lower() or "element",
                    "locator": locator,
                })
            if page_approved:
                approved.extend(page_approved)
                break
    unique_payloads: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in approved:
        key = f"{item.get('page','').lower()}::{item.get('name','').lower()}::{item.get('locator','').lower()}"
        if key in seen:
            continue
        seen.add(key)
        unique_payloads.append(item)
    return unique_payloads[:80]


def sanitize_reuse_analysis(reuse_analysis: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(reuse_analysis, dict):
        return {
            "duplicateVariables": [],
            "duplicateKeywords": [],
            "variableReuseCandidates": [],
            "keywordReuseCandidates": [],
            "ownershipConflicts": [],
            "summary": {},
        }

    def _primary_resource(item: Any) -> str:
        if not isinstance(item, dict):
            return ""
        return clean_text(item.get("resource") or item.get("ownerResource") or item.get("owner"))

    def _secondary_resource(item: Any) -> str:
        if not isinstance(item, dict):
            return ""
        return clean_text(item.get("duplicateResource") or item.get("candidateResource") or item.get("reusedFrom") or item.get("candidate"))

    def _is_cross_resource(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        primary = _primary_resource(item)
        secondary = _secondary_resource(item)
        if primary and secondary:
            return primary.lower() != secondary.lower()
        return bool(primary or secondary)

    sanitized = dict(reuse_analysis)
    for key in ("duplicateVariables", "duplicateKeywords", "variableReuseCandidates", "keywordReuseCandidates", "ownershipConflicts"):
        values = ensure_list(sanitized.get(key))
        filtered = [item for item in values if _is_cross_resource(item)]
        sanitized[key] = filtered

    summary = sanitized.get("summary") if isinstance(sanitized.get("summary"), dict) else {}
    sanitized["summary"] = {
        "duplicateVariableCount": len(sanitized.get("duplicateVariables", [])),
        "duplicateKeywordCount": len(sanitized.get("duplicateKeywords", [])),
        "variableReuseCandidateCount": len(sanitized.get("variableReuseCandidates", [])),
        "keywordReuseCandidateCount": len(sanitized.get("keywordReuseCandidates", [])),
        "ownershipConflictCount": len(sanitized.get("ownershipConflicts", [])),
        **{k: v for k, v in summary.items() if k not in {
            "duplicateVariableCount", "duplicateKeywordCount", "variableReuseCandidateCount", "keywordReuseCandidateCount", "ownershipConflictCount"
        }},
    }
    return sanitized


def collect_resource_knowledge(workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    resource_files = [str(item).replace('\\', '/').strip() for item in ensure_list(workflow_input.get('resourceFiles')) if clean_text(item)]
    inferred = workflow_input.get('inferredReuseContext') if isinstance(workflow_input.get('inferredReuseContext'), dict) else {}
    authoritative = [str(item).replace('\\', '/').strip() for item in ensure_list(inferred.get('authoritativeResourceFiles')) if clean_text(item)]
    inferred_relevant = [str(item).replace('\\', '/').strip() for item in ensure_list(inferred.get('inferredRelevantResourceFiles')) if clean_text(item)]
    merged_resources: List[str] = []
    for item in resource_files + authoritative + inferred_relevant:
        if item and item not in merged_resources:
            merged_resources.append(item)

    resource_summaries: List[Dict[str, Any]] = []
    resource_ownership: List[Dict[str, Any]] = []
    shared_resources: List[str] = []

    for rel_path in merged_resources:
        normalized_rel = rel_path.replace('\\', '/').lstrip('/')
        candidate_paths = [BASE_DIR / normalized_rel, POM_DIR / normalized_rel]
        path = next((item for item in candidate_paths if item.exists()), None)
        if not path:
            continue
        text = read_text(path)
        variables = extract_variables_from_resource(text)
        keywords = extract_keywords_from_resource(text)
        variable_names = unique_strings([item.get('name', '') for item in variables], limit=40)
        keyword_names = unique_strings([item.get('name', '') for item in keywords], limit=60)
        rel_from_base = str(path.relative_to(BASE_DIR)).replace('\\', '/')
        resource_type = 'common' if rel_from_base.startswith('resources/') else 'page'
        resource_summaries.append({
            'resourceFile': rel_from_base,
            'type': resource_type,
            'variableNames': variable_names,
            'keywordNames': keyword_names,
        })
        resource_ownership.append({
            'resource': rel_from_base,
            'variables': variable_names,
            'keywords': keyword_names,
        })

    for common_path in sorted(RESOURCES_DIR.glob('*.resource')):
        rel_path = str(common_path.relative_to(BASE_DIR)).replace('\\', '/')
        if rel_path in {item.get('resourceFile') for item in resource_summaries}:
            shared_resources.append(rel_path)
            continue
        shared_resources.append(rel_path)
        text = read_text(common_path)
        variables = extract_variables_from_resource(text)
        keywords = extract_keywords_from_resource(text)
        resource_summaries.append({
            'resourceFile': rel_path,
            'type': 'common',
            'variableNames': unique_strings([item.get('name', '') for item in variables], limit=40),
            'keywordNames': unique_strings([item.get('name', '') for item in keywords], limit=60),
        })

    reuse_analysis = {
        "duplicateVariables": [],
        "duplicateKeywords": [],
        "variableReuseCandidates": [],
        "keywordReuseCandidates": [],
        "ownershipConflicts": [],
        "summary": {},
    }

    return {
        'authoritativeResources': unique_strings(merged_resources, limit=30),
        'sharedResources': unique_strings(shared_resources, limit=20),
        'resourceSummaries': resource_summaries,
        'resourceOwnership': resource_ownership,
        'reuseSignals': reuse_analysis,
    }


def collect_manual_coverage(manual_data: Dict[str, Any]) -> Dict[str, Any]:
    cases = extract_manual_test_cases(manual_data)
    scenarios = []
    validations: List[str] = []
    for case in cases:
        title = clean_text(case.get('title'))
        expected = clean_text(case.get('expectedResult') or case.get('expected') or case.get('expectedOutcome'))
        if title:
            scenarios.append({
                'id': clean_text(case.get('id')),
                'title': title,
                'type': clean_text(case.get('type') or case.get('scenarioType') or '').lower(),
                'expectedResult': expected,
            })
        if expected:
            validations.append(expected)
    return {
        'approvedScenarios': scenarios[:40],
        'validations': unique_strings(validations, limit=20),
        'transitions': [],
    }


def collect_automation_knowledge(workflow_slug: str, workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    approved_keywords: List[Dict[str, Any]] = []
    seen_keyword_keys: set[str] = set()
    for page in ensure_list(workflow_input.get('pages')):
        if not isinstance(page, dict):
            continue
        page_name = clean_text(page.get('name'))
        if not page_name:
            continue
        resource_path = POM_DIR / page_name / f'{page_name}.resource'
        if resource_path.exists():
            for item in extract_keywords_from_resource(read_text(resource_path)):
                name = clean_text(item.get('name'))
                if not name:
                    continue
                key = f"{page_name.lower()}::{name.lower()}"
                if key in seen_keyword_keys:
                    continue
                seen_keyword_keys.add(key)
                approved_keywords.append({
                    'page': page_name,
                    'name': name,
                    'targetElement': '',
                    'action': '',
                })
            continue
        for path in [
            POM_DIR / page_name / 'metadata' / f'{page_name}.keywords.reviewed.json',
            POM_DIR / page_name / 'metadata' / f'{page_name}.keywords.json',
        ]:
            payload = safe_load_json(path)
            if payload and isinstance(payload, dict):
                for item in ensure_list(payload.get('keywords')):
                    if not isinstance(item, dict):
                        continue
                    name = clean_text(item.get('keywordName'))
                    key = f"{page_name.lower()}::{name.lower()}"
                    if not name or key in seen_keyword_keys:
                        continue
                    seen_keyword_keys.add(key)
                    approved_keywords.append({
                        'page': page_name,
                        'name': name,
                        'targetElement': clean_text(item.get('targetElement')),
                        'action': clean_text(item.get('action')).lower(),
                    })
                if approved_keywords:
                    break

    suite_candidates = [
        TESTS_DIR / f'{workflow_slug}_tests.robot',
        TESTS_DIR / f'{clean_text(workflow_input.get("testIdentifierPrefix", "")).lower()}_tests.robot',
    ]
    approved_tests: List[Dict[str, str]] = []
    for suite_path in suite_candidates:
        if not suite_path.exists():
            continue
        in_test_cases = False
        for line in read_text(suite_path).splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if lowered == '*** test cases ***':
                in_test_cases = True
                continue
            if stripped.startswith('***') and lowered != '*** test cases ***':
                in_test_cases = False
                continue
            if in_test_cases and stripped and not line.startswith((' ', '\t')):
                approved_tests.append({'name': stripped})
        if approved_tests:
            break

    return {
        'approvedKeywords': [item for item in approved_keywords if item.get('name')][:80],
        'approvedTests': unique_strings([item.get('name') for item in approved_tests], limit=80),
        'wrapperExpectations': [
            'Reuse approved shared/common wrapper keywords before low-level SeleniumLibrary actions.',
            'Do not invent suite-level custom keywords; compose from approved upstream resource knowledge.',
        ],
    }


def extract_upstream_workflow_candidates(workflow_input: Dict[str, Any], resource_knowledge: Dict[str, Any], story_sections: Dict[str, List[str]]) -> List[str]:
    del resource_knowledge, story_sections
    candidates: List[str] = []
    inferred = workflow_input.get('inferredReuseContext') if isinstance(workflow_input.get('inferredReuseContext'), dict) else {}
    current_slug = slugify(clean_text(workflow_input.get('workflowName')) or clean_text(workflow_input.get('feature')))
    for resource in ensure_list(inferred.get('authoritativeResourceFiles')) + ensure_list(inferred.get('inferredRelevantResourceFiles')):
        normalized = str(resource).replace('\\', '/').strip()
        page_name = Path(normalized).parent.name
        slug = slugify(page_name.replace('_page', '')) if page_name else ''
        if slug and slug != current_slug and slug not in candidates:
            candidates.append(slug)
    return candidates[:10]


def collect_unresolved_gaps_for_workflow(workflow_input: Dict[str, Any]) -> List[str]:
    gaps: List[str] = []
    for page in ensure_list(workflow_input.get('pages')):
        if not isinstance(page, dict):
            continue
        page_name = clean_text(page.get('name'))
        if not page_name:
            continue
        reviewed_path = POM_DIR / page_name / 'metadata' / f'{page_name}.elements.reviewed.json'
        payload = safe_load_json(reviewed_path)
        if not isinstance(payload, dict):
            continue
        review_summary = payload.get('reviewSummary') if isinstance(payload.get('reviewSummary'), dict) else {}
        for issue in ensure_list(review_summary.get('issues')):
            if isinstance(issue, dict):
                message = clean_text(issue.get('message'))
                if message:
                    gaps.append(message)
    return unique_strings(gaps, limit=20)


def derive_reusable_flows(workflow_input: Dict[str, Any], navigation_model: Dict[str, Any], resource_knowledge: Dict[str, Any]) -> List[Dict[str, Any]]:
    resource_files = [str(item).replace('\\', '/').strip() for item in ensure_list(workflow_input.get('resourceFiles')) if clean_text(item)]
    entry_point = navigation_model.get('entryPoint') if isinstance(navigation_model.get('entryPoint'), dict) else {}
    flows: List[Dict[str, Any]] = []

    for resource_file in resource_files:
        page_name = Path(resource_file).stem.strip()
        if not page_name:
            continue
        resource_path = POM_DIR / resource_file
        if not resource_path.exists():
            continue
        resource_text = read_text(resource_path)
        keywords = extract_keywords_from_resource(resource_text)
        variables = extract_variables_from_resource(resource_text)
        variable_by_name = {clean_text(item.get('name')): clean_text(item.get('value')) for item in variables}

        click_keywords = {
            clean_text(item.get('name')): item
            for item in keywords
            if clean_text(item.get('name')).lower().startswith('click ')
        }
        verify_keywords = [item for item in keywords if clean_text(item.get('name')).lower().startswith('verify ') and 'redirect' in clean_text(item.get('name')).lower()]

        signal_pool: Dict[str, List[Dict[str, Any]]] = {}
        for verify_keyword in verify_keywords:
            verify_name = clean_text(verify_keyword.get('name'))
            signal_key = slugify(verify_name.replace('Verify ', '', 1).replace('Navigation Redirect', '').strip())
            for body_line in ensure_list(verify_keyword.get('body')):
                line = clean_text(body_line)
                if not line:
                    continue
                parts = re.split(r"\s{2,}|\t+", line)
                command = ''
                target_value = ''
                if len(parts) >= 2:
                    command = clean_text(parts[0]).lower()
                    target_value = clean_text(parts[-1])
                else:
                    variable_match = re.search(r"(\$\{[^}]+\})", line)
                    if variable_match:
                        target_value = clean_text(variable_match.group(1))
                        command = clean_text(line[:variable_match.start()]).lower()
                if not command or not target_value:
                    continue
                if target_value.startswith('${') and target_value.endswith('}'):
                    target_value = variable_by_name.get(target_value[2:-1].strip(), '')
                target_value = clean_text(target_value)
                if not target_value:
                    continue
                signal_type = ''
                if 'location should be' in command or 'location is' in command:
                    signal_type = 'urlEquals'
                elif 'location should contain' in command or 'location contains' in command:
                    signal_type = 'urlContains'
                if signal_type:
                    signal_pool.setdefault(signal_key, []).append({'type': signal_type, 'value': target_value})

        for keyword_name in click_keywords:
            element_label = keyword_name.replace('Click ', '', 1)
            normalized_label = element_label.replace(' Button', '').strip()
            flow_signal_key = slugify(normalized_label)
            matched_signals: List[Dict[str, Any]] = signal_pool.get(flow_signal_key, [])[:]
            unique_signals: List[Dict[str, Any]] = []
            seen_signal_keys: set[str] = set()
            for signal in matched_signals:
                signal_type = clean_text(signal.get('type'))
                signal_value = clean_text(signal.get('value'))
                if not signal_type or not signal_value:
                    continue
                marker = f"{signal_type.lower()}::{signal_value.lower()}"
                if marker in seen_signal_keys:
                    continue
                seen_signal_keys.add(marker)
                unique_signals.append({'type': signal_type, 'value': signal_value})
            if not unique_signals:
                continue
            primary_signal = unique_signals[0]
            signal_value = clean_text(primary_signal.get('value'))
            target_name = ''
            if signal_value:
                signal_slug = slugify(signal_value.strip('/').split('?', 1)[0].split('/')[-1])
                target_name = f"{signal_slug}_page" if signal_slug else ''
            flows.append({
                'flowId': f"{page_name}.entry_via_{slugify(element_label)}",
                'entryPage': {
                    'name': clean_text(entry_point.get('name')) or page_name,
                    'url': clean_text(entry_point.get('url')),
                    'state': clean_text(entry_point.get('state')),
                },
                'targetPage': {
                    'name': target_name,
                    'url': signal_value,
                },
                'steps': [{
                    'action': 'clickKnownElement',
                    'page': page_name,
                    'element': slugify(element_label),
                }],
                'targetSignals': unique_signals,
                'resourceFiles': resource_knowledge.get('authoritativeResources', []),
            })

    deduped: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for flow in flows:
        marker = clean_text(flow.get('flowId'))
        if not marker or marker in seen:
            continue
        seen.add(marker)
        deduped.append(flow)
    return deduped[:25]


def build_workflow_knowledge_context(workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    from scripts.workflow_context import build_workflow_resource_context

    workflow_name = clean_text(workflow_input.get('workflowName')) or clean_text(workflow_input.get('feature')) or 'workflow'
    workflow_slug = slugify(workflow_name)
    enriched_workflow_input = dict(workflow_input)
    enriched_workflow_input['resourceContext'] = build_workflow_resource_context(enriched_workflow_input)
    story_sections = collect_workflow_story_lines(enriched_workflow_input)
    approved_elements = load_approved_elements_for_workflow(enriched_workflow_input)
    resource_knowledge = collect_resource_knowledge(enriched_workflow_input)
    navigation_model = derive_navigation_model(enriched_workflow_input, story_sections)
    unresolved_gaps = collect_unresolved_gaps_for_workflow(enriched_workflow_input)

    feature = clean_text(enriched_workflow_input.get('feature')) or clean_text(enriched_workflow_input.get('workflowName')) or workflow_slug
    application_code = clean_text(enriched_workflow_input.get('applicationCode'))
    test_identifier_prefix = clean_text(enriched_workflow_input.get('testIdentifierPrefix'))
    upstream_workflow_slugs = extract_upstream_workflow_candidates(enriched_workflow_input, resource_knowledge, story_sections)

    downstream_guidance = {
        'mustReuseResources': resource_knowledge.get('authoritativeResources', []),
        'upstreamWorkflowKnowledge': upstream_workflow_slugs,
        'mustNotInvent': [
            'suite-level custom keywords',
            'duplicate ownership for controls already owned in approved upstream resources',
            'hardcoded workflow routing or mapped page logic in Python',
        ],
        'generationRule': 'Downstream generation must consume approved workflow knowledge plus approved resource context before creating new artifacts.',
    }
    reusable_flows = derive_reusable_flows(enriched_workflow_input, navigation_model, resource_knowledge)

    entry_url = clean_text(((navigation_model.get('entryPoint') or {}).get('url')))
    target_url = clean_text(((navigation_model.get('target') or {}).get('url')))
    if entry_url and target_url and entry_url == target_url:
        direct_access_policy = "direct_access_allowed"
    else:
        direct_access_policy = "must_use_entry_journey" if navigation_model.get('journey') else "direct_access_allowed"

    entry_journey = [
        {
            'page': clean_text(item.get('page')),
            'action': clean_text(item.get('action')),
            'element': clean_text(item.get('element')),
        }
        for item in navigation_model.get('journey', [])
        if isinstance(item, dict) and any(clean_text(item.get(field)) for field in ('page', 'action', 'element'))
    ][:10]

    success_destination = []
    return_destinations = []

    return {
        'workflowName': clean_text(enriched_workflow_input.get('workflowName')) or workflow_slug,
        'workflowSlug': workflow_slug,
        'module': clean_text(enriched_workflow_input.get('module')),
        'feature': feature,
        'applicationCode': application_code,
        'testIdentifierPrefix': test_identifier_prefix,
        'status': 'approved_artifact_memory',
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'businessContext': {
            'userStory': story_sections.get('userStory', []),
            'applicationContext': story_sections.get('applicationContext', []),
            'entryConditions': story_sections.get('entryConditions', []),
            'acceptanceCriteria': story_sections.get('acceptanceCriteria', []),
            'behaviorRules': story_sections.get('behaviorRules', []),
            'validationExpectations': story_sections.get('validationExpectations', []),
            'transitionExpectations': story_sections.get('transitionExpectations', []),
            'approvedTestDataGuidance': story_sections.get('approvedTestDataGuidance', []),
            'reuseGuidance': story_sections.get('reuseGuidance', []),
        },
        'navigationModel': navigation_model,
        'journeyKnowledge': {
            'directAccessPolicy': direct_access_policy,
            'entryJourney': entry_journey,
            'successDestination': success_destination,
            'returnDestinations': return_destinations,
            'authoritativeEntryResources': resource_knowledge.get('authoritativeResources', []),
            'authoritativeDestinationValidationResources': resource_knowledge.get('authoritativeResources', []),
        },
        'resourceKnowledge': resource_knowledge,
        'elementKnowledge': {
            'approvedElements': approved_elements,
        },
        'manualCoverage': {},
        'automationKnowledge': {},
        'downstreamGuidance': downstream_guidance,
        'reusableFlows': reusable_flows,
        'unresolvedGaps': unresolved_gaps,
        'provenance': {
            'workflowInput': '',
            'approvedManualTests': '',
            'approvedResourceFiles': resource_knowledge.get('authoritativeResources', []),
        },
    }


def build_workflow_knowledge(workflow_slug: str) -> Dict[str, Any]:
    workflow_path = WORKFLOW_INPUT_DIR / f'{workflow_slug}.json'
    workflow_input = load_json(workflow_path)
    manual_path = MANUAL_DIR / workflow_slug / f'{workflow_slug}.json'
    manual_data = safe_load_json(manual_path) or {}
    knowledge = build_workflow_knowledge_context(workflow_input)
    knowledge['manualCoverage'] = collect_manual_coverage(manual_data)
    knowledge['automationKnowledge'] = collect_automation_knowledge(workflow_slug, workflow_input)
    knowledge['provenance'] = {
        'workflowInput': str(workflow_path.relative_to(BASE_DIR)).replace('\\', '/'),
        'approvedManualTests': str(manual_path.relative_to(BASE_DIR)).replace('\\', '/') if manual_path.exists() else '',
        'approvedResourceFiles': (knowledge.get('resourceKnowledge') or {}).get('authoritativeResources', []),
    }
    return knowledge


def persist_reusable_flow_artifacts(workflow_input: Dict[str, Any], knowledge: Dict[str, Any]) -> list[str]:
    persisted_paths: list[str] = []
    resource_files = [str(item).replace('\\', '/').strip() for item in ensure_list(workflow_input.get('resourceFiles')) if clean_text(item)]
    reusable_flows = [item for item in ensure_list(knowledge.get('reusableFlows')) if isinstance(item, dict)]
    if not resource_files or not reusable_flows:
        return persisted_paths

    flows_by_page: Dict[str, list[Dict[str, Any]]] = {}
    for flow in reusable_flows:
        flow_id = clean_text(flow.get('flowId'))
        if not flow_id:
            continue
        flow_page = flow_id.split('.', 1)[0].strip()
        if not flow_page:
            continue
        flows_by_page.setdefault(flow_page, []).append(flow)

    for resource_file in resource_files:
        page_name = Path(resource_file).stem.strip()
        if not page_name:
            continue
        page_flows = flows_by_page.get(page_name, [])
        if not page_flows:
            continue
        target_path = POM_METADATA_DIR / page_name / 'metadata' / f'{page_name}.flows.json'
        target_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'pageName': page_name,
            'flows': page_flows,
            'provenance': {
                'workflowName': clean_text(workflow_input.get('workflowName')),
                'workflowSlug': clean_text(knowledge.get('workflowSlug')),
                'resourceFile': resource_file,
            },
        }
        target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        persisted_paths.append(str(target_path.relative_to(BASE_DIR)).replace('\\', '/'))
    return persisted_paths


def save_workflow_knowledge(workflow_slug: str) -> Path:
    WORKFLOW_KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    knowledge = build_workflow_knowledge(workflow_slug)
    workflow_path = WORKFLOW_INPUT_DIR / f'{workflow_slug}.json'
    workflow_input = load_json(workflow_path)
    persisted_flow_artifacts = persist_reusable_flow_artifacts(workflow_input, knowledge)
    if persisted_flow_artifacts:
        knowledge['provenance'] = knowledge.get('provenance', {}) if isinstance(knowledge.get('provenance'), dict) else {}
        knowledge['provenance']['reusableFlowArtifacts'] = persisted_flow_artifacts
    target = WORKFLOW_KNOWLEDGE_DIR / f'{workflow_slug}.json'
    target.write_text(json.dumps(knowledge, indent=2, ensure_ascii=False), encoding='utf-8')
    return target


def load_workflow_knowledge(workflow_slug: str) -> Dict[str, Any] | None:
    path = WORKFLOW_KNOWLEDGE_DIR / f'{workflow_slug}.json'
    return safe_load_json(path)


def summarize_workflow_knowledge_for_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    business = payload.get('businessContext') if isinstance(payload.get('businessContext'), dict) else {}
    resources = payload.get('resourceKnowledge') if isinstance(payload.get('resourceKnowledge'), dict) else {}
    elements = payload.get('elementKnowledge') if isinstance(payload.get('elementKnowledge'), dict) else {}
    manual = payload.get('manualCoverage') if isinstance(payload.get('manualCoverage'), dict) else {}
    automation = payload.get('automationKnowledge') if isinstance(payload.get('automationKnowledge'), dict) else {}
    downstream = payload.get('downstreamGuidance') if isinstance(payload.get('downstreamGuidance'), dict) else {}

    def compact_journey_steps(steps: List[Any]) -> List[Dict[str, Any]]:
        compacted: List[Dict[str, Any]] = []
        for item in ensure_list(steps):
            if not isinstance(item, dict):
                continue
            page = clean_text(item.get('page'))
            action = clean_text(item.get('action'))
            element = clean_text(item.get('element'))
            if not any([page, action, element]):
                continue
            compacted.append({
                'page': page,
                'action': action,
                'element': element,
            })
        return compacted[:6]

    return {
        'workflowSlug': clean_text(payload.get('workflowSlug')),
        'workflowName': clean_text(payload.get('workflowName')),
        'feature': clean_text(payload.get('feature')),
        'applicationCode': clean_text(payload.get('applicationCode')),
        'businessContext': {
            'userStory': unique_strings(ensure_list(business.get('userStory')), limit=4),
            'applicationContext': unique_strings(ensure_list(business.get('applicationContext')), limit=4),
            'entryConditions': unique_strings(ensure_list(business.get('entryConditions')), limit=4),
            'acceptanceCriteria': unique_strings(ensure_list(business.get('acceptanceCriteria')), limit=6),
            'behaviorRules': unique_strings(ensure_list(business.get('behaviorRules')), limit=6),
            'validationExpectations': unique_strings(ensure_list(business.get('validationExpectations')), limit=6),
            'transitionExpectations': unique_strings(ensure_list(business.get('transitionExpectations')), limit=6),
            'reuseGuidance': unique_strings(ensure_list(business.get('reuseGuidance')), limit=6),
            'approvedTestDataGuidance': unique_strings(ensure_list(business.get('approvedTestDataGuidance')), limit=4),
        },
        'navigationModel': {
            'entryPoint': payload.get('navigationModel', {}).get('entryPoint', {}),
            'target': payload.get('navigationModel', {}).get('target', {}),
            'journey': compact_journey_steps(payload.get('navigationModel', {}).get('journey')),
        },
        'journeyKnowledge': {
            'directAccessPolicy': clean_text((payload.get('journeyKnowledge') or {}).get('directAccessPolicy')),
            'entryJourney': compact_journey_steps((payload.get('journeyKnowledge') or {}).get('entryJourney')),
            'successDestination': unique_strings(ensure_list((payload.get('journeyKnowledge') or {}).get('successDestination')), limit=8),
            'returnDestinations': unique_strings(ensure_list((payload.get('journeyKnowledge') or {}).get('returnDestinations')), limit=8),
            'authoritativeEntryResources': unique_strings(ensure_list((payload.get('journeyKnowledge') or {}).get('authoritativeEntryResources')), limit=10),
            'authoritativeDestinationValidationResources': unique_strings(ensure_list((payload.get('journeyKnowledge') or {}).get('authoritativeDestinationValidationResources')), limit=10),
        },
        'resourceKnowledge': {
            'authoritativeResources': unique_strings(ensure_list(resources.get('authoritativeResources')), limit=10),
            'sharedResources': unique_strings(ensure_list(resources.get('sharedResources')), limit=10),
            'resourceOwnership': [
                {
                    'resource': clean_text(item.get('resource')),
                    'variables': unique_strings(ensure_list(item.get('variables')), limit=12),
                    'keywords': unique_strings(ensure_list(item.get('keywords')), limit=16),
                }
                for item in ensure_list(resources.get('resourceOwnership'))[:8]
                if isinstance(item, dict) and clean_text(item.get('resource'))
            ],
        },
        'elementKnowledge': {
            'approvedElements': [
                {
                    'page': clean_text(item.get('page')),
                    'name': clean_text(item.get('name')),
                    'type': clean_text(item.get('type')),
                    'locator': clean_text(item.get('locator')),
                }
                for item in ensure_list(elements.get('approvedElements'))[:20]
                if isinstance(item, dict) and clean_text(item.get('name'))
            ]
        },
        'manualCoverage': {
            'approvedScenarios': [
                {
                    'id': clean_text(item.get('id')),
                    'title': clean_text(item.get('title')),
                    'type': clean_text(item.get('type')),
                    'expectedResult': clean_text(item.get('expectedResult')),
                }
                for item in ensure_list(manual.get('approvedScenarios'))[:12]
                if isinstance(item, dict) and clean_text(item.get('title'))
            ],
            'validations': unique_strings(ensure_list(manual.get('validations')), limit=10),
            'transitions': [],
        },
        'automationKnowledge': {
            'approvedKeywords': [
                {
                    'page': clean_text(item.get('page')),
                    'name': clean_text(item.get('name')),
                    'targetElement': clean_text(item.get('targetElement')),
                    'action': clean_text(item.get('action')),
                }
                for item in ensure_list(automation.get('approvedKeywords'))[:20]
                if isinstance(item, dict) and clean_text(item.get('name'))
            ],
            'approvedTests': [
                {'name': clean_text(item)}
                for item in ensure_list(automation.get('approvedTests'))[:12]
                if clean_text(item)
            ],
            'wrapperExpectations': unique_strings(ensure_list(automation.get('wrapperExpectations')), limit=6),
        },
        'downstreamGuidance': {
            'mustReuseResources': unique_strings(ensure_list(downstream.get('mustReuseResources')), limit=10),
            'upstreamWorkflowKnowledge': unique_strings(ensure_list(downstream.get('upstreamWorkflowKnowledge')), limit=10),
            'mustNotInvent': unique_strings(ensure_list(downstream.get('mustNotInvent')), limit=8),
            'generationRule': clean_text(downstream.get('generationRule')),
        },
        'unresolvedGaps': unique_strings(ensure_list(payload.get('unresolvedGaps')), limit=10),
    }


def discover_relevant_workflow_knowledge(workflow_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    current_slug = slugify(clean_text(workflow_input.get('workflowName')) or clean_text(workflow_input.get('feature')))
    current_resources = {
        str(item).replace('\\', '/').strip()
        for item in ensure_list(workflow_input.get('resourceFiles'))
        if clean_text(item)
    }

    for path in sorted(WORKFLOW_KNOWLEDGE_DIR.glob('*.json')):
        payload = safe_load_json(path)
        if not payload:
            continue
        workflow_slug = clean_text(payload.get('workflowSlug') or path.stem)
        if workflow_slug == current_slug:
            continue
        authoritative_resources = {
            str(item).replace('\\', '/').strip()
            for item in ensure_list(((payload.get('resourceKnowledge') or {}).get('authoritativeResources')))
            if clean_text(item)
        }
        if not (current_resources & authoritative_resources):
            continue
        results.append({
            'workflowSlug': workflow_slug,
            'workflowName': clean_text(payload.get('workflowName')),
            'score': len(current_resources & authoritative_resources),
            'knowledge': summarize_workflow_knowledge_for_generation(payload),
        })

    results.sort(key=lambda item: (-int(item.get('score', 0)), item.get('workflowSlug', '')))
    return results
