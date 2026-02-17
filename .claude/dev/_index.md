# AgentLoop v3.0

> **Agentic Development (Level 2)** — Explore first, define clearly, match intelligently, reflect always.
> SDD-lite workflow with the Agent Matching Engine for context-aware agent assignment.

---

## The 3-Level Development Spectrum

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DEVELOPMENT SPECTRUM                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   LEVEL 1                  LEVEL 2 (AgentLoop)        LEVEL 3 (AgentSpec)      │
│   Vibe Coding              Agentic Development         Spec-Driven Dev (SDD)   │
│   ───────────              ────────────────────        ─────────────────────    │
│                                                                                  │
│   • Just prompts           • SDD-lite workflow         • 5-phase pipeline       │
│   • No structure           • EXPLORE → DEFINE →        • Full traceability      │
│   • Hope it works            DESIGN → EXECUTE          • Quality gates          │
│   • Quick fixes            • Agent Matching Engine     • Enterprise audit       │
│                            • Requirements capture      • ADRs and specs         │
│                            • REFLECT on completion                              │
│                                                                                  │
│   Command: (none)          Command: /dev               Command: /brainstorm+    │
│   Time: < 30 min           Time: 1-4 hours             Time: Multi-day          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## How It Works (v3.0)

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AGENTLOOP FLOW (v3.0)                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   /dev "description"                      /dev tasks/PROMPT_*.md                │
│         │                                        │                               │
│         ▼                                        ▼                               │
│   ┌─────────────────────┐                ┌─────────────────┐                    │
│   │  PROMPT CRAFTER     │                │  AGENTLOOP      │                    │
│   │      (v3.0)         │                │  EXECUTOR       │                    │
│   │                     │                │                 │                    │
│   │  0. EXPLORE         │                │  1. Load        │                    │
│   │     (Brainstorm)    │ ── generates → │  2. Pick        │                    │
│   │  1. DEFINE          │    PROMPT.md   │     (🔴→🟡→🟢)  │                    │
│   │     (Requirements)  │    with spec   │  3. Execute     │                    │
│   │  2. DESIGN          │    + matching  │     (@agent)    │                    │
│   │     (Matching       │    engine      │  4. Verify      │                    │
│   │      Engine)        │                │  5. Update      │                    │
│   │  3. GENERATE        │                │  6. Loop        │                    │
│   │     (Smart PROMPT)  │                └────────┬────────┘                    │
│   └─────────────────────┘                         │                              │
│                                                   ▼                              │
│                                          ┌─────────────────┐                    │
│                                          │  EXIT_COMPLETE  │                    │
│                                          └────────┬────────┘                    │
│                                                   │                              │
│                                                   ▼                              │
│                                          ┌─────────────────┐                    │
│                                          │    REFLECT      │                    │
│                                          │ (Lessons Learned)│                    │
│                                          └─────────────────┘                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Option 1: Let the Crafter Guide You (Recommended)

```bash
/dev "I want to build a date parser utility"
```

The **Prompt Crafter (v3.0)** will:

1. **EXPLORE** — Search codebase, present 2-3 approaches with trade-offs
2. **DEFINE** — Capture requirements (FR-1, FR-2...), quality tier, out-of-scope
3. **DESIGN** — Fingerprint project, decompose task, score agents, build execution chain
4. **GENERATE** — Create PROMPT.md with embedded spec and @agent annotations
5. Hand off for execution

### Option 2: Execute an Existing PROMPT

```bash
/dev tasks/PROMPT_DATE_PARSER.md
```

### Option 3: Manual PROMPT Creation

```bash
# Copy template
cp .claude/dev/templates/PROMPT_TEMPLATE.md \
   .claude/dev/tasks/PROMPT_MY_TASK.md

# Edit, then execute
/dev tasks/PROMPT_MY_TASK.md
```

---

## Folder Structure

```text
.claude/dev/
├── _index.md                        # This documentation
├── readme.md                        # Feature overview
│
├── docs/                            # Supporting documentation
│   └── AGENT_MATCHING_ENGINE.md     # Matching Engine algorithm
│
├── tasks/                           # Your PROMPT files (active work)
│   └── PROMPT_*.md
│
├── progress/                        # Memory bridge (auto-managed)
│   └── PROGRESS_*.md
│
├── logs/                            # Execution logs
│   └── LOG_*.md
│
├── templates/                       # Templates
│   ├── PROMPT_TEMPLATE.md           # Blank template
│   ├── PROGRESS_TEMPLATE.md         # Progress file template
│   ├── PROMPT_EXAMPLE_FEATURE.md    # Example: Python utility
│   └── PROMPT_EXAMPLE_KB.md         # Example: KB domain
│
└── examples/                        # Real-world examples
    ├── README.md                    # Examples documentation
    ├── PROMPT_*.md                  # Example PROMPT files
    ├── PROGRESS_*.md                # Example PROGRESS files
    └── LOG_*.md                     # Example LOG files
```

---

## The Two Agents (v3.0)

### 1. Prompt Crafter (`prompt-crafter`)

**When:** You describe what you want in natural language
**What:** SDD-lite workflow with the Agent Matching Engine

```bash
/dev "Add Redis caching to the API"
```

**v3.0 Enhancements:**
- EXPLORE phase (brainstorm-lite) — surfaces options before commitment
- DEFINE phase (requirements-lite) — captures FR/NFR formally
- DESIGN phase (matching engine) — 5-step algorithm: FINGERPRINT → DECOMPOSE → SCORE → CHAIN → VERIFY
- 4-dimension agent scoring: Technology (35%) + Task (30%) + Domain (25%) + Phase (10%)
- Tier 2 specialist activation via Project DNA

### 2. AgentLoop Executor (`agentloop-executor`)

**When:** You have a PROMPT.md ready to execute
**What:** Runs tasks with @agent invocation, verification, and REFLECT phase

```bash
/dev tasks/PROMPT_REDIS_CACHE.md
```

**v3.0 Enhancements:**
- Execution chain awareness (follows agent sequence from Matching Engine)
- Agent effectiveness tracking in LOG files
- REFLECT phase captures Matching Engine feedback
- Enhanced agent roster (14 agents available for invocation)

---

## Key Concepts

### Agent Matching Engine

The core intelligence of AgentLoop. Instead of keyword matching, it uses a 5-step algorithm:

```text
FINGERPRINT → DECOMPOSE → SCORE → CHAIN → VERIFY
(project DNA)  (task DNA)  (4-dim)  (sequence)  (sanity)
```

**Scoring Formula:**
```text
FINAL_SCORE = (TECH × 0.35) + (TASK × 0.30) + (DOMAIN × 0.25) + (PHASE × 0.10)
```

See `.claude/dev/docs/AGENT_MATCHING_ENGINE.md` for full algorithm.

### Quality Tiers

| Tier | Behavior |
|------|----------|
| `prototype` | Speed over perfection. Minimal verification. |
| `production` | Tests required. Full verification. |
| `library` | Backward compatibility. Full docs. |

### Task Priority

| Priority | Symbol | Execute Order |
|----------|--------|---------------|
| RISKY | 🔴 | First — fail fast on hard problems |
| CORE | 🟡 | Second — main implementation |
| POLISH | 🟢 | Last — cleanup and optimization |

### Execution Modes

| Mode | Behavior | Best For |
|------|----------|----------|
| `hitl` | Human-in-the-loop. Pause for review. | Learning, risky tasks |
| `afk` | Autonomous. Commit per task. | Bulk work, low-risk tasks |

### Memory Bridge

Progress files persist state between iterations:
- Prevents token burn from re-exploration
- Records key decisions
- Tracks files changed
- Enables session recovery after interruption

---

## Session Recovery

### Why Recovery Matters

Long-running agentic sessions face several challenges:
- **Context rot** — Token limits cause information loss
- **Timeouts** — Network or system interruptions
- **Human interruption** — User needs to pause and resume later

The memory bridge solves these with automatic state persistence.

### How It Works

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SESSION RECOVERY FLOW                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Session 1 (Interrupted)              Session 2 (Resumed)                      │
│   ────────────────────────             ──────────────────────                   │
│                                                                                  │
│   /dev tasks/PROMPT_X.md               /dev tasks/PROMPT_X.md --resume          │
│         │                                    │                                   │
│         ▼                                    ▼                                   │
│   ┌─────────────┐                      ┌─────────────┐                          │
│   │ Task 1 ✅   │                      │ Load        │                          │
│   │ Task 2 ✅   │ ──── saves ────→     │ PROGRESS.md │                          │
│   │ Task 3 🔄   │     progress         └──────┬──────┘                          │
│   │ [TIMEOUT]   │                             │                                  │
│   └─────────────┘                             ▼                                  │
│                                        ┌─────────────┐                          │
│                                        │ Skip 1, 2   │                          │
│                                        │ Continue 3  │                          │
│                                        │ Task 4...   │                          │
│                                        └─────────────┘                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Recovery Files

| File | Location | Purpose |
|------|----------|---------|
| **PROGRESS** | `progress/PROGRESS_{NAME}.md` | Iteration log, key decisions, files changed |
| **LOG** | `logs/LOG_{NAME}_{TS}.md` | Final execution report with statistics |

### Resume Command

```bash
# Resume an interrupted session
/dev tasks/PROMPT_REDIS_CACHE.md --resume

# The executor will:
# 1. Load PROGRESS file
# 2. Skip completed tasks
# 3. Restore key decisions context
# 4. Continue from next incomplete task
```

### Validate Before Execution

```bash
# Dry run to validate PROMPT structure
/dev tasks/PROMPT_AUTH.md --dry-run

# Shows:
# - Task counts by priority (🔴 🟡 🟢)
# - Agent matching chain
# - Verification commands
# - Any validation issues
```

---

## Command Options

| Option | Description |
|--------|-------------|
| `--mode hitl` | Human-in-the-loop (default) — pause for review |
| `--mode afk` | Autonomous — run without pauses |
| `--resume` | Resume from existing PROGRESS file |
| `--dry-run` | Validate and show plan without executing |
| `--max N` | Override max iterations (default: 30) |

---

## Agent Integration

Reference agents with `@agent-name` in tasks:

```markdown
### 🟡 CORE
- [ ] @kb-architect: Create Redis KB domain
- [ ] @python-developer: Implement cache wrapper
- [ ] @test-generator: Add unit tests
```

### Available Agents

| Agent | Use For |
|-------|---------|
| `@kb-architect` | Building knowledge bases |
| `@python-developer` | Writing Python code |
| `@test-generator` | Adding tests |
| `@code-reviewer` | Quality checks |
| `@code-cleaner` | Refactoring |
| `@code-documenter` | Documentation |
| `@llm-specialist` | Prompt engineering |
| `@function-developer` | Cloud Run functions |
| `@extraction-specialist` | Document AI extraction |
| `@infra-deployer` | Terraform deployment |
| `@pipeline-architect` | Pipeline architecture |
| `@spark-specialist` | Spark optimization |
| `@ci-cd-specialist` | CI/CD pipelines |
| `@genai-architect` | AI system design |

---

## Safeguards

| Safeguard | Default | Purpose |
|-----------|---------|---------|
| `max_iterations` | 30 | Prevent infinite loops |
| `max_retries` | 3 | Retry failed tasks |
| `circuit_breaker` | 3 | Stop if no progress |
| `small_steps` | true | One logical change per task |
| `feedback_loops` | [] | Commands to run between tasks |

---

## When to Use Level 2 vs Level 3

| Scenario | Level 2 (AgentLoop) | Level 3 (AgentSpec) |
|----------|---------------------|---------------------|
| KB building | ✅ | |
| Prototypes | ✅ | |
| Single features | ✅ | |
| Utilities/parsers | ✅ | |
| Multi-component features | | ✅ |
| Production systems | | ✅ |
| Team projects | | ✅ |
| Full audit trail needed | | ✅ |

---

## Best Practices

1. **Start with questions** — Use `/dev "description"` to let crafter guide you
2. **Trust the Matching Engine** — Let it fingerprint and score before overriding
3. **Prioritize risky work** — Fail fast on hard problems
4. **Use verification commands** — Objective, exit-code based
5. **Track progress** — Memory bridge reduces token burn
6. **Take small steps** — One logical change per task
7. **Reflect** — Capture lessons for continuous improvement

---

## Related Files

| File | Purpose |
|------|---------|
| `.claude/commands/dev/dev.md` | Command definition |
| `.claude/agents/dev/prompt-crafter.md` | PROMPT crafting agent |
| `.claude/agents/dev/agentloop-executor.md` | Execution agent |
| `.claude/dev/docs/AGENT_MATCHING_ENGINE.md` | Matching Engine algorithm |
| `.claude/dev/templates/PROMPT_TEMPLATE.md` | Blank PROMPT template |
| `.claude/dev/templates/PROMPT_EXAMPLE_FEATURE.md` | Example: Python utility |
| `.claude/dev/templates/PROMPT_EXAMPLE_KB.md` | Example: KB domain |
| `.claude/dev/templates/PROGRESS_TEMPLATE.md` | Progress file template |
| `.claude/dev/examples/` | Real-world examples from actual feature builds |

---

## References

- [11 Tips For AI Coding With Ralph Wiggum](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum) — Matt Pocock
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Anthropic

---

*AgentLoop v3.0 — Explore first, define clearly, match intelligently, reflect always*
