# AI Automation Framework Architecture

## 1. Executive Summary

This repository implements an AI-assisted, human-in-the-loop automation generation MVP for web UI workflows.

Its purpose is to transform workflow input and live page inspection into reusable, reviewable automation artifacts and executable Robot Framework scripts.

Instead of generating final automation directly from a text prompt, the framework follows a staged pipeline where each stage produces an artifact that can be reviewed and refined before being reused downstream.

---

## 2. Architecture Goal

The goal of the framework is to convert workflow intent and live application understanding into reviewed automation assets and final Robot Framework suites.

It is intentionally designed as a layered, review-driven pipeline rather than a single-step generator.

### Non-negotiable architecture rule

The framework must not encode workflow-specific generation behavior through Python-side mappings, hardcoded page logic, keyword substitution tables, or resource-specific repair branches.

Instead, the framework must:
- infer reusable upstream/downstream relationships from approved workflow/business context
- retrieve approved resource knowledge from prior stages and prior workflows
- persist that knowledge as downstream-consumable artifacts or context objects
- require AI generation to stay inside that approved knowledge boundary
- validate that downstream suites reuse approved resource variables, locators, keywords, validations, and navigation knowledge before inventing anything new

This means navigation journeys, page transitions, setup paths, and downstream assertions must be generated from approved workflow context plus retrieved approved resource knowledge, not from hardcoded workflow handlers.

### Workflow knowledge as cumulative approved memory

A workflow knowledge artifact must be created and maintained for each workflow at:
- `artifacts/workflow_knowledge/<workflow>.json`

This artifact is the approved cumulative memory of a workflow. It must accumulate concise, downstream-usable knowledge from:
- approved workflow input / user story
- approved element extraction
- approved manual tests
- approved resource keywords and variables
- approved automation suites

The artifact must be concise and normalized rather than a raw dump. It should capture the highest-value reusable facts for downstream generation:
- business goal and application context
- approved navigation journey and state transitions
- approved resource ownership, variables, and keywords
- approved elements and control expectations
- approved scenario coverage and validation expectations
- upstream workflow knowledge references needed by downstream workflows

Each time a stage is approved, the workflow knowledge artifact should be refreshed so future workflows can consume the latest approved application intelligence before generating new code.

The purpose of workflow knowledge is not archival storage. Its purpose is to provide compact, authoritative application and workflow intelligence for downstream generation.

A downstream workflow such as `login` must consult relevant upstream workflow knowledge such as `home` before generating new manual tests, resources, or Robot suites. This keeps AI grounded in:
- application context
- approved navigation journeys
- approved ownership boundaries
- approved reusable keywords and variables
- approved state transitions and validations

The framework should therefore prefer this order for generation context:
1. current approved workflow input
2. relevant approved workflow knowledge artifacts
3. approved resource context retrieved from those artifacts
4. current-stage approved artifacts
5. AI inference inside that approved boundary

---

## 3. Architectural Style

Each stage in the framework:
- accepts structured inputs
- performs deterministic logic and/or AI-assisted generation
- produces a file-based artifact
- allows human review before the next major stage

Core characteristics:
- staged asset generation
- live page grounding where possible
- AI-assisted generation where useful
- manual approval between critical transitions
- POM/resource-oriented reuse

---

## 4. High-Level Flow

```text
Workflow Input
    ↓
Page Inspection and Extraction
    ↓
Elements Draft
    ↓
Human Review
    ↓
Manual Test Generation
    ↓
Human Review
    ↓
Keyword / Resource Generation and Review
    ↓
Human Review
    ↓
Robot Framework Generation
    ↓
Human Review
    ↓
Final Saved Automation
```

This reflects the current UI and script flow in the repository more accurately than a full execution platform view.

---

## 5. Main Components

## 5.1 UI and Orchestration Layer

### Main component
- `app/main.py`

### Responsibilities
- provide the FastAPI UI
- render workflow, page review, keyword review, manual test, and automation screens
- read and write workflow and generated artifacts
- trigger extraction and AI-assisted generation steps
- persist review decisions back to repository files
- validate generated resources against approved reviewed artifacts before downstream use
- enrich reviewed manual artifacts with generic interaction-intent metadata used as AI guidance in later stages

### Templates
- `app/templates/base.html`
- `app/templates/index.html`
- `app/templates/workflow_form.html`
- `app/templates/page_review.html`
- `app/templates/keyword_review.html`
- `app/templates/manual_tests.html`
- `app/templates/automation.html`

---

## 5.2 Workflow Input Layer

### Main artifacts
- `workflow_inputs/*.json`
- `config/page_model_config.json`

### Responsibilities
- define workflow name and module/feature context
- define page URL and resource relationships
- capture preconditions, steps, expected result, validations, and test data
- store generation and AI configuration
- provide sufficient story context for SPA-dependent workflows where direct page URL may be absent and navigation must be inferred from workflow narrative plus approved upstream resources

The current sample workflow is `workflow_inputs/login.json`.

---

## 5.3 Page Inspection and Extraction Layer

### Main component
- `scripts/extract_page_model.py`

### Responsibilities
- open the configured target page using Playwright
- inspect the DOM
- identify relevant interactive elements
- infer labels, roles, and locator candidates
- generate evidence artifacts such as screenshots and debug HTML
- create a page resource draft
- support SPA-dependent extraction by inferring entry URLs, upstream reusable resources, and pre-extraction navigation steps from workflow story context
- persist navigation debug artifacts and richer timeout diagnostics when story-driven navigation or target-state recognition fails

### Typical outputs
- `pom_pages/<page>/<page>.elements.json`
- `pom_pages/<page>/<page>.resource`
- `pom_pages/<page>/<page>.png`
- `pom_pages/<page>/<page>.debug.html`

These directories are typically generated at runtime and may not exist in a fresh checkout.

---

## 5.4 Keyword and Resource Review Layer

### Main implementation
- review routes and persistence logic in `app/main.py`

### Responsibilities
- load extracted element artifacts
- allow a human to approve or correct names and locators
- derive keyword drafts from approved elements
- save reviewed keyword/resource content for downstream reuse

This review stage is an important part of the current framework and should be considered a first-class step in the architecture.

---

## 5.5 Manual Test Generation Layer

### Main component
- `scripts/generate_manual_tests_json.py`

### Responsibilities
- read workflow input JSON
- build an AI prompt for manual test generation
- call the configured AI endpoint
- normalize and standardize returned content
- persist manual test artifacts for review
- preserve reviewer-approved scenario coverage while enriching manual artifacts with downstream-friendly semantics such as stronger expected outcomes and interaction-intent cues

### Typical output
- `manual_tests/<workflow>.json`

---

## 5.6 Automation Generation Layer

### Main component
- `scripts/generate_robot_from_manual.py`

### Responsibilities
- load approved manual tests
- load and parse approved resource files
- extract available resource keywords
- build a constrained AI prompt using resource and manual test context
- generate a Robot Framework suite
- validate structure and imports before save
- preserve approved artifact lineage so downstream suite generation stays aligned with approved names and semantics
- guide the AI to preserve manual interaction intent without introducing Python-side scenario routing tables
- validate resource-keyword invocation quality, including mandatory argument/signature compliance
- warn when suites drift away from shared/common abstractions, canonical reusable variables, or evidence-backed assertion expectations

### Typical output
- `tests/<workflow>_tests.robot`

---

## 6. End-to-End Runtime Flow

1. A workflow is created or edited through the UI.
2. Workflow data is stored under `workflow_inputs/`.
3. A target page is extracted using `scripts/extract_page_model.py`.
4. Extracted elements are reviewed and saved.
5. Manual test generation is triggered using workflow input plus approved page elements.
6. Manual tests are reviewed and approved.
7. Keyword/resource generation is triggered using approved elements and approved manual tests.
8. Keyword/resource content is reviewed and saved.
9. Robot suite generation is triggered.
10. Generated automation is reviewed and saved.

This sequence reflects the current repository behavior more accurately than documents that assume all runtime artifact folders already exist in the repo.

---

## 7. Repository Structure and Purpose

```text
app/
  main.py                  FastAPI application and orchestration
  templates/               MVP UI templates

config/
  page_model_config.json   Framework and generation configuration

docs/
  ARCHITECTURE.md          Architecture overview
  CAPABILITY_MATRIX.md     Capability and status matrix
  ROADMAP.md               Future roadmap

resources/
  common_keywords.resource Shared Robot keywords

scripts/
  extract_page_model.py           Page extraction and resource generation
  generate_manual_tests_json.py   Manual test generation
  generate_robot_from_manual.py   Robot suite generation

workflow_inputs/
  *.json                  Workflow definition inputs
```

Runtime-generated folders commonly include:
- `pom_pages/`
- `manual_tests/`
- `tests/`

---

## 8. AI Integration Design

AI is used as a controlled generation mechanism rather than an unrestricted code author.

Current AI-assisted areas:
- manual test generation and review/refinement
- page resource refinement
- Robot Framework suite generation and review/refinement

Design pattern:
1. create structured input payload
2. include approved-artifact lineage and prior reviewed context where relevant
3. build a constrained prompt
4. call the configured AI endpoint
5. normalize returned output
6. validate structure, framework rules, resource alignment, and signature correctness
7. surface warnings for weak assertions or drift from reusable abstractions
8. save artifact for human review

---

## 9. Human Governance Model

Human review is a core architectural principle.

Review checkpoints in the current implementation include:
- page element and locator review
- keyword/resource review
- manual test review
- final automation review

This prevents low-quality outputs from flowing downstream without intervention.

---

## 10. Current Strengths

- strong staged architecture
- real UI grounding through page inspection
- reusable resource/POM layer
- AI-assisted manual and automation generation
- clear human-in-the-loop review model
- working MVP UI for orchestration

---

## 11. Current Limitations

- current demonstration is centered mostly on a login flow
- many generated artifact folders are runtime outputs, not checked-in content
- AI outputs still require human validation and refinement
- broader multi-page orchestration remains limited
- validation and governance logic can be strengthened

---

## 12. Summary

This framework is best described as a review-driven AI automation generation pipeline for Robot Framework, orchestrated through FastAPI, grounded with Playwright-based page inspection, and persisted through file-based artifacts.
