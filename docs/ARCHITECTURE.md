# AI Automation Framework Architecture

## 1. Executive Summary

This repository implements an AI-assisted, human-in-the-loop automation generation MVP for web UI workflows.

Its purpose is to transform workflow input and live page inspection into reusable, reviewable automation artifacts and executable Robot Framework scripts.

Instead of generating final automation directly from a text prompt, the framework follows a staged pipeline where each stage produces an artifact that can be reviewed and refined before being reused downstream.

---

## 2. Architecture Goal

The goal of the framework is to convert workflow intent and live application understanding into reviewed automation assets and final Robot Framework suites.

It is intentionally designed as a layered, review-driven pipeline rather than a single-step generator.

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
- manual test generation
- Robot Framework suite generation

Design pattern:
1. create structured input payload
2. build a constrained prompt
3. call the configured AI endpoint
4. normalize returned output
5. validate structure and framework rules
6. save artifact for human review

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
