# Smart Agent Assignment Strategy

> Intelligence layer for matching the right agent to each task in Dev Loop

---

## Overview

Smart Agent Assignment analyzes tasks across **5 dimensions** to recommend the optimal agent:

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AGENT ASSIGNMENT DIMENSIONS                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   1. TASK TYPE        What kind of work? (code, test, review, docs, KB)         │
│   2. TECHNOLOGY       What stack? (Python, Spark, AWS, GCP, Terraform)          │
│   3. COMPLEXITY       How hard? (simple, moderate, complex, architectural)      │
│   4. PHASE            When in workflow? (risky, core, polish)                   │
│   5. CONTEXT          What's around it? (new file, existing code, integration)  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Registry

### Tier 1: Universal Agents (Always Available)

| Agent | Primary Domain | Trigger Keywords | Strengths |
|-------|---------------|------------------|-----------|
| `@python-developer` | Python code | python, class, function, module, dataclass, pydantic | Clean patterns, type hints, generators |
| `@test-generator` | Testing | test, pytest, unittest, coverage, fixture, mock | pytest expertise, edge cases, fixtures |
| `@code-reviewer` | Quality | review, quality, security, refactor, improve | OWASP, best practices, code smells |
| `@code-cleaner` | Refactoring | clean, refactor, DRY, simplify, remove | Removes duplication, modernizes |
| `@code-documenter` | Documentation | document, docstring, README, API docs | Clear documentation |
| `@kb-architect` | Knowledge Base | KB, knowledge base, domain, concept, pattern | KB structure, MCP validation |
| `@codebase-explorer` | Analysis | explore, understand, analyze, find, search | Codebase navigation |
| `@adaptive-explainer` | Communication | explain, teach, clarify, stakeholder | Adapts to audience |
| `@the-planner` | Planning | plan, strategy, roadmap, architecture | Strategic thinking |
| `@meeting-analyst` | Extraction | meeting, notes, decisions, requirements | Structured extraction |

### Tier 2: Specialized Agents (Domain-Specific)

| Agent | Primary Domain | Trigger Keywords | When to Use |
|-------|---------------|------------------|-------------|
| `@spark-specialist` | Apache Spark | spark, pyspark, dataframe, RDD, partition | Spark optimization |
| `@spark-troubleshooter` | Spark Debugging | spark error, OOM, shuffle, skew | Spark issues |
| `@lakeflow-architect` | Databricks DLT | lakeflow, DLT, medallion, bronze, silver, gold | Pipeline design |
| `@lambda-builder` | AWS Lambda | lambda, serverless, S3 trigger, SAM | Lambda functions |
| `@aws-lambda-architect` | AWS SAM/IAM | SAM template, IAM policy, least privilege | Lambda architecture |
| `@ci-cd-specialist` | DevOps | pipeline, CI/CD, terraform, deploy, Azure DevOps | Automation |
| `@infra-deployer` | Infrastructure | terraform, terragrunt, GCP, infrastructure | IaC deployment |
| `@llm-specialist` | Prompts | prompt, LLM, extraction, structured output | Prompt engineering |
| `@genai-architect` | AI Systems | agent, multi-agent, orchestration, chatbot | AI architecture |
| `@extraction-specialist` | Document AI | extract, invoice, document, Gemini, vision | Document extraction |

---

## Assignment Algorithm

### Step 1: Parse Task

```text
Input: "Create a Redis cache wrapper with connection pooling"

Extracted:
  - Action: Create
  - Subject: Redis cache wrapper
  - Details: connection pooling
  - Type: Code (new file)
```

### Step 2: Identify Signals

| Signal Type | Examples | Weight |
|-------------|----------|--------|
| **Explicit Technology** | "Python", "Spark", "Lambda" | High |
| **Implicit Technology** | "dataframe" → Spark, "pytest" → Testing | Medium |
| **Action Verbs** | "test" → test-generator, "review" → code-reviewer | High |
| **File Patterns** | `test_*.py` → test-generator, `*.tf` → ci-cd-specialist | High |
| **Keywords** | "clean", "refactor", "document" | Medium |

### Step 3: Match Against Registry

```text
Task: "Create a Redis cache wrapper with connection pooling"

Signal Analysis:
  ✓ "Create" + "wrapper" → Code creation
  ✓ "Redis" → Infrastructure/Python
  ✓ "connection pooling" → Python patterns
  ✗ No test keywords
  ✗ No Spark keywords
  
Best Match: @python-developer (score: 0.92)
Reason: Python code creation with design patterns
```

### Step 4: Consider Phase

| Phase | Agent Preference | Reasoning |
|-------|------------------|-----------|
| 🔴 RISKY | `@the-planner`, `@codebase-explorer` | Need analysis before commitment |
| 🟡 CORE | Domain specialists | Main implementation work |
| 🟢 POLISH | `@code-reviewer`, `@code-cleaner`, `@code-documenter` | Quality and cleanup |

---

## Assignment Matrix

### By Task Type

| Task Type | Primary Agent | Secondary Agent | Fallback |
|-----------|--------------|-----------------|----------|
| **New Python code** | `@python-developer` | - | - |
| **New tests** | `@test-generator` | `@python-developer` | - |
| **Code review** | `@code-reviewer` | `@dual-reviewer` | - |
| **Refactoring** | `@code-cleaner` | `@python-developer` | - |
| **Documentation** | `@code-documenter` | - | - |
| **KB creation** | `@kb-architect` | - | - |
| **Codebase analysis** | `@codebase-explorer` | - | - |
| **Architecture design** | `@the-planner` | `@genai-architect` | - |
| **Prompt engineering** | `@llm-specialist` | `@extraction-specialist` | - |
| **Infrastructure** | `@ci-cd-specialist` | `@infra-deployer` | - |
| **Spark code** | `@spark-specialist` | `@python-developer` | - |
| **Lambda functions** | `@lambda-builder` | `@python-developer` | - |

### By Technology Stack

| Technology | Primary Agent | Notes |
|------------|--------------|-------|
| **Python (general)** | `@python-developer` | Default for .py files |
| **Python (Pydantic)** | `@python-developer` | Knows Pydantic patterns |
| **Python (pytest)** | `@test-generator` | Test specialist |
| **Apache Spark** | `@spark-specialist` | PySpark, optimization |
| **Databricks/DLT** | `@lakeflow-architect` | Medallion architecture |
| **AWS Lambda** | `@lambda-builder` | Serverless Python |
| **AWS SAM/IAM** | `@aws-lambda-architect` | Templates, policies |
| **Terraform** | `@ci-cd-specialist` | IaC |
| **GCP** | `@infra-deployer` | Cloud Run, Pub/Sub |
| **LLM/AI** | `@llm-specialist` | Prompts, extraction |
| **Multi-agent** | `@genai-architect` | Orchestration |

### By Complexity

| Complexity | Approach | Agent Strategy |
|------------|----------|----------------|
| **Simple** | Single agent | Best match only |
| **Moderate** | Primary + verification | Primary agent + `@code-reviewer` at end |
| **Complex** | Specialist + support | Domain specialist + `@python-developer` support |
| **Architectural** | Planning first | `@the-planner` → then specialists |

---

## Keyword Detection Rules

### Code Creation Keywords
```
create, implement, build, add, write, develop, make
→ Match to domain specialist based on technology
```

### Testing Keywords
```
test, pytest, unittest, coverage, fixture, mock, assert, TDD
→ @test-generator
```

### Review Keywords
```
review, check, audit, security, quality, OWASP, vulnerability
→ @code-reviewer
```

### Cleanup Keywords
```
clean, refactor, DRY, simplify, remove, deduplicate, modernize
→ @code-cleaner
```

### Documentation Keywords
```
document, docstring, README, API docs, comments, explain code
→ @code-documenter
```

### KB Keywords
```
KB, knowledge base, domain, concept, pattern, quick reference
→ @kb-architect
```

### Analysis Keywords
```
explore, understand, analyze, find, search, investigate, where is
→ @codebase-explorer
```

### Planning Keywords
```
plan, design, architect, strategy, roadmap, how should, approach
→ @the-planner
```

### Infrastructure Keywords
```
terraform, deploy, CI/CD, pipeline, infrastructure, IaC, cloud
→ @ci-cd-specialist or @infra-deployer
```

### Spark Keywords
```
spark, pyspark, dataframe, RDD, partition, broadcast, shuffle
→ @spark-specialist
```

### LLM Keywords
```
prompt, LLM, GPT, Claude, Gemini, extraction, structured output
→ @llm-specialist
```

---

## Multi-Agent Patterns

### Pattern 1: Build → Test → Review
```markdown
### 🟡 CORE
- [ ] @python-developer: Implement the feature
- [ ] @test-generator: Create unit tests
- [ ] @code-reviewer: Review implementation
```

### Pattern 2: Explore → Plan → Build
```markdown
### 🔴 RISKY
- [ ] @codebase-explorer: Analyze existing patterns
- [ ] @the-planner: Design integration approach

### 🟡 CORE
- [ ] @python-developer: Implement based on plan
```

### Pattern 3: Specialist → Support → Quality
```markdown
### 🟡 CORE
- [ ] @spark-specialist: Implement Spark transformation
- [ ] @python-developer: Add helper utilities
- [ ] @test-generator: Create Spark tests

### 🟢 POLISH
- [ ] @code-reviewer: Review for performance
```

### Pattern 4: AI Pipeline
```markdown
### 🔴 RISKY
- [ ] @llm-specialist: Design extraction prompt

### 🟡 CORE
- [ ] @python-developer: Implement extraction wrapper
- [ ] @extraction-specialist: Optimize prompt accuracy
- [ ] @test-generator: Create evaluation tests
```

---

## Assignment Examples

### Example 1: API Feature

**Task**: "Add pagination to the /api/products endpoint"

```text
Analysis:
  - Type: Code modification
  - Tech: Python (API)
  - Complexity: Moderate
  - Phase: CORE

Assignment:
  🟡 @python-developer: Add pagination parameters and logic
  🟡 @test-generator: Create pagination tests
  🟢 @code-reviewer: Review for edge cases
```

### Example 2: Performance Issue

**Task**: "Optimize slow Spark job that processes user events"

```text
Analysis:
  - Type: Optimization
  - Tech: Spark
  - Complexity: Complex
  - Phase: RISKY → CORE

Assignment:
  🔴 @spark-troubleshooter: Diagnose bottleneck
  🟡 @spark-specialist: Implement optimization
  🟡 @spark-performance-analyzer: Validate improvement
```

### Example 3: New KB Domain

**Task**: "Create a Redis KB with caching patterns"

```text
Analysis:
  - Type: KB creation
  - Tech: Redis
  - Complexity: Moderate
  - Phase: CORE

Assignment:
  🟡 @kb-architect: Create domain structure
  🟡 @kb-architect: Write concepts
  🟡 @kb-architect: Document patterns
  🟢 @code-reviewer: Review for completeness
```

### Example 4: Infrastructure Setup

**Task**: "Set up Terraform modules for GCS buckets"

```text
Analysis:
  - Type: Infrastructure
  - Tech: Terraform, GCP
  - Complexity: Moderate
  - Phase: CORE

Assignment:
  🔴 @the-planner: Design module structure
  🟡 @ci-cd-specialist: Implement Terraform modules
  🟡 @infra-deployer: Configure Terragrunt
  🟢 @code-reviewer: Review for security
```

---

## Confidence Scoring

Each assignment includes a confidence score:

| Score | Meaning | Action |
|-------|---------|--------|
| 0.9+ | High confidence | Auto-assign |
| 0.7-0.9 | Good match | Assign with note |
| 0.5-0.7 | Uncertain | Present options to user |
| <0.5 | Low confidence | Ask user to clarify |

### Score Calculation

```text
base_score = keyword_match_score (0-0.4)
           + technology_match_score (0-0.3)
           + task_type_match_score (0-0.2)
           + phase_appropriateness (0-0.1)

Example:
  Task: "Create pytest fixtures for the cache module"
  
  keyword_match: "pytest", "fixtures" → @test-generator (0.4)
  technology: Python testing (0.3)
  task_type: Test creation (0.2)
  phase: CORE appropriate (0.1)
  
  Total: 1.0 → High confidence @test-generator
```

---

## Fallback Rules

1. **No clear match** → `@python-developer` (most versatile)
2. **Architecture unclear** → `@the-planner` first
3. **Unknown technology** → `@codebase-explorer` to investigate
4. **Quality gate** → Always end with `@code-reviewer` for production tier

---

## Integration with Prompt Crafter

The Enhanced Prompt Crafter uses this strategy in Phase 2 (DESIGN):

```text
DESIGN PHASE
============
Based on your requirements, here's the agent assignment:

🤖 Agent Assignments:

| Task | Agent | Confidence | Reasoning |
|------|-------|------------|-----------|
| Implement Redis client | @python-developer | 0.95 | Python code with patterns |
| Create cache decorator | @python-developer | 0.92 | Python decorator expertise |
| Add unit tests | @test-generator | 0.98 | pytest specialist |
| Review for security | @code-reviewer | 0.90 | Quality gate |

💡 Assignment Strategy:
   • Primary: @python-developer for all implementation
   • Testing: @test-generator for comprehensive coverage
   • Quality: @code-reviewer as final gate

Approve agent assignments? [Yes / Modify]
```

---

*Agent Assignment Strategy v1.0 — Intelligence for task-agent matching*
