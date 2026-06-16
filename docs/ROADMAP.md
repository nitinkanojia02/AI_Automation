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

### 1. Fix current correctness issues
Focus areas:
- align workflow status handling in the UI
- fix Robot validation return-value handling
- normalize workflow/manual test field usage
- improve error handling around generation stages

### 2. Strengthen Robot generation quality
Focus areas:
- stronger validation of generated Robot suites
- prevention of framework violations in generated output
- improved prompt constraints for resource-first generation
- automatic repair or regeneration when validation fails

### 3. Deepen resource/POM intelligence
Focus areas:
- better parsing of resource files
- classification of open, action, and validation keywords
- richer page object generation patterns
- stronger reuse of existing keywords during automation generation

### 4. Introduce a stronger test data strategy
Focus areas:
- central reusable test data definitions
- reduced hardcoded values in generated automation
- improved separation of data from test logic

### 5. Improve governance and artifact review
Focus areas:
- approval state tracking
- workflow and artifact status visibility
- clearer review feedback in the UI
- version-aware artifact handling

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
- connect failed steps back to resources and test assets
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

1. fix current correctness bugs
2. strengthen `scripts/generate_robot_from_manual.py`
3. improve resource parsing and semantic understanding
4. introduce a formal test data layer
5. strengthen validation and regeneration loops
6. improve workflow and artifact status visibility in the UI
7. expand support beyond the current demo workflow shape

---

## Expected Outcome

By following this roadmap, the framework can evolve from a strong MVP and engineering accelerator into a more dependable, reusable, and organization-shareable AI-assisted automation platform.
