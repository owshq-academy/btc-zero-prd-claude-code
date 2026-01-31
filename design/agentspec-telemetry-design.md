# AgentSpec Telemetry Design

> Privacy-first analytics for continuous product improvement

---

## Executive Summary

AgentSpec telemetry is a **local-first, opt-in** system that captures anonymous usage patterns to improve the framework. Users always get local analytics; community benchmarks require explicit opt-in.

**Principles:**
1. **Transparency** - Exactly what's collected is documented and verifiable
2. **Opt-in** - Never default to sharing; users must explicitly enable
3. **Value exchange** - Users get insights back for participating
4. **No secrets** - Code, content, and PII never leave the machine

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER'S MACHINE (Local-First)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   SDD Pipeline → Local Analytics Store → [Opt-in Gate]          │
│                  .claude/telemetry/                              │
│                                                                  │
│   Always available:                                              │
│   • agentspec insights (your data only)                         │
│   • Phase completion rates                                       │
│   • Agent effectiveness                                          │
│   • Personal recommendations                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ (Only if opted-in)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTSPEC ANALYTICS BACKEND                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Ingestion → Anonymization → Aggregation → Public Dashboard    │
│                                                                  │
│   Available to opted-in users:                                   │
│   • agentspec insights --community                              │
│   • Benchmarks vs community                                      │
│   • Recommended patterns                                         │
│   • Agent effectiveness leaderboard                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Schema

### What We Capture

```yaml
session:
  id: "uuid-v4"  # Random, not linked to user
  timestamp: "ISO-8601"
  agentspec_version: "semver"

feature:
  complexity:
    file_count: integer
    estimated_loc: "range"  # "100-500", not exact
    phases_used: ["define", "design", "build", "ship"]
    has_iac: boolean
    has_llm: boolean
    has_tests: boolean

  timing:
    define_duration_seconds: integer
    design_duration_seconds: integer
    build_duration_seconds: integer
    total_duration_seconds: integer

  outcome:
    shipped: boolean
    iterations: integer
    judge_used: boolean

agents:
  matching:
    - agent_type: string  # Generic type only
      file_type: string   # .py, .tf, .yaml
      confidence: float
      was_overridden: boolean

  effectiveness:
    - agent_type: string
      assigned_files: integer
      build_success: boolean
      quality_score: float | null

judge:
  enabled: boolean
  reviewers_count: integer
  pre_design_score: float | null
  post_build_score: float | null
  consensus_reached: boolean
  human_override: boolean

kb:
  domains_consulted: [string]  # Domain names only
  patterns_used: integer       # Count only

errors:
  phase_failed: string | null
  error_category: string | null
  recovered: boolean | null
```

### What We NEVER Capture

```yaml
# Published in NEVER_CAPTURE.yaml for transparency

code:
  ❌ source_code
  ❌ file_contents
  ❌ function_names
  ❌ variable_names
  ❌ comments

identifiers:
  ❌ file_paths
  ❌ file_names
  ❌ project_name
  ❌ git_repo
  ❌ branch_names

personal:
  ❌ user_name
  ❌ email
  ❌ ip_address
  ❌ machine_id
  ❌ api_keys

content:
  ❌ prompt_content
  ❌ llm_responses
  ❌ judge_feedback
  ❌ kb_content
  ❌ brainstorm_notes
```

---

## Value Exchange

### Tier 1: Local Analytics (Always Available)

```
agentspec insights

YOUR SDD METRICS (Last 30 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Features Started:    12
Features Shipped:    10 (83%)
Average Duration:    2.3 hours

PHASE COMPLETION
━━━━━━━━━━━━━━━━━
Brainstorm → Define:  100%
Define → Design:       92%
Design → Build:        85%
Build → Ship:          77% ← Investigate

YOUR TOP AGENTS
━━━━━━━━━━━━━━━
@python-developer     Used 10x  Quality: 8.9
@test-generator       Used 8x   Quality: 8.7
@function-developer   Used 6x   Quality: 8.2
```

### Tier 2: Community Benchmarks (Opt-In Required)

```
agentspec insights --community

HOW YOU COMPARE
━━━━━━━━━━━━━━━━
                    You      Community
Ship Rate:          83%      78%         +5% 🎉
Avg Duration:       2.3h     3.1h        -26% 🎉
Agent Usage:        4.2      3.1         +35%
Judge Adoption:     60%      34%         +26% 🎉

AGENT EFFECTIVENESS (Community Data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Best for Data Pipelines:
  @spark-specialist + @test-generator (94% success)

Best for Infrastructure:
  @terraform-specialist + @infra-deployer (91% success)

Best for AI/LLM Features:
  @extraction-specialist + @llm-specialist (89% success)
```

### Tier 3: Early Access (Active Contributors)

Users who opt-in AND contribute patterns get:
- Early access to new agents
- Priority bug fixes
- Recognition in release notes
- Input on roadmap

---

## User Commands

```bash
# Enable telemetry (shows consent dialog)
agentspec telemetry --enable

# Disable telemetry
agentspec telemetry --disable

# View what would be sent
agentspec telemetry --preview

# View local insights (always available)
agentspec insights

# View with community benchmarks (requires opt-in)
agentspec insights --community

# Export your data (GDPR-friendly)
agentspec telemetry --export

# Delete all telemetry data
agentspec telemetry --purge

# View consent status
agentspec telemetry --status
```

---

## Implementation

### Local Collector

```python
# .claude/telemetry/collector.py

@dataclass
class PhaseEvent:
    session_id: str
    phase: str
    started_at: datetime
    completed_at: datetime | None
    success: bool
    agent_count: int
    file_count: int
    judge_enabled: bool
    judge_score: float | None

class TelemetryCollector:
    """Local-first telemetry with opt-in sharing."""

    def __init__(self, project_root: Path):
        self.store = project_root / ".claude" / "telemetry"
        self.session_id = str(uuid.uuid4())
        self._sharing_enabled = self._check_consent()

    def record_phase(self, event: PhaseEvent) -> None:
        """Always record locally."""
        self._write_local(event)
        if self._sharing_enabled:
            self._queue_for_upload(self._anonymize(event))

    def _anonymize(self, event) -> dict:
        """Strip any potentially identifying information."""
        # Session ID already random UUID
        # File types generic (.py, .tf)
        # Agent types generic categories
        # No names, paths, content
        return asdict(event)
```

### Integration Points

```python
# Each phase command integrates telemetry

def execute_define(feature_path: str):
    collector = TelemetryCollector(Path.cwd())

    event = PhaseEvent(
        session_id=collector.session_id,
        phase="define",
        started_at=datetime.now(),
        ...
    )

    try:
        # Execute phase
        result = run_define_phase(feature_path)
        event.success = True
    except Exception:
        event.success = False
        raise
    finally:
        collector.record_phase(event)
```

---

## Backend Architecture

```
INGESTION
─────────
• API Gateway (rate limited)
• Validation (schema check)
• Queue (async processing)

PROCESSING
──────────
• Aggregation pipeline
• Pattern extraction
• Anomaly detection

STORAGE
───────
• Aggregated metrics only
• No raw events after 7 days
• Public dashboard data

OUTPUTS
───────
• Community dashboard (web)
• CLI API (insights --community)
• Improvement signals (internal)
```

---

## Product Insights Enabled

### What You Can Learn

| Signal | Insight | Action |
|--------|---------|--------|
| Phase drop-off | Where users abandon | Improve UX |
| Agent usage | Which agents matter | Invest there |
| Agent success rates | Which need work | Fix them |
| Judge adoption | Is it working | Promote or fix |
| Complexity trends | What users build | Prioritize |
| Error patterns | Common failures | Fix root causes |

### Example Discoveries

```
INSIGHT: Judge Impact
Features with Judge:     94% success, 8.7 quality
Features without:        82% success, 7.2 quality
→ Judge improves outcomes 12%

INSIGHT: Agent Gap
67% of .tf features use @terraform-specialist
With agent:    93% success
Without:       71% success
→ Auto-suggest agents for infrastructure

INSIGHT: Complexity Ceiling
<10 files:    92% ship rate
10-30 files:  85% ship rate
>30 files:    67% ship rate
→ Large features need more support
```

---

## Implementation Roadmap

### Phase 1: Local Analytics (Week 1-2)
- [ ] Build TelemetryCollector
- [ ] Integrate into commands
- [ ] Build `insights` command
- [ ] Local storage only

### Phase 2: Consent Flow (Week 2-3)
- [ ] Build opt-in dialog
- [ ] Build preview command
- [ ] Build export command
- [ ] Publish NEVER_CAPTURE.yaml

### Phase 3: Backend (Week 3-4)
- [ ] Build ingestion API
- [ ] Build aggregation
- [ ] Build public dashboard
- [ ] Build --community flag

### Phase 4: Feedback Loop (Week 4+)
- [ ] Use insights to improve
- [ ] Publish monthly reports
- [ ] Pattern recommendations
- [ ] Recommendation engine

---

## Privacy Commitments

1. **No tracking without consent** - Local analytics only until opt-in
2. **No fingerprinting** - No machine IDs, IPs, or persistent identifiers
3. **No content capture** - Code and prompts never leave the machine
4. **Right to delete** - `--purge` removes everything
5. **Right to export** - `--export` gives you your data
6. **Transparency** - Schema and NEVER_CAPTURE.yaml are public
7. **Aggregation only** - Raw events deleted after 7 days

---

*Document created: 2026-01-31*
*Status: Design complete, ready for implementation*
