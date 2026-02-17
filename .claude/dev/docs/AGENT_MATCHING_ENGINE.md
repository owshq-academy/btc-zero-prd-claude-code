# Agent Matching Engine

> The intelligence core of AgentLoop — context-aware agent assignment that goes beyond keywords

---

## Why This Exists

Keyword matching is fragile. The word "retry" means different things in different contexts:

```text
"Add retry to the Lambda"        → @lambda-builder
"Add retry to the Spark job"     → @spark-specialist
"Add retry to the Terraform"     → @infra-deployer
"Add retry to the extractor"     → @function-developer (domain-specific)
```

The Matching Engine understands **context**, not just **words**.

---

## The 5-Step Algorithm

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        AGENT MATCHING ENGINE                                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────┐ │
│   │ FINGER-   │───▶│ DECOMPOSE │───▶│   SCORE   │───▶│   CHAIN   │───▶│VERIFY │ │
│   │  PRINT    │    │           │    │           │    │           │    │       │ │
│   └───────────┘    └───────────┘    └───────────┘    └───────────┘    └───────┘ │
│                                                                                  │
│   "Know the       "Break the       "Rank every      "Build the       "Sanity   │
│    project"        task apart"      agent"           sequence"        check"    │
│                                                                                  │
│   Run ONCE         Per task         Per agent         Per assignment   Always    │
│   per project      description      per operation     graph           last      │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: FINGERPRINT — Know the Project

Scan the project once to build a **Project DNA** profile. This profile persists across tasks within the same session.

### What to Scan

| Source | Signals Extracted |
|--------|-------------------|
| `pyproject.toml` / `package.json` | Languages, frameworks, dependencies |
| Directory structure | Patterns (monorepo, serverless, microservices) |
| `*.tf` / `*.hcl` files | Infrastructure stack |
| `CLAUDE.md` | Explicit project context, tech stack, conventions |
| Existing agents usage | Which agents have been effective before |

### Output: Project DNA

```yaml
# Auto-generated Project DNA
project_dna:
  languages:
    - python: 3.11
  frameworks:
    - cloud-run-functions
    - pytest
    - pydantic-v2
  cloud:
    provider: gcp
    services: [cloud-run, bigquery, gcs, pubsub, secret-manager]
  patterns:
    - adapter-pattern
    - event-driven
    - serverless
    - pub-sub-messaging
  domains:
    - invoice-processing
    - document-extraction
    - data-engineering
  llm:
    primary: gemini-2.0-flash
    fallback: openrouter
    observability: langfuse
  infra:
    iac: terraform
    orchestrator: terragrunt
    environments: [dev, prod]
```

### Why This Matters

Without fingerprinting, a task like "add error handling" could match any agent. With fingerprinting:

```text
Project DNA says: GCP + Cloud Run Functions + Python + Pydantic
Task: "add error handling"

Without fingerprint: @python-developer (generic, score 0.6)
With fingerprint:    @function-developer (domain match, score 0.88)
```

---

## Step 2: DECOMPOSE — Break the Task Apart

Parse every task into **atomic operations** using structured extraction.

### Task DNA Structure

```text
Input: "Add retry logic with exponential backoff to the data extractor function"

Task DNA:
┌────────────────────────────────────────────────┐
│  Intent:      ENHANCE (modify existing code)   │
│  Subject:     data-extractor function           │
│  Operations:                                    │
│    1. {verb: add, noun: retry-logic}           │
│    2. {verb: implement, noun: backoff-pattern} │
│    3. {verb: modify, noun: existing-function}  │
│  Tech Signals: [python, cloud-run, resilience] │
│  Domain Signals: [data-extractor, pipeline]    │
│  Complexity: MODERATE                           │
│  Implied Tasks:                                 │
│    - Tests for retry behavior                   │
│    - Config for retry parameters                │
└────────────────────────────────────────────────┘
```

### Intent Classification

| Intent | Signals | Typical Flow |
|--------|---------|--------------|
| **CREATE** | new, create, build, add (new file) | Design → Build → Test |
| **ENHANCE** | add (to existing), extend, improve | Explore → Build → Test |
| **FIX** | fix, bug, broken, error, failing | Explore → Fix → Verify |
| **OPTIMIZE** | optimize, slow, performance, speed | Profile → Optimize → Benchmark |
| **REFACTOR** | refactor, clean, simplify, DRY | Explore → Refactor → Verify |
| **EXPLORE** | understand, analyze, find, what is | Explore → Report |
| **DOCUMENT** | document, README, API docs | Read → Document |
| **TEST** | test, coverage, fixture, TDD | Read → Test → Verify |
| **DEPLOY** | deploy, release, promote, ship | Plan → Deploy → Verify |
| **CONFIGURE** | setup, configure, install, environment | Plan → Configure → Verify |

### Implied Task Detection

The engine automatically detects tasks the user didn't explicitly ask for but are necessary:

```text
Explicit:  "Create a new Cloud Run function for PDF processing"
Implied:
  → Need to follow adapter pattern (from Project DNA)
  → Need Pydantic schema for messages (from Project DNA)
  → Need unit tests (from quality tier)
  → Need to update Pub/Sub topic config (from event-driven pattern)
```

---

## Step 3: SCORE — Rank Every Agent

For each atomic operation, score every eligible agent across **4 weighted dimensions**.

### Scoring Formula

```text
FINAL_SCORE = (TECH × 0.35) + (TASK × 0.30) + (DOMAIN × 0.25) + (PHASE × 0.10)
```

### Dimension Breakdown

#### Technology Fit (35% weight)

How well does the agent know the tech stack involved?

```text
Scoring:
  1.0  — Agent's primary technology (e.g., @spark-specialist + PySpark)
  0.8  — Agent's secondary technology (e.g., @python-developer + pytest)
  0.5  — Agent can handle it but it's not core (e.g., @python-developer + SQL)
  0.2  — Tangentially related (e.g., @code-reviewer + Terraform)
  0.0  — No technology overlap
```

#### Task Fit (30% weight)

Does this operation match the agent's core strength?

```text
Scoring:
  1.0  — Exact match (e.g., @test-generator + "write tests")
  0.8  — Strong match (e.g., @python-developer + "create class")
  0.5  — Partial match (e.g., @code-reviewer + "implement feature")
  0.2  — Weak match (e.g., @kb-architect + "write code")
  0.0  — No task overlap
```

#### Domain Fit (25% weight)

Is this agent experienced in the project's domain?

```text
Scoring:
  1.0  — Domain specialist (e.g., @function-developer in this pipeline project)
  0.8  — Domain-adjacent (e.g., @extraction-specialist for invoice work)
  0.5  — Generic but capable (e.g., @python-developer for any Python)
  0.2  — Unrelated domain (e.g., @spark-specialist in a web app project)
  0.0  — Cannot operate in this domain
```

#### Phase Fit (10% weight)

Is this the right agent for the current execution phase?

```text
Scoring:
  1.0  — Natural phase agent (e.g., @code-reviewer in POLISH phase)
  0.7  — Acceptable in this phase (e.g., @python-developer in CORE)
  0.3  — Misplaced (e.g., @code-reviewer in RISKY phase)
  0.0  — Wrong phase entirely
```

### Scoring Example

```text
Task: "Add retry logic to the data extractor function"
Project: GCP + Cloud Run + Python + Invoice Pipeline

Agent: @function-developer
  TECH:   0.9 × 0.35 = 0.315  (Cloud Run functions = primary tech)
  TASK:   0.8 × 0.30 = 0.240  (enhancing functions = core strength)
  DOMAIN: 1.0 × 0.25 = 0.250  (invoice pipeline = exact domain)
  PHASE:  0.7 × 0.10 = 0.070  (CORE phase = good fit)
  TOTAL:  0.875 ✅ High confidence

Agent: @python-developer
  TECH:   0.8 × 0.35 = 0.280  (Python = primary, but not GCP-specific)
  TASK:   0.8 × 0.30 = 0.240  (code creation = core strength)
  DOMAIN: 0.5 × 0.25 = 0.125  (generic, not domain-specific)
  PHASE:  0.7 × 0.10 = 0.070  (CORE phase = good fit)
  TOTAL:  0.715 ⚠️ Good match but not best

Agent: @spark-specialist
  TECH:   0.0 × 0.35 = 0.000  (no Spark in this project)
  TASK:   0.3 × 0.30 = 0.090  (can write code, not core strength)
  DOMAIN: 0.0 × 0.25 = 0.000  (wrong domain entirely)
  PHASE:  0.5 × 0.10 = 0.050  (neutral)
  TOTAL:  0.140 ❌ Not a match

WINNER: @function-developer (0.875)
```

---

## Step 4: CHAIN — Build the Execution Graph

Don't just pick agents — **sequence them** as a directed graph with dependencies.

### Chain Types

#### Sequential Chain

Operations that must run in order:

```text
[codebase-explorer] ──▶ [function-developer] ──▶ [test-generator]
   "understand"            "implement"              "verify"
```

#### Parallel Chain

Independent operations that can run simultaneously:

```text
                    ┌──▶ [test-generator]     "unit tests"
[python-developer] ─┤
                    └──▶ [code-documenter]    "docstrings"
```

#### Gate Chain

Agent that blocks progression until quality is met:

```text
[function-developer] ──▶ [test-generator] ──▶ ║ @code-reviewer ║
   "implement"             "test"               ║  QUALITY GATE  ║
                                                ║  must pass     ║
```

### Chain Construction Rules

1. **EXPLORE before BUILD** — Always understand existing code first
2. **BUILD before TEST** — Can't test what doesn't exist
3. **TEST before REVIEW** — Reviewer assumes tests pass
4. **Domain specialist as PRIMARY** — Generic agents are SUPPORT
5. **Quality gate as FINAL** — @code-reviewer is always last for production tier
6. **Max 4 agents per chain** — More than 4 suggests task needs decomposition

### Chain Templates

| Task Intent | Chain Template |
|-------------|----------------|
| **CREATE** | `explore → [specialist] → test → review` |
| **ENHANCE** | `explore → [specialist] → test → review` |
| **FIX** | `explore → [specialist/troubleshooter] → test` |
| **OPTIMIZE** | `[analyzer] → [specialist] → test → review` |
| **REFACTOR** | `explore → [cleaner] → test → review` |
| **TEST** | `explore → [test-generator] → review` |
| **DOCUMENT** | `explore → [documenter]` |
| **DEPLOY** | `[planner] → [deployer] → verify` |

---

## Step 5: VERIFY — Sanity Check Everything

Before finalizing, validate the full assignment:

### Validation Rules

| Rule | Check | Action if Failed |
|------|-------|------------------|
| **Confidence Floor** | Primary agent score ≥ 0.70 | Ask user to clarify task |
| **Single Primary** | Exactly 1 primary agent per operation | Pick highest scorer |
| **No Overload** | No agent assigned > 4 tasks | Split tasks or add support |
| **Phase Coherence** | RISKY tasks before CORE tasks | Reorder task list |
| **Quality Gate** | Production tier must end with reviewer | Append @code-reviewer |
| **Domain Alignment** | Primary agent's domain matches project | Flag mismatch to user |
| **No Duplicates** | Same agent not assigned redundant tasks | Merge tasks |

### Confidence Actions

| Score Range | Label | Action |
|-------------|-------|--------|
| **0.85 – 1.00** | Definitive | Auto-assign, no confirmation needed |
| **0.70 – 0.84** | Confident | Assign with brief reasoning shown |
| **0.50 – 0.69** | Uncertain | Present top 2 options to user |
| **Below 0.50** | Low | Ask user to clarify or choose manually |

---

## Agent Registry

### Tier 1: Universal Agents

Always available regardless of project type.

| Agent | Core Strength | Tech Affinity | Domain Affinity |
|-------|---------------|---------------|-----------------|
| `@python-developer` | Python code, patterns, types | Python, Pydantic, dataclasses | Any Python project |
| `@test-generator` | Tests, fixtures, edge cases | pytest, unittest, mock | Any testable code |
| `@code-reviewer` | Quality, security, patterns | All languages | Any codebase |
| `@code-cleaner` | Refactoring, DRY, modernization | Python | Any Python project |
| `@code-documenter` | Docs, README, API docs | Markdown, docstrings | Any project |
| `@kb-architect` | Knowledge base creation | MCP, YAML, Markdown | Any KB domain |
| `@codebase-explorer` | Code analysis, navigation | All | Any codebase |
| `@adaptive-explainer` | Communication, teaching | All | Any audience |
| `@the-planner` | Strategy, architecture | All | Complex decisions |
| `@meeting-analyst` | Extraction, decisions | Natural language | Meeting/comms |

### Tier 2: Domain Specialists

Activated when Project DNA matches their specialty.

| Agent | Activation Signal | Primary Tech | Best For |
|-------|-------------------|--------------|----------|
| `@function-developer` | Cloud Run, GCP serverless | Python, GCP | Pipeline functions |
| `@extraction-specialist` | LLM extraction, Gemini | Gemini, Pydantic | Document AI |
| `@infra-deployer` | Terraform, Terragrunt, IaC | HCL, GCP | Infrastructure |
| `@pipeline-architect` | Event-driven, Pub/Sub | GCP, serverless | Architecture |
| `@dataops-builder` | CrewAI, monitoring, agents | Python, CrewAI | Autonomous ops |
| `@spark-specialist` | PySpark, Spark optimization | Spark, Python | Spark jobs |
| `@spark-troubleshooter` | Spark errors, OOM, skew | Spark | Spark debugging |
| `@lakeflow-architect` | DLT, medallion, Databricks | Spark, SQL | Data pipelines |
| `@lambda-builder` | AWS Lambda, SAM, serverless | Python, AWS | Lambda functions |
| `@aws-lambda-architect` | SAM templates, IAM, policies | CloudFormation | AWS architecture |
| `@ci-cd-specialist` | Pipelines, DevOps, deploy | YAML, Terraform | CI/CD |
| `@llm-specialist` | Prompts, structured output | LLM APIs | Prompt engineering |
| `@genai-architect` | Multi-agent, orchestration | CrewAI, LangChain | AI systems |

### Tier 2 Activation Logic

```text
IF project_dna.cloud.provider == "gcp":
  ACTIVATE: @function-developer, @infra-deployer, @pipeline-architect

IF project_dna.llm is not empty:
  ACTIVATE: @extraction-specialist, @llm-specialist

IF "spark" in project_dna.frameworks:
  ACTIVATE: @spark-specialist, @spark-troubleshooter

IF "terraform" in project_dna.infra.iac:
  ACTIVATE: @infra-deployer, @ci-cd-specialist

IF "crewai" in project_dna.frameworks:
  ACTIVATE: @dataops-builder, @genai-architect
```

---

## Multi-Agent Orchestration Patterns

### Pattern 1: Standard Build

For most feature development.

```text
@codebase-explorer ──▶ @{domain-specialist} ──▶ @test-generator ──▶ @code-reviewer
   Understand             Implement                Test                 Review
   (RISKY)                (CORE)                   (CORE)               (POLISH)
```

### Pattern 2: AI/LLM Pipeline

For extraction or prompt work.

```text
@llm-specialist ──▶ @extraction-specialist ──▶ @python-developer ──▶ @test-generator
   Design prompt     Optimize accuracy          Integrate              Evaluate
   (RISKY)           (CORE)                     (CORE)                 (CORE)
```

### Pattern 3: Infrastructure

For IaC and deployment work.

```text
@the-planner ──▶ @infra-deployer ──▶ @ci-cd-specialist ──▶ @code-reviewer
   Architecture    Terraform           Pipeline config       Security review
   (RISKY)         (CORE)              (CORE)                (POLISH)
```

### Pattern 4: Diagnosis & Fix

For bugs and performance issues.

```text
@codebase-explorer ──▶ @{troubleshooter} ──▶ @{specialist} ──▶ @test-generator
   Investigate           Diagnose              Fix                Regression test
   (RISKY)               (RISKY)               (CORE)             (CORE)
```

### Pattern 5: Knowledge Base

For KB creation tasks.

```text
@codebase-explorer ──▶ @kb-architect ──▶ @code-reviewer
   Gather context        Build KB           Validate completeness
   (RISKY)               (CORE)             (POLISH)
```

---

## Integration with Prompt Crafter

The Matching Engine runs during **Phase 2: DESIGN** of the AgentLoop prompt crafter.

### Engine Output Format

```markdown
## Agent Assignment (Matching Engine v2.0)

**Project DNA:** Python 3.11 | GCP | Cloud Run | Pydantic | Gemini

### Execution Chain

| # | Phase | Agent | Task | Score | Role |
|---|-------|-------|------|-------|------|
| 1 | 🔴 RISKY | @codebase-explorer | Analyze existing retry patterns | 0.90 | Explore |
| 2 | 🟡 CORE | @function-developer | Implement retry with backoff | 0.88 | Primary |
| 3 | 🟡 CORE | @test-generator | Create retry test suite | 0.95 | Verify |
| 4 | 🟢 POLISH | @code-reviewer | Review for edge cases | 0.92 | Gate |

**Chain:** `explore → build → test → review` (Sequential)
**Confidence:** HIGH (avg 0.91)
**Domain Specialists Activated:** @function-developer, @extraction-specialist
```

---

## Worked Examples

### Example 1: Simple Feature

**Task:** "Add a health check endpoint to the API"

```text
Step 1 — FINGERPRINT: Python + GCP + Cloud Run (already cached)
Step 2 — DECOMPOSE:
  Intent: CREATE
  Operations: [{add, health-endpoint}, {add, response-model}]
  Implied: [tests, documentation]

Step 3 — SCORE:
  @function-developer: TECH 0.9 + TASK 0.8 + DOMAIN 1.0 + PHASE 0.7 = 0.875
  @python-developer:   TECH 0.8 + TASK 0.8 + DOMAIN 0.5 + PHASE 0.7 = 0.715

Step 4 — CHAIN:
  @function-developer → @test-generator → @code-reviewer
  (build)              (verify)           (gate)

Step 5 — VERIFY: ✅ Primary ≥ 0.70, single primary, quality gate present
```

### Example 2: Cross-Cutting Concern

**Task:** "Add structured logging to all Cloud Run functions"

```text
Step 1 — FINGERPRINT: 5 Cloud Run functions, shared/ directory exists
Step 2 — DECOMPOSE:
  Intent: ENHANCE (modify multiple existing files)
  Operations: [{create, logging-utility}, {modify, 5-functions}, {update, shared-utils}]
  Implied: [tests for logging, consistency check]
  Complexity: HIGH (touches 5+ files)

Step 3 — SCORE:
  @function-developer: TECH 0.9 + TASK 0.7 + DOMAIN 1.0 + PHASE 0.7 = 0.840
  @python-developer:   TECH 0.8 + TASK 0.8 + DOMAIN 0.5 + PHASE 0.7 = 0.715

Step 4 — CHAIN:
  @codebase-explorer → @function-developer → @test-generator → @code-reviewer
  (map all functions)   (implement logging)    (verify output)    (consistency)

Step 5 — VERIFY: ✅ All checks pass. Flag: "5+ files modified, recommend incremental approach"
```

### Example 3: Ambiguous Task

**Task:** "Make the pipeline faster"

```text
Step 1 — FINGERPRINT: Event-driven pipeline with 5 functions
Step 2 — DECOMPOSE:
  Intent: OPTIMIZE (ambiguous — which part?)
  Operations: [{profile, pipeline}, {identify, bottleneck}, {optimize, ???}]
  Complexity: UNKNOWN until explored

Step 3 — SCORE:
  Insufficient signal for confident match.
  Best guess: @codebase-explorer (0.65) for initial exploration

Step 4 — CHAIN:
  @codebase-explorer → [ASK USER] → @{specialist TBD}
  (investigate)         (clarify)     (optimize)

Step 5 — VERIFY: ⚠️ Confidence below 0.70 for primary task.
  ACTION: Ask user "Which part of the pipeline is slow? (TIFF conversion / classification / extraction / BigQuery write)"
```

---

## Continuous Improvement

The Matching Engine improves through the **REFLECT** phase:

### Feedback Signals

| Signal | Source | Improvement |
|--------|--------|-------------|
| Agent completed task successfully | PROGRESS file | Increase that agent's domain score |
| Agent was replaced mid-task | User intervention | Decrease confidence for that matching |
| Task required unexpected agent | REFLECT notes | Add new signal pattern |
| Assignment was perfect | User feedback | Reinforce the pattern |

### Memory Integration

After each session, REFLECT captures:

```markdown
## Agent Effectiveness
- @function-developer: Effective for retry logic (was scored 0.88, actual fit: excellent)
- @test-generator: Generated comprehensive tests, good assignment
- Lesson: For resilience patterns, @function-developer > @python-developer in this project
```

This feeds back into future fingerprinting and scoring.

---

*Agent Matching Engine v2.0 — Context-aware intelligence for AgentLoop*
