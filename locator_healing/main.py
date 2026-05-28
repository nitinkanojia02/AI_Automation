import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from extractor import extract_locators
from locator_healing import heal_locator

def load_locators(file_path="locators.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def demo():
    url = "https://example.com"

    extract_locators(url, "locators.json")
    locators = load_locators("locators.json")

    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        for item in locators[:10]:
            result = heal_locator(driver, item)
            print(f'Element: {item["elementName"]}')
            print(f'Result: {result["status"]}')
            if result["locator"]:
                print(f'Locator used: {result["locator"]}')
            if result.get("score") is not None:
                print(f'Score: {result["score"]}')
            print("-" * 50)

    finally:
        driver.quit()

if __name__ == "__main__":
    demo()