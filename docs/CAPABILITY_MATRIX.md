# Capability and Status Matrix

This document summarizes the framework capability set based on the current repository implementation.

## Capability Matrix

| Capability Area | Description | Current Status | Notes |
|---|---|---|---|
| Workflow definition | Define workflow input artifacts | Implemented | Workflow JSON is stored under `workflow_inputs/` and managed through the UI |
| Workflow editing UI | Create or update workflow definitions | Implemented | Available in FastAPI UI |
| Page inspection | Open and inspect configured target pages | Implemented | Driven through `scripts/extract_page_model.py` |
| DOM understanding | Extract relevant page controls and metadata | Implemented | Heuristic and DOM-driven extraction |
| Locator generation | Create locator variables for page resources | Implemented | Generated as part of page resource creation |
| Resource/POM generation | Create reusable Robot Framework resource files | Implemented | Includes locators and page keywords |
| Page review UI | Review extracted page elements and locators | Implemented | Supported in the UI |
| Keyword review UI | Review generated keyword/resource content | Implemented | Supported in the UI |
| Approved-artifact alignment validation | Keep generated resources aligned with approved reviewed artifacts | Implemented | Generic validation exists in the orchestration layer before downstream reuse |
| Manual test generation | Generate manual test scenarios from workflow inputs | Implemented | AI-assisted |
| Manual intent enrichment | Preserve interaction nuance in reviewed manual artifacts | Implemented | Generic interaction-intent metadata is added as AI guidance, not as hardcoded scenario routing |
| Manual test review | Review and refine generated manual tests | Implemented | Supported in the UI |
| Automation generation | Generate Robot Framework suites from manual tests | Implemented | AI-assisted, lineage-aware, and resource-aware |
| Resource grounding | Use available resource files during automation generation | Implemented | Present in current Robot generation design |
| Automation review UI | Review generated automation before save | Implemented | Available in the UI |
| Robot keyword/signature validation | Check generated keyword usage against imported resource signatures | Implemented | Includes mandatory argument compliance and unsupported-keyword detection |
| Assertion guidance and warnings | Push suites toward evidence-backed observable checks | Implemented | Warnings and refinement guidance are present for weak or action-only outcomes |
| Local execution support | Execute generated Robot suites locally | Partial | Depends on generated tests and local environment; execution UI is not a core feature |
| Execution result artifacts | Produce Robot logs and reports | Partial | Possible via standard Robot commands, but execution outputs are not represented in the checked-in repo |
| Validation of generated Robot output | Enforce generated suite quality | Implemented | Structural, resource-alignment, signature, naming, setup/teardown, and reusable-data warnings are present, though still evolving |
| Structured test data strategy | Centralize reusable test data cleanly | Partial | Some workflow test data exists, but no strong abstraction layer yet |
| Approval workflow metadata | Track review, approval, version, and ownership | Partial | Basic status exists, governance metadata is limited |
| Multi-page workflow orchestration | Support larger cross-page journeys | Partial | Current MVP is strongest on focused flows |
| Execution feedback loop | Feed failures back into refinement | Limited | Not yet a structured closed loop |
| Self-healing | Detect and repair broken automation intelligently | Not Yet Implemented | Future direction |
| Knowledge retention layer | Persist and reuse learned patterns across runs | Not Yet Implemented | Future direction |
| Enterprise governance | Audit, versioning, role alignment, and controlled promotion | Early Stage | Requires substantial future expansion |

---

## Maturity Summary

| Area | Maturity Assessment |
|---|---|
| Overall architecture | Strong |
| UI orchestration | Good MVP |
| Page extraction | Practical MVP |
| Resource generation | Good foundation |
| Manual test generation | Implemented and useful |
| Robot generation | Implemented and useful, but still improving |
| Validation and governance | Improving MVP |
| Execution intelligence | Early |
| Healing and learning | Planned |
| Production readiness | Early-stage MVP |

---

## Summary Interpretation

The framework already demonstrates a full staged pipeline from workflow definition to generated Robot Framework output.

Its strongest current value lies in:
- staged artifact generation
- human-in-the-loop review
- reusable resource/POM creation
- acceleration of manual and automated test design

Its biggest current growth opportunities are:
- broader multi-page orchestration depth
- richer framework intelligence in review/refinement layers
- stronger reusable test-data strategy
- execution-aware improvement
- future healing and knowledge reuse
