# DEFINE: LangFuse Observability for Invoice Extraction

> Instrument LLM calls in the data_extractor function with LangFuse for cost tracking, quality monitoring, and debugging

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | LANGFUSE_OBSERVABILITY |
| **Date** | 2026-01-30 |
| **Author** | define-agent |
| **Status** | Ready for Design |
| **Clarity Score** | 15/15 |
| **Source** | [BRAINSTORM_LANGFUSE_OBSERVABILITY.md](BRAINSTORM_LANGFUSE_OBSERVABILITY.md) |

---

## Problem Statement

LLM calls in the invoice extraction pipeline lack observability for cost tracking, quality monitoring, and debugging. This makes it difficult to verify the **$0.01/invoice cost target**, measure progress toward the **90% extraction accuracy requirement**, and troubleshoot failures in production. Without instrumentation, the team is flying blind on their most critical (and expensive) pipeline component.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| **Data Engineers** | Pipeline operators | Cannot debug extraction failures without detailed LLM call logs and error context |
| **FinOps** | Cost management | Cannot track LLM costs per invoice or detect cost anomalies |
| **ML Engineers** | Model quality | Cannot measure extraction accuracy over time or identify failing patterns |

---

## Goals

| Priority | Goal |
|----------|------|
| **MUST** | Trace all Gemini and OpenRouter LLM calls with prompt, response, and metadata |
| **MUST** | Capture token usage and calculate cost per extraction |
| **MUST** | Record latency (end-to-end LLM call time) for performance monitoring |
| **MUST** | Attach confidence scores to each extraction based on schema validation |
| **MUST** | Gracefully degrade if LangFuse is unavailable (silent fallback) |
| **SHOULD** | Add retry attempt tracking to understand fallback behavior |
| **COULD** | Capture image count metadata (without storing images) |

---

## Success Criteria

Measurable outcomes:

- [ ] **100% LLM call coverage** - Every Gemini and OpenRouter call is traced in LangFuse
- [ ] **Token visibility** - Input/output tokens visible in LangFuse dashboard
- [ ] **Cost tracking** - Cost per extraction calculable (target: < $0.003/extraction)
- [ ] **Latency monitoring** - P95 extraction latency measurable via LangFuse
- [ ] **Instrumentation overhead** - < 50ms added latency per LLM call
- [ ] **Zero extraction failures** - LangFuse unavailability never blocks invoice processing
- [ ] **Confidence scores** - Every extraction has a numeric confidence score (0.0-1.0)

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Gemini extraction traced | LangFuse is available, Gemini call succeeds | `GeminiAdapter.extract()` is called | Trace appears in LangFuse with prompt, response, tokens, latency |
| AT-002 | OpenRouter fallback traced | Gemini fails, OpenRouter succeeds | Fallback occurs | Both attempts traced with correct provider metadata |
| AT-003 | Cost calculated | Extraction completes | View LangFuse dashboard | Cost in USD is displayed based on model pricing |
| AT-004 | Confidence scored | Schema validation passes | Extraction completes | Score `extraction_confidence` = 1.0 attached to trace |
| AT-005 | Confidence scored (partial) | Schema validation has warnings | Extraction completes | Score `extraction_confidence` < 1.0 reflects issues |
| AT-006 | Silent fallback | LangFuse API unreachable | Extraction is attempted | Extraction succeeds, warning logged, no trace sent |
| AT-007 | Minimal overhead | Normal operation | 100 extractions measured | LangFuse overhead < 50ms per call (P95) |

---

## Out of Scope

Explicitly NOT included in this feature:

- **Full pipeline tracing** - Only data_extractor; tiff_to_png, classifier, bigquery_writer excluded
- **Prompt management in LangFuse** - Keep prompts in local files, not LangFuse prompt registry
- **LLM-as-Judge evaluation** - No ground truth dataset available; defer to post-MVP
- **Custom alerting rules** - Use LangFuse built-in dashboards first
- **Session/conversation linking** - Single invoice = single trace (no session concept)
- **Image capture in traces** - Only log image count and bytes, not actual images
- **Distributed trace linking** - No trace_id propagation from upstream functions

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| **Timeline** | Production launch April 1, 2026 | Must complete by mid-March for testing |
| **Security** | Credentials via GCP Secret Manager | Requires Terraform changes for secret mounting |
| **Reliability** | Never block invoice processing | Requires try/catch around all LangFuse calls |
| **Performance** | < 50ms overhead per LLM call | Use async SDK methods where possible |
| **Scope** | Extraction function only | No changes to other Cloud Run functions |

---

## Technical Context

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `functions/gcp/v1/src/shared/adapters/llm.py` | Adapter-level instrumentation |
| **KB Domains** | langfuse, gcp, gemini | Patterns: cloud-run-instrumentation, python-sdk-integration |
| **IaC Impact** | Modify existing | Add Secret Manager secret for LANGFUSE_SECRET_KEY |

**Implementation Approach:** Adapter-Level Instrumentation
- Instrument `GeminiAdapter` and `OpenRouterAdapter` classes directly
- Create `LangfuseObserver` wrapper that encapsulates tracing logic
- Inject observer into adapters via dependency injection
- Observer handles all LangFuse SDK calls with error handling

---

## Assumptions

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | LangFuse Python SDK supports async flush | Would need sync flush in finally block | [ ] |
| A-002 | LangFuse cloud has 99.9% availability | May need local buffering if unreliable | [ ] |
| A-003 | Gemini API returns token usage in response | Would need to estimate tokens from text length | [ ] |
| A-004 | OpenRouter returns token usage in response | Already confirmed via OpenAI SDK compatibility | [x] |
| A-005 | LangFuse auto-calculates cost from model name | May need manual cost lookup table | [ ] |

---

## Trace Data Specification

Each LLM call will capture:

| Category | Field | Source | Required |
|----------|-------|--------|----------|
| **Identity** | trace_id | Auto-generated | Yes |
| **Identity** | name | "gemini-extraction" or "openrouter-extraction" | Yes |
| **Model** | model | Adapter config (gemini-2.5-flash, claude-3.5-sonnet) | Yes |
| **Model** | model_parameters | {temperature, max_tokens} | Yes |
| **Input** | prompt | Full prompt text with schema | Yes |
| **Output** | response | LLM output text | Yes |
| **Usage** | input_tokens | Response usage metadata | Yes |
| **Usage** | output_tokens | Response usage metadata | Yes |
| **Timing** | latency_ms | End-to-end call time | Yes |
| **Metadata** | provider | "gemini" or "openrouter" | Yes |
| **Metadata** | retry_attempt | 0, 1, 2 | Yes |
| **Metadata** | image_count | Number of images in request | Yes |
| **Score** | extraction_confidence | 0.0-1.0 based on validation | Yes |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Specific targets: $0.01/invoice, 90% accuracy |
| Users | 3 | Three personas with distinct pain points |
| Goals | 3 | Prioritized with MUST/SHOULD/COULD |
| Success | 3 | Measurable with specific numbers (50ms, 100% coverage) |
| Scope | 3 | 6 items explicitly excluded |
| **Total** | **15/15** | Ready for Design |

---

## Open Questions

None - ready for Design.

---

## Key Decisions from Brainstorm

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Adapter-level instrumentation | Minimal code changes, follows existing patterns |
| 2 | Secret Manager for credentials | Production security best practice |
| 3 | Silent fallback on failure | Business continuity over observability |
| 4 | Skip image capture | Storage cost, not needed for debugging |
| 5 | Confidence via schema validation | No ground truth available for accuracy |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-30 | define-agent | Initial version from BRAINSTORM |

---

## Next Step

**Ready for:** `/design .claude/sdd/features/DEFINE_LANGFUSE_OBSERVABILITY.md`
