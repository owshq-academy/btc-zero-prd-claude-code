# AgentSpec Telemetry

> Local analytics for understanding your AgentSpec usage

---

## Overview

Telemetry captures metrics from your shipped features to help you:
- Understand phase timing and bottlenecks
- Measure agent effectiveness
- Identify patterns and improvements
- Generate actionable reports

**All data is local.** Nothing leaves your machine.

---

## Quick Start

### Capture telemetry when shipping

```bash
/ship DEFINE_MY_FEATURE.md --telemetry
```

### Generate a report

```bash
/telemetry report
```

### View quick summary

```bash
/telemetry summary
```

---

## Folder Structure

```
.claude/telemetry/
├── readme.md                # This file
├── SESSION_SCHEMA.yaml      # Session data format
├── REPORT_TEMPLATE.md       # Report template
│
├── sessions/                # Raw session data
│   └── YYYY-MM-DD_FEATURE.json
│
├── reports/                 # Generated reports
│   ├── REPORT_LATEST.md
│   ├── REPORT_YYYY-MM.md
│   └── REPORT_YYYY-WNN.md
│
└── aggregates/              # Computed metrics
    ├── agent_effectiveness.json
    ├── phase_metrics.json
    └── trends.json
```

---

## What Gets Captured

### Phase Metrics
- Duration per phase (brainstorm, define, design, build)
- Clarity scores (from define)
- Technical context (location, KB domains, IaC impact)
- Iteration count (from build)

### Agent Metrics
- Which agents were used
- Files assigned per agent
- Success/failure per agent
- Quality scores (if Judge enabled)

### Feature Metrics
- Total duration
- File count
- Test count
- Ship success

---

## Commands

| Command | Description |
|---------|-------------|
| `/telemetry report` | Generate full report (REPORT_LATEST.md) |
| `/telemetry report --weekly` | Generate weekly report |
| `/telemetry report --monthly` | Generate monthly report |
| `/telemetry summary` | Quick console summary |
| `/telemetry sessions` | List all session files |

---

## Integration

### With /ship

Add `--telemetry` flag to capture session data:

```bash
/ship DEFINE_INVOICE_PIPELINE.md --telemetry
```

### Future: Auto-capture

Session capture could be automatic for all shipped features:

```yaml
# .claude/settings.yaml (future)
telemetry:
  auto_capture: true
  reports:
    auto_generate: weekly
```

---

## Privacy

- **Local only**: Data never leaves your machine
- **No PII**: Only metrics, never content
- **User controlled**: Delete anytime with `rm -rf .claude/telemetry/`
- **Opt-in**: Only captures when you use `--telemetry` flag

---

## Files

| File | Purpose |
|------|---------|
| `SESSION_SCHEMA.yaml` | Documents session JSON format |
| `REPORT_TEMPLATE.md` | Template for generated reports |
| `sessions/*.json` | Raw session data |
| `reports/*.md` | Generated reports |
| `aggregates/*.json` | Computed metrics |
