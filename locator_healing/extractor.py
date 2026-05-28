import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


JS_EXTRACT_RELEVANT = r"""
return (function () {
  function safeText(value) {
    return (value || '').replace(/\s+/g, ' ').trim();
  }

  function getTag(el) {
    return el && el.tagName ? el.tagName.toLowerCase() : '';
  }

  function getClassName(el) {
    if (!el) return '';
    if (typeof el.className === 'string') return el.className;
    if (el.getAttribute) return el.getAttribute('class') || '';
    return '';
  }

  function getText(el) {
    if (!el) return '';
    return safeText(el.innerText || el.textContent || '');
  }

  function getOwnText(el) {
    if (!el) return '';
    let text = '';
    for (const node of Array.from(el.childNodes || [])) {
      if (node.nodeType === Node.TEXT_NODE) {
        text += ' ' + node.textContent;
      }
    }
    return safeText(text);
  }

  function isVisible(el) {
    if (!el || !el.isConnected) return false;
    const style = window.getComputedStyle(el);
    if (
      style.display === 'none' ||
      style.visibility === 'hidden' ||
      parseFloat(style.opacity || '1') === 0
    ) {
      return false;
    }

    const rect = el.getBoundingClientRect();
    return rect.width > 0 || rect.height > 0;
  }

  function isDisabled(el) {
    return !!(
      el.disabled ||
      el.getAttribute('disabled') !== null ||
      el.getAttribute('aria-disabled') === 'true'
    );
  }

  function isProbablyInteractive(el) {
    if (!el) return false;

    const tag = getTag(el);
    const role = (el.getAttribute('role') || '').toLowerCase();
    const cls = getClassName(el);
    const tabindex = el.getAttribute('tabindex');

    return !!(
      ['input', 'button', 'select', 'textarea', 'a', 'img'].includes(tag) ||
      [
        'ion-input', 'ion-button', 'ion-select', 'ion-textarea',
        'ion-checkbox', 'ion-radio', 'ion-toggle', 'ion-fab-button',
        'ion-searchbar'
      ].includes(tag) ||
      ['button', 'link', 'textbox', 'checkbox', 'radio', 'switch', 'img'].includes(role) ||
      tabindex !== null ||
      el.onclick ||
      el.getAttribute('onclick') ||
      /button|btn|click|input|field|toggle|select|radio|checkbox|login|submit|image|icon|logo/i.test(cls)
    );
  }

  function collectAllElements(root, out = []) {
    if (!root) return out;

    let children = [];
    if (root instanceof Document || root instanceof ShadowRoot || root instanceof Element) {
      children = root.children ? Array.from(root.children) : [];
    }

    for (const el of children) {
      out.push(el);

      if (el.shadowRoot) {
        collectAllElements(el.shadowRoot, out);
      }

      collectAllElements(el, out);
    }

    return out;
  }

  function getAttributes(el) {
    const attrs = {};
    if (!el || !el.attributes) return attrs;
    for (const attr of Array.from(el.attributes)) {
      attrs[attr.name] = attr.value;
    }
    return attrs;
  }

  function getDomPath(el) {
    if (!el || el.nodeType !== 1) return '';
    const parts = [];
    let current = el;

    while (current && current.nodeType === 1) {
      const tag = getTag(current);
      let index = 1;
      let sibling = current.previousElementSibling;

      while (sibling) {
        if (getTag(sibling) === tag) index++;
        sibling = sibling.previousElementSibling;
      }

      parts.unshift(`${tag}[${index}]`);
      current = current.parentElement;
    }

    return '/' + parts.join('/');
  }

  function makeCssSelector(el) {
    if (!el || !el.tagName) return '';
    const tag = getTag(el);
    const id = el.id ? `#${CSS.escape(el.id)}` : '';

    if (id) return `${tag}${id}`;

    const name = el.getAttribute('name');
    if (name) return `${tag}[name="${name.replace(/"/g, '\\"')}"]`;

    const type = el.getAttribute('type');
    const placeholder = el.getAttribute('placeholder');
    const aria = el.getAttribute('aria-label');
    const alt = el.getAttribute('alt');
    const src = el.getAttribute('src');

    if (type) return `${tag}[type="${type.replace(/"/g, '\\"')}"]`;
    if (placeholder) return `${tag}[placeholder="${placeholder.replace(/"/g, '\\"')}"]`;
    if (aria) return `${tag}[aria-label="${aria.replace(/"/g, '\\"')}"]`;
    if (alt) return `${tag}[alt="${alt.replace(/"/g, '\\"')}"]`;
    if (src) return `${tag}[src="${src.replace(/"/g, '\\"')}"]`;

    return tag;
  }

  function makeXpath(el, text) {
    const tag = getTag(el);
    const id = el.id || '';
    const name = el.getAttribute('name') || '';
    const placeholder = el.getAttribute('placeholder') || '';
    const aria = el.getAttribute('aria-label') || '';
    const alt = el.getAttribute('alt') || '';
    const src = el.getAttribute('src') || '';

    if (id) return `//*[@id="${id}"]`;
    if (name) return `//${tag}[@name="${name}"]`;
    if (placeholder) return `//${tag}[@placeholder="${placeholder}"]`;
    if (aria) return `//${tag}[@aria-label="${aria}"]`;
    if (alt) return `//${tag}[@alt="${alt}"]`;
    if (src) return `//${tag}[@src="${src}"]`;
    if (text && text.length <= 50) return `//${tag}[contains(normalize-space(.), "${text}")]`;

    return '';
  }

  function getElementName(el, index, text) {
    const tag = getTag(el);
    const attrs = getAttributes(el);

    const raw =
      el.id ||
      attrs.name ||
      attrs['aria-label'] ||
      attrs.placeholder ||
      attrs.alt ||
      attrs.title ||
      attrs['data-testid'] ||
      text ||
      `${tag}_${index + 1}`;

    return safeText(raw).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  function hasMeaningfulText(text) {
    if (!text) return false;
    if (text.length < 2) return false;
    if (text.length > 80) return false;
    return true;
  }

  function isRelevantImage(el, attrs, text, interactive) {
    const tag = getTag(el);
    if (tag !== 'img') return false;

    const alt = attrs.alt || '';
    const src = attrs.src || '';
    const title = attrs.title || '';
    const aria = attrs['aria-label'] || '';

    return !!(
      interactive ||
      alt ||
      aria ||
      title ||
      src
    );
  }

  const layoutTags = new Set([
    'html', 'body', 'div', 'span',
    'ion-grid', 'ion-row', 'ion-col',
    'ion-content', 'ion-router-outlet',
    'ion-header', 'ion-toolbar', 'ion-title',
    'ion-buttons', 'ion-list', 'ion-item-group'
  ]);

  const controlTags = new Set([
    'input', 'button', 'select', 'textarea', 'a',
    'ion-input', 'ion-button', 'ion-select', 'ion-textarea',
    'ion-checkbox', 'ion-radio', 'ion-toggle',
    'ion-fab-button', 'ion-searchbar'
  ]);

  const textTags = new Set([
    'label', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ion-text'
  ]);

  const all = collectAllElements(document, []);
  const results = [];
  const seenKeys = new Set();

  for (let i = 0; i < all.length; i++) {
    const el = all[i];
    if (!el) continue;
    if (!isVisible(el)) continue;

    const tag = getTag(el);
    const attrs = getAttributes(el);
    const text = getText(el);
    const ownText = getOwnText(el);
    const role = (attrs.role || '').toLowerCase();
    const interactive = isProbablyInteractive(el);

    const keepAsControl =
      controlTags.has(tag) || interactive;

    const keepAsText =
      textTags.has(tag) && hasMeaningfulText(text);

    const keepSpecialNativeInput =
      tag === 'input' &&
      ['text', 'password', 'email', 'number', 'search', 'tel', 'url', ''].includes((attrs.type || '').toLowerCase());

    const keepAsImage =
      isRelevantImage(el, attrs, text, interactive);

    const rejectLayoutOnly =
      layoutTags.has(tag) && !interactive;

    const rejectEmpty =
      !text &&
      !ownText &&
      !attrs.placeholder &&
      !attrs['aria-label'] &&
      !attrs.name &&
      !attrs.id &&
      !attrs.alt &&
      !attrs.src;

    const rejectDisabledDecorative =
      isDisabled(el) && !keepAsText && !keepAsImage;

    if (rejectLayoutOnly) continue;
    if (rejectEmpty && !keepAsControl && !keepAsText && !keepSpecialNativeInput && !keepAsImage) continue;
    if (rejectDisabledDecorative) continue;

    if (!(keepAsControl || keepAsText || keepSpecialNativeInput || keepAsImage)) continue;

    const elementName = getElementName(el, i, ownText || text);
    const domPath = getDomPath(el);
    const cssSelector = makeCssSelector(el);
    const xpath = makeXpath(el, ownText || text);

    const dedupeKey = [
      tag,
      attrs.id || '',
      attrs.name || '',
      attrs.placeholder || '',
      attrs['aria-label'] || '',
      attrs.alt || '',
      attrs.src || '',
      ownText || text || '',
      domPath
    ].join('|');

    if (seenKeys.has(dedupeKey)) continue;
    seenKeys.add(dedupeKey);

    results.push({
      elementName: elementName,
      tag: tag,
      text: text,
      ownText: ownText,
      id: attrs.id || '',
      class: getClassName(el),
      name: attrs.name || '',
      type: attrs.type || '',
      role: role,
      placeholder: attrs.placeholder || '',
      title: attrs.title || '',
      alt: attrs.alt || '',
      src: attrs.src || '',
      ariaLabel: attrs['aria-label'] || '',
      dataTestId: attrs['data-testid'] || '',
      disabled: isDisabled(el),
      interactive: interactive || controlTags.has(tag),
      cssSelector: cssSelector,
      xpath: xpath,
      domPath: domPath,
      attributes: attrs
    });
  }

  return {
    title: document.title,
    url: window.location.href,
    totalFound: results.length,
    elements: results
  };
})();
"""


def wait_for_page_ready(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def extract_locators(url, output_file="locators.json"):
    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    try:
        print(f"Opening URL: {url}")
        driver.get(url)

        wait_for_page_ready(driver)
        time.sleep(8)

        result = driver.execute_script(JS_EXTRACT_RELEVANT)

        print(f"Page title: {result['title']}")
        print(f"Current URL: {result['url']}")
        print(f"Total extracted: {result['totalFound']}")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result["elements"], f, indent=2, ensure_ascii=False)

        print(f"Saved {len(result['elements'])} locators to {output_file}")

        for idx, item in enumerate(result["elements"][:20], start=1):
            print(
                f"{idx}. tag={item['tag']}, "
                f"name={item['elementName']}, "
                f"text={item['text'][:50]}, "
                f"alt={item.get('alt', '')[:50]}, "
                f"src={item.get('src', '')[:80]}, "
                f"interactive={item['interactive']}"
            )

        return result["elements"]

    finally:
        driver.quit()


if __name__ == "__main__":
    test_url = "http://172.21.166.115/washtabui/login?data=undefined"
    extract_locators(test_url)