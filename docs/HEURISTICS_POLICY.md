# Heuristics Policy

## Goal
Keep framework behavior driven by:
- approved workflow inputs
- approved/reviewed page artifacts
- approved resource reuse
- prompt instructions
- generic structural validation

Avoid turning Python/scripts into a semantic patch layer that must be updated whenever story wording changes.

---

## 1. Acceptable heuristics

These are okay because they are **generic, structural, syntax-oriented, or lineage-oriented**, not business-word mapping.

### A. Structural completeness checks
Allowed:
- missing title
- missing steps
- missing expected result
- empty artifacts
- duplicate scenario signatures
- thin scenario count
- missing reviewed artifacts
- missing required files in a generation chain

Why okay:
- they do not infer business meaning from wording
- they only validate artifact completeness/shape

---

### B. Generic syntax / format parsing
Allowed:
- Robot keyword extraction
- variable extraction
- JSON field existence checks
- markdown section parsing
- line normalization
- duplicate string removal
- filename/path normalization

Why okay:
- format-level parsing is framework infrastructure, not business mapping

---

### C. Generic abstraction-quality checks
Allowed:
- detect low-value wrapper keywords when implementation is only one/two low-level steps
- flag direct locator-heavy tests when approved page keywords already exist
- flag repeated setup-like sequences across many tests
- flag literal duplication when approved variables already exist

Why okay:
- this evaluates reuse/abstraction quality generically
- it does not depend on page names or domain terms like login/home/logout

---

### D. Generic lineage/reuse checks
Allowed:
- detect when downstream artifacts ignore available approved resources
- detect when approved variables exist but tests hardcode values
- detect when reviewed artifacts and final resources diverge in naming
- detect when repeated steps could be absorbed into reusable setup/resource keywords

Why okay:
- these are contract/reuse checks, not workflow-behavior mapping

---

### E. Generic normalization
Allowed:
- deduplicate repeated lines
- trim broken formatting
- cap noisy lists by limit
- prefer concise normalized output over repeated prose
- preserve source text without semantic reinterpretation

Why okay:
- normalization improves artifact quality without inventing meaning

---

## 2. Should-never-add heuristics

These should be treated as anti-patterns unless there is an explicit, reviewed architecture decision.

### A. Token lists that infer business meaning
Do not add logic like:
- if text contains `"login"`, `"logout"`, `"dashboard"`, `"home"`
- if text contains `"authenticated"`
- if text contains `"mask"`, `"visible"`, `"enabled"`
- if text contains `"redirect"`, `"landing"`, `"error"`

Why not:
- every new wording variation causes more mapping work
- framework enters permanent update mode
- wording becomes more important than approved artifacts

---

### B. Page/workflow-specific behavior branching in Python
Do not add:
- if current page is login, then...
- if story mentions person/profile, then...
- if workflow is SPA, inject specific target signals...
- if home resource exists, create special navigation assumptions...

Why not:
- this hardcodes today’s app semantics into scripts
- reuse should come from approved resources/workflow knowledge, not custom page rules

---

### C. Data-value mapping or semantic bucket classification
Do not add:
- classify expectations into `control_state`, `destination_state`, `field_property`, etc. using keywords
- infer success/failure behavior from word buckets
- infer observational behavior from word lists
- infer auth transitions from phrases

Why not:
- semantic bucketing always grows over time
- it is brittle and incomplete by design

---

### D. Hidden repair logic that manufactures missing behavior
Do not add code that:
- silently converts weak tests into stronger ones by guessing intent
- injects missing page transitions not present in approved lineage
- fills missing URLs/behaviors with assumed defaults
- creates synthetic ownership when page ownership is unclear

Why not:
- hides real artifact gaps
- makes the framework appear stable while accumulating invisible logic debt

---

### E. Hardcoded domain vocabularies as “generic” logic
Avoid pretending these are generic:
- authentication words
- navigation words
- button/control vocabularies
- app-specific section names
- page names

Why not:
- once added, they become maintenance commitments

---

## 3. Preferred design choices instead

When quality gaps are found, prefer these fixes in order.

### 1. Fix prompts first
Use prompts to instruct the model to:
- preserve observational/manual-open outcomes
- align reviewed naming with final resources
- reuse approved page/resource artifacts
- avoid inventing behavior
- normalize workflow knowledge more cleanly

Best first choice because:
- semantics belong at generation/review level

---

### 2. Strengthen approved artifacts
Improve:
- reviewed elements
- reviewed keywords
- workflow inputs
- manual expected results
- workflow knowledge summaries

Best when the issue is really missing approved evidence.

---

### 3. Add generic structural guardrails only
If Python must help, keep it generic:
- completeness
- duplication
- abstraction quality
- reuse availability
- naming divergence
- placeholder-value hygiene

---

### 4. Escalate unclear cases instead of guessing
If the framework cannot know behavior from approved artifacts:
- preserve observational wording
- emit a warning
- require review
- do not resolve by assumption

---

## 4. Simple decision test for future changes

Before adding any script logic, ask:

### Test 1
Would this rule still make sense if the app had different page names and different domain language?
- If no → don’t add it in Python

### Test 2
Is the rule checking structure/reuse/consistency rather than interpreting business meaning?
- If yes → probably acceptable

### Test 3
Will new wording variations force us to add more tokens later?
- If yes → don’t add it

### Test 4
Can this be handled by prompt guidance or approved artifacts instead?
- If yes → do that first

### Test 5
Does this rule invent missing behavior rather than exposing a gap?
- If yes → reject it

---

## 5. Short repo rule of thumb

### Good
- “This artifact is incomplete”
- “This resource ignores approved variables”
- “This suite repeats setup too much”
- “This reviewed/resource naming diverges”
- “This output is noisy/duplicated”

### Bad
- “This must be login behavior because the text says sign in”
- “This is authenticated success because it says dashboard”
- “This must be a field property check because it says masked”
- “This workflow should reuse home because the story mentions person/profile”

---

## 6. Core repo principle

Python may validate structure, reuse, lineage, and artifact quality.
Python must not interpret business behavior through token mapping.
Business semantics should come from approved artifacts and prompt-guided generation, not script-side hardcoding.
