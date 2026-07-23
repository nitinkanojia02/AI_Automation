import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
POM_DIR = BASE_DIR / "pom_pages"
RESOURCES_DIR = BASE_DIR / "resources"
ROBOT_TESTS_DIR = BASE_DIR / "tests"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_locator(value: str) -> str:
    return clean_text(value).lower()


def normalize_name_tokens(value: str) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\b(button|btn|field|input|textbox|link|icon|label|page|section|panel|form|menu|nav|navigation)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_keyword_body_lines(lines: List[Any]) -> str:
    normalized: List[str] = []
    for raw_line in lines:
        line = clean_text(raw_line)
        if not line:
            continue
        line = re.sub(r"\$\{[^}]+\}", "${VAR}", line)
        line = re.sub(r"\b(id|name|xpath|css)\s*=\s*[^\s]+", "LOCATOR", line, flags=re.IGNORECASE)
        normalized.append(line.lower())
    return "\n".join(normalized)


def keyword_signature(keyword_name: str, body_lines: List[Any]) -> str:
    name_tokens = normalize_name_tokens(keyword_name)
    body_signature = normalize_keyword_body_lines(body_lines)
    if name_tokens and body_signature:
        return f"{name_tokens}::{body_signature}"
    return name_tokens or body_signature


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


def parse_resource_file(resource_path: Path) -> Dict[str, Any]:
    text = resource_path.read_text(encoding="utf-8")
    rel_path = str(resource_path.relative_to(BASE_DIR)).replace("\\", "/")
    resource_type = "common" if rel_path.startswith("resources/") else "page"
    return {
        "file": rel_path,
        "type": resource_type,
        "variables": extract_variables_from_resource(text),
        "keywords": extract_keywords_from_resource(text),
        "source": text,
    }


def collect_existing_resource_context(include_common: bool = True) -> List[Dict[str, Any]]:
    resources: List[Dict[str, Any]] = []
    for resource_path in sorted(POM_DIR.glob("*/*.resource")):
        resources.append(parse_resource_file(resource_path))
    if include_common:
        for resource_path in sorted(RESOURCES_DIR.glob("*.resource")):
            resources.append(parse_resource_file(resource_path))
    return resources


def analyze_reuse_conflicts(candidate_content: str, candidate_file: str = "") -> Dict[str, Any]:
    existing_resources = collect_existing_resource_context(include_common=True)
    candidate_variables = extract_variables_from_resource(candidate_content)
    candidate_keywords = extract_keywords_from_resource(candidate_content)

    locator_owners: Dict[str, List[Dict[str, str]]] = {}
    keyword_name_owners: Dict[str, List[Dict[str, str]]] = {}
    keyword_body_owners: Dict[str, List[Dict[str, str]]] = {}
    keyword_signature_owners: Dict[str, List[Dict[str, str]]] = {}

    for resource in existing_resources:
        resource_file = str(resource.get("file", ""))
        if candidate_file and resource_file == candidate_file:
            continue
        for variable in resource.get("variables", []):
            locator = normalize_locator(str(variable.get("value", "")))
            if locator:
                locator_owners.setdefault(locator, []).append({
                    "resource": resource_file,
                    "name": clean_text(variable.get("name", "")),
                })
        for keyword in resource.get("keywords", []):
            keyword_name = clean_text(keyword.get("name", ""))
            if keyword_name:
                keyword_name_owners.setdefault(keyword_name.lower(), []).append({
                    "resource": resource_file,
                    "name": keyword_name,
                })
            normalized_body = normalize_keyword_body_lines(keyword.get("body", []))
            if normalized_body:
                keyword_body_owners.setdefault(normalized_body, []).append({
                    "resource": resource_file,
                    "name": keyword_name,
                })
            signature = keyword_signature(keyword_name, keyword.get("body", []))
            if signature:
                keyword_signature_owners.setdefault(signature, []).append({
                    "resource": resource_file,
                    "name": keyword_name,
                })

    duplicate_variables: List[Dict[str, Any]] = []
    variable_reuse_candidates: List[Dict[str, Any]] = []
    for variable in candidate_variables:
        locator = normalize_locator(str(variable.get("value", "")))
        if not locator:
            continue
        owners = locator_owners.get(locator, [])
        if owners:
            duplicate_variables.append({
                "candidateName": clean_text(variable.get("name", "")),
                "locator": locator,
                "existingOwners": owners,
            })
            variable_reuse_candidates.append({
                "candidateName": clean_text(variable.get("name", "")),
                "reuseFrom": owners[0],
                "reason": "Same locator already exists in approved resource context.",
            })

    duplicate_keywords: List[Dict[str, Any]] = []
    keyword_reuse_candidates: List[Dict[str, Any]] = []
    for keyword in candidate_keywords:
        name = clean_text(keyword.get("name", ""))
        if not name:
            continue
        normalized_body = normalize_keyword_body_lines(keyword.get("body", []))
        signature = keyword_signature(name, keyword.get("body", []))
        same_name = keyword_name_owners.get(name.lower(), [])
        same_body = keyword_body_owners.get(normalized_body, []) if normalized_body else []
        same_signature = keyword_signature_owners.get(signature, []) if signature else []
        if same_name or same_body or same_signature:
            duplicate_keywords.append({
                "candidateName": name,
                "sameNameOwners": same_name,
                "sameBodyOwners": same_body,
                "sameSignatureOwners": same_signature,
            })
            chosen_owner = (same_name or same_signature or same_body)[0]
            keyword_reuse_candidates.append({
                "candidateName": name,
                "reuseFrom": chosen_owner,
                "reason": "Same keyword name, normalized implementation, or semantic signature already exists in approved resource context.",
            })

    ownership_conflicts: List[Dict[str, Any]] = []
    for variable in duplicate_variables:
        candidate_tokens = normalize_name_tokens(variable.get("candidateName", ""))
        for owner in variable.get("existingOwners", []):
            owner_tokens = normalize_name_tokens(owner.get("name", ""))
            if candidate_tokens == owner_tokens and candidate_tokens:
                ownership_conflicts.append({
                    "type": "shared_locator_semantic_overlap",
                    "candidateName": variable.get("candidateName", ""),
                    "existingOwner": owner,
                    "locator": variable.get("locator", ""),
                })

    owner_resource_frequency = Counter(
        owner.get("resource", "")
        for item in duplicate_variables
        for owner in item.get("existingOwners", [])
        if owner.get("resource")
    )
    canonical_resource_candidates = [
        {"resource": resource, "support": count}
        for resource, count in owner_resource_frequency.most_common(10)
    ]

    return {
        "duplicateVariables": duplicate_variables,
        "duplicateKeywords": duplicate_keywords,
        "variableReuseCandidates": variable_reuse_candidates,
        "keywordReuseCandidates": keyword_reuse_candidates,
        "ownershipConflicts": ownership_conflicts,
        "canonicalResourceCandidates": canonical_resource_candidates,
        "summary": {
            "duplicateVariableCount": len(duplicate_variables),
            "duplicateKeywordCount": len(duplicate_keywords),
            "ownershipConflictCount": len(ownership_conflicts),
        },
    }


def normalize_text_signature(value: str) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def analyze_manual_test_reuse(manual_data: Dict[str, Any], workflow_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    workflow_context = workflow_context or {}
    current_knowledge = workflow_context.get("current_workflow_knowledge") or {}
    relevant_knowledge = workflow_context.get("relevant_workflow_knowledge") or []
    reuse_context = workflow_context.get("reuse_context") or workflow_context.get("inferred_reuse_context") or {}

    approved_resource_files = {
        clean_text(item).lower()
        for item in (manual_data.get("resourceFiles") or [])
        if clean_text(item)
    }
    approved_resource_files.update(
        clean_text(item).lower()
        for item in (reuse_context.get("resourceFiles") or [])
        if clean_text(item)
    )

    authoritative_resources = {
        clean_text(item).lower()
        for item in (current_knowledge.get("authoritativeResources") or [])
        if clean_text(item)
    }
    for item in relevant_knowledge:
        if not isinstance(item, dict):
            continue
        for resource in (item.get("authoritativeResources") or []):
            cleaned = clean_text(resource).lower()
            if cleaned:
                authoritative_resources.add(cleaned)

    scenarios = manual_data.get("testCases") or []
    seen_signatures: Dict[Tuple[str, str], List[str]] = {}
    weak_expected_results: List[Dict[str, str]] = []
    duplicate_scenarios: List[Dict[str, Any]] = []
    transition_coverage_gaps: List[str] = []
    resource_lineage_gaps: List[str] = []
    reused_intent_markers: List[str] = []

    for case in scenarios:
        if not isinstance(case, dict):
            continue
        title = clean_text(case.get("title", ""))
        expected = clean_text(case.get("expectedResult", ""))
        case_id = clean_text(case.get("id", "")) or title
        steps = [clean_text(step) for step in (case.get("steps") or []) if clean_text(step)]
        combined = " ".join([title, expected, *steps])
        signature = (
            normalize_text_signature(title),
            normalize_text_signature(expected),
        )
        seen_signatures.setdefault(signature, []).append(case_id)

        expected_signature = normalize_text_signature(expected)
        if expected_signature and len(expected_signature.split()) <= 4:
            weak_expected_results.append({"id": case_id, "title": title, "expectedResult": expected})

        if any(clean_text(step) for step in steps):
            reused_intent_markers.append(case_id)

    for signature, case_ids in seen_signatures.items():
        if len(case_ids) > 1:
            duplicate_scenarios.append({
                "signature": " | ".join(part for part in signature if part),
                "caseIds": case_ids,
            })

    success_destinations = [
        clean_text(item)
        for item in (current_knowledge.get("successDestination") or [])
        if clean_text(item)
    ]
    if success_destinations:
        for destination in success_destinations:
            normalized_destination = normalize_text_signature(destination)
            if normalized_destination and not any(
                normalized_destination in normalize_text_signature(
                    " ".join([
                        clean_text(case.get("title", "")),
                        clean_text(case.get("expectedResult", "")),
                        " ".join(clean_text(step) for step in (case.get("steps") or []) if clean_text(step)),
                    ])
                )
                for case in scenarios if isinstance(case, dict)
            ):
                transition_coverage_gaps.append(destination)

    if authoritative_resources and approved_resource_files:
        if not (approved_resource_files & authoritative_resources):
            resource_lineage_gaps.append(
                "Manual artifact resourceFiles do not reflect authoritative upstream/current resources from workflow knowledge."
            )

    return {
        "weakExpectedResults": weak_expected_results,
        "duplicateScenarios": duplicate_scenarios,
        "transitionCoverageGaps": transition_coverage_gaps,
        "resourceLineageGaps": resource_lineage_gaps,
        "reusedIntentMarkers": sorted(set(reused_intent_markers)),
        "summary": {
            "weakExpectedResultCount": len(weak_expected_results),
            "duplicateScenarioCount": len(duplicate_scenarios),
            "transitionCoverageGapCount": len(transition_coverage_gaps),
            "resourceLineageGapCount": len(resource_lineage_gaps),
        },
    }


def analyze_keyword_artifact_reuse(keywords: List[Dict[str, Any]], page_name: str = "") -> Dict[str, Any]:
    candidate_lines = ["*** Keywords ***"]
    candidate_keyword_names: List[str] = []
    for keyword in keywords:
        if not isinstance(keyword, dict):
            continue
        keyword_name = clean_text(keyword.get("keywordName", ""))
        if not keyword_name:
            continue
        candidate_keyword_names.append(keyword_name)
        candidate_lines.append(keyword_name)
        arguments = keyword.get("arguments", []) or []
        if isinstance(arguments, str):
            arguments = [part.strip() for part in arguments.split(",") if clean_text(part)]
        if arguments:
            candidate_lines.append("    [Arguments]    " + "    ".join(f"${{{clean_text(arg).replace('${', '').replace('}', '')}}}" for arg in arguments if clean_text(arg)))
        implementation = keyword.get("implementation", []) or []
        if isinstance(implementation, str):
            implementation = [line.rstrip() for line in implementation.splitlines() if clean_text(line)]
        for line in implementation:
            if clean_text(line):
                candidate_lines.append(f"    {str(line).rstrip()}")

    candidate_file = ""
    if page_name:
        candidate_path = POM_DIR / page_name / f"{page_name}.resource"
        if candidate_path.exists():
            candidate_file = str(candidate_path.relative_to(BASE_DIR)).replace("\\", "/")

    conflict_analysis = analyze_reuse_conflicts("\n".join(candidate_lines) + "\n", candidate_file)

    existing_resources = collect_existing_resource_context(include_common=True)
    common_keyword_names = {
        clean_text(keyword.get("name", "")).lower()
        for resource in existing_resources
        if clean_text(resource.get("type", "")) == "common"
        for keyword in resource.get("keywords", [])
        if clean_text(keyword.get("name", ""))
    }

    low_value_wrapper_keywords: List[Dict[str, Any]] = []
    common_reuse_opportunities: List[Dict[str, Any]] = []
    for keyword in keywords:
        if not isinstance(keyword, dict):
            continue
        keyword_name = clean_text(keyword.get("keywordName", ""))
        implementation = keyword.get("implementation", []) or []
        if isinstance(implementation, str):
            implementation = [line.rstrip() for line in implementation.splitlines() if clean_text(line)]
        normalized_lines = [clean_text(line) for line in implementation if clean_text(line)]
        normalized_name = keyword_name.lower()
        references_page_variable = any("${" in line for line in normalized_lines)

        if len(normalized_lines) <= 1 and not references_page_variable:
            low_value_wrapper_keywords.append({
                "keywordName": keyword_name,
                "reason": "Keyword is a very thin wrapper and may not provide enough reusable page-level abstraction.",
            })
        if normalized_name in common_keyword_names:
            common_reuse_opportunities.append({
                "keywordName": keyword_name,
                "reason": "Keyword name overlaps an approved shared/common helper and should not be redefined at page level.",
            })

    return {
        "conflictAnalysis": conflict_analysis,
        "lowValueWrapperKeywords": low_value_wrapper_keywords,
        "commonReuseOpportunities": common_reuse_opportunities,
        "summary": {
            "duplicateKeywordCount": conflict_analysis.get("summary", {}).get("duplicateKeywordCount", 0),
            "duplicateVariableCount": conflict_analysis.get("summary", {}).get("duplicateVariableCount", 0),
            "ownershipConflictCount": conflict_analysis.get("summary", {}).get("ownershipConflictCount", 0),
            "lowValueWrapperCount": len(low_value_wrapper_keywords),
            "commonReuseOpportunityCount": len(common_reuse_opportunities),
        },
    }


def analyze_robot_suite_reuse(robot_content: str, resource_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    approved_variable_values: Dict[str, List[Dict[str, str]]] = {}
    approved_keywords: Dict[str, List[Dict[str, str]]] = {}
    common_keywords: set[str] = set()
    page_keywords: set[str] = set()

    for resource in resource_context:
        resource_file = clean_text(resource.get("file", ""))
        resource_type = clean_text(resource.get("type", "")) or "page"
        for variable in resource.get("variables", []):
            value = clean_text(variable.get("value", ""))
            name = clean_text(variable.get("name", ""))
            if value and name:
                approved_variable_values.setdefault(value, []).append({
                    "resource": resource_file,
                    "name": name,
                })
        for keyword in resource.get("keywords", []):
            name = clean_text(keyword.get("name", ""))
            if not name:
                continue
            normalized_name = name.lower()
            approved_keywords.setdefault(normalized_name, []).append({
                "resource": resource_file,
                "name": name,
                "type": resource_type,
            })
            if resource_type == "common":
                common_keywords.add(normalized_name)
            else:
                page_keywords.add(normalized_name)

    literal_value_hits: List[Dict[str, Any]] = []
    low_level_calls_with_reuse_available: List[Dict[str, Any]] = []
    reused_keywords: set[str] = set()
    suite_called_keywords: List[str] = []
    framework_keywords, _ = get_framework_keyword_catalog()

    for raw_line in robot_content.splitlines():
        stripped = raw_line.strip()
        if not raw_line.startswith((" ", "\t")) or not stripped or stripped.startswith("["):
            continue
        parts = [part.strip() for part in re.split(r"\s{2,}|\t+", stripped) if part.strip()]
        if not parts:
            continue
        keyword_name = clean_text(parts[0]).lower()
        args = parts[1:]
        suite_called_keywords.append(keyword_name)
        if keyword_name in approved_keywords:
            reused_keywords.add(keyword_name)
        for arg in args:
            candidate = clean_text(arg)
            if not candidate or candidate.startswith("${"):
                continue
            owners = approved_variable_values.get(candidate, [])
            if owners:
                literal_value_hits.append({
                    "literal": candidate,
                    "approvedVariables": owners,
                    "usedByKeyword": keyword_name,
                })
                if keyword_name in framework_keywords:
                    low_level_calls_with_reuse_available.append({
                        "keyword": keyword_name,
                        "literal": candidate,
                        "approvedVariables": owners,
                        "reason": "Suite uses a framework/library keyword with a literal even though approved resource variables already exist.",
                    })

    missing_common_wrapper_reuse: List[str] = []

    return {
        "literalReuseOpportunities": literal_value_hits,
        "lowLevelReuseOpportunities": low_level_calls_with_reuse_available,
        "missingCommonWrapperReuse": sorted(set(missing_common_wrapper_reuse)),
        "reusedApprovedKeywords": sorted(reused_keywords),
        "summary": {
            "literalReuseOpportunityCount": len(literal_value_hits),
            "lowLevelReuseOpportunityCount": len(low_level_calls_with_reuse_available),
            "reusedApprovedKeywordCount": len(reused_keywords),
        },
    }
