# AgentSpec Open Source Plan - Executive Summary

> Complete action plan for open-sourcing and enhancing AgentSpec

---

## Vision

Transform AgentSpec from a project-specific framework into the **leading open-source spec-driven development framework** for AI-native teams, with validated agent matching, multi-LLM review, and community-driven improvement.

---

## What We Planned (This Session)

### 1. GitHub Repository Structure

**Decision:** Monorepo with core + plugins separation

```
agentspec/
├── packages/
│   ├── core/           # SDD framework, templates, workflow agents
│   ├── agents/         # Agent library (19 universal agents)
│   └── kb/             # KB framework + pydantic domain
│
├── plugins/
│   ├── plugin-gcp/     # GCP specialists + KB (gcp, terraform, terragrunt)
│   ├── plugin-aws/     # AWS specialists + KB
│   ├── plugin-data/    # Spark, Lakeflow, Medallion
│   ├── plugin-ai/      # LLM specialists + KB (gemini, langfuse, openrouter)
│   └── plugin-crewai/  # CrewAI specialists + KB
│
├── examples/           # Full example projects
├── docs/               # Documentation site
└── cli/                # Future CLI tool
```

**Document:** `design/agentspec-open-source-plan.md`

---

### 2. Core Framework Improvements

**Current State:** 7.5/10 quality
**Target State:** 9.2/10 quality

| # | Improvement | Impact | Effort |
|---|-------------|--------|--------|
| 1 | Confidence scoring in agent matching | High | Medium |
| 2 | KB freshness indicators | Medium | Easy |
| 3 | Complexity estimates in file manifest | Medium | Easy |
| 4 | Build→Design auto-feedback loop | High | Medium |
| 5 | Cross-feature dependencies | Medium | Medium |
| 6 | Agent composition (multi-agent per file) | High | Complex |

**Document:** `design/agentspec-improvement-analysis.md`

---

### 3. LLM-as-Judge Feature

**Purpose:** Validate specs before expensive BUILD phase, catch agent matching errors

**Architecture:**
```
DEFINE ──► JUDGE (Phase 1.5) ──► DESIGN
            │
            ├── Claude (Opus) review
            ├── GPT-4 (via OpenRouter) review
            ├── Gemini (via OpenRouter) review
            ├── MCP validation against KB
            │
            ▼
        JUDGE_REPORT.md
            │
            ├── Score >= 8? → Proceed to DESIGN
            └── Score < 8? → /iterate DEFINE
```

**Key Features:**
- Configurable number of judges (1-3)
- Consensus threshold (2/3 agreement)
- MCP validation against KB patterns
- Human-in-the-loop final authority
- Auto-trigger for complex features (>10 files, IaC impact)
- Optional for simple features

**Evidence from shipped features:**
- TERRAFORM_TERRAGRUNT (34 files) shipped with NO agents
- SMOKE_TEST (19 files) shipped with NO agents
- Judge would have caught these gaps

**Document:** `design/agentspec-improvement-analysis.md`

---

### 4. Local Telemetry System

**Purpose:** Capture usage metrics locally to understand patterns and improve

**Structure:**
```
.claude/telemetry/
├── sessions/           # Raw session JSON (per shipped feature)
├── reports/            # Generated reports
├── aggregates/         # Computed metrics
├── SESSION_SCHEMA.yaml # Data format spec
└── REPORT_TEMPLATE.md  # Report template
```

**Capture via:** `/ship DEFINE_*.md --telemetry`

**Data captured:**
- Phase timing and completion rates
- Agent usage and effectiveness
- Technical context (location, KB domains, IaC)
- Judge scores (when enabled)
- Test counts and iterations

**Implementation:** Created in `.claude/telemetry/` and `.claude/commands/core/telemetry.md`

---

### 5. Unified /report Command

**Purpose:** Replace fragmented commands with one comprehensive view

```bash
/report                        # Full ecosystem report
/report --section=telemetry    # Just usage metrics
/report --section=agents       # Agent inventory & effectiveness
/report --section=kb           # Knowledge base health
/report --section=sdd          # SDD pipeline status
/report --summary              # Quick executive summary
```

**Sections:**
1. **Executive Summary** - Health score, key metrics
2. **SDD Pipeline Status** - Active, stale, shipped features
3. **Agent Inventory** - Available, usage, effectiveness, gaps
4. **KB Health** - Domains, freshness, coverage
5. **Telemetry** - Phase funnel, timing, trends
6. **Recommendations** - Priority actions

**Status:** Designed, not yet implemented

---

## Action Items

### Phase 1: Foundation (Week 1-2)

#### Repository Setup
- [ ] Create GitHub repository (name: `agentspec`)
- [ ] Add LICENSE (MIT)
- [ ] Add CODE_OF_CONDUCT.md
- [ ] Add CONTRIBUTING.md
- [ ] Set up branch protection
- [ ] Create issue templates

#### Extract Core Framework
- [ ] Copy and sanitize SDD templates (remove project-specific content)
- [ ] Copy WORKFLOW_CONTRACTS.yaml
- [ ] Copy Dev Loop templates
- [ ] Copy 6 workflow agents
- [ ] Copy 2 dev agents
- [ ] Copy 11 utility agents (code quality, communication, exploration)
- [ ] Create CLAUDE.md.template
- [ ] Create KB index template

#### Create Plugins
- [ ] Extract plugin-gcp (agents + KB)
- [ ] Extract plugin-aws (agents + KB)
- [ ] Extract plugin-data (agents)
- [ ] Extract plugin-ai (agents + KB)
- [ ] Extract plugin-crewai (agents + KB)
- [ ] Create plugin manifest schema

---

### Phase 2: Core Improvements (Week 2-3)

#### Agent Matching Enhancements
- [ ] Add confidence scoring to agent matching algorithm
- [ ] Add fallback agent support
- [ ] Document matching criteria explicitly

#### KB Improvements
- [ ] Add freshness indicators (staleness_threshold_days)
- [ ] Add warning for stale domains (>90 days)

#### File Manifest Improvements
- [ ] Add complexity estimates (S/M/L)
- [ ] Add cross-feature dependency tracking

---

### Phase 3: Judge Implementation (Week 3-4)

#### Pre-Design Judge
- [ ] Create `/judge` command
- [ ] Create `judge-agent.md`
- [ ] Integrate OpenRouter for multi-LLM review
- [ ] Add MCP validation checks
- [ ] Create JUDGE_REPORT_TEMPLATE.md
- [ ] Add auto-trigger logic (>10 files, IaC impact)

#### Post-Build Judge (Optional)
- [ ] Add quality scoring after BUILD
- [ ] Capture agent effectiveness metrics
- [ ] Feed back to agent matching

#### Update /ship
- [ ] Add `--judge` flag to capture judge data
- [ ] Update session schema for judge metrics

---

### Phase 4: Unified Report (Week 4-5)

#### Create /report Command
- [ ] Create `report.md` command definition
- [ ] Implement Executive Summary section
- [ ] Implement SDD Pipeline Status section
- [ ] Implement Agent Inventory section
- [ ] Implement KB Health section
- [ ] Implement Telemetry section
- [ ] Implement Recommendations engine
- [ ] Support `--section=X` filtering
- [ ] Support `--summary` for quick view

#### Deprecate /telemetry
- [ ] Merge telemetry into /report
- [ ] Keep telemetry data structure (sessions/, aggregates/)

---

### Phase 5: Documentation & Launch (Week 5-6)

#### Documentation
- [ ] Write hero README with demo GIF
- [ ] Set up documentation site (Docusaurus/MkDocs)
- [ ] Write Getting Started guide (15-min quickstart)
- [ ] Write SDD Workflow deep-dive
- [ ] Write Agent creation guide
- [ ] Write KB domain creation guide
- [ ] Write Plugin development guide

#### Examples
- [ ] Sanitize invoice-pipeline as example
- [ ] Create minimal "hello-world" example
- [ ] Document both with walkthroughs

#### Launch
- [ ] Create demo video (30 seconds)
- [ ] Write launch blog post
- [ ] Post to Hacker News (Show HN)
- [ ] Post to Reddit (r/programming, r/artificial)
- [ ] Post to Twitter/X, LinkedIn
- [ ] Submit to Product Hunt
- [ ] Set up Discord community

---

## Files Created This Session

| File | Purpose |
|------|---------|
| `design/agentspec-open-source-plan.md` | GitHub structure, plugin architecture, mainstream roadmap |
| `design/agentspec-improvement-analysis.md` | Core improvements, LLM-as-Judge proposal |
| `design/agentspec-telemetry-design.md` | External telemetry design (for reference) |
| `.claude/telemetry/readme.md` | Local telemetry overview |
| `.claude/telemetry/SESSION_SCHEMA.yaml` | Session data format |
| `.claude/telemetry/REPORT_TEMPLATE.md` | Report template |
| `.claude/commands/core/telemetry.md` | /telemetry command (to be replaced by /report) |

---

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repo structure | Monorepo with plugins | Easier contribution, single versioning |
| License | MIT | Maximum adoption |
| Telemetry | Local-only, opt-in capture | Privacy-first, user controlled |
| Judge | Multi-LLM via OpenRouter | Diverse perspectives, fair comparison |
| Report | Unified command | Full ecosystem visibility |

---

## Success Metrics

### Framework Quality
| Metric | Current | Target |
|--------|---------|--------|
| Agent matching accuracy | 7.5/10 | 9.2/10 |
| Features with agents | 60% | 95% |
| Judge adoption | 0% | 50% |
| KB freshness | 85% | 95% |

### Open Source Traction (6 months)
| Metric | Target |
|--------|--------|
| GitHub Stars | 2,000 |
| Monthly Downloads | 500 |
| Contributors | 15 |
| Community Plugins | 10 |
| Discord Members | 200 |

---

## Differentiation

| Feature | GitHub Spec-Kit | OpenSpec | AgentSpec |
|---------|-----------------|----------|-----------|
| Agent Matching | ❌ Manual | ❌ None | ✅ Automatic |
| Agent Validation | ❌ None | ❌ None | ✅ Judge layer |
| KB Grounding | ❌ None | ❌ None | ✅ 8+ domains |
| Multi-LLM Review | ❌ None | ❌ None | ✅ OpenRouter |
| Usage Analytics | ❌ None | ❌ None | ✅ Local telemetry |
| Ecosystem Report | ❌ None | ❌ None | ✅ /report command |

---

## Next Immediate Actions

1. **Today:** Review this summary, prioritize phases
2. **This Week:** Create GitHub repo, extract core framework
3. **Next Week:** Implement core improvements (confidence scoring, KB freshness)
4. **Week 3:** Implement Judge MVP (single judge + MCP validation)
5. **Week 4:** Implement unified /report command
6. **Week 5:** Documentation and examples
7. **Week 6:** Launch

---

*Summary created: 2026-01-31*
*Session: claude/plan-std-github-structure-aXIAt*
