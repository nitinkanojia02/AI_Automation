import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException


def load_validated_locators(file_path="validated_locators.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_by(by_value):
    mapping = {
        "id": By.ID,
        "name": By.NAME,
        "xpath": By.XPATH,
        "css selector": By.CSS_SELECTOR,
        "class name": By.CLASS_NAME,
        "tag name": By.TAG_NAME,
        "link text": By.LINK_TEXT,
        "partial link text": By.PARTIAL_LINK_TEXT
    }
    return mapping.get(by_value, by_value)


def try_locator(driver, locator):
    try:
        by = get_by(locator["by"])
        elements = driver.find_elements(by, locator["value"])
        if len(elements) == 1:
            el = elements[0]
            if el.is_displayed():
                return el
        elif len(elements) > 1:
            for el in elements:
                try:
                    if el.is_displayed():
                        return el
                except Exception:
                    pass
        return None
    except (NoSuchElementException, TimeoutException, WebDriverException):
        return None


def find_element_with_healing(driver, element_name, repository_file="validated_locators.json"):
    repo = load_validated_locators(repository_file)

    target = next((item for item in repo if item.get("elementName") == element_name), None)
    if not target:
        raise Exception(f"Element '{element_name}' not found in repository")

    locators_to_try = []
    if target.get("bestLocator"):
        locators_to_try.append(target["bestLocator"])

    locators_to_try.extend(target.get("fallbackLocators", []))

    for locator in locators_to_try:
        element = try_locator(driver, locator)
        if element is not None:
            print(f"[HEALED] Found '{element_name}' using {locator['type']} = {locator['value']}")
            return element

    raise Exception(f"Unable to locate element '{element_name}' using best or fallback locators")