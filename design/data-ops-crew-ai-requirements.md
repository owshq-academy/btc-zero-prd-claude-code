# CrewAI Autonomous Monitoring - Developer Requirements

> **Document Type:** Technical Requirements Specification
> **Source:** Consolidated from 6 planning meetings (notes/summary-requirements.md)
> **Last Updated:** January 31, 2026
> **Owner:** Joao Silva

---

## Executive Summary

Build an autonomous monitoring system using CrewAI to detect, analyze, and report pipeline issues. The system uses a three-agent architecture that reads logs from GCS, performs root cause analysis, and sends alerts to Slack.

**Key Constraint:** Phase 1 is monitoring-only. No auto-remediation until trust is established.

---

## 1. Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| **D27** | Implement CrewAI for autonomous monitoring | Reduce manual log monitoring burden |
| **D28** | Three-agent architecture (Triage → Root Cause → Reporter) | Separation of concerns, specialized agents |
| **D29** | Cloud Logging export to GCS for agent consumption | Structured, queryable log storage |
| **D30** | Slack integration for alerts and reports | Team already uses Slack for ops |
| **D4** | Start with monitoring-only, add auto-remediation later | Build trust before automation |
| **D5** | Weekly autonomous ops review cadence | Regular validation of agent accuracy |

---

## 2. Architecture

### 2.1 Data Flow

```text
┌─────────────────┐     ┌──────────┐     ┌──────────────────────────────────────────┐
│  Cloud Logging  │────▶│   GCS    │────▶│              CrewAI Pipeline              │
│  (all services) │     │ (logs/)  │     │                                          │
└─────────────────┘     └──────────┘     │  ┌─────────┐   ┌───────────┐   ┌────────┐│
        │                    │           │  │ TRIAGE  │──▶│ROOT CAUSE │──▶│REPORTER││
        │                    │           │  │  Agent  │   │   Agent   │   │ Agent  ││
        ▼                    ▼           │  └─────────┘   └───────────┘   └────────┘│
┌─────────────────┐     < 1 minute       └──────────────────────────────────────────┘
│ Cloud Monitoring│     export latency                                        │
└─────────────────┘                                                           ▼
        │                                                              ┌──────────┐
        └──────────────────────────────────────────────────────────────│  Slack   │
                           (metrics query)                             │#alerts-ops│
                                                                       └──────────┘
```

### 2.2 Three-Agent Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CrewAI PIPELINE                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐          │
│  │   TRIAGE AGENT   │    │ ROOT CAUSE AGENT │    │  REPORTER AGENT  │          │
│  │                  │    │                  │    │                  │          │
│  │ Role: Monitor    │    │ Role: Investigator   │ Role: Communicator│          │
│  │                  │    │                  │    │                  │          │
│  │ Input:           │    │ Input:           │    │ Input:           │          │
│  │ - GCS log files  │───▶│ - Triaged events │───▶│ - Analysis report│          │
│  │                  │    │ - Metrics data   │    │                  │          │
│  │ Output:          │    │                  │    │ Output:          │          │
│  │ - Filtered events│    │ Output:          │    │ - Slack message  │          │
│  │ - Severity class │    │ - Root cause     │    │ - Resolution     │          │
│  │                  │    │ - Suggested fix  │    │   tracking       │          │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Specifications

### 3.1 Triage Agent

| Attribute | Value |
|-----------|-------|
| **Role** | Log monitor and filter |
| **Goal** | Identify and classify issues from raw logs |
| **Backstory** | First line of defense for pipeline health |

**Capabilities:**
- Read logs from GCS bucket
- Parse structured log data (JSON format)
- Classify severity: `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- Identify anomalies and patterns
- Filter noise, pass relevant events downstream

**Tools Required:**
```python
tools = [
    GCSReaderTool(),      # Read log files from GCS
    LogParserTool(),      # Parse structured logs
    PatternMatchTool(),   # Identify error patterns
]
```

**Output Schema:**
```python
class TriagedEvent(BaseModel):
    timestamp: datetime
    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    source_service: str  # e.g., "data-extractor", "tiff-converter"
    error_type: str
    error_message: str
    occurrence_count: int  # How many times in analysis window
    raw_log_path: str
```

### 3.2 Root Cause Agent

| Attribute | Value |
|-----------|-------|
| **Role** | Investigator |
| **Goal** | Analyze issues and determine likely root cause |
| **Backstory** | Deep analysis expert for complex pipeline issues |

**Capabilities:**
- Receive triaged events from Triage Agent
- Query Cloud Monitoring for correlated metrics
- Analyze patterns across multiple log entries
- Determine likely root cause
- Suggest remediation steps

**Tools Required:**
```python
tools = [
    LogParserTool(),       # Parse related logs
    MetricsQueryTool(),    # Query Cloud Monitoring
    LLMAnalysisTool(),     # Use Gemini for complex analysis
]
```

**Output Schema:**
```python
class RootCauseAnalysis(BaseModel):
    event: TriagedEvent
    root_cause: str
    confidence: float  # 0.0 - 1.0
    evidence: list[str]  # Supporting log entries
    affected_count: int  # Number of affected items
    suggested_fix: str
    escalation_needed: bool
    escalation_contacts: list[str]  # e.g., ["@ana", "@joao"]
```

### 3.3 Reporter Agent

| Attribute | Value |
|-----------|-------|
| **Role** | Communicator |
| **Goal** | Create human-readable reports and send to Slack |
| **Backstory** | Bridge between AI analysis and human operators |

**Capabilities:**
- Receive analysis from Root Cause Agent
- Format human-readable reports
- Send notifications to Slack
- Track resolution status

**Tools Required:**
```python
tools = [
    SlackSenderTool(),     # Send Slack messages
    ReportFormatterTool(), # Format reports
]
```

**Output Format (Slack Message):**
```text
🔴 ERROR: Gemini extraction failures detected

**Root Cause:** Multi-page invoice handling bug
**Confidence:** 85%
**Affected:** 5 invoices in last hour

**Evidence:**
- data-extractor: JSONDecodeError at line 42
- Gemini response truncated for pages > 3

**Suggested Fix:** Check prompt template for page handling

**Escalation:** @ana @joao

_Detected by CrewAI at 2026-04-15 14:32:00 UTC_
```

---

## 4. Data Inputs

### 4.1 Log Sources

| Source | Type | Location | Purpose |
|--------|------|----------|---------|
| Cloud Logging | System logs | Exported to GCS | Errors, traces, events |
| Cloud Monitoring | Metrics | API query | CPU, memory, latency |
| LangFuse | LLM metrics | API query | Cost, accuracy, tokens |

### 4.2 GCS Log Structure

```text
gs://invoice-pipeline-{env}-logs/
├── YYYY/MM/DD/
│   ├── {timestamp}-{severity}.json
│   └── ...
```

**Log Entry Format:**
```json
{
  "timestamp": "2026-04-15T14:30:00Z",
  "severity": "ERROR",
  "service": "data-extractor",
  "function": "extract_invoice",
  "message": "Gemini returned invalid JSON",
  "trace_id": "abc123",
  "labels": {
    "invoice_id": "INV-2026-001234",
    "environment": "prod"
  },
  "error": {
    "type": "JSONDecodeError",
    "message": "Expecting ',' delimiter: line 42 column 5"
  }
}
```

### 4.3 Export Configuration

| Setting | Value |
|---------|-------|
| Export latency | < 1 minute |
| Retention | 30 days |
| Format | JSON (newline delimited) |
| Filter | severity >= WARNING |

---

## 5. Slack Integration

### 5.1 Channel Configuration

| Channel | Purpose | Members |
|---------|---------|---------|
| `#alerts-ops` | CrewAI automated alerts | Joao, Pedro, Ana |

### 5.2 Message Types

| Severity | Emoji | Action Required |
|----------|-------|-----------------|
| CRITICAL | 🚨 | Immediate escalation |
| ERROR | 🔴 | Investigation needed |
| WARNING | 🟡 | Monitor closely |
| INFO | ℹ️ | Awareness only |

### 5.3 Webhook Configuration

**Requirement:** Slack Incoming Webhook with permissions to post to `#alerts-ops`

**Environment Variable:**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXX
```

---

## 6. Infrastructure Requirements

### 6.1 GCS Log Export

**Log Sink Configuration:**
```hcl
resource "google_logging_project_sink" "crewai_logs" {
  name                   = "crewai-log-sink"
  destination            = "storage.googleapis.com/${google_storage_bucket.logs.name}"
  filter                 = "severity >= WARNING"
  unique_writer_identity = true
}
```

### 6.2 Compute (Cloud Run)

| Setting | Value |
|---------|-------|
| Runtime | Python 3.11 |
| Memory | 1 GiB |
| Timeout | 300 seconds |
| Trigger | Cloud Scheduler (every 5 min) OR GCS event |
| Concurrency | 1 (single instance) |

### 6.3 Service Account Permissions

| Permission | Purpose |
|------------|---------|
| `roles/storage.objectViewer` | Read logs from GCS |
| `roles/monitoring.viewer` | Query Cloud Monitoring metrics |
| `roles/logging.viewer` | Read Cloud Logging (fallback) |

### 6.4 Secrets

| Secret | Purpose |
|--------|---------|
| `SLACK_WEBHOOK_URL` | Slack notifications |
| `GOOGLE_API_KEY` | Gemini for LLM analysis |
| `LANGFUSE_PUBLIC_KEY` | LangFuse observability |
| `LANGFUSE_SECRET_KEY` | LangFuse authentication |

---

## 7. Guardrails

### 7.1 Phase 1 Constraints

| Guardrail | Implementation |
|-----------|----------------|
| **No auto-remediation** | Agents suggest only, no action taken |
| **Maximum retries** | Max 3 retries per issue analysis |
| **Circuit breaker** | Stop after 10 consecutive failures |
| **Human-in-the-loop** | All suggestions require human action |
| **Audit log** | Log all agent actions to GCS |

### 7.2 Audit Log Schema

```python
class AgentAuditLog(BaseModel):
    timestamp: datetime
    agent_name: str
    action: str
    input_summary: str
    output_summary: str
    duration_ms: int
    success: bool
    error: Optional[str]
```

### 7.3 Risk Mitigation (R8)

| Risk | Mitigation |
|------|------------|
| Agent runaway behavior | Circuit breaker pattern |
| False positive alerts | Confidence threshold (> 0.7) |
| Alert fatigue | Deduplication, severity filtering |
| Cost runaway | Token limits, execution limits |

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to detect** | < 5 minutes | CrewAI → Slack timestamp delta |
| **False positive rate** | < 10% | Manual review of alerts |
| **Alert coverage** | > 95% | Known issues detected |
| **Agent accuracy** | > 80% | Root cause correctness |

---

## 9. Action Items

| ID | Owner | Task | Due Date | Dependencies |
|----|-------|------|----------|--------------|
| **A29** | Pedro Lima | Configure Cloud Logging export to GCS | Feb 20, 2026 | None |
| **A30** | Pedro Lima | Set up Slack webhook | Feb 21, 2026 | None |
| **A10** | Joao Silva | Set up CrewAI project structure | Feb 21, 2026 | A29 |
| **A20** | Ana Costa | Define error patterns for Triage Agent | Feb 22, 2026 | A10 |
| **A11** | Joao Silva | Define agent prompts and capabilities | Feb 24, 2026 | A10, A20 |
| **A35** | Marina Santos | Create runbook for escalation | Feb 25, 2026 | None |

### Dependency Graph

```text
A29 (GCS Export) ─┬─▶ A10 (CrewAI Structure) ─┬─▶ A11 (Agent Prompts)
                  │                            │
A30 (Slack)──────┘                            └─▶ A20 (Error Patterns)

A35 (Runbook) ─────▶ Independent
```

---

## 10. Timeline

| Phase | Dates | Deliverables |
|-------|-------|--------------|
| **Infrastructure** | Feb 20-21, 2026 | GCS export, Slack webhook |
| **Development** | Feb 21-28, 2026 | CrewAI agents implemented |
| **Testing** | Mar 1-15, 2026 | Agent accuracy validation |
| **Pilot** | Apr 1-30, 2026 | Production monitoring pilot |

### Key Milestone

| Date | Milestone |
|------|-----------|
| **Apr 30, 2026** | CrewAI pilot complete |

### Prerequisites

1. ✅ Production pipeline deployed (Apr 1, 2026)
2. ⏳ GCS log export configured (A29)
3. ⏳ Slack webhook configured (A30)
4. ⏳ Error patterns defined (A20)
5. ⏳ Escalation runbook created (A35)

---

## 11. Example Workflow

**Scenario:** Gemini returns invalid JSON for multi-page invoice

```text
14:30:00  data-extractor throws JSONDecodeError
          ↓
14:30:05  Error logged to Cloud Logging
          ↓
14:30:45  Log exported to GCS (< 1 min)
          ↓
14:31:00  Triage Agent reads new logs
          - Classifies as ERROR
          - Detects 5 similar errors in last hour
          ↓
14:31:30  Root Cause Agent analyzes
          - Queries related logs
          - Checks Gemini response patterns
          - Determines: "Multi-page invoice handling bug"
          ↓
14:32:00  Reporter Agent sends Slack alert
          ↓
14:32:00  Team notified in #alerts-ops

TOTAL TIME: 2 minutes (< 5 min target ✓)
```

---

## 12. Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Agent Framework | CrewAI | 0.28+ |
| LLM | Gemini 2.0 Flash | Latest |
| Compute | Cloud Run | Gen2 |
| Logs | Cloud Logging + GCS | N/A |
| Metrics | Cloud Monitoring | N/A |
| Alerts | Slack | Webhooks |
| Validation | Pydantic | v2 |
| Observability | LangFuse | Latest |

---

## 13. Future Phase 2 Capabilities

> **Note:** These are NOT in scope for Phase 1. Documented for planning only.

| Capability | Description | Prerequisite |
|------------|-------------|--------------|
| Auto-retry | Automatic retry with backoff | Agent accuracy > 90% |
| Auto-remediation | Fix known issues automatically | Runbook coverage > 80% |
| Proactive alerts | Predict issues before they occur | 6 months of training data |

---

## 14. Open Questions

| ID | Question | Owner | Priority |
|----|----------|-------|----------|
| Q8 | What guardrails for auto-remediation in Phase 2? | Joao Silva | MEDIUM |
| Q9 | How to handle LangFuse integration for agent observability? | Joao Silva | LOW |

---

## Appendix A: RACI Matrix

| Activity | Responsible | Accountable | Consulted | Informed |
|----------|-------------|-------------|-----------|----------|
| Agent architecture | Joao | Joao | Ana | Pedro, Marina |
| Infrastructure setup | Pedro | Joao | Joao | Ana, Marina |
| Error pattern definition | Ana | Joao | Joao | Pedro, Marina |
| Escalation runbook | Marina | Marina | All | All |

---

## Appendix B: Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Summary Requirements | [notes/summary-requirements.md](../notes/summary-requirements.md) | Source of all requirements |
| Autonomous DataOps Notes | [notes/06-autonomous-dataops.md](../notes/06-autonomous-dataops.md) | Original meeting notes |
| Cloud Run Architecture | [design/gcp-cloud-run-fncs.md](gcp-cloud-run-fncs.md) | Function deployment patterns |
| CrewAI KB | [.claude/kb/crewai/](../.claude/kb/crewai/) | CrewAI implementation patterns |
