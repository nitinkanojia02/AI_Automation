# Roadmap

This roadmap describes valuable next steps for evolving the current MVP into a more reliable and governed AI-assisted automation tool.

## Roadmap Objective

Improve the framework across five dimensions:
- automation quality
- determinism and governance
- resource and data intelligence
- execution reliability
- platform maturity and scalability

---

## Near-Term Priorities

### 1. Consolidate recent quality improvements
Focus areas:
- keep approved-artifact alignment validation generic and reusable
- continue strengthening Robot keyword/signature validation and unsupported-keyword detection
- improve warning clarity and error handling around generation stages
- verify documentation and UI messaging stay aligned with implemented validation behavior

### 2. Strengthen Robot generation quality further
Focus areas:
- improve repair/regeneration loops when validation fails
- deepen evidence-backed assertion guidance for negative and state-validation scenarios
- keep generated suites thin and resource-first
- reduce low-level interaction leakage when approved page/common abstractions exist

### 3. Deepen resource/POM intelligence
Focus areas:
- better parsing of resource files
- clearer classification of open, action, and validation keywords
- richer page object generation patterns
- stronger reuse of existing keywords during automation generation

### 4. Introduce a stronger test data strategy
Focus areas:
- central reusable test data definitions
- reduced hardcoded values in generated automation
- improved separation of data from test logic
- clearer handling of canonical semantic variables for reusable negative and role-based data

### 5. Improve governance and artifact review
Focus areas:
- approval state tracking
- workflow and artifact status visibility
- clearer review feedback in the UI
- version-aware artifact handling
- better surfacing of lineage and warning metadata across stages

---

## Mid-Term Priorities

### 6. Improve page understanding robustness
Focus areas:
- better DOM heuristics
- stronger locator quality rules
- support for more complex page structures
- improved duplicate handling and semantic naming

### 7. Expand workflow coverage
Focus areas:
- support more than login-style workflows
- handle multi-page business journeys
- improve cross-page artifact relationships
- support broader enterprise application modules

### 8. Improve execution visibility
Focus areas:
- clearer execution guidance in the UI
- better error surfacing
- stronger linkage between generated automation and execution outcomes
- history and trend visibility over time

---

## Long-Term Priorities

### 9. Introduce execution-aware refinement
Focus areas:
- use execution failures to suggest automation updates
- detect likely locator breakage
- connect failed steps back to resources and approved artifacts
- improve regeneration based on runtime feedback

### 10. Add self-healing capabilities
Focus areas:
- locator repair assistance
- regeneration of impacted page resources
- controlled revalidation of updated automation
- safe review-first healing behavior

### 11. Add knowledge storage and reuse
Focus areas:
- persist reusable learned patterns
- retain stable keyword and locator recommendations
- support cross-workflow reuse
- evolve toward a reusable automation knowledge layer

### 12. Evolve into a broader platform experience
Focus areas:
- richer dashboard and stage visibility
- multi-user collaboration support
- stronger governance and auditability
- improved enterprise-shareable user experience

---

## Recommended Immediate Sequence

1. keep documentation, prompts, and validation behavior aligned
2. continue strengthening `scripts/generate_robot_from_manual.py`
3. improve resource parsing and semantic understanding
4. introduce a formal reusable test-data layer
5. strengthen validation and regeneration loops
6. improve workflow and artifact status visibility in the UI
7. expand support beyond the current curated `login` and `home` demo workflow shapes

---

## Expected Outcome

By following this roadmap, the framework can evolve from a strong MVP and engineering accelerator into a more dependable, reusable, and organization-shareable AI-assisted automation platform.
