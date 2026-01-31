# AgentSpec Open Source Plan

> Comprehensive plan for open-sourcing the Spec-Driven Development (SDD) framework

---

## Executive Summary

**Project Name:** AgentSpec
**Tagline:** Spec-Driven Development for AI-Native Teams
**Target Launch:** Q1 2026

AgentSpec is a 5-phase development workflow with 40+ specialized AI agents and curated knowledge bases. It transforms requirements into working code with full traceability, addressing the gap between unstructured "vibe coding" and stale traditional specifications.

---

## 1. Repository Structure

```
agentspec/
├── README.md
├── LICENSE (MIT)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
│
├── docs/                              # Documentation site
│   ├── getting-started/
│   ├── guides/
│   ├── reference/
│   └── examples/
│
├── packages/                          # Core framework
│   ├── core/                          # Always required
│   │   ├── sdd/
│   │   │   ├── architecture/
│   │   │   └── templates/
│   │   ├── dev/
│   │   │   └── templates/
│   │   ├── commands/
│   │   ├── CLAUDE.md.template
│   │   └── README.md
│   │
│   ├── agents/                        # Agent library
│   │   ├── workflow/                  # 6 SDD agents
│   │   ├── dev/                       # 2 Dev Loop agents
│   │   ├── code-quality/              # 6 utility agents
│   │   ├── communication/             # 3 explanation agents
│   │   └── exploration/               # 2 codebase agents
│   │
│   └── kb/                            # KB framework
│       ├── _index.yaml.template
│       ├── _templates/
│       └── pydantic/                  # Universal domain
│
├── plugins/                           # Domain plugins
│   ├── plugin-aws/
│   ├── plugin-gcp/
│   ├── plugin-data-engineering/
│   ├── plugin-ai-ml/
│   └── plugin-crewai/
│
├── examples/                          # Full example projects
│   ├── invoice-pipeline/              # Real-world example
│   └── simple-api/                    # Minimal example
│
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 2. Plugin Architecture

### Plugin Manifest Schema

```yaml
# manifest.yaml
name: "plugin-{name}"
version: "1.0.0"
description: "Plugin description"
author: "Author Name"
license: "MIT"

requires:
  agentspec: ">=1.0.0"

agents:
  - path: "agents/agent-name.md"
    target: ".claude/agents/category/agent-name.md"

commands:
  - path: "commands/command-name.md"
    target: ".claude/commands/category/command-name.md"

kb_domains:
  - path: "kb/domain-name"
    target: ".claude/kb/domain-name"

depends:
  - plugin-core

post_install:
  - "Configuration instructions"
```

### Installation Methods

**Method 1: Manual Copy**
```bash
git clone --depth 1 https://github.com/yourorg/agentspec
cp -r agentspec/packages/core/* .claude/
cp -r agentspec/plugins/plugin-gcp/* .claude/
```

**Method 2: CLI (Future)**
```bash
agentspec init
agentspec install plugin-gcp
agentspec install plugin-ai-ml
```

---

## 3. Core Package Contents

### 3.1 SDD Framework

| File | Purpose |
|------|---------|
| `sdd/architecture/WORKFLOW_CONTRACTS.yaml` | Phase definitions, quality gates, status transitions |
| `sdd/templates/BRAINSTORM_TEMPLATE.md` | Phase 0 template |
| `sdd/templates/DEFINE_TEMPLATE.md` | Phase 1 template |
| `sdd/templates/DESIGN_TEMPLATE.md` | Phase 2 template |
| `sdd/templates/BUILD_REPORT_TEMPLATE.md` | Phase 3 output template |
| `sdd/templates/SHIPPED_TEMPLATE.md` | Phase 4 archive template |

### 3.2 Dev Loop Framework

| File | Purpose |
|------|---------|
| `dev/templates/PROMPT_TEMPLATE.md` | Task definition format |
| `dev/templates/PROGRESS_TEMPLATE.md` | Memory bridge format |

### 3.3 Workflow Agents (6)

| Agent | Model | Phase |
|-------|-------|-------|
| `brainstorm-agent` | Opus | 0 |
| `define-agent` | Opus | 1 |
| `design-agent` | Opus | 2 |
| `build-agent` | Sonnet | 3 |
| `ship-agent` | Haiku | 4 |
| `iterate-agent` | Sonnet | Any |

### 3.4 Dev Loop Agents (2)

| Agent | Purpose |
|-------|---------|
| `prompt-crafter` | Interactive PROMPT.md generation |
| `dev-loop-executor` | Execute with verification and recovery |

### 3.5 Utility Agents (11)

| Agent | Category | Purpose |
|-------|----------|---------|
| `code-reviewer` | Code Quality | Security + quality review |
| `code-cleaner` | Code Quality | Remove comments, DRY |
| `code-documenter` | Code Quality | Generate documentation |
| `python-developer` | Code Quality | Python implementation |
| `test-generator` | Code Quality | pytest generation |
| `dual-reviewer` | Code Quality | CodeRabbit + Claude review |
| `adaptive-explainer` | Communication | Multi-audience explanations |
| `meeting-analyst` | Communication | Extract insights from meetings |
| `the-planner` | Communication | Strategic planning |
| `codebase-explorer` | Exploration | Analyze unfamiliar codebases |
| `kb-architect` | Exploration | Build KB domains |

### 3.6 Commands (10)

| Command | Phase/Category |
|---------|----------------|
| `/brainstorm` | Phase 0 |
| `/define` | Phase 1 |
| `/design` | Phase 2 |
| `/build` | Phase 3 |
| `/ship` | Phase 4 |
| `/iterate` | Any phase |
| `/dev` | Dev Loop |
| `/memory` | Core |
| `/sync-context` | Core |
| `/create-kb` | Knowledge |

---

## 4. Plugin Packages

### plugin-gcp

| Component | Contents |
|-----------|----------|
| Agents | function-developer, infra-deployer |
| KB | gcp/, terraform/, terragrunt/ |

### plugin-aws

| Component | Contents |
|-----------|----------|
| Agents | lambda-builder, aws-deployer, aws-lambda-architect, ci-cd-specialist |
| KB | aws/ |

### plugin-data-engineering

| Component | Contents |
|-----------|----------|
| Agents | spark-specialist, spark-troubleshooter, spark-performance-analyzer, spark-streaming-architect, lakeflow-*, medallion-architect |
| KB | spark/, lakeflow/ |

### plugin-ai-ml

| Component | Contents |
|-----------|----------|
| Agents | llm-specialist, genai-architect, ai-prompt-specialist, ai-data-engineer |
| KB | gemini/, langfuse/, openrouter/ |

### plugin-crewai

| Component | Contents |
|-----------|----------|
| Agents | dataops-builder |
| KB | crewai/ |

---

## 5. Implementation Phases

### Phase 1: Foundation (Week 1-2)

- [ ] Create GitHub repository
- [ ] Add LICENSE (MIT), CODE_OF_CONDUCT, CONTRIBUTING
- [ ] Extract and sanitize core framework files
- [ ] Extract and sanitize workflow agents
- [ ] Extract and sanitize utility agents
- [ ] Create CLAUDE.md.template
- [ ] Create KB index template
- [ ] Set up branch protection
- [ ] Set up issue/PR templates

### Phase 2: Documentation (Week 2-3)

- [ ] Write hero README with GIF/video
- [ ] Set up documentation site (Docusaurus/MkDocs)
- [ ] Write Getting Started guide (15-min quickstart)
- [ ] Write SDD Workflow deep-dive
- [ ] Write Dev Loop guide
- [ ] Write Agent creation guide
- [ ] Write KB domain creation guide
- [ ] Document WORKFLOW_CONTRACTS.yaml schema
- [ ] Document plugin manifest schema

### Phase 3: Examples & Validation (Week 3-4)

- [ ] Sanitize invoice-pipeline as example
- [ ] Create minimal "simple-api" example
- [ ] Find 5-10 beta users
- [ ] Collect and address feedback
- [ ] Iterate on documentation
- [ ] Set up CI/CD (lint, validate, docs deploy)

### Phase 4: Launch (Week 4-5)

- [ ] Create logo and visual identity
- [ ] Create demo video (30 seconds)
- [ ] Write launch blog post
- [ ] Post to Hacker News (Show HN)
- [ ] Post to Reddit (r/programming, r/artificial)
- [ ] Post to Twitter/X, LinkedIn
- [ ] Submit to Product Hunt
- [ ] Set up Discord/Slack community

### Phase 5: Growth (Ongoing)

- [ ] Release official plugins
- [ ] Feature community contributions
- [ ] Weekly/monthly content (blog, video)
- [ ] Create comparison guides
- [ ] Gather case studies
- [ ] Consider enterprise features

---

## 6. Key Differentiators

| Feature | GitHub Spec-Kit | OpenSpec | AgentSpec |
|---------|-----------------|----------|-----------|
| Agent Matching | Manual | None | Automatic discovery |
| KB Grounding | None | None | 8+ curated domains |
| Session Recovery | None | None | PROGRESS memory bridge |
| Quality Gates | Informal | Informal | Objective, automated |
| Phase Governance | None | None | WORKFLOW_CONTRACTS.yaml |
| Build Attribution | None | None | Agent table in BUILD_REPORT |
| Two Speed Modes | None | None | Dev Loop + SDD |

---

## 7. Marketing Messaging

### Individual Developers
> "Ship features faster with structured AI workflows and specialized agents."

### Team Leads
> "Bring consistency to AI-assisted development with quality gates and traceability."

### Enterprise
> "Governance-first AI development with full audit trail from requirement to deployment."

---

## 8. Success Metrics

| Metric | 3 Month | 6 Month | 12 Month |
|--------|---------|---------|----------|
| GitHub Stars | 500 | 2,000 | 5,000 |
| Monthly Downloads | 100 | 500 | 2,000 |
| Contributors | 5 | 15 | 30 |
| Community Plugins | 2 | 10 | 25 |
| Discord Members | 50 | 200 | 500 |

---

## 9. Files to Extract from Current Project

### Core (Required)

| Source | Target |
|--------|--------|
| `.claude/sdd/architecture/WORKFLOW_CONTRACTS.yaml` | `packages/core/sdd/architecture/` |
| `.claude/sdd/templates/*.md` | `packages/core/sdd/templates/` |
| `.claude/dev/templates/*.md` | `packages/core/dev/templates/` |
| `.claude/commands/workflow/*.md` | `packages/core/commands/workflow/` |
| `.claude/commands/dev/*.md` | `packages/core/commands/dev/` |
| `.claude/commands/core/*.md` | `packages/core/commands/core/` |

### Agents (Required)

| Source | Target |
|--------|--------|
| `.claude/agents/workflow/*.md` | `packages/agents/workflow/` |
| `.claude/agents/dev/*.md` | `packages/agents/dev/` |
| `.claude/agents/code-quality/*.md` | `packages/agents/code-quality/` |
| `.claude/agents/communication/*.md` | `packages/agents/communication/` |
| `.claude/agents/exploration/*.md` | `packages/agents/exploration/` |

### KB (Required)

| Source | Target |
|--------|--------|
| `.claude/kb/_index.yaml` | `packages/kb/_index.yaml.template` |
| `.claude/kb/_templates/` | `packages/kb/_templates/` |
| `.claude/kb/pydantic/` | `packages/kb/pydantic/` |

### Plugins (Optional)

| Source | Target Plugin |
|--------|---------------|
| `.claude/agents/aws/*.md` | `plugin-aws` |
| `.claude/agents/domain/function-developer.md` | `plugin-gcp` |
| `.claude/agents/domain/infra-deployer.md` | `plugin-gcp` |
| `.claude/agents/data-engineering/*.md` | `plugin-data-engineering` |
| `.claude/agents/ai-ml/*.md` | `plugin-ai-ml` |
| `.claude/kb/gcp/` | `plugin-gcp` |
| `.claude/kb/terraform/` | `plugin-gcp` |
| `.claude/kb/terragrunt/` | `plugin-gcp` |
| `.claude/kb/gemini/` | `plugin-ai-ml` |
| `.claude/kb/langfuse/` | `plugin-ai-ml` |
| `.claude/kb/openrouter/` | `plugin-ai-ml` |
| `.claude/kb/crewai/` | `plugin-crewai` |

---

## 10. Sanitization Checklist

Before publishing, remove or anonymize:

- [ ] Company-specific names and projects
- [ ] Internal URLs and endpoints
- [ ] API keys and secrets (even expired ones)
- [ ] Personal names (unless permission granted)
- [ ] Project-specific business logic
- [ ] Vendor-specific prompts (UberEats, DoorDash, etc.)
- [ ] Internal meeting notes references
- [ ] Client data schemas (replace with generic)

---

## 11. License Considerations

**Recommended: MIT License**

Pros:
- Maximum adoption (businesses love it)
- Simple and well-understood
- Compatible with most other licenses

Alternative: Apache 2.0
- Explicit patent grant
- Contribution terms clearer
- Slightly more complex

---

## 12. Community Guidelines

### Contribution Types

| Type | Description | Approval |
|------|-------------|----------|
| Bug Fix | Fix issues in core/plugins | PR review |
| New Agent | Add specialist agent | PR review + docs |
| New KB Domain | Add knowledge domain | PR review + validation |
| New Plugin | Add domain plugin | Separate repo or PR |
| Documentation | Improve docs | PR review |
| Example | Add example project | PR review |

### Code of Conduct

Use Contributor Covenant 2.1 (industry standard).

### Issue Triage

| Label | SLA |
|-------|-----|
| bug | 48 hours |
| feature | 7 days |
| docs | 7 days |
| question | 48 hours |

---

## 13. Next Actions

1. **Immediate**: Create new GitHub repository
2. **This week**: Extract core framework files
3. **This week**: Write hero README
4. **Next week**: Set up documentation site
5. **Next week**: Create example projects
6. **Week 3**: Beta test with 5-10 users
7. **Week 4**: Launch publicly

---

*Document created: 2026-01-31*
*Author: AgentSpec Team*
