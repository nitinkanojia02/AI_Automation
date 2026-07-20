import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

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
    generic_wrapper_names = {
        "go to url", "click when ready", "wait for element to be ready", "input text when ready",
        "input text", "input password", "wait until page contains element", "click element"
    }

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
                if keyword_name in generic_wrapper_names:
                    low_level_calls_with_reuse_available.append({
                        "keyword": keyword_name,
                        "literal": candidate,
                        "approvedVariables": owners,
                        "reason": "Suite is using a low-level or generic interaction with a literal even though approved semantic variables already exist.",
                    })

    missing_common_wrapper_reuse: List[str] = []
    if "input text when ready" in common_keywords and any(name in suite_called_keywords for name in {"input text", "input password"}):
        missing_common_wrapper_reuse.append("input text when ready")
    if "click when ready" in common_keywords and "click element" in suite_called_keywords:
        missing_common_wrapper_reuse.append("click when ready")

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
