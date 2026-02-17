# AgentLoop Examples

> Real-world example artifacts from the Invoice Extractor feature

---

## Contents

| File | Type | Description |
| ---- | ---- | ----------- |
| `PROMPT_INVOICE_EXTRACTOR.md` | PROMPT | Production-quality LLM extraction pipeline |
| `PROGRESS_INVOICE_EXTRACTOR.md` | PROGRESS | Memory bridge with 27 iterations logged |
| `LOG_INVOICE_EXTRACTOR_20260129_100000.md` | LOG | Complete execution log with statistics |

---

## Using These Examples

These examples demonstrate the full AgentLoop workflow for a real feature:

```text
/dev "I want to build an invoice extractor" → prompt-crafter asks questions
         ↓
PROMPT_INVOICE_EXTRACTOR.md                 → Generated PROMPT (352 lines)
         ↓
/dev tasks/PROMPT_INVOICE_EXTRACTOR.md      → agentloop-executor runs
         ↓
PROGRESS_INVOICE_EXTRACTOR.md               → Memory bridge (updated each iteration)
         ↓
LOG_INVOICE_EXTRACTOR_*.md                  → Final execution report
```

---

## Key Patterns Demonstrated

### PROMPT File

- **27 tasks** organized by priority (🔴 RISKY, 🟡 CORE, 🟢 POLISH)
- **Agent references** (`@python-developer`, `@llm-specialist`, `@test-generator`)
- **Exit criteria** with objective verification commands
- **Safeguards** (max_iterations, circuit_breaker, max_retries)
- **Quality tier**: production (requires tests, validation)

### PROGRESS File (Memory Bridge)

- **Iteration log** preserving key decisions across sessions
- **Status tracking** for session recovery (`--resume`)
- **Architecture decisions** recorded for context
- **Exit criteria status** updated after each verification

### LOG File

- **Task execution summary** with pass/fail counts
- **Key decisions made** throughout execution
- **Files created/modified** inventory
- **Statistics** (tasks completed, duration, coverage)
- **Recovery information** for interrupted sessions

---

## Statistics from This Example

```text
Total Tasks:     27
├── 🔴 RISKY:    3 tasks
├── 🟡 CORE:     15 tasks
└── 🟢 POLISH:   6 tasks

Duration:        1 hour 15 minutes
Files Created:   35+ files
Lines of Code:   ~7000+ LOC
Exit Reason:     EXIT_COMPLETE (success)
```

---

## Note

These examples use project-specific details (GCP, Gemini, Parquet, invoice extraction) but the structure and patterns are framework-agnostic. Use them as references for understanding:

1. How `prompt-crafter` generates comprehensive PROMPTs
2. How `agentloop-executor` tracks progress and enables recovery
3. How the priority system (RISKY → CORE → POLISH) organizes work
4. How agent references (`@agent-name`) enable specialist delegation
5. How verification commands ensure objective completion

---

## Templates

For creating your own PROMPTs, see:

- `templates/PROMPT_TEMPLATE.md` - Blank template with all sections
- `templates/PROMPT_EXAMPLE_FEATURE.md` - Simple Python utility example
- `templates/PROMPT_EXAMPLE_KB.md` - Knowledge base building example
