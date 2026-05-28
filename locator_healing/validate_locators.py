import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import InvalidSelectorException, WebDriverException


def wait_for_page_ready(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def safe_find_elements(driver, by, value):
    try:
        return driver.find_elements(by, value)
    except (InvalidSelectorException, WebDriverException):
        return []


def build_candidate_locators(item):
    candidates = []

    def add(locator_type, by, value, score):
        if value and str(value).strip():
            candidates.append({
                "type": locator_type,
                "by": by,
                "value": value,
                "baseScore": score
            })

    tag = item.get("tag", "")
    el_id = item.get("id", "")
    name = item.get("name", "")
    placeholder = item.get("placeholder", "")
    aria = item.get("ariaLabel", "")
    text = item.get("ownText") or item.get("text") or ""
    alt = item.get("alt", "")
    src = item.get("src", "")
    title = item.get("title", "")
    css = item.get("cssSelector", "")
    xpath = item.get("xpath", "")
    attributes = item.get("attributes", {}) or {}

    add("id", By.ID, el_id, 100)

    if name:
        add("name", By.NAME, name, 95)
        if tag:
            add("css_name", By.CSS_SELECTOR, f'{tag}[name="{name}"]', 92)

    if attributes.get("data-testid"):
        add("data-testid", By.CSS_SELECTOR, f'[data-testid="{attributes["data-testid"]}"]', 99)

    if aria:
        add("aria-label", By.CSS_SELECTOR, f'{tag}[aria-label="{aria}"]' if tag else f'[aria-label="{aria}"]', 90)

    if placeholder:
        add("placeholder", By.CSS_SELECTOR, f'{tag}[placeholder="{placeholder}"]' if tag else f'[placeholder="{placeholder}"]', 88)

    if alt:
        add("alt", By.CSS_SELECTOR, f'{tag}[alt="{alt}"]' if tag else f'[alt="{alt}"]', 87)

    if title:
        add("title", By.CSS_SELECTOR, f'{tag}[title="{title}"]' if tag else f'[title="{title}"]', 86)

    if src:
        add("src", By.CSS_SELECTOR, f'{tag}[src="{src}"]' if tag else f'[src="{src}"]', 70)

    if text and len(text) <= 60 and tag:
        normalized = " ".join(text.split())
        add("xpath_text", By.XPATH, f'//{tag}[contains(normalize-space(.), "{normalized}")]', 75)
        add("xpath_any_text", By.XPATH, f'//*[contains(normalize-space(.), "{normalized}")]', 65)

    if xpath:
        add("extracted_xpath", By.XPATH, xpath, 60)

    if css:
        add("extracted_css", By.CSS_SELECTOR, css, 55)

    return candidates


def evaluate_locator(driver, locator):
    matches = safe_find_elements(driver, locator["by"], locator["value"])
    count = len(matches)

    visible = False
    enabled = False
    tag = ""
    matched_text = ""
    matched_attrs = {}

    if count >= 1:
        el = matches[0]
        try:
            visible = el.is_displayed()
        except Exception:
            visible = False

        try:
            enabled = el.is_enabled()
        except Exception:
            enabled = False

        try:
            tag = el.tag_name
        except Exception:
            tag = ""

        try:
            matched_text = (el.text or "").strip()
        except Exception:
            matched_text = ""

        try:
            matched_attrs = {
                "id": el.get_attribute("id"),
                "name": el.get_attribute("name"),
                "type": el.get_attribute("type"),
                "placeholder": el.get_attribute("placeholder"),
                "aria-label": el.get_attribute("aria-label"),
                "alt": el.get_attribute("alt"),
                "src": el.get_attribute("src"),
                "title": el.get_attribute("title"),
                "class": el.get_attribute("class")
            }
        except Exception:
            matched_attrs = {}

    uniqueness_bonus = 20 if count == 1 else 0
    visibility_bonus = 10 if visible else 0
    enabled_bonus = 5 if enabled else 0
    penalty = 30 if count == 0 else (10 if count > 1 else 0)

    final_score = locator["baseScore"] + uniqueness_bonus + visibility_bonus + enabled_bonus - penalty

    return {
        "type": locator["type"],
        "by": locator["by"],
        "value": locator["value"],
        "matchCount": count,
        "visible": visible,
        "enabled": enabled,
        "score": final_score,
        "matchedTag": tag,
        "matchedText": matched_text,
        "matchedAttributes": matched_attrs
    }


def dedupe_candidates(candidates):
    seen = set()
    deduped = []
    for c in candidates:
        key = (c["by"], c["value"])
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    return deduped


def validate_locators(url, input_file="locators.json", output_file="validated_locators.json"):
    with open(input_file, "r", encoding="utf-8") as f:
        extracted = json.load(f)

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    validated = []

    try:
        print(f"Opening URL: {url}")
        driver.get(url)
        wait_for_page_ready(driver)
        time.sleep(8)

        for idx, item in enumerate(extracted, start=1):
            element_name = item.get("elementName", f"element_{idx}")
            print(f"Validating {idx}/{len(extracted)}: {element_name}")

            candidates = build_candidate_locators(item)
            candidates = dedupe_candidates(candidates)

            evaluations = []
            for locator in candidates:
                result = evaluate_locator(driver, locator)
                evaluations.append(result)

            working = [
                e for e in evaluations
                if e["matchCount"] >= 1
            ]

            unique_working = [
                e for e in working
                if e["matchCount"] == 1
            ]

            ranked = sorted(
                unique_working if unique_working else working,
                key=lambda x: x["score"],
                reverse=True
            )

            best = ranked[0] if ranked else None

            validated.append({
                "elementName": element_name,
                "tag": item.get("tag", ""),
                "original": item,
                "bestLocator": best,
                "fallbackLocators": ranked[1:6] if len(ranked) > 1 else [],
                "allEvaluations": ranked
            })

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(validated, f, indent=2, ensure_ascii=False)

        print(f"Saved validated locators to {output_file}")
        return validated

    finally:
        driver.quit()


if __name__ == "__main__":
    test_url = "http://172.21.166.115/washtabui/login?data=undefined"
    validate_locators(test_url)