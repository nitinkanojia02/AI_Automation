import re
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
POM_DIR = BASE_DIR / "pom_pages"
RESOURCES_DIR = BASE_DIR / "resources"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_locator(value: str) -> str:
    return clean_text(value).lower()


def normalize_name_tokens(value: str) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\b(button|btn|field|input|textbox|link|icon|label|page)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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
            normalized_body = "\n".join(clean_text(line) for line in keyword.get("body", []) if clean_text(line))
            if normalized_body:
                keyword_body_owners.setdefault(normalized_body.lower(), []).append({
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
        normalized_body = "\n".join(clean_text(line) for line in keyword.get("body", []) if clean_text(line)).lower()
        same_name = keyword_name_owners.get(name.lower(), [])
        same_body = keyword_body_owners.get(normalized_body, []) if normalized_body else []
        if same_name or same_body:
            duplicate_keywords.append({
                "candidateName": name,
                "sameNameOwners": same_name,
                "sameBodyOwners": same_body,
            })
            chosen_owner = (same_name or same_body)[0]
            keyword_reuse_candidates.append({
                "candidateName": name,
                "reuseFrom": chosen_owner,
                "reason": "Same keyword name or normalized implementation already exists in approved resource context.",
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

    return {
        "duplicateVariables": duplicate_variables,
        "duplicateKeywords": duplicate_keywords,
        "variableReuseCandidates": variable_reuse_candidates,
        "keywordReuseCandidates": keyword_reuse_candidates,
        "ownershipConflicts": ownership_conflicts,
        "summary": {
            "duplicateVariableCount": len(duplicate_variables),
            "duplicateKeywordCount": len(duplicate_keywords),
            "ownershipConflictCount": len(ownership_conflicts),
        },
    }
