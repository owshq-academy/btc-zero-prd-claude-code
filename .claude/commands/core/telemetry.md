# /telemetry

> Generate insights from your AgentSpec usage

---

## Usage

```bash
# Generate latest report
/telemetry report

# Generate weekly report
/telemetry report --weekly

# Generate monthly report
/telemetry report --monthly

# Show quick summary
/telemetry summary

# List all sessions
/telemetry sessions
```

---

## What It Does

The `/telemetry` command analyzes your shipped features and generates actionable insights:

1. **Reads session data** from `.claude/telemetry/sessions/`
2. **Computes aggregates** (phase timing, agent effectiveness, trends)
3. **Generates reports** in `.claude/telemetry/reports/`
4. **Provides recommendations** based on patterns

---

## Report Types

### Latest Report (`/telemetry report`)
- All-time or last 30 days
- Full analysis with recommendations
- Saved to `REPORT_LATEST.md`

### Weekly Report (`/telemetry report --weekly`)
- Current week's features
- Week-over-week trends
- Saved to `REPORT_YYYY-WNN.md`

### Monthly Report (`/telemetry report --monthly`)
- Current month's features
- Month-over-month trends
- Saved to `REPORT_YYYY-MM.md`

### Quick Summary (`/telemetry summary`)
- Console output only
- Key metrics at a glance
- No file generated

---

## Data Sources

Telemetry reads from:
- `.claude/sdd/archive/*/` - Shipped feature artifacts
- `.claude/telemetry/sessions/` - Session JSON files

Session data is captured automatically when you run `/ship --telemetry`.

---

## Output Location

```
.claude/telemetry/
├── sessions/           # Raw session JSON (one per feature)
├── reports/            # Generated markdown reports
└── aggregates/         # Computed metrics JSON
```

---

## Example Output

```
/telemetry summary

AGENTSPEC TELEMETRY SUMMARY
═══════════════════════════

Features Shipped:  5
Ship Rate:         100%
Avg Duration:      7.25 hours

TOP AGENTS
──────────
@python-developer     5 features  100% success
@test-generator       4 features  100% success
@function-developer   3 features  100% success

RECOMMENDATIONS
───────────────
⚠ Consider @terraform-specialist for TERRAFORM_TERRAGRUNT_INFRA
⚠ Enable Judge for features >30 files

Run '/telemetry report' for full analysis.
```

---

## Integration with /ship

To capture telemetry automatically:

```bash
/ship DEFINE_MY_FEATURE.md --telemetry
```

This will:
1. Archive the feature (normal /ship behavior)
2. Extract metrics from artifacts
3. Save session JSON to `.claude/telemetry/sessions/`
4. Update aggregates

---

## Privacy

All telemetry is **local only**:
- Data never leaves your machine
- No external APIs called
- You control all data
- Delete anytime: `rm -rf .claude/telemetry/`
