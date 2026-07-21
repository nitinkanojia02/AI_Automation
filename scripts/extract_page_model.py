import argparse
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import urllib3
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

try:
    from scripts.workflow_context import infer_workflow_reuse_context
    from scripts.workflow_knowledge import build_workflow_knowledge_context, discover_relevant_workflow_knowledge
except ModuleNotFoundError:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from scripts.workflow_context import infer_workflow_reuse_context
    from scripts.workflow_knowledge import build_workflow_knowledge_context, discover_relevant_workflow_knowledge
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "page_model_config.json"
PROMPTS_DIR = BASE_DIR / "prompts"

SUPPORTED_BROWSERS = {"chromium", "chrome", "edge", "firefox", "webkit"}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("extract_page_model")

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def build_story_text(workflow_like: dict) -> str:
    if not isinstance(workflow_like, dict):
        return ""
    parts = [
        str(workflow_like.get("title", "")),
        str(workflow_like.get("description", "")),
        str(workflow_like.get("userStory", "")),
        str(workflow_like.get("workflowName", "")),
    ]
    for key in ("observedSteps", "observedExpectedResults", "observedValidations", "acceptanceCriteria"):
        value = workflow_like.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value:
            parts.append(str(value))
    return "\n".join(part for part in parts if clean_text(part))


def first_url_in_text(text: str) -> str:
    match = re.search(r"https?://[^\s)]+", text or "")
    return clean_text(match.group(0)) if match else ""


def resolve_entry_url(workflow_like: dict) -> str:
    if not isinstance(workflow_like, dict):
        return "http://localhost/"

    direct_url = clean_text(
        str(
            workflow_like.get("pageUrl")
            or workflow_like.get("pageURL")
            or workflow_like.get("url")
            or (workflow_like.get("entryPage") or {}).get("url", "")
            or ""
        )
    )
    if direct_url:
        return direct_url

    story_url = first_url_in_text(build_story_text(workflow_like))
    if story_url:
        return story_url

    try:
        inferred = infer_workflow_reuse_context(workflow_like)
    except Exception:
        inferred = {}
    for candidate in inferred.get("discoveredUrls", []):
        resolved = clean_text(str(candidate))
        if resolved:
            return resolved

    return "http://localhost/"

def split_camel_case(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    return clean_text(text)

def slugify(text: str) -> str:
    text = split_camel_case(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "element"

def title_case(text: str) -> str:
    return " ".join(word.capitalize() for word in re.split(r"[_\-\s]+", clean_text(text)) if word)

def xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f"\"{value}\""
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{p}'" for p in parts) + ")"

def get_ai_token(ai_cfg: dict) -> str:
    token = str(ai_cfg.get("token", "")).strip()
    if token:
        return token

    token_env_var = str(ai_cfg.get("token_env_var", "")).strip()
    if token_env_var:
        return os.getenv(token_env_var, "").strip()

    return ""

def load_prompt_markdown(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()

def extract_json_object(text: str) -> dict:
    raw = clean_text(text)
    if not raw:
        raise ValueError("AI response was empty")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))

def call_ai_chat(endpoint: str, token: str, messages: List[dict], temperature: float = 0.2, timeout_seconds: int = 120, verify_ssl: bool = False) -> str:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"messages": messages, "temperature": temperature}
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout_seconds, verify=verify_ssl)
    resp.raise_for_status()
    data = resp.json() if "application/json" in resp.headers.get("Content-Type", "") else {"content": resp.text}

    if isinstance(data, dict):
        if data.get("choices"):
            return data["choices"][0]["message"]["content"].strip()
        if "content" in data:
            return str(data["content"]).strip()
        if "response" in data:
            return str(data["response"]).strip()
        if "answer" in data:
            return str(data["answer"]).strip()

    return json.dumps(data, indent=2)

def build_page_elements_from_review(review_data: dict) -> dict:
    approved = review_data.get("approved_elements", []) if isinstance(review_data, dict) else []
    elements = []
    for item in approved:
        if not isinstance(item, dict):
            continue
        name = clean_text(str(item.get("name", "")))
        element_type = clean_text(str(item.get("type", "")))
        locator = clean_text(str(item.get("locator", "")))
        description = clean_text(str(item.get("description", "")))
        if name and element_type and locator:
            elements.append({
                "name": slugify(name),
                "type": element_type,
                "locator": locator,
                "description": description,
            })
    return {"elements": elements}

def refine_page_elements_with_ai(config: dict, page_name: str, url: str, elements: List[dict], screenshot_path: Path, html_path: Path, metadata_dir: Path, workflow_like: dict | None = None) -> dict | None:
    ai = config.get("ai", {})
    if not ai.get("enabled", False):
        return None

    endpoint = ai.get("endpoint", "")
    token = get_ai_token(ai)
    if not endpoint or not token:
        logger.warning("AI enabled but endpoint/token missing. Skipping page elements review/refinement.")
        return None

    reviewer_md = load_prompt_markdown("page_elements_reviewer.md")
    refiner_md = load_prompt_markdown("page_elements_refiner.md")
    if not reviewer_md or not refiner_md:
        logger.warning("Page elements reviewer/refiner prompt missing. Skipping page elements AI stage.")
        return None

    timeout_seconds = int(ai.get("timeout_seconds", 120))
    verify_ssl = bool(ai.get("verify_ssl", False))
    temperature = float(ai.get("temperature", 0.2))
    workflow_context = {
        "page_name": page_name,
        "page_slug": slugify(page_name),
        "url": url,
        "artifact_purpose": "approved page model for downstream resource and automation generation"
    }
    workflow_memory = {}
    relevant_workflow_knowledge = []
    if isinstance(workflow_like, dict) and workflow_like:
        try:
            workflow_memory = build_workflow_knowledge_context(workflow_like)
            relevant_workflow_knowledge = discover_relevant_workflow_knowledge(workflow_like)
        except Exception as exc:
            logger.warning("Workflow knowledge discovery failed for %s page review: %s", page_name, exc)
    reviewer_payload = {
        "workflow_context": workflow_context,
        "current_workflow_knowledge": workflow_memory,
        "relevant_workflow_knowledge": relevant_workflow_knowledge,
        "page_name": page_name,
        "screenshot_path": str(screenshot_path.relative_to(BASE_DIR)).replace("\\", "/") if screenshot_path.exists() else "",
        "debug_html_path": str(html_path.relative_to(BASE_DIR)).replace("\\", "/") if html_path.exists() else "",
        "draft_elements": elements,
    }

    try:
        review_text = call_ai_chat(
            endpoint,
            token,
            messages=[
                {"role": "system", "content": reviewer_md},
                {"role": "user", "content": json.dumps(reviewer_payload, indent=2, ensure_ascii=False)}
            ],
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
        review_data = extract_json_object(review_text)
        review_path = metadata_dir / f"{slugify(page_name)}.elements.review.json"
        review_path.write_text(json.dumps(review_data, indent=2, ensure_ascii=False), encoding="utf-8")

        refiner_payload = {
            "workflow_context": workflow_context,
            "current_workflow_knowledge": workflow_memory,
            "relevant_workflow_knowledge": relevant_workflow_knowledge,
            "page_name": page_name,
            "screenshot_path": reviewer_payload["screenshot_path"],
            "debug_html_path": reviewer_payload["debug_html_path"],
            "draft_elements": elements,
            "review_findings": review_data,
        }
        refined_text = call_ai_chat(
            endpoint,
            token,
            messages=[
                {"role": "system", "content": refiner_md},
                {"role": "user", "content": json.dumps(refiner_payload, indent=2, ensure_ascii=False)}
            ],
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
        refined_data = extract_json_object(refined_text)
        if not isinstance(refined_data, dict) or not isinstance(refined_data.get("elements"), list):
            refined_data = build_page_elements_from_review(review_data)
        refined_data["page_name"] = page_name
        approved_path = metadata_dir / f"{slugify(page_name)}.elements.approved.json"
        refined_data["artifacts"] = {
            "screenshot_path": reviewer_payload["screenshot_path"],
            "debug_html_path": reviewer_payload["debug_html_path"],
            "review_path": str(review_path.relative_to(BASE_DIR)).replace("\\", "/"),
        }
        approved_path.write_text(json.dumps(refined_data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("AI-reviewed page elements written: %s", review_path)
        logger.info("AI-approved page elements written: %s", approved_path)
        return refined_data
    except Exception as exc:
        logger.warning("AI page elements review/refinement failed for %s: %s", page_name, exc)
        return None

def validate_config(config: dict) -> dict:
    pages = config.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError("'pages' must be a list.")

    browser = str(config.get("browser", "chromium")).lower()
    if browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"Unsupported browser '{browser}'. Supported: {sorted(SUPPORTED_BROWSERS)}")

    config["browser"] = browser
    config["pom_output_dir"] = str(config.get("pom_output_dir", "pom_pages"))
    config["headless"] = bool(config.get("headless", True))
    config["wait_seconds"] = int(config.get("wait_seconds", 3))
    config["accept_cookies"] = bool(config.get("accept_cookies", False))
    config["cookie_button_text"] = str(config.get("cookie_button_text", "Accept"))

    if "generation_control" not in config:
        config["generation_control"] = {}

    gc = config["generation_control"]
    gc["regenerate_pom_pages"] = bool(gc.get("regenerate_pom_pages", True))
    gc["overwrite_pom_pages"] = bool(gc.get("overwrite_pom_pages", False))
    gc["excluded_pom_modules"] = [slugify(x) for x in gc.get("excluded_pom_modules", []) if str(x).strip()]

    if "ai" not in config:
        config["ai"] = {}

    ai = config["ai"]
    ai["enabled"] = bool(ai.get("enabled", False))
    ai["endpoint"] = str(ai.get("endpoint", "")).strip()
    ai["temperature"] = float(ai.get("temperature", 0.2))

    return config

def is_meaningless_label(text: str) -> bool:
    return slugify(text) in {
        "input", "button", "link", "textbox", "password",
        "select", "dropdown", "element", "ion_input", "ion_button"
    }

def infer_role(item: dict) -> str:
    tag = (item.get("tag") or "").lower()
    attrs = item.get("attributes", {}) or {}
    shadow = item.get("shadow", {}) or {}
    shadow_tag = clean_text(shadow.get("tag", "")).lower()
    input_type = (attrs.get("type") or shadow.get("type") or "").lower()

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
            return "password"
        if input_type == "checkbox":
            return "checkbox"
        if input_type == "radio":
            return "radio"
        return "textbox"
    if shadow_tag == "button" and clean_text(attrs.get("id", "")):
        return "button"
    return "element"

def infer_label(item: dict) -> str:
    attrs = item.get("attributes", {}) or {}
    shadow = item.get("shadow", {}) or {}
    tag = (item.get("tag") or "").lower()
    locator_hint = build_best_locator(item).lower()

    primary_candidates = [
        item.get("label", ""),
        attrs.get("aria-label", ""),
        attrs.get("placeholder", ""),
        attrs.get("name", ""),
        attrs.get("id", ""),
        attrs.get("data-testid", ""),
        attrs.get("icsicon", ""),
        item.get("text", "")
    ]
    shadow_candidates = [
        shadow.get("aria_label", ""),
        shadow.get("placeholder", ""),
        shadow.get("icon_aria_label", ""),
        shadow.get("text", "")
    ]

    raw_label = ""
    for c in primary_candidates:
        c = clean_text(c)
        if c and not is_meaningless_label(c):
            raw_label = c
            break

    if not raw_label:
        for c in shadow_candidates:
            c = clean_text(c)
            if c and not is_meaningless_label(c):
                raw_label = c
                break

    raw_label = raw_label or clean_text(item.get("tag", "element")) or "element"
    normalized = slugify(raw_label)

    normalized = re.sub(r"^(btn|button)_", "", normalized)
    normalized = re.sub(r"_(outline|icon)$", "", normalized)
    if normalized in {"person", "profile", "user"}:
        normalized = "profile"

    button_like = tag in {"button", "ion-button", "ion-fab-button", "app-main-button"}
    button_like = button_like or "btn_" in locator_hint or "button" in locator_hint or attrs.get("tappable") is not None

    if button_like and normalized and not normalized.endswith("button"):
        normalized = f"{normalized}_button"

    return normalized or "element"

def best_identity(item: dict) -> Tuple[str, str, str, str, str]:
    attrs = item.get("attributes", {}) or {}
    return (
        infer_role(item),
        clean_text(attrs.get("id", "")),
        clean_text(attrs.get("name", "")),
        clean_text(attrs.get("placeholder", "")),
        infer_label(item),
    )

def make_var_name(label: str, role: str, used_names: set) -> str:
    base = slugify(label)
    if is_meaningless_label(base):
        base = role
    if not base.endswith(role):
        base = f"{base}_{role}"

    name = base.upper()
    i = 2
    while name in used_names:
        name = f"{base.upper()}_{i}"
        i += 1
    used_names.add(name)
    return name

def build_best_locator(item: dict) -> str:
    tag = (item.get("tag") or "").lower()
    attrs = item.get("attributes", {}) or {}
    shadow = item.get("shadow", {}) or {}

    text = clean_text(item.get("text", ""))
    placeholder = clean_text(attrs.get("placeholder", "") or shadow.get("placeholder", ""))
    aria = clean_text(attrs.get("aria-label", "") or shadow.get("aria_label", "") or shadow.get("icon_aria_label", ""))
    name = clean_text(attrs.get("name", ""))
    el_id = clean_text(attrs.get("id", ""))
    data_testid = clean_text(attrs.get("data-testid", "") or attrs.get("testid", ""))
    formcontrolname = clean_text(attrs.get("formcontrolname", ""))

    if data_testid:
        return f"xpath=//*[@data-testid={xpath_literal(data_testid)}]"
    if el_id:
        return f"id={el_id}"
    if formcontrolname:
        return f"xpath=//*[@formcontrolname={xpath_literal(formcontrolname)}]"
    if tag == "ion-input":
        if placeholder:
            return f"xpath=//input[@placeholder={xpath_literal(placeholder)}]"
        if name:
            return f"xpath=//input[@name={xpath_literal(name)}]"
        if aria:
            return f"xpath=//input[@aria-label={xpath_literal(aria)}]"
        return "xpath=//ion-input"
    if tag in {"ion-button", "ion-fab-button"}:
        if text:
            if tag == "ion-fab-button":
                return f"xpath=//ion-fab-button[.//ion-icon[@aria-label={xpath_literal(text)}] or normalize-space(.)={xpath_literal(text)}]"
            return f"xpath=//{tag}[normalize-space(.)={xpath_literal(text)}]"
        if aria:
            return f"xpath=//{tag}[@aria-label={xpath_literal(aria)}]"
        if name:
            return f"xpath=//{tag}[@name={xpath_literal(name)}]"
        return f"xpath=//{tag}"
    if tag == "app-main-button":
        if el_id:
            return f"id={el_id}"
        if name:
            return f"xpath=//app-main-button[@name={xpath_literal(name)}]"
        if aria:
            return f"xpath=//app-main-button[@aria-label={xpath_literal(aria)}]"
        if text:
            return f"xpath=//app-main-button[normalize-space(.)={xpath_literal(text)}]"
        return "xpath=//app-main-button"
    if name and tag in {"input", "textarea", "select"}:
        return f"xpath=//{tag}[@name={xpath_literal(name)}]"
    if placeholder and tag in {"input", "textarea"}:
        return f"xpath=//{tag}[@placeholder={xpath_literal(placeholder)}]"
    if aria:
        return f"xpath=//{tag}[@aria-label={xpath_literal(aria)}]"
    if text and tag in {"button", "a"}:
        return f"xpath=//{tag}[normalize-space(.)={xpath_literal(text)}]"
    return f"xpath=//{tag}"

def should_skip_item(item: dict) -> bool:
    tag = (item.get("tag") or "").lower()
    attrs = item.get("attributes", {}) or {}
    shadow = item.get("shadow", {}) or {}
    text = clean_text(item.get("text", ""))
    label = clean_text(item.get("label", ""))
    placeholder = clean_text(attrs.get("placeholder", "") or shadow.get("placeholder", ""))
    aria = clean_text(attrs.get("aria-label", "") or shadow.get("aria_label", "") or shadow.get("icon_aria_label", ""))
    name = clean_text(attrs.get("name", ""))
    el_id = clean_text(attrs.get("id", ""))
    formcontrolname = clean_text(attrs.get("formcontrolname", ""))
    data_testid = clean_text(attrs.get("data-testid", ""))
    role_attr = clean_text(attrs.get("role", ""))
    css_class = clean_text(attrs.get("class", ""))
    href = clean_text(attrs.get("href", ""))
    visibility = item.get("visibility", {}) or {}
    shadow_disabled = bool(shadow.get("disabled", False))
    is_enabled = not bool(attrs.get("disabled")) and not shadow_disabled

    interactive_tags = {
        "input", "textarea", "select", "button", "a",
        "ion-button", "ion-input", "ion-select", "ion-fab-button", "app-main-button"
    }
    semantic_text_tags = {"label", "p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "span", "svg"}
    allowed = interactive_tags | semantic_text_tags
    if tag not in allowed:
        return True

    if not visibility.get("is_visible", False):
        return True

    if tag in interactive_tags and not is_enabled:
        return True

    if tag == "button":
        parent_tag = clean_text(str(attrs.get("data-shadow-host-tag", ""))).lower()
        if parent_tag in {"ion-fab-button", "ion-button", "app-main-button", "ion-input"}:
            return True

    meaningful_content = any([text, label, placeholder, aria, name, el_id, formcontrolname, data_testid, href])
    interactive_candidate = (
        tag in interactive_tags
        or role_attr in {"button", "link", "textbox", "combobox", "menuitem"}
        or attrs.get("tappable") is not None
        or clean_text(attrs.get("onclick", ""))
        or clean_text(attrs.get("tabindex", ""))
        or bool(href)
    )
    semantic_candidate = (
        tag in semantic_text_tags
        and meaningful_content
        and (
            len(text) >= 3
            or len(label) >= 3
            or role_attr in {"heading", "link", "img", "button"}
            or "forgot" in text.lower()
            or "title" in css_class.lower()
            or "header" in css_class.lower()
            or "link" in css_class.lower()
            or tag == "svg"
        )
    )

    if not interactive_candidate and not semantic_candidate:
        return True

    if tag in {"input", "textarea", "select", "ion-input", "ion-select"}:
        return not any([placeholder, aria, name, el_id, formcontrolname, data_testid, label, text])

    if tag in {"button", "a", "ion-button", "ion-fab-button", "app-main-button"}:
        return not any([text, aria, name, el_id, label, data_testid, href])

    if tag == "svg":
        return not any([aria, label, text, css_class])

    return not meaningful_content

def is_duplicate_item(item: dict, seen_identity: set, seen_locator: set) -> bool:
    identity = best_identity(item)
    locator = build_best_locator(item).lower()
    if identity in seen_identity or locator in seen_locator:
        return True

    role = infer_role(item)
    if role in {"textbox", "password"}:
        attrs = item.get("attributes", {}) or {}
        placeholder = clean_text(attrs.get("placeholder", ""))
        name = clean_text(attrs.get("name", ""))
        el_id = clean_text(attrs.get("id", ""))
        semantic_locator = f"{role}|{placeholder}|{name}|{el_id}"
        if semantic_locator in seen_locator:
            return True
        seen_locator.add(semantic_locator)

    seen_identity.add(identity)
    seen_locator.add(locator)
    return False

def score_item(item: dict) -> int:
    tag = (item.get("tag") or "").lower()
    attrs = item.get("attributes", {}) or {}
    text = clean_text(item.get("text", ""))
    label = clean_text(item.get("label", ""))
    placeholder = clean_text(attrs.get("placeholder", ""))
    aria = clean_text(attrs.get("aria-label", ""))
    name = clean_text(attrs.get("name", ""))
    el_id = clean_text(attrs.get("id", ""))
    css_class = clean_text(attrs.get("class", ""))
    href = clean_text(attrs.get("href", ""))
    role = infer_role(item)

    score = 0
    if tag in {"input", "ion-input", "textarea", "select", "ion-select", "button", "ion-button", "app-main-button", "ion-fab-button", "a"}:
        score += 40
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "label", "p", "svg"}:
        score += 20
    if role in {"textbox", "password", "dropdown", "button", "link"}:
        score += 25
    if placeholder:
        score += 30
    if label:
        score += 20
    if aria:
        score += 15
    if text:
        score += 15
    if name:
        score += 10
    if el_id:
        score += 10
    if href:
        score += 15
    if "forgot" in text.lower() or "forgot" in css_class.lower():
        score += 30
    if any(token in css_class.lower() for token in {"title", "header", "link", "icon"}):
        score += 10
    if clean_text(attrs.get("data-shadow-host-tag", "")):
        score -= 20
    return score


def collect_elements(page) -> List[dict]:
    js = """
    () => {
      const hasVisibleStyle = (el) => {
        if (!el) return false;
        const s = window.getComputedStyle(el);
        if (!s) return false;
        if (s.visibility === 'hidden' || s.display === 'none') return false;
        if (Number.parseFloat(s.opacity || '1') === 0) return false;
        if (s.pointerEvents === 'none') return false;
        if (el.hasAttribute('hidden') || el.getAttribute('aria-hidden') === 'true') return false;
        return true;
      };

      const getParentElement = (node) => {
        if (!node) return null;
        if (node.parentElement) return node.parentElement;
        const root = node.getRootNode && node.getRootNode();
        if (root && root.host) return root.host;
        return null;
      };

      const hasVisibleDescendant = (el) => {
        const visit = (root) => {
          if (!root || !root.querySelectorAll) return false;
          const descendants = root.querySelectorAll('*');
          for (const child of descendants) {
            if (!hasVisibleStyle(child)) continue;
            const r = child.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) return true;
            if (child.shadowRoot && visit(child.shadowRoot)) return true;
          }
          return false;
        };
        return visit(el);
      };

      const isActuallyVisible = (el) => {
        if (!el || !el.isConnected) return false;
        let current = el;
        while (current && current.nodeType === Node.ELEMENT_NODE) {
          if (!hasVisibleStyle(current)) return false;
          current = getParentElement(current);
        }
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) {
          return hasVisibleDescendant(el);
        }
        return true;
      };

      const getTextFromRoot = (root) => {
        if (!root) return '';
        const direct = (root.innerText || root.textContent || '').trim();
        if (direct) return direct;

        const child = root.querySelector && root.querySelector('button, span, div, label, p, h1, h2, h3, h4, h5, h6, slot');
        if (child) {
          const childText = (child.innerText || child.textContent || '').trim();
          if (childText) return childText;
        }

        const icon = root.querySelector && root.querySelector('ion-icon[aria-label]');
        if (icon) {
          const iconAria = (icon.getAttribute('aria-label') || '').trim();
          if (iconAria) return iconAria;
        }

        return '';
      };

      const getText = (el) => {
        const placeholder = (el.getAttribute('placeholder') || '').trim();
        if (placeholder) return placeholder;

        const aria = (el.getAttribute('aria-label') || '').trim();
        if (aria) return aria;

        const href = (el.getAttribute('href') || '').trim();
        if (!href) {
          const cls = (el.getAttribute('class') || '').toLowerCase();
          if (cls.includes('forgot') || cls.includes('link') || cls.includes('title') || cls.includes('header')) {
            const clsText = getTextFromRoot(el);
            if (clsText) return clsText;
          }
        }

        const hostText = getTextFromRoot(el);
        if (hostText) return hostText;
        if (el.shadowRoot) {
          const shadowText = getTextFromRoot(el.shadowRoot);
          if (shadowText) return shadowText;
        }

        const id = (el.getAttribute('id') || '').trim();
        if (id) return id;

        return '';
      };

      const getShadowInfo = (el) => {
        const shadow = el.shadowRoot;
        if (!shadow) return null;
        const nativeControl = shadow.querySelector('button, input, textarea, select, a, [role="button"], [role="link"]');
        const icon = shadow.querySelector('ion-icon[aria-label], [aria-label]');
        const control = nativeControl || icon;
        if (!control) return {
          has_shadow_root: true,
          has_native_control: false,
          text: getTextFromRoot(shadow),
          icon_aria_label: '',
          aria_label: '',
          tag: '',
          type: '',
          disabled: false,
          placeholder: ''
        };
        return {
          has_shadow_root: true,
          has_native_control: !!nativeControl,
          text: getTextFromRoot(control) || getTextFromRoot(shadow),
          icon_aria_label: (shadow.querySelector('ion-icon[aria-label]')?.getAttribute('aria-label') || '').trim(),
          aria_label: (control.getAttribute('aria-label') || '').trim(),
          tag: (control.tagName || '').toLowerCase(),
          type: (control.getAttribute('type') || '').trim(),
          disabled: control.hasAttribute('disabled') || !!control.disabled,
          placeholder: (control.getAttribute('placeholder') || '').trim()
        };
      };

      const tags = [
        'input',
        'textarea',
        'select',
        'button',
        'a',
        'label',
        'p',
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'div',
        'span',
        'svg',
        'ion-button',
        'ion-input',
        'ion-select',
        'ion-fab-button',
        'app-main-button',
        'ion-item'
      ];

      const attrSelectors = [
        '[tappable]',
        '[role="button"]',
        '[role="link"]',
        '[onclick]',
        '[tabindex]',
        '[id^="btn_"]'
      ];

      const nodes = [];
      const seen = new Set();

      const pushNode = (node) => {
        if (!node || seen.has(node)) return;
        seen.add(node);
        nodes.push(node);
      };

      const collectFromRoot = (root, hostTag = '') => {
        if (!root || !root.querySelectorAll) return;
        for (const node of root.querySelectorAll(tags.join(','))) {
          if (hostTag) node.setAttribute('data-shadow-host-tag', hostTag);
          pushNode(node);
        }
        for (const node of root.querySelectorAll(attrSelectors.join(','))) {
          if (hostTag) node.setAttribute('data-shadow-host-tag', hostTag);
          pushNode(node);
        }
        for (const el of root.querySelectorAll('*')) {
          if (el.shadowRoot) {
            pushNode(el);
            collectFromRoot(el.shadowRoot, (el.tagName || '').toLowerCase());
          }
        }
      };

      const isRelevantFabButton = (el) => {
        if (!el || (el.tagName || '').toLowerCase() !== 'ion-fab-button') return true;
        const iconLabel = (el.querySelector('ion-icon[aria-label]')?.getAttribute('aria-label') || '').trim().toLowerCase();
        const hostText = getText(el).trim().toLowerCase();
        const label = iconLabel || hostText;
        return ['home', 'arrow back', 'back', 'notifications', 'person', 'profile', 'user'].includes(label);
      };

      collectFromRoot(document);

      return nodes
        .filter(el => {
          if (!isRelevantFabButton(el)) return false;
          return true;
        })
        .map(el => {
          const attrs = {};
          for (const a of el.attributes) attrs[a.name] = a.value;

          let label = '';
          const id = el.getAttribute('id');
          if (id) {
            const linked = document.querySelector(`label[for="${id}"]`);
            if (linked) label = (linked.innerText || linked.textContent || '').trim();
          }
          if (!label) {
            const parent = el.closest && el.closest('label');
            if (parent) label = (parent.innerText || parent.textContent || '').trim();
          }

          const rect = el.getBoundingClientRect();
          const shadow = getShadowInfo(el);
          const visibility = {
            is_visible: isActuallyVisible(el),
            is_in_viewport: rect.bottom > 0 && rect.right > 0 && rect.top < window.innerHeight && rect.left < window.innerWidth,
            is_covered: false,
            has_visible_descendant: hasVisibleDescendant(el),
            width: rect.width,
            height: rect.height,
            x: rect.x,
            y: rect.y
          };

          return {
            tag: (el.tagName || '').toLowerCase(),
            text: getText(el),
            attributes: attrs,
            label: label,
            visibility: visibility,
            shadow: shadow
          };
        })
        .filter(item => item.visibility && item.visibility.is_visible);
    }
    """
    raw = page.evaluate(js)
    logger.info("Raw extracted nodes count: %s", len(raw))

    raw_sorted = sorted(raw, key=score_item, reverse=True)

    out, seen_id, seen_loc = [], set(), set()
    for item in raw_sorted:
        if should_skip_item(item):
            continue
        if is_duplicate_item(item, seen_id, seen_loc):
            continue
        out.append(item)

    logger.info("Filtered extracted elements count: %s", len(out))
    if out:
        tags_summary = {}
        for item in out:
            tag = item.get("tag", "unknown")
            tags_summary[tag] = tags_summary.get(tag, 0) + 1
        logger.info("Element tags after filtering: %s", tags_summary)

    return out

def build_fallback_keyword_name(label: str, role: str) -> str:
    label_title = title_case(label)
    if role == "dropdown":
        return f"Select {label_title}"
    if role == "checkbox":
        return f"Set {label_title}"
    if role in {"textbox", "password"}:
        return f"Enter {label_title}"
    if role in {"button", "link", "radio"}:
        return label_title if clean_text(label_title).lower().startswith(("click ", "open ", "select ")) else f"Click {label_title}"
    return label_title or "Interact With Element"


def build_fallback_keyword_arguments(role: str) -> List[str]:
    if role == "textbox":
        return ["${text}"]
    if role == "password":
        return ["${password}"]
    if role == "dropdown":
        return ["${value}"]
    return []


def build_fallback_keyword_steps(var_name: str, role: str) -> List[str]:
    steps = [f"Wait Until Element Is Visible    ${{{var_name}}}"]
    if role in {"button", "link", "radio", "element"}:
        steps.append(f"Click Element    ${{{var_name}}}")
        return steps
    if role == "textbox":
        steps.append(f"Input Text    ${{{var_name}}}    ${{text}}")
        return steps
    if role == "password":
        steps.append(f"Input Password    ${{{var_name}}}    ${{password}}")
        return steps
    if role == "dropdown":
        steps.append(f"Select From List By Label    ${{{var_name}}}    ${{value}}")
        return steps
    if role == "checkbox":
        steps.append(f"Select Checkbox    ${{{var_name}}}")
        return steps
    steps.append(f"Click Element    ${{{var_name}}}")
    return steps


def generate_fallback_keyword_block(var_name: str, label: str, role: str) -> dict:
    keyword_name = build_fallback_keyword_name(label, role)
    return {
        "keywordName": keyword_name,
        "arguments": build_fallback_keyword_arguments(role),
        "implementation": build_fallback_keyword_steps(var_name, role),
        "approved": True,
        "origin": "generator_fallback",
    }


def load_reviewed_keyword_artifact(page_name: str, metadata_dir: Path) -> dict:
    candidates = [
        metadata_dir / f"{slugify(page_name)}.keywords.reviewed.json",
        metadata_dir / f"{slugify(page_name)}.keywords.json",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return {}


def normalize_placeholder_page_url(value: str) -> str:
    cleaned = clean_text(value)
    if not cleaned:
        return ""
    if cleaned.lower() in {"none", "null", "n/a", "na"}:
        return ""
    return cleaned


def _normalize_keyword_implementation_lines(lines: object) -> List[str]:
    if isinstance(lines, str):
        raw_lines = lines.splitlines()
    elif isinstance(lines, list):
        raw_lines = [str(item) for item in lines]
    else:
        raw_lines = []
    normalized: List[str] = []
    for idx, line in enumerate(raw_lines):
        text = str(line).rstrip()
        if not clean_text(text):
            continue
        if idx == 0 and text.lstrip().startswith("["):
            normalized.append("    " + text.lstrip())
        elif text.startswith((" ", "\t")):
            normalized.append(text)
        else:
            normalized.append("    " + text.lstrip())
    return normalized


def _derive_keyword_name_from_element_name(element_name: str, role: str, fallback_name: str) -> str:
    normalized_element = slugify(element_name)
    if not normalized_element:
        return clean_text(fallback_name)
    return build_fallback_keyword_name(normalized_element, role)


def normalize_reviewed_keyword_block(keyword: dict, approved_elements_by_name: Dict[str, dict] | None = None) -> str:
    keyword_name = clean_text(str(keyword.get("keywordName", "")))
    role = clean_text(str(keyword.get("role", ""))).lower()
    approved_elements_by_name = approved_elements_by_name or {}
    matched_element_name = ""
    locator = clean_text(str(keyword.get("targetElement", "")))
    if locator:
        for element_name, element in approved_elements_by_name.items():
            if clean_text(str(element.get("locator", ""))) == locator:
                matched_element_name = element_name
                if not role:
                    role = clean_text(str(element.get("type", ""))).lower()
                break
    if matched_element_name:
        keyword_name = _derive_keyword_name_from_element_name(matched_element_name, role or "element", keyword_name)
    if not keyword_name:
        return ""
    block_lines = [keyword_name]
    arguments = keyword.get("arguments", []) or []
    if isinstance(arguments, str):
        arguments = [part.strip() for part in arguments.split(",") if clean_text(part)]
    normalized_args = []
    for arg in arguments:
        cleaned_arg = clean_text(str(arg)).replace("${", "").replace("}", "")
        if cleaned_arg:
            normalized_args.append(f"${{{cleaned_arg}}}")
    if normalized_args:
        block_lines.append("    [Arguments]    " + "    ".join(normalized_args))
    block_lines.extend(_normalize_keyword_implementation_lines(keyword.get("implementation", [])))
    return "\n".join(block_lines)


def generate_resource(url: str, elements: List[dict], page_name: str = "", metadata_dir: Path | None = None) -> str:
    used_names, variables = set(), []
    fallback_keyword_blocks: List[dict] = []
    normalized_page_url = normalize_placeholder_page_url(url)

    for item in elements:
        if isinstance(item, dict) and {"name", "type", "locator"}.issubset(item.keys()):
            role = clean_text(str(item.get("type", ""))).lower() or "element"
            label = slugify(str(item.get("name", "")))
            locator = clean_text(str(item.get("locator", "")))
        else:
            role = infer_role(item)
            label = infer_label(item)
            locator = build_best_locator(item)
        var_name = make_var_name(label, role, used_names)

        variables.append(f"${{{var_name}}}    {locator}")
        fallback_keyword_blocks.append(generate_fallback_keyword_block(var_name, label, role))

    approved_elements_by_name: Dict[str, dict] = {}
    for item in elements:
        if isinstance(item, dict) and {"name", "type", "locator"}.issubset(item.keys()):
            element_name = clean_text(str(item.get("name", "")))
            if element_name:
                approved_elements_by_name[element_name] = item

    reviewed_keyword_blocks: List[dict] = []
    reviewed_keywords: List[str] = []
    if page_name and metadata_dir is not None:
        reviewed_artifact = load_reviewed_keyword_artifact(page_name, metadata_dir)
        raw_keywords = reviewed_artifact.get("keywords", []) if isinstance(reviewed_artifact, dict) else []
        if isinstance(raw_keywords, list):
            for item in raw_keywords:
                if not isinstance(item, dict):
                    continue
                if item.get("approved") is False:
                    continue
                reviewed_keyword_blocks.append(item)
                block = normalize_reviewed_keyword_block(item, approved_elements_by_name)
                if block:
                    reviewed_keywords.append(block)

    settings_block = """*** Settings ***
Resource    ../../resources/common_keywords.resource"""

    variables_block = "*** Variables ***"
    if normalized_page_url:
        variables_block += f"\n${{PAGE_URL}}    {normalized_page_url}"
    if variables:
        variables_block += "\n" + "\n".join(variables)

    keywords_block = "*** Keywords ***"
    final_keywords = reviewed_keywords
    if not final_keywords:
        final_keywords = [normalize_reviewed_keyword_block(item, approved_elements_by_name) for item in fallback_keyword_blocks if normalize_reviewed_keyword_block(item, approved_elements_by_name)]
    if final_keywords:
        keywords_block += "\n" + "\n\n".join(final_keywords)

    if reviewed_keyword_blocks and fallback_keyword_blocks:
        reviewed_names = {clean_text(str(item.get("keywordName", ""))).lower() for item in reviewed_keyword_blocks if clean_text(str(item.get("keywordName", "")))}
        fallback_names = {clean_text(str(item.get("keywordName", ""))).lower() for item in fallback_keyword_blocks if clean_text(str(item.get("keywordName", "")))}
        missing_reviewed_names = sorted(name for name in reviewed_names if name and name not in {clean_text(block.splitlines()[0]).lower() for block in final_keywords if clean_text(block)})
        if missing_reviewed_names:
            logger.warning(
                "Reviewed approved keyword names were not fully reflected in generated resource for %s: %s",
                page_name,
                ", ".join(missing_reviewed_names[:10]),
            )
        if reviewed_names and reviewed_names != fallback_names:
            logger.info(
                "Fallback element-derived keyword names differ from reviewed approved names for %s; reviewed names were preferred during resource generation.",
                page_name,
            )

        reviewed_keyword_text = "\n".join(reviewed_keywords)
        legacy_alias_refs = sorted(set(re.findall(r"\$\{([A-Z0-9_]+)\}", reviewed_keyword_text)))
        legacy_alias_refs = [name for name in legacy_alias_refs if name.startswith("AUTO_")]
        if legacy_alias_refs:
            logger.warning(
                "Reviewed approved keyword implementations for %s still reference non-canonical legacy alias variables: %s",
                page_name,
                ", ".join(legacy_alias_refs[:10]),
            )

    return f"{settings_block}\n\n{variables_block}\n\n{keywords_block}\n"

def is_valid_ai_resource(content: str) -> bool:
    if not content.strip():
        return False
    if "```" in content:
        return False
    if "*** Keywords ***" not in content or "*** Variables ***" not in content:
        return False
    return True

def maybe_ai_generate_keywords(config: dict, page_name: str, url: str, elements: List[dict], resource_path: Path):
    ai = config.get("ai", {})
    if not ai.get("enabled", False):
        return

    endpoint = ai.get("endpoint", "")
    token = get_ai_token(ai)
    temperature = ai.get("temperature", 0.2)

    if not endpoint or not token:
        logger.warning("AI enabled but endpoint/token missing. Skipping AI keyword generation.")
        return

    system_prompt = (
        "You are an expert Robot Framework engineer. "
        "Generate a single valid .resource file with *** Settings ***, *** Variables ***, *** Keywords ***. "
        "Use SeleniumLibrary. Include [Documentation] for every keyword. "
        "Prefer reliable locators from provided elements. Return only Robot code."
    )
    user_payload = {
        "page_name": page_name,
        "url": url,
        "elements": elements
    }

    try:
        ai_content = call_ai_chat(
            endpoint,
            token,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, indent=2)}
            ],
            temperature=temperature
        )
        if is_valid_ai_resource(ai_content):
            resource_path.write_text(ai_content, encoding="utf-8")
            logger.info("AI-enhanced resource generated: %s", resource_path)
        else:
            logger.warning("AI response not in expected Robot format. Kept deterministic resource.")
    except Exception as exc:
        logger.warning("AI keyword generation failed for %s: %s", page_name, exc)

def get_browser_engine(playwright, browser_name: str):
    if browser_name in {"chromium", "chrome", "edge"}:
        return playwright.chromium
    if browser_name == "firefox":
        return playwright.firefox
    if browser_name == "webkit":
        return playwright.webkit
    raise ValueError(f"Unsupported browser: {browser_name}")

def maybe_accept_cookies(page, enabled: bool, button_text: str):
    if not enabled:
        return
    xpath = f"//button[normalize-space(.)={xpath_literal(button_text)}] | //ion-button[normalize-space(.)={xpath_literal(button_text)}]"
    try:
        loc = page.locator(xpath)
        if loc.count() > 0:
            loc.first.click(timeout=3000)
            logger.info("Clicked cookie button: %s", button_text)
    except Exception:
        logger.info("Cookie button not found/click failed. Continuing.")

def wait_for_meaningful_page_content(page, wait_seconds: int):
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        logger.info("Networkidle wait timed out; continuing with additional waits.")

    selectors_to_try = [
        "input",
        "button",
        "textarea",
        "select",
        "ion-input",
        "ion-button",
        "ion-fab-button",
        "app-main-button",
        "[tappable]",
        "[id^='btn_']"
    ]

    found_selector = None
    for selector in selectors_to_try:
        try:
            page.wait_for_selector(selector, state="visible", timeout=5000)
            found_selector = selector
            break
        except Exception:
            continue

    if found_selector:
        logger.info("Meaningful visible selector found: %s", found_selector)
    else:
        logger.warning("No meaningful visible selector found during wait stage.")

    page.wait_for_timeout(wait_seconds * 1000)

    try:
        page.wait_for_function(
            """
            () => {
              const meaningful = Array.from(document.querySelectorAll('input, textarea, select, button, a, ion-input, ion-button, ion-select, ion-fab-button, app-main-button, [tappable], [role="button"], [id^="btn_"]'))
                .filter(el => {
                  const s = window.getComputedStyle(el);
                  const r = el.getBoundingClientRect();
                  return s.visibility !== 'hidden' && s.display !== 'none' && r.width > 0 && r.height > 0;
                });
              return meaningful.length >= 2;
            }
            """,
            timeout=8000
        )
        logger.info("Meaningful control count reached expected threshold.")
    except Exception:
        logger.warning("Meaningful control count threshold was not reached before timeout.")

def get_page_resource_variables(page_name: str) -> List[dict]:
    page_slug = slugify(page_name)
    resource_path = BASE_DIR / "pom_pages" / page_slug / f"{page_slug}.resource"
    if not resource_path.exists():
        return []
    try:
        resource_text = resource_path.read_text(encoding="utf-8")
    except Exception:
        return []

    variables: List[dict] = []
    in_variables = False
    for line in resource_text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if lowered == "*** variables ***":
            in_variables = True
            continue
        if stripped.startswith("***") and lowered != "*** variables ***":
            in_variables = False
            continue
        if not in_variables or not stripped:
            continue
        parts = re.split(r"\s{2,}|\t+", stripped, maxsplit=1)
        if len(parts) != 2:
            continue
        variable_token, value = parts
        if variable_token.startswith("${") and variable_token.endswith("}"):
            variables.append({
                "name": variable_token[2:-1].strip(),
                "value": value.strip(),
            })
    return variables


def resolve_known_element_locator(page_name: str, element_name: str) -> str:
    normalized_page = slugify(page_name)
    normalized_element = slugify(element_name)
    element_tokens = {token for token in re.split(r"[_\s]+", normalized_element) if token}

    best_locator = ""
    best_score = -1
    for item in get_page_resource_variables(normalized_page):
        variable_name = clean_text(str(item.get("name", "")))
        locator = clean_text(str(item.get("value", "")))
        slug_name = slugify(variable_name)
        if not locator:
            continue
        if slug_name == normalized_element:
            return locator
        score = 0
        variable_tokens = {token for token in re.split(r"[_\s]+", slug_name) if token}
        overlap = len(element_tokens & variable_tokens)
        if overlap:
            score += overlap
        if normalized_element and normalized_element in slug_name:
            score += 2
        if score > best_score:
            best_score = score
            best_locator = locator
    if best_locator and best_score > 0:
        return best_locator
    raise ValueError(f"Known element '{element_name}' was not found in resource variables for page '{page_name}'.")


def infer_story_navigation_steps(page_name: str, workflow_like: dict) -> Tuple[List[dict], List[dict]]:
    if not isinstance(workflow_like, dict):
        return [], []

    current_page = slugify(page_name)
    reuse_context = workflow_like.get("inferred_reuse_context") if isinstance(workflow_like.get("inferred_reuse_context"), dict) else {}
    relevant_resources = [str(item).replace("\\", "/").strip() for item in reuse_context.get("authoritativeResourceFiles", []) if str(item).strip()]
    if not relevant_resources:
        explicit_resources = workflow_like.get("resourceFiles", []) if isinstance(workflow_like.get("resourceFiles"), list) else []
        relevant_resources = [str(item).replace("\\", "/").strip() for item in explicit_resources if str(item).strip()]

    navigation_steps: List[dict] = []
    target_page_signals: List[dict] = []

    entry_page_payload = workflow_like.get("entryPage") if isinstance(workflow_like.get("entryPage"), dict) else {}
    target_page_payload = workflow_like.get("targetPage") if isinstance(workflow_like.get("targetPage"), dict) else {}
    entry_page_name = slugify(clean_text(str(entry_page_payload.get("name", ""))))
    target_page_name = slugify(clean_text(str(target_page_payload.get("name", ""))))

    if relevant_resources and entry_page_name and target_page_name and entry_page_name != target_page_name and current_page == target_page_name:
        navigation_steps.append({
            "action": "reuseApprovedEntryContext",
            "page": f"{entry_page_name}_page",
            "element": "",
        })

    deduped_signals: List[dict] = []
    seen = set()
    for signal in target_page_signals:
        key = json.dumps(signal, sort_keys=True)
        if key not in seen:
            seen.add(key)
            deduped_signals.append(signal)

    return navigation_steps, deduped_signals


def perform_navigation_steps(page, navigation_steps: List[dict], wait_seconds: int, navigation_debug: List[dict] | None = None):
    expanded_steps: List[dict] = []
    for step in navigation_steps:
        if not isinstance(step, dict):
            continue
        action = clean_text(str(step.get("action", "")))
        if action == "reuseApprovedEntryContext":
            source_page = clean_text(str(step.get("page", "")))
            inferred_context = step.get("inferredReuseContext") if isinstance(step.get("inferredReuseContext"), dict) else {}
            authoritative_resources = inferred_context.get("authoritativeResourceFiles", []) if isinstance(inferred_context.get("authoritativeResourceFiles"), list) else []
            start_count = len(expanded_steps)
            for resource_path in authoritative_resources:
                resource_name = Path(str(resource_path)).parent.name.strip()
                normalized_page = clean_text(resource_name)
                if not normalized_page:
                    continue
                if not normalized_page.endswith("_page"):
                    normalized_page = f"{normalized_page}_page"
                if source_page and normalized_page != source_page:
                    continue
                for candidate in extract_keywords_from_resource_file(normalized_page):
                    keyword_name = clean_text(str(candidate.get("name", "")))
                    if not keyword_name.lower().startswith("click "):
                        continue
                    element_name = keyword_name[6:].strip()
                    if not element_name:
                        continue
                    expanded_steps.append({
                        "action": "clickKnownElement",
                        "page": normalized_page,
                        "element": element_name,
                    })
                if len(expanded_steps) > start_count:
                    break
            if len(expanded_steps) == start_count:
                raise ValueError(f"Unable to expand approved entry context for step targeting '{source_page or 'unknown'}'.")
            continue
        expanded_steps.append(step)

    for index, step in enumerate(expanded_steps, start=1):
        action = clean_text(str(step.get("action", "")))
        source_page = clean_text(str(step.get("page", "")))
        element_name = clean_text(str(step.get("element", "")))
        if action != "clickKnownElement":
            raise ValueError(f"Unsupported navigation action '{action}' in step {index}. MVP supports only clickKnownElement and reuseApprovedEntryContext.")
        locator = resolve_known_element_locator(source_page, element_name)
        debug_entry = {
            "step": index,
            "action": action,
            "source_page": source_page,
            "element": element_name,
            "locator": locator,
        }
        logger.info("Navigation step %s: %s -> %s.%s using locator %s", index, action, source_page, element_name, locator)
        target = page.locator(locator).first
        try:
            debug_entry["count"] = target.count()
        except Exception:
            debug_entry["count"] = -1
        try:
            debug_entry["visible_before_click"] = target.is_visible(timeout=3000)
        except Exception:
            debug_entry["visible_before_click"] = False
        target.click(timeout=30000)
        debug_entry["clicked"] = True
        page.wait_for_timeout(max(wait_seconds, 1) * 1000)
        debug_entry["url_after_click"] = page.url
        if navigation_debug is not None:
            navigation_debug.append(debug_entry)


def semantic_login_state_satisfied(page) -> bool:
    try:
        password_present = page.locator("input[type='password']").count() > 0
    except Exception:
        password_present = False
    try:
        user_like_present = (
            page.locator("input[type='text'], input[type='email'], input[name*='user' i], input[id*='user' i], input[placeholder*='user' i], input[placeholder*='email' i]").count() > 0
        )
    except Exception:
        user_like_present = False
    try:
        action_present = (
            page.get_by_role("button", name=re.compile(r"log\s*in|login|sign\s*in", re.I)).count() > 0
            or page.locator("button, input[type='submit']").count() > 0
        )
    except Exception:
        action_present = False
    return password_present and (user_like_present or action_present)


def write_signal_timeout_debug(page, metadata_dir: Path, page_name: str):
    try:
        ensure_dir(metadata_dir)
        page.screenshot(path=str(metadata_dir / f"{page_name}.target-signal-timeout.png"), full_page=True)
    except Exception:
        pass
    try:
        (metadata_dir / f"{page_name}.target-signal-timeout.html").write_text(page.content(), encoding="utf-8")
    except Exception:
        pass
    try:
        controls = {
            "url": page.url,
            "title": page.title(),
            "inputs": page.locator("input").evaluate_all("els => els.map(e => ({type: e.type || '', id: e.id || '', name: e.name || '', placeholder: e.placeholder || ''}))"),
            "buttons": page.locator("button, input[type='submit'], a").evaluate_all("els => els.slice(0,50).map(e => ({text: (e.innerText || e.value || '').trim(), id: e.id || '', name: e.name || '', role: e.getAttribute('role') || ''}))"),
        }
        (metadata_dir / f"{page_name}.target-signal-timeout.controls.json").write_text(json.dumps(controls, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def wait_for_target_page_signals(page, target_page_signals: List[dict], wait_seconds: int, metadata_dir: Path | None = None, page_name: str = "page"):
    if not target_page_signals:
        logger.info("No target page signals were provided. Waiting briefly before extraction.")
        page.wait_for_timeout(max(wait_seconds, 1) * 1000)
        return

    login_like = any(clean_text(str(signal.get("value", ""))).lower() in {"username", "password", "login"} for signal in target_page_signals)
    timeout_ms = max(wait_seconds, 1) * 1000 * 6
    deadline = time.time() + (timeout_ms / 1000)
    pending = list(target_page_signals)
    while time.time() < deadline:
        if login_like and semantic_login_state_satisfied(page):
            logger.info("Semantic login-state detection satisfied target page signals.")
            return
        remaining = []
        for signal in pending:
            signal_type = clean_text(str(signal.get("type", "")))
            if signal_type == "knownElement":
                try:
                    locator = resolve_known_element_locator(str(signal.get("page", "")), str(signal.get("element", "")))
                    if page.locator(locator).first.is_visible(timeout=500):
                        continue
                except Exception:
                    pass
                remaining.append(signal)
                continue
            value = clean_text(str(signal.get("value", "")))
            if signal_type == "text":
                try:
                    if value and page.get_by_text(value, exact=False).first.is_visible(timeout=500):
                        continue
                except Exception:
                    pass
                remaining.append(signal)
                continue
            if signal_type == "selector":
                try:
                    if value and page.locator(value).first.is_visible(timeout=500):
                        continue
                except Exception:
                    pass
                remaining.append(signal)
                continue
            if signal_type == "title":
                try:
                    if value and value.lower() in page.title().lower():
                        continue
                except Exception:
                    pass
                remaining.append(signal)
                continue
            if signal_type == "urlContains":
                if value and value.lower() in page.url.lower():
                    continue
                remaining.append(signal)
                continue
            remaining.append(signal)
        if not remaining:
            logger.info("All target page signals were satisfied.")
            return
        pending = remaining
        page.wait_for_timeout(500)
    if metadata_dir is not None:
        write_signal_timeout_debug(page, metadata_dir, page_name)
    raise ValueError(f"Target page signals were not satisfied before timeout: {json.dumps(pending, ensure_ascii=False)}")


def process_page(playwright, config: dict, page_entry: Dict[str, str]):
    gc = config["generation_control"]
    page_name_raw = page_entry["page_name"]
    page_name = slugify(page_name_raw)
    url = page_entry["url"]

    if page_name in set(gc.get("excluded_pom_modules", [])):
        logger.warning(
            "Page '%s' is listed in generation_control.excluded_pom_modules; extraction will be skipped.",
            page_name_raw,
        )
        return

    root_pom_dir = BASE_DIR / config["pom_output_dir"]
    page_output_dir = root_pom_dir / page_name
    metadata_dir = page_output_dir / "metadata"
    ensure_dir(page_output_dir)
    ensure_dir(metadata_dir)

    json_path = metadata_dir / f"{page_name}.elements.json"
    resource_path = page_output_dir / f"{page_name}.resource"
    screenshot_path = metadata_dir / f"{page_name}.png"
    html_path = metadata_dir / f"{page_name}.debug.html"

    if resource_path.exists() and not gc.get("overwrite_pom_pages", False):
        logger.info("Skipped existing POM resource (overwrite disabled): %s", resource_path)
        return

    engine = get_browser_engine(playwright, config["browser"])
    browser = engine.launch(headless=config["headless"])
    page = browser.new_page(viewport={"width": 1920, "height": 1080})

    try:
        logger.info("Opening URL: %s", url)
        page.goto(url, wait_until="domcontentloaded", timeout=120000)

        navigation_steps = page_entry.get("navigation_steps", []) if isinstance(page_entry.get("navigation_steps"), list) else []
        target_page_signals = page_entry.get("target_page_signals", []) if isinstance(page_entry.get("target_page_signals"), list) else []
        navigation_debug: List[dict] = [{
            "page": page_name,
            "entry_url": url,
            "received_navigation_steps": navigation_steps,
            "received_target_page_signals": target_page_signals,
            "has_inferred_reuse_context": bool(page_entry.get("inferred_reuse_context")),
            "resource_files": (page_entry.get("inferred_reuse_context") or {}).get("authoritativeResourceFiles", []) if isinstance(page_entry.get("inferred_reuse_context"), dict) else [],
            "raw_resource_files": page_entry.get("resourceFiles", []) if isinstance(page_entry.get("resourceFiles"), list) else [],
            "story_excerpt": build_story_text(page_entry)[:800],
            "external_story_excerpt": build_story_text(page_entry.get("externalContext", {}))[:800] if isinstance(page_entry.get("externalContext"), dict) else "",
        }]
        debug_path = metadata_dir / f"{page_name}.navigation.debug.json"
        if not navigation_steps:
            inferred_steps, inferred_signals = infer_story_navigation_steps(page_name, page_entry)
            navigation_debug.append({
                "inferred_navigation_steps": inferred_steps,
                "inferred_target_page_signals": inferred_signals,
            })
            if inferred_steps:
                navigation_steps = inferred_steps
                if not target_page_signals:
                    target_page_signals = inferred_signals
                logger.info("Using story-driven inferred navigation steps for page '%s': %s", page_name, json.dumps(navigation_steps, ensure_ascii=False))

        debug_path.write_text(json.dumps(navigation_debug, indent=2, ensure_ascii=False), encoding="utf-8")

        if navigation_steps:
            try:
                perform_navigation_steps(page, navigation_steps, config["wait_seconds"], navigation_debug)
                wait_for_target_page_signals(page, target_page_signals, config["wait_seconds"], metadata_dir=metadata_dir, page_name=page_name)
                navigation_debug.append({"target_signals_satisfied": True, "final_url": page.url})
            except Exception as nav_exc:
                navigation_debug.append({"target_signals_satisfied": False, "final_url": page.url, "error": str(nav_exc)})
                debug_path.write_text(json.dumps(navigation_debug, indent=2, ensure_ascii=False), encoding="utf-8")
                raise
            debug_path.write_text(json.dumps(navigation_debug, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            navigation_debug.append({"navigation_attempted": False, "reason": "No navigation steps were available or inferred.", "final_url": page.url})
            debug_path.write_text(json.dumps(navigation_debug, indent=2, ensure_ascii=False), encoding="utf-8")

        wait_for_meaningful_page_content(page, config["wait_seconds"])

        logger.info("Final page URL after load: %s", page.url)
        try:
            logger.info("Page title: %s", page.title())
        except Exception:
            logger.info("Unable to fetch page title.")

        maybe_accept_cookies(page, config["accept_cookies"], config["cookie_button_text"])

        try:
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception as exc:
            logger.warning("Screenshot failed for %s: %s", page_name, exc)

        try:
            html_path.write_text(page.content(), encoding="utf-8")
        except Exception as exc:
            logger.warning("HTML save failed for %s: %s", page_name, exc)

        elements = collect_elements(page)

        if not elements:
            logger.warning("No meaningful elements extracted for page: %s", page_name)

        json_path.write_text(json.dumps(elements, indent=2, ensure_ascii=False), encoding="utf-8")

        approved_page_model = refine_page_elements_with_ai(
            config,
            page_name,
            url,
            elements,
            screenshot_path,
            html_path,
            metadata_dir,
        )
        if isinstance(approved_page_model, dict) and page_entry.get("inferred_reuse_context"):
            approved_page_model["inferredReuseContext"] = page_entry.get("inferred_reuse_context")
            approved_path = metadata_dir / f"{slugify(page_name)}.elements.approved.json"
            approved_path.write_text(json.dumps(approved_page_model, indent=2, ensure_ascii=False), encoding="utf-8")
        resource_elements = approved_page_model.get("elements", []) if isinstance(approved_page_model, dict) else elements

        resource_content = generate_resource(url, resource_elements, page_name=page_name, metadata_dir=metadata_dir)
        reviewed_keyword_artifact = load_reviewed_keyword_artifact(page_name, metadata_dir)
        reviewed_keyword_names = {
            clean_text(str(item.get("keywordName", "")))
            for item in (reviewed_keyword_artifact.get("keywords", []) if isinstance(reviewed_keyword_artifact, dict) else [])
            if isinstance(item, dict) and clean_text(str(item.get("keywordName", ""))) and item.get("approved") is not False
        }
        generated_keyword_names = {
            clean_text(match.group(1))
            for match in re.finditer(r"(?m)^([^\s].+?)\n(?:\s+\[Documentation\]|\s+\[Arguments\]|\s+\S)", resource_content.split("*** Keywords ***", 1)[1] if "*** Keywords ***" in resource_content else "")
            if clean_text(match.group(1))
        }
        missing_reviewed_names = sorted(name for name in reviewed_keyword_names if name not in generated_keyword_names)
        if missing_reviewed_names:
            logger.warning(
                "Reviewed approved keyword names were not fully reflected in generated resource for %s: %s",
                page_name,
                ", ".join(missing_reviewed_names[:10]),
            )
        resource_path.write_text(resource_content, encoding="utf-8")
        logger.info("Generated deterministic resource: %s", resource_path)

        maybe_ai_generate_keywords(config, page_name, url, resource_elements, resource_path)

        logger.info("Generated: %s", json_path)
        logger.info("Generated: %s", screenshot_path)
        logger.info("Generated: %s", html_path)

    except PlaywrightTimeoutError as exc:
        logger.error("Timeout while processing %s: %s", url, exc)
        raise
    finally:
        browser.close()

def build_single_page_config(config: dict, page_name: str, url: str) -> dict:
    single_config = dict(config)
    page_entry = {"page_name": page_name}
    resolved_url = clean_text(url) or "http://localhost/"
    page_entry["url"] = resolved_url
    single_config["pages"] = [page_entry]
    return single_config


def build_navigation_page_config(config: dict, page_name: str, entry_url: str, navigation_payload: dict) -> dict:
    single_config = dict(config)
    entry_page_payload = navigation_payload.get("entryPage", {}) if isinstance(navigation_payload.get("entryPage"), dict) else {}
    target_page_payload = navigation_payload.get("targetPage", {}) if isinstance(navigation_payload.get("targetPage"), dict) else {}
    workflow_like_payload = {
        "workflowName": clean_text(str(navigation_payload.get("workflowName", page_name))) or page_name,
        "feature": clean_text(str(navigation_payload.get("feature", ""))),
        "testIdentifierPrefix": clean_text(str(navigation_payload.get("testIdentifierPrefix", ""))),
        "applicationCode": clean_text(str(navigation_payload.get("applicationCode", ""))),
        "resourceFiles": navigation_payload.get("resourceFiles", []),
        "externalContext": navigation_payload.get("externalContext", {}) if isinstance(navigation_payload.get("externalContext"), dict) else {},
        "pages": navigation_payload.get("pages", []) if isinstance(navigation_payload.get("pages"), list) else [],
        "entryPage": {
            "name": clean_text(str(entry_page_payload.get("name", ""))) or page_name,
            "url": clean_text(str(entry_page_payload.get("url", ""))) or entry_url,
        },
        "targetPage": {
            "name": clean_text(str(target_page_payload.get("name", ""))) or page_name,
            "url": clean_text(str(target_page_payload.get("url", ""))),
        },
        "navigationSteps": navigation_payload.get("navigationSteps", []),
        "targetPageSignals": navigation_payload.get("targetPageSignals", []),
        "observedSteps": navigation_payload.get("observedSteps", []),
        "observedValidations": navigation_payload.get("observedValidations", []),
        "acceptanceCriteria": navigation_payload.get("acceptanceCriteria", []),
        "description": navigation_payload.get("description", ""),
        "userStory": navigation_payload.get("userStory", ""),
    }
    page_entry = {
        "page_name": page_name,
        "url": entry_url,
        "navigation_steps": [
            {
                **step,
                "inferredReuseContext": infer_workflow_reuse_context(workflow_like_payload),
            } if isinstance(step, dict) else step
            for step in navigation_payload.get("navigationSteps", [])
        ],
        "target_page_signals": navigation_payload.get("targetPageSignals", []),
        "inferred_reuse_context": infer_workflow_reuse_context(workflow_like_payload),
    }
    single_config["pages"] = [page_entry]
    return single_config

def parse_args():
    parser = argparse.ArgumentParser(description="Extract page model(s) and generate POM resources.")
    parser.add_argument("--page-name", help="Extract only this page name.")
    parser.add_argument("--url", help="Extract only this page URL.")
    parser.add_argument("--entry-url", help="Entry URL for navigation-based extraction.")
    parser.add_argument("--navigation-json", help="Navigation payload JSON for SPA extraction.")
    return parser.parse_args()

def main():
    args = parse_args()
    config = validate_config(load_config())
    gc = config["generation_control"]

    if not gc.get("regenerate_pom_pages", True):
        logger.info("POM generation is disabled via config (regenerate_pom_pages=false). Exiting.")
        return

    if args.navigation_json or args.entry_url:
        if not args.page_name:
            raise ValueError("--page-name must be provided for navigation-based extraction.")
        if not args.entry_url:
            raise ValueError("--entry-url must be provided for navigation-based extraction.")
        if not args.navigation_json:
            raise ValueError("--navigation-json must be provided for navigation-based extraction.")
        navigation_payload = json.loads(args.navigation_json)
        config = build_navigation_page_config(config, args.page_name, args.entry_url, navigation_payload)
    elif args.page_name or args.url:
        if not args.page_name:
            raise ValueError("--page-name must be provided for single-page extraction.")
        if not args.url:
            raise ValueError("--url must be provided for single-page extraction.")
        config = build_single_page_config(config, args.page_name, args.url)

    pages = config.get("pages", [])
    if not pages:
        raise ValueError("No pages available for extraction.")

    ensure_dir(BASE_DIR / config["pom_output_dir"])

    with sync_playwright() as playwright:
        for page_entry in pages:
            try:
                process_page(playwright, config, page_entry)
            except Exception as exc:
                logger.error("Failed page '%s': %s", page_entry.get("page_name"), exc)
                raise

if __name__ == "__main__":
    main()