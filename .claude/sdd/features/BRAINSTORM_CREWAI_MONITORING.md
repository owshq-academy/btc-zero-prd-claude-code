# BRAINSTORM: CrewAI Autonomous Monitoring

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | CREWAI_MONITORING |
| **Date** | 2026-01-31 |
| **Author** | brainstorm-agent |
| **Status** | Ready for Define |

---

## Initial Idea

**Raw Input:** Architect and implement the entire CrewAI autonomous monitoring solution for the invoice processing pipeline.

**Context Gathered:**
- Comprehensive requirements already exist in `design/data-ops-crew-ai-requirements.md`
- Three-agent architecture defined: Triage → Root Cause → Reporter
- Timeline: Pilot complete by April 30, 2026
- CrewAI KB exists at `.claude/kb/crewai/` with patterns and concepts
- Sample error logs already exist in `dataops/samples/`

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `dataops/` (new top-level directory) | Clean separation from pipeline code |
| Relevant KB Domains | crewai, pydantic, gcp, openrouter | Patterns for agents, validation, tools |
| IaC Patterns | Terraform modules exist in `infra/` | Can extend for CrewAI Cloud Run later |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | What to brainstorm? | Full CrewAI implementation | Comprehensive architecture needed |
| 2 | Code location? | New `dataops/` directory | Clean separation, independent deployment |
| 3 | Trigger mechanism? | Manual only (for pilot) | Simplifies Phase 1, add scheduling later |
| 4 | Sample data available? | Yes, 3 error samples in `dataops/samples/` | Can ground Triage Agent with real patterns |
| 5 | LLM provider? | OpenRouter | Avoids Gemini quota conflicts |
| 6 | Testing strategy? | Manual testing only | Fast iteration for pilot validation |

---

## Sample Data Inventory

> Samples improve LLM accuracy through in-context learning and few-shot prompting.

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Error logs | `dataops/samples/` | 3 | Real extraction failures |
| Input files | N/A | 0 | Not needed for log analysis |
| Ground truth | `dataops/samples/*.error.json` | 3 | Verified error patterns |
| Related code | `functions/gcp/v1/src/` | 5 | Existing Cloud Run functions |

**Sample Error Patterns Identified:**

| Sample | Error Type | HTTP Code | Classification |
|--------|-----------|-----------|----------------|
| `fail_empty.tiff.error.json` | Quota exceeded | 429 | WARNING (recoverable) |
| `fail_html.tiff.error.json` | Quota exceeded | 429 | WARNING (recoverable) |
| `fail_random_small.tiff.error.json` | Invalid image | 400 | ERROR (non-recoverable) |

**How samples will be used:**
- Few-shot examples in Triage Agent prompts
- Test fixtures for manual validation
- Pattern recognition training for error classification

---

## Approaches Explored

### Approach A: Monolithic Crew (Single Deployment) ⭐ Recommended

**Description:** All three agents run in a single process, orchestrated by CrewAI's sequential process. One entry point, one deployment unit.

```text
dataops/
├── src/monitoring/
│   ├── cli.py           # Entry point
│   ├── crew.py          # Crew definition
│   ├── config/          # Decoupled configuration
│   ├── agents/          # Triage, Root Cause, Reporter
│   ├── tools/           # GCS reader
│   └── schemas/         # Pydantic models
├── config/              # Environment configs
├── samples/             # Error samples (exists)
└── pyproject.toml
```

**Pros:**
- Simplest architecture - one deployment unit
- Native CrewAI orchestration handles agent handoffs
- Shared memory between agents within execution
- Easy to debug - single log stream
- Matches requirements doc architecture

**Cons:**
- All agents share same resource limits
- Can't scale agents independently

**Why Recommended:** For a pilot with manual triggers, simplicity wins. CrewAI is designed to orchestrate agents in a single process.

---

### Approach B: Microservice Agents (Separate Deployments)

**Description:** Each agent is its own Cloud Run service, communicating via Pub/Sub messages.

**Pros:**
- Independent scaling per agent
- Isolated failures

**Cons:**
- Loses CrewAI orchestration benefits
- Complex Pub/Sub wiring between agents
- Harder to debug (distributed tracing needed)
- More infrastructure to manage
- Overkill for pilot

**Why Not Recommended:** Defeats the purpose of CrewAI. The framework's value is in-process agent collaboration.

---

### Approach C: Hybrid (Crew + Separate Reporter)

**Description:** Triage and Root Cause run together, Reporter is separate for Slack isolation.

**Pros:**
- Isolates Slack integration
- Can rate-limit alerts independently

**Cons:**
- Added complexity for marginal benefit
- Still need Pub/Sub between crew and reporter
- Overkill for pilot phase

**Why Not Recommended:** Circuit breaker in Approach A handles rate limiting. Unnecessary complexity.

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A: Monolithic Crew |
| **User Confirmation** | 2026-01-31 |
| **Reasoning** | Simplicity for pilot, native CrewAI orchestration, easy debugging |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | New `dataops/` directory | Clean separation from pipeline | Inside `functions/` or `src/` |
| 2 | Manual trigger only | Simplest for pilot validation | Cloud Scheduler, GCS events |
| 3 | OpenRouter as LLM | Avoids Gemini quota conflicts | Gemini 2.0 Flash |
| 4 | Decoupled config via Pydantic Settings | Type-safe, env var support | Hardcoded values |
| 5 | Default bucket: `eda-gemini-dev-invoices-failed` | Where pipeline writes failures | Generic bucket name |
| 6 | Sequential process | Simpler than hierarchical | Hierarchical with manager |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| Slack sender tool | Not needed for pilot validation | Yes (Phase 2) |
| Cloud Scheduler | Manual trigger sufficient | Yes (Phase 2) |
| Cloud Monitoring metrics | Log analysis only for MVP | Yes (Phase 2) |
| LangFuse tracing | Add after pilot validates accuracy | Yes (Phase 2) |
| Long-term memory (SQLite) | Not needed for manual runs | Yes (Phase 2) |
| Auto-retry logic | Phase 1 is monitoring-only | Yes (Phase 2) |
| Multiple Slack channels | Single channel sufficient | Yes (Phase 2) |
| Hierarchical process | Sequential is simpler | Maybe |
| GCS audit log | Log to stdout instead | Yes (Phase 2) |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Project structure | ✅ | Add config decoupling | Yes |
| GCS bucket location | ✅ | Default = `eda-gemini-dev-invoices-failed` | Yes |
| MVP scope | ✅ | Remove Slack sender | Yes |
| Approach selection | ✅ | Confirmed Approach A | No |

---

## Suggested Requirements for /define

Based on this brainstorm session, the following should be captured in the DEFINE phase:

### Problem Statement (Draft)

Build a CrewAI-based autonomous monitoring system that reads pipeline error logs from GCS, classifies issues by severity, performs root cause analysis, and outputs structured reports for manual review.

### Target Users (Draft)

| User | Pain Point |
|------|------------|
| DataOps Engineer | Manual log monitoring is time-consuming |
| On-call Engineer | Need quick root cause identification |
| Team Lead | Need visibility into pipeline health |

### Success Criteria (Draft)

- [ ] Triage Agent correctly classifies 3 sample errors by severity
- [ ] Root Cause Agent provides plausible analysis for each error
- [ ] Reporter Agent outputs valid JSON report to stdout
- [ ] Full crew executes via CLI in < 60 seconds
- [ ] Configuration is decoupled (no hardcoded values)

### Constraints Identified

- Manual trigger only (no scheduling for pilot)
- No Slack integration (stdout only)
- No Cloud Monitoring metrics (logs only)
- OpenRouter as sole LLM provider
- Short-term memory only (no persistence between runs)

### Out of Scope (Confirmed)

- Slack notifications (Phase 2)
- Cloud Scheduler automation (Phase 2)
- LangFuse observability (Phase 2)
- Auto-remediation (Phase 2)
- Cloud Monitoring metrics (Phase 2)
- Long-term memory (Phase 2)

---

## Architecture Summary

### MVP Crew Flow

```text
┌─────────────────────────────────────────────────────────────────┐
│                        MVP CREW FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CLI Trigger (python -m monitoring.cli)                        │
│       │                                                          │
│       ▼                                                          │
│   ┌─────────┐     ┌─────────────┐     ┌──────────┐              │
│   │ TRIAGE  │────▶│ ROOT CAUSE  │────▶│ REPORTER │──▶ stdout    │
│   │  Agent  │     │    Agent    │     │  Agent   │   (JSON)     │
│   └─────────┘     └─────────────┘     └──────────┘              │
│       │                 │                                        │
│       ▼                 ▼                                        │
│   GCS Reader       OpenRouter                                    │
│   (bucket)         (LLM calls)                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Project Structure

```text
dataops/
├── src/
│   └── monitoring/
│       ├── __init__.py
│       ├── cli.py               # Manual trigger entry point
│       ├── crew.py              # Crew definition
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py      # Pydantic Settings
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── triage.py
│       │   ├── root_cause.py
│       │   └── reporter.py
│       ├── tools/
│       │   ├── __init__.py
│       │   └── gcs_reader.py
│       └── schemas/
│           ├── __init__.py
│           └── models.py
├── config/
│   ├── dev.env
│   └── prod.env
├── samples/                     # Already exists
│   ├── fail_empty.tiff.error.json
│   ├── fail_html.tiff.error.json
│   └── fail_random_small.tiff.error.json
├── tests/
├── pyproject.toml
└── README.md
```

### Configuration

```python
# Environment variables (DATAOPS_ prefix)
DATAOPS_GCS_BUCKET=eda-gemini-dev-invoices-failed
DATAOPS_OPENROUTER_API_KEY=sk-or-...
DATAOPS_OPENROUTER_MODEL=anthropic/claude-3-haiku
DATAOPS_MAX_ITERATIONS=10
DATAOPS_VERBOSE=true
```

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 6 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 9 |
| Validations Completed | 4 |
| Duration | ~15 minutes |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_CREWAI_MONITORING.md`

---

## References

| Document | Location | Purpose |
|----------|----------|---------|
| Requirements | `design/data-ops-crew-ai-requirements.md` | Full requirements spec |
| CrewAI KB | `.claude/kb/crewai/` | Implementation patterns |
| Sample Data | `dataops/samples/` | Error log samples |
| OpenRouter KB | `.claude/kb/openrouter/` | LLM integration patterns |
