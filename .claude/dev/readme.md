# AgentLoop

> **Agentic Development (Level 2)** — Explore first, match intelligently, execute perfectly, recover gracefully.

AgentLoop is a structured iteration system that sits between "vibe coding" and full Spec-Driven Development (AgentSpec). It provides PROMPT-driven task execution with the Agent Matching Engine for context-aware agent assignment, verification loops, session recovery, and intelligent orchestration.

---

## Quick Start

### Option 1: Guided PROMPT Creation (Recommended)

```bash
/dev "I want to build a date parser utility"
```

The **Prompt Crafter** will:
1. Explore your codebase for context
2. Ask targeted questions about scope and quality
3. Run the **Matching Engine** to assign optimal agents
4. Generate a complete `PROMPT.md` file
5. Hand off for execution

### Option 2: Execute Existing PROMPT

```bash
/dev tasks/PROMPT_DATE_PARSER.md
```

### Option 3: Manual PROMPT Creation

```bash
# Copy template
cp templates/PROMPT_TEMPLATE.md tasks/PROMPT_MY_TASK.md

# Edit the file, then execute
/dev tasks/PROMPT_MY_TASK.md
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Agent Matching Engine** | Context-aware 4-dimension agent scoring |
| **SDD-Lite Workflow** | EXPLORE → DEFINE → DESIGN → GENERATE |
| **Priority Execution** | 🔴 RISKY → 🟡 CORE → 🟢 POLISH |
| **Verification Loops** | Objective, exit-code based checks |
| **Memory Bridge** | PROGRESS files prevent token burn |
| **Session Recovery** | `--resume` continues interrupted work |
| **REFLECT Phase** | Captures lessons learned + agent effectiveness |
| **Audit Trail** | LOG files capture execution history |

---

## Folder Structure

```text
.claude/dev/
├── README.md                        # This file
├── _index.md                        # Full documentation
├── docs/                            # Supporting documentation
│   └── AGENT_MATCHING_ENGINE.md     # Core matching algorithm
│
├── tasks/                           # Your PROMPT files (active work)
│   └── PROMPT_*.md
│
├── progress/                        # Memory bridge (auto-managed)
│   └── PROGRESS_*.md
│
├── logs/                            # Execution logs (auto-generated)
│   └── LOG_*.md
│
└── templates/                       # Templates and examples
    ├── PROMPT_TEMPLATE.md           # Blank template
    ├── PROGRESS_TEMPLATE.md         # Progress file template
    ├── PROMPT_EXAMPLE_FEATURE.md    # Example: Python utility
    └── PROMPT_EXAMPLE_KB.md         # Example: KB domain
```

---

## Command Reference

### Basic Usage

```bash
# Craft a new PROMPT (interactive)
/dev "description of what you want"

# Execute a PROMPT
/dev tasks/PROMPT_NAME.md

# List available PROMPTs
/dev --list
```

### Command Options

| Option | Description |
|--------|-------------|
| `--mode hitl` | Human-in-the-loop (default) — pause for review |
| `--mode afk` | Autonomous — run without pauses |
| `--resume` | Resume from existing PROGRESS file |
| `--dry-run` | Validate and show plan without executing |
| `--max N` | Override max iterations (default: 30) |

---

## Agent Matching Engine

The core intelligence of AgentLoop. A 5-step algorithm that goes beyond keyword matching:

```text
FINGERPRINT → DECOMPOSE → SCORE → CHAIN → VERIFY
(project DNA)  (task DNA)  (4-dim)  (sequence)  (sanity)
```

**Scoring Formula:**
```text
FINAL_SCORE = (TECH × 0.35) + (TASK × 0.30) + (DOMAIN × 0.25) + (PHASE × 0.10)
```

**Confidence Actions:**

| Score | Label | Action |
|-------|-------|--------|
| 0.85+ | Definitive | Auto-assign |
| 0.70-0.84 | Confident | Assign with reasoning |
| 0.50-0.69 | Uncertain | Present options to user |
| Below 0.50 | Low | Ask user to clarify |

See `docs/AGENT_MATCHING_ENGINE.md` for the full algorithm.

---

## The 3-Level Development Spectrum

```text
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT SPECTRUM                          │
├─────────────────────────────────────────────────────────────────┤
│  LEVEL 1           LEVEL 2              LEVEL 3                 │
│  Vibe Coding       AgentLoop            AgentSpec SDD           │
│  ───────────       ─────────            ───────────────         │
│  • Just prompts    • PROMPT.md driven   • 5-phase pipeline      │
│  • No structure    • Matching Engine    • Full traceability     │
│  • Hope it works   • Agent leverage     • Quality gates         │
│                    • Memory bridge      • Enterprise audit      │
│                                                                  │
│  Time: < 30 min    Time: 1-4 hours      Time: Multi-day         │
│  Command: (none)   Command: /dev        Command: /build-feature │
└─────────────────────────────────────────────────────────────────┘
```

---

## Related Resources

| Resource | Path |
|----------|------|
| Full Documentation | `_index.md` |
| Matching Engine | `docs/AGENT_MATCHING_ENGINE.md` |
| PROMPT Template | `templates/PROMPT_TEMPLATE.md` |
| Feature Example | `templates/PROMPT_EXAMPLE_FEATURE.md` |
| KB Example | `templates/PROMPT_EXAMPLE_KB.md` |
| Prompt Crafter Agent | `.claude/agents/dev/prompt-crafter.md` |
| AgentLoop Executor | `.claude/agents/dev/agentloop-executor.md` |

---

## References

- [11 Tips For AI Coding With Ralph Wiggum](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum) — Matt Pocock
- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Anthropic

---

*AgentLoop v3.0 — Explore first, match intelligently, execute perfectly, recover gracefully*
