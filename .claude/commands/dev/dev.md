# /dev Command

> **AgentLoop** — Agentic Development (Level 2) with structured iteration, Agent Matching Engine, and intelligent routing.

## Usage

```bash
# Craft a new PROMPT (prompt-crafter guides you)
/dev "I want to build a date parser"
/dev "Add caching to the API"

# Execute an existing PROMPT
/dev tasks/PROMPT_DATE_PARSER.md
/dev tasks/PROMPT_CACHE.md --mode afk

# Resume an interrupted session
/dev tasks/PROMPT_CACHE.md --resume

# Validate without executing
/dev tasks/PROMPT_AUTH.md --dry-run

# List available PROMPTs
/dev --list
```

## How It Works

The `/dev` command intelligently routes between two modes:

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              /dev COMMAND ROUTING                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   User Input                              Action                                 │
│   ──────────                              ──────                                 │
│                                                                                  │
│   /dev "description"         →  prompt-crafter (explore, define, match, generate)│
│   /dev tasks/PROMPT_*.md     →  agentloop-executor (execute the PROMPT)          │
│   /dev --list                →  Show available PROMPTs                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Mode 1: Craft (New Request)

When you provide a description (not a file path), the **prompt-crafter** agent:

1. **Explores** the codebase for context
2. **Defines** requirements via targeted questions
3. **Designs** architecture with the **Matching Engine** (fingerprint → decompose → score → chain → verify)
4. **Generates** a complete PROMPT.md file with @agent assignments and confidence scores

```bash
/dev "I want to create a Redis caching layer"
```

**Output:**
```text
PROMPT CRAFTER (AgentLoop v3.0)
===============================
I'll help you create a ready-to-execute PROMPT for: Redis caching layer

Let me explore the codebase and guide you through the workflow...

[EXPLORE → DEFINE → DESIGN (Matching Engine) → GENERATE]

✅ PROMPT CREATED
=================
File: .claude/dev/tasks/PROMPT_REDIS_CACHE.md
Tasks: 6 (🔴2 🟡3 🟢1)
Chain: @codebase-explorer → @python-developer → @test-generator → @code-reviewer
Confidence: HIGH (avg 0.89)

To execute:
  /dev tasks/PROMPT_REDIS_CACHE.md
```

---

## Mode 2: Execute (Existing PROMPT)

When you provide a PROMPT file path, the **agentloop-executor** agent:

1. **Loads** PROMPT.md + existing PROGRESS.md
2. **Picks** next task by priority (🔴→🟡→🟢)
3. **Executes** task (invokes @agent if specified)
4. **Verifies** with objective commands
5. **Updates** progress (memory bridge)
6. **Loops** until done or safeguard triggers
7. **Reflects** on completion (lessons learned + agent effectiveness)

```bash
/dev tasks/PROMPT_REDIS_CACHE.md
```

**Options:**
```bash
--mode afk     # Autonomous execution (no pauses)
--mode hitl    # Human-in-the-loop (default)
--max N        # Override max iterations
--dry-run      # Validate without executing
```

---

## Arguments

| Argument | Description |
|----------|-------------|
| `"description"` | Natural language request → triggers prompt-crafter |
| `tasks/PROMPT_*.md` | Path to PROMPT file → triggers agentloop-executor |
| `--list` | List available PROMPTs in `.claude/dev/tasks/` |
| `--mode` | Execution mode: `hitl` (default) or `afk` |
| `--resume` | Resume from existing PROGRESS file (memory bridge) |
| `--dry-run` | Validate and show plan without executing |
| `--max N` | Override max iterations (default: 30) |

---

## Workflow

### Complete Flow

```text
1. /dev "I want to build X"        # Craft phase (with Matching Engine)
   ↓
2. [EXPLORE → DEFINE → DESIGN]     # SDD-lite workflow
   ↓
3. PROMPT.md generated              # Ready to execute
   ↓
4. /dev tasks/PROMPT_X.md           # Execute phase
   ↓
5. [Loop with verification]         # Automated with agent chain
   ↓
6. EXIT_COMPLETE → REFLECT          # Done + lessons learned
```

### Skip Crafting (If You Know What You Want)

```bash
# Copy template and edit manually
cp .claude/dev/templates/PROMPT_TEMPLATE.md \
   .claude/dev/tasks/PROMPT_MY_TASK.md

# Then execute
/dev tasks/PROMPT_MY_TASK.md
```

---

## The 3-Level Development Spectrum

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DEVELOPMENT SPECTRUM                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   LEVEL 1                  LEVEL 2                     LEVEL 3                  │
│   Vibe Coding              AgentLoop                   AgentSpec SDD            │
│   ───────────              ─────────                   ─────────────            │
│                                                                                  │
│   • Just prompts           • PROMPT.md driven          • 5-phase pipeline       │
│   • No structure           • Matching Engine           • Full traceability      │
│   • Hope it works          • Agent leverage            • Quality gates          │
│   • Quick fixes            • Memory bridge             • Enterprise audit       │
│                            • SDD-lite workflow         • ADRs and specs         │
│                                                                                  │
│   Command: (none)          Command: /dev               Command: /build-feature  │
│   Time: < 30 min           Time: 1-4 hours             Time: Multi-day          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Examples

### Example 1: Build a Utility

```bash
# Start with a description
/dev "I need a date parser that handles multiple formats"

# Answer questions about scope, quality, verification
# Matching Engine assigns agents with confidence scores
# Get a generated PROMPT

# Execute
/dev tasks/PROMPT_DATE_PARSER.md
```

### Example 2: Build a KB Domain

```bash
/dev "Create a Redis knowledge base"

# Questions about topics, depth, examples
# Generated PROMPT with @kb-architect tasks

/dev tasks/PROMPT_REDIS_KB.md
```

### Example 3: Refactor Code

```bash
/dev "Refactor the authentication module to use JWT"

# Questions about backward compatibility, tests
# Matching Engine scores agents, builds chain
# Generated PROMPT with risky tasks first

/dev tasks/PROMPT_AUTH_REFACTOR.md --mode hitl
```

### Example 4: Validate Before Execution

```bash
# Dry run to see task breakdown and verify structure
/dev tasks/PROMPT_COMPLEX_FEATURE.md --dry-run

# Output shows:
# - Task summary (🔴 RISKY, 🟡 CORE, 🟢 POLISH counts)
# - Agent matching chain with confidence scores
# - Verification commands
# - Any validation issues
```

### Example 5: Resume Interrupted Session

```bash
# Session was interrupted (context rot, timeout, etc.)
# Progress was saved to: .claude/dev/progress/PROGRESS_REDIS_CACHE.md

# Resume from where you left off
/dev tasks/PROMPT_REDIS_CACHE.md --resume
```

---

## Session Recovery

The memory bridge system ensures no work is lost:

### Recovery Files

| File | Purpose |
|------|---------|
| `progress/PROGRESS_{NAME}.md` | Tracks completed tasks, key decisions, iteration log |
| `logs/LOG_{NAME}_{TS}.md` | Final execution report with statistics + agent effectiveness |

---

## Folder Structure

```text
.claude/dev/
├── _index.md                        # Documentation
├── docs/                            # Supporting docs
│   └── AGENT_MATCHING_ENGINE.md     # Core matching algorithm
├── tasks/                           # Your PROMPT files (active work)
│   └── PROMPT_*.md
├── progress/                        # Memory bridge (auto-managed)
│   └── PROGRESS_*.md
├── logs/                            # Execution logs
│   └── LOG_*.md
└── templates/                       # Templates and examples
    ├── PROMPT_TEMPLATE.md           # Blank template
    ├── PROGRESS_TEMPLATE.md         # Progress file template
    ├── PROMPT_EXAMPLE_FEATURE.md    # Example: Python utility
    └── PROMPT_EXAMPLE_KB.md         # Example: KB domain
```

---

## See Also

| Resource | Path |
|----------|------|
| AgentLoop Overview | `.claude/dev/_index.md` |
| Matching Engine | `.claude/dev/docs/AGENT_MATCHING_ENGINE.md` |
| Prompt Crafter Agent | `.claude/agents/dev/prompt-crafter.md` |
| AgentLoop Executor | `.claude/agents/dev/agentloop-executor.md` |
| PROMPT Template | `.claude/dev/templates/PROMPT_TEMPLATE.md` |
| Level 3 (AgentSpec) | `.claude/sdd/_index.md` |

---

*AgentLoop v3.0 — Explore first, match intelligently, execute perfectly, recover gracefully*
