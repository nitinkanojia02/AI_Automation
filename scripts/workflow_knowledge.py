import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

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


def normalize_text_blocks(value: Any) -> List[str]:
    if isinstance(value, list):
        flattened: List[str] = []
        for item in value:
            flattened.extend(split_story_sentences(item) if isinstance(item, str) else normalize_text_blocks(item))
        return unique_strings(flattened)
    if isinstance(value, str):
        parts = [clean_text(part) for part in re.split(r"\n+", value) if clean_text(part)]
        expanded: List[str] = []
        for part in parts:
            expanded.extend(split_story_sentences(part))
        return unique_strings(expanded)
    return []


def split_story_sentences(value: Any) -> List[str]:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    if not clean_text(text):
        return []
    heading_pattern = r"\b(USER STORY|APPLICATION CONTEXT|ENTRY CONDITIONS|WORKFLOW SCOPE|PRIMARY NAVIGATION JOURNEY|APPROVED TEST DATA|PAGE / COMPONENT ELEMENTS|PAGE COMPONENT ELEMENTS|BUSINESS RULES|VALIDATION EXPECTATIONS|TRANSITION EXPECTATIONS|RESOURCE REUSE GUIDANCE|DOWNSTREAM AUTOMATION GUIDANCE|TEST CREDENTIALS|LOGIN PAGE ELEMENTS|BEHAVIOR RULES|POM REUSE GUIDANCE|APPROVED TEST DATA GUIDANCE|ACCEPTANCE CRITERIA)\s*:?[ \t]*"
    text = re.sub(heading_pattern, "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^\s*\d+\.\s+", "", text)
    text = re.sub(r"(?m)^\s*[-*]\s+", "", text)
    text = re.sub(r"\n{2,}", "\n", text)

    parts: List[str] = []
    for raw_line in text.split("\n"):
        line = clean_text(raw_line.strip(" :-\t"))
        if not line:
            continue
        line = re.sub(r"^\d+\.\s*", "", line)
        line = re.sub(r"\s+\d+\.$", "", line)
        line = clean_text(line)
        if not line or re.fullmatch(r"\d+", line):
            continue
        subparts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", line)
        for part in subparts:
            cleaned = clean_text(part.strip(" :-\t"))
            if cleaned and not re.fullmatch(r"\d+", cleaned):
                parts.append(cleaned)

    filtered = []
    for part in parts:
        cleaned = clean_text(part)
        if not cleaned:
            continue
        if cleaned.endswith(":") and len(cleaned.split()) <= 8:
            continue
        if re.fullmatch(r"[A-Za-z0-9 /_-]+", cleaned) and cleaned == cleaned.title() and len(cleaned.split()) <= 6:
            continue
        filtered.append(cleaned)
    return unique_strings(filtered)


def select_relevant_lines(values: List[str], keywords: List[str], limit: int = 12) -> List[str]:
    if not values:
        return []
    return unique_strings(values, limit=limit)


def compact_story_lines(values: List[str], limit: int = 12) -> List[str]:
    compacted: List[str] = []
    for item in unique_strings(values):
        cleaned = clean_text(item)
        if not cleaned:
            continue
        if len(cleaned) > 320 and " - " in cleaned:
            segments = [clean_text(part) for part in cleaned.split(" - ") if clean_text(part)]
            for segment in segments:
                if segment and len(segment) <= 240:
                    compacted.append(segment)
                if len(compacted) >= limit:
                    return unique_strings(compacted, limit=limit)
            continue
        compacted.append(cleaned)
        if len(compacted) >= limit:
            break
    return unique_strings(compacted, limit=limit)


def extract_story_urls(story_sections: Dict[str, List[str]]) -> List[str]:
    urls: List[str] = []
    for section_values in story_sections.values():
        for item in ensure_list(section_values):
            for match in re.findall(r"https?://[^\s)]+", str(item or "")):
                cleaned = clean_text(match)
                if cleaned:
                    urls.append(cleaned)
    return unique_strings(urls, limit=10)


def looks_like_journey_action(value: str) -> bool:
    cleaned = clean_text(value)
    if not cleaned:
        return False
    if cleaned.endswith(":"):
        return False
    if len(cleaned.split()) < 2:
        return False
    if re.fullmatch(r"https?://[^\s]+", cleaned):
        return False
    lowered = cleaned.lower()
    if re.fullmatch(r"[A-Za-z0-9 /_-]+", cleaned) and cleaned == cleaned.title() and len(cleaned.split()) <= 6:
        return False
    if not re.search(r"\b(click|open|launch|navigate|return|go|submit|enter|select|use|press|observe|verify)\b", lowered):
        return False
    return True


def collect_workflow_story_lines(workflow_input: Dict[str, Any]) -> Dict[str, List[str]]:
    external = workflow_input.get("externalContext") if isinstance(workflow_input.get("externalContext"), dict) else {}
    story_blob = unique_strings([
        workflow_input.get("userStory"),
        external.get("title"),
        external.get("description"),
    ])
    story_lines = unique_strings(sum([split_story_sentences(item) for item in story_blob], []), limit=20)
    acceptance = unique_strings(
        normalize_text_blocks(workflow_input.get("acceptanceCriteria"))
        + normalize_text_blocks(external.get("acceptanceCriteria")),
        limit=20,
    )
    validation_expectations = unique_strings(
        normalize_text_blocks(external.get("validationExpectations"))
        + normalize_text_blocks(workflow_input.get("observedValidations")),
        limit=20,
    )
    entry_conditions = compact_story_lines(unique_strings(
        normalize_text_blocks(external.get("entryConditions"))
        + normalize_text_blocks(workflow_input.get("observedPreconditions")),
        limit=10,
    ), limit=10)
    transition_expectations = compact_story_lines(unique_strings(
        normalize_text_blocks(external.get("transitionExpectations")),
        limit=12,
    ), limit=12)
    return {
        "userStory": compact_story_lines(story_lines[:4], limit=4),
        "applicationContext": compact_story_lines(unique_strings(normalize_text_blocks(external.get("applicationContext")), limit=6), limit=6),
        "entryConditions": entry_conditions,
        "acceptanceCriteria": compact_story_lines(acceptance, limit=10),
        "behaviorRules": compact_story_lines(unique_strings(normalize_text_blocks(external.get("behaviorRules")), limit=10), limit=10),
        "validationExpectations": compact_story_lines(validation_expectations, limit=10),
        "transitionExpectations": transition_expectations,
        "reuseGuidance": compact_story_lines(unique_strings(normalize_text_blocks(external.get("pomReuseGuidance")), limit=8), limit=8),
        "approvedTestDataGuidance": compact_story_lines(unique_strings(normalize_text_blocks(external.get("approvedTestDataGuidance")), limit=8), limit=8),
    }


def derive_navigation_model(workflow_input: Dict[str, Any], story_sections: Dict[str, List[str]]) -> Dict[str, Any]:
    entry_page = workflow_input.get("entryPage") if isinstance(workflow_input.get("entryPage"), dict) else {}
    target_page = workflow_input.get("targetPage") if isinstance(workflow_input.get("targetPage"), dict) else {}
    pages = workflow_input.get("pages") if isinstance(workflow_input.get("pages"), list) else []
    primary_page = pages[0] if pages and isinstance(pages[0], dict) else {}

    inferred_target_name = clean_text(target_page.get("name") or primary_page.get("name"))
    inferred_target_url = clean_text(target_page.get("url") or primary_page.get("url"))
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

    if not inferred_target_url:
        inferred_target_url = clean_text(target_page.get("url"))

    story_urls = extract_story_urls(story_sections)
    if not inferred_entry_url and story_urls:
        inferred_entry_url = story_urls[0]
    if not inferred_target_url and story_urls:
        inferred_target_url = story_urls[0]

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

    if not journey:
        candidate_lines = compact_story_lines(
            story_sections.get("acceptanceCriteria", []) + story_sections.get("reuseGuidance", []) + story_sections.get("transitionExpectations", []),
            limit=16,
        )
        for line in candidate_lines:
            if not looks_like_journey_action(line):
                continue
            page_name = inferred_target_name or inferred_entry_name
            lowered = line.lower()
            if inferred_target_name and inferred_target_name.lower() in lowered:
                page_name = inferred_target_name
            elif inferred_entry_name and inferred_entry_name.lower() in lowered:
                page_name = inferred_entry_name
            journey.append({
                "page": page_name,
                "action": line,
                "element": "",
            })
            if len(journey) >= 8:
                break

    return {
        "entryPoint": {
            "name": inferred_entry_name,
            "url": inferred_entry_url,
        },
        "target": {
            "name": inferred_target_name,
            "url": inferred_target_url,
        },
        "journey": journey[:10],
        "targetSignals": [item for item in ensure_list(workflow_input.get("targetPageSignals")) if isinstance(item, dict)][:10],
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

    def _is_cross_resource_conflict(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        owner = clean_text(item.get("ownerResource") or item.get("owner") or item.get("resource"))
        candidate = clean_text(item.get("candidateResource") or item.get("candidate") or item.get("reusedFrom"))
        if owner and candidate:
            return owner.lower() != candidate.lower()
        return True

    sanitized = dict(reuse_analysis)
    for key in ("duplicateVariables", "duplicateKeywords", "variableReuseCandidates", "keywordReuseCandidates", "ownershipConflicts"):
        values = ensure_list(sanitized.get(key))
        sanitized[key] = [item for item in values if _is_cross_resource_conflict(item)]
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

    combined_resource_text = "\n\n".join(
        read_text(BASE_DIR / rel_path) if (BASE_DIR / rel_path).exists() else read_text(POM_DIR / rel_path)
        for rel_path in merged_resources
        if clean_text(rel_path)
    )
    reuse_analysis = sanitize_reuse_analysis(analyze_reuse_conflicts(combined_resource_text, "")) if clean_text(combined_resource_text) else {
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
    transitions: List[str] = []
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
            transitions.append(expected)
    return {
        'approvedScenarios': scenarios[:40],
        'validations': unique_strings(validations, limit=20),
        'transitions': unique_strings(transitions, limit=20),
    }


def collect_automation_knowledge(workflow_slug: str, workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    approved_keywords: List[Dict[str, Any]] = []
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
                lowered = name.lower()
                action = 'generic'
                if lowered.startswith('click '):
                    action = 'click'
                elif lowered.startswith('verify ') or lowered.startswith('validate '):
                    action = 'verify'
                elif lowered.startswith('open '):
                    action = 'open'
                elif lowered.startswith('enter ') or lowered.startswith('input '):
                    action = 'input'
                approved_keywords.append({
                    'page': page_name,
                    'name': name,
                    'targetElement': '',
                    'action': action,
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
                    approved_keywords.append({
                        'page': page_name,
                        'name': clean_text(item.get('keywordName')),
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
        'approvedTests': approved_tests[:80],
        'wrapperExpectations': [
            'Reuse approved shared/common wrapper keywords before low-level SeleniumLibrary actions.',
            'Do not invent suite-level custom keywords; compose from approved upstream resource knowledge.',
        ],
    }


def extract_upstream_workflow_candidates(workflow_input: Dict[str, Any], resource_knowledge: Dict[str, Any], story_sections: Dict[str, List[str]]) -> List[str]:
    candidates: List[str] = []
    inferred = workflow_input.get('inferredReuseContext') if isinstance(workflow_input.get('inferredReuseContext'), dict) else {}
    for resource in ensure_list(inferred.get('authoritativeResourceFiles')) + ensure_list(inferred.get('inferredRelevantResourceFiles')):
        normalized = str(resource).replace('\\', '/').strip()
        page_name = Path(normalized).parent.name
        slug = slugify(page_name.replace('_page', '')) if page_name else ''
        if slug and slug not in candidates:
            candidates.append(slug)
    journey_blob = ' '.join(story_sections.get('acceptanceCriteria', []) + story_sections.get('reuseGuidance', []) + story_sections.get('transitionExpectations', [])).lower()
    for summary in ensure_list(resource_knowledge.get('resourceSummaries')):
        resource_file = clean_text((summary or {}).get('resourceFile'))
        page_name = Path(resource_file).parent.name
        slug = slugify(page_name.replace('_page', '')) if page_name else ''
        if slug and slug not in candidates and slug in journey_blob:
            candidates.append(slug)
    referenced_workflows = [path.stem for path in sorted(WORKFLOW_KNOWLEDGE_DIR.glob('*.json'))]
    for workflow_slug in referenced_workflows:
        if workflow_slug and workflow_slug not in candidates and workflow_slug in journey_blob:
            candidates.append(workflow_slug)
    current_slug = slugify(clean_text(workflow_input.get('workflowName')) or clean_text(workflow_input.get('feature')))
    return [item for item in candidates if item and item != current_slug][:10]


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
        candidate_text = [
            review_summary.get('summary'),
            review_summary.get('overall_quality'),
        ]
        candidate_text.extend(review_summary.get('issues', []) if isinstance(review_summary.get('issues'), list) else [])
        for item in unique_strings(candidate_text, limit=20):
            lowered = item.lower()
            if any(token in lowered for token in ['gap', 'missing', 'cannot validate', 'not modeled', 'unresolved', 'absence']):
                gaps.append(item)
    return unique_strings(gaps, limit=20)


def build_workflow_knowledge_context(workflow_input: Dict[str, Any]) -> Dict[str, Any]:
    from scripts.workflow_context import infer_workflow_reuse_context

    workflow_name = clean_text(workflow_input.get('workflowName')) or clean_text(workflow_input.get('feature')) or 'workflow'
    workflow_slug = slugify(workflow_name)
    enriched_workflow_input = dict(workflow_input)
    enriched_workflow_input['inferredReuseContext'] = infer_workflow_reuse_context(enriched_workflow_input)
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

    entry_url = clean_text(((navigation_model.get('entryPoint') or {}).get('url')))
    target_url = clean_text(((navigation_model.get('target') or {}).get('url')))
    if entry_url and target_url and entry_url == target_url:
        direct_access_policy = "direct_access_allowed"
    else:
        direct_access_policy = "must_use_entry_journey" if navigation_model.get('journey') else "direct_access_allowed"

    entry_journey = compact_story_lines(unique_strings(
        [
            item.get('action', '')
            for item in navigation_model.get('journey', [])
            if isinstance(item, dict) and clean_text(item.get('action', ''))
        ]
        + select_relevant_lines(
            story_sections.get('acceptanceCriteria', []) + story_sections.get('reuseGuidance', []) + story_sections.get('entryConditions', []),
            [],
            limit=10,
        ),
        limit=10,
    ), limit=10)

    success_destination = compact_story_lines(unique_strings(
        select_relevant_lines(
            story_sections.get('transitionExpectations', []) + story_sections.get('validationExpectations', []) + story_sections.get('acceptanceCriteria', []),
            [],
            limit=8,
        ),
        limit=8,
    ), limit=8)

    return_destinations = compact_story_lines(unique_strings(
        select_relevant_lines(
            story_sections.get('transitionExpectations', []) + story_sections.get('acceptanceCriteria', []) + story_sections.get('reuseGuidance', []),
            [],
            limit=8,
        ),
        limit=8,
    ), limit=8)

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


def save_workflow_knowledge(workflow_slug: str) -> Path:
    WORKFLOW_KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    knowledge = build_workflow_knowledge(workflow_slug)
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
            'entryJourney': unique_strings(ensure_list((payload.get('journeyKnowledge') or {}).get('entryJourney')), limit=8),
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
            'transitions': unique_strings(ensure_list(manual.get('transitions')), limit=10),
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
                {'name': clean_text(item.get('name'))}
                for item in ensure_list(automation.get('approvedTests'))[:12]
                if isinstance(item, dict) and clean_text(item.get('name'))
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
    story_blob = ' '.join(unique_strings([
        workflow_input.get('workflowName'),
        workflow_input.get('feature'),
        workflow_input.get('userStory'),
        workflow_input.get('observedExpectedResult'),
        *ensure_list(workflow_input.get('observedSteps')),
        *ensure_list(workflow_input.get('observedValidations')),
        *((ensure_list((workflow_input.get('externalContext') or {}).get('description'))) if isinstance(workflow_input.get('externalContext'), dict) else []),
        *((ensure_list((workflow_input.get('externalContext') or {}).get('acceptanceCriteria'))) if isinstance(workflow_input.get('externalContext'), dict) else []),
    ])).lower()

    for path in sorted(WORKFLOW_KNOWLEDGE_DIR.glob('*.json')):
        payload = safe_load_json(path)
        if not payload:
            continue
        workflow_slug = clean_text(payload.get('workflowSlug') or path.stem)
        if workflow_slug == current_slug:
            continue
        score = 0
        authoritative_resources = {
            str(item).replace('\\', '/').strip()
            for item in ensure_list(((payload.get('resourceKnowledge') or {}).get('authoritativeResources')))
            if clean_text(item)
        }
        if current_resources & authoritative_resources:
            score += 5
        for resource in authoritative_resources:
            page_token = Path(resource).parent.name.replace('_page', '').replace('_', ' ')
            if page_token and page_token in story_blob:
                score += 3
        for term in unique_strings([
            payload.get('workflowName'),
            payload.get('feature'),
            *(((payload.get('businessContext') or {}).get('acceptanceCriteria')) if isinstance(payload.get('businessContext'), dict) else []),
            *(((payload.get('businessContext') or {}).get('reuseGuidance')) if isinstance(payload.get('businessContext'), dict) else []),
        ]):
            normalized = clean_text(term).lower()
            if normalized and normalized in story_blob:
                score += 1
        if workflow_slug in {
            slugify(item)
            for item in ensure_list(((payload.get('downstreamGuidance') or {}).get('upstreamWorkflowKnowledge')))
        }:
            score += 1
        if score <= 0:
            continue
        results.append({
            'workflowSlug': workflow_slug,
            'workflowName': clean_text(payload.get('workflowName')),
            'score': score,
            'knowledge': summarize_workflow_knowledge_for_generation(payload),
        })

    results.sort(key=lambda item: (-int(item.get('score', 0)), item.get('workflowSlug', '')))
    return results
