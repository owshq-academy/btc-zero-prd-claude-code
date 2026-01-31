# BRAINSTORM: LangFuse Observability for Invoice Extraction

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | LANGFUSE_OBSERVABILITY |
| **Date** | 2026-01-30 |
| **Author** | brainstorm-agent |
| **Status** | Ready for Define |

---

## Initial Idea

**Raw Input:** Add LangFuse observability end-to-end to the GCP Cloud Run functions (functions/gcp/v1). The pipeline uses Gemini 2.5 Flash for invoice extraction. Instrument all LLM calls with LangFuse for tracing, cost tracking, and quality monitoring.

**Context Gathered:**
- Pipeline has 4 Cloud Run functions: tiff_to_png → classifier → extractor → bigquery_writer
- LLM calls happen in `data_extractor` function via `GeminiAdapter` and `OpenRouterAdapter`
- Existing `LLMResponse` dataclass already tracks latency_ms and tokens_used
- LangFuse KB exists with Cloud Run instrumentation patterns
- Production deadline: April 1, 2026

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `functions/gcp/v1/src/shared/adapters/llm.py` | Instrument adapters directly |
| Relevant KB Domains | langfuse, gcp, gemini | Use existing patterns |
| IaC Patterns | Terraform/Terragrunt for GCP | Secret Manager integration |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | What's your primary goal for adding LangFuse observability? | All of the above (cost, quality, debugging) | Full observability scope |
| 2 | Which pipeline stages should be instrumented? | Extraction Only | Focus on data_extractor and LLM adapters |
| 3 | How should LangFuse credentials be managed? | Secret Manager (Recommended) | Production-ready, IaC-managed |
| 4 | If LangFuse is unavailable, how should extraction behave? | Silent Fallback | Never block invoice processing |
| 5 | Do you have sample data for quality scoring? | Sample Invoices Only | Implement confidence scoring, defer accuracy |

---

## Sample Data Inventory

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | `gen/synthetic-invoice-gen/` | Available | Can generate test invoices |
| Output examples | N/A | 0 | No verified ground truth |
| Ground truth | N/A | 0 | To be built after MVP |
| Related code | `functions/gcp/v1/src/shared/adapters/llm.py` | 1 | Adapter pattern to extend |

**How samples will be used:**
- Synthetic invoices for end-to-end testing
- Schema validation success as proxy for quality
- Manual review to build ground truth dataset post-MVP

---

## Approaches Explored

### Approach A: Adapter-Level Instrumentation ⭐ Recommended

**Description:** Instrument the `GeminiAdapter` and `OpenRouterAdapter` classes directly, keeping tracing logic encapsulated within the adapter pattern.

**Pros:**
- Minimal code changes - only touches llm.py
- Follows existing adapter pattern
- Automatically traces OpenRouter fallback calls
- Easy to test in isolation

**Cons:**
- Less context about the calling function (vendor type, file name)
- Trace hierarchy is flat (no parent span)

**Why Recommended:** Fastest path to value, maintains clean architecture, extensible later.

---

### Approach B: Orchestration-Level Instrumentation

**Description:** Instrument at the `extract_invoice()` function level in extractor.py, wrapping the entire extraction flow with parent trace and child spans.

**Pros:**
- Rich trace hierarchy with full context
- Can capture vendor_type, file metadata in parent trace
- Clear visualization of retry/fallback flow

**Cons:**
- More invasive changes to extractor.py
- Requires creating a LangFuse context wrapper
- Adapter still needs modification for generation details

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A: Adapter-Level Instrumentation |
| **User Confirmation** | 2026-01-30 |
| **Reasoning** | Minimal changes, encapsulated, fast implementation |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | Instrument adapters, not orchestration | Faster, cleaner, extensible | Orchestration-level spans |
| 2 | Use Secret Manager for credentials | Production security best practice | Direct env vars |
| 3 | Silent fallback on LangFuse failure | Invoice processing > observability | Fail fast |
| 4 | Skip image capture in traces | Storage cost, not needed for debugging | Full image logging |
| 5 | Confidence scoring via schema validation | No ground truth available | LLM-as-Judge |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| Prompt management in LangFuse | Keep prompts in files for now | Yes |
| Session linking | Single invoice = single trace | Yes |
| LLM-as-Judge evaluation | No ground truth dataset | Yes |
| Custom dashboards/alerts | Use LangFuse built-in first | Yes |
| Distributed trace linking | Extraction-only scope for MVP | Yes |
| Full pipeline tracing | Focus on high-value LLM calls | Yes |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Primary goal | ✅ | All observability aspects needed | No |
| Instrumentation scope | ✅ | Extraction only (not full pipeline) | Yes - scoped down |
| Approach selection | ✅ | Adapter-level preferred | No |
| Image capture | ✅ | Skip images in traces | No |
| YAGNI features | ✅ | Agreed to defer 6 features | No |

---

## Trace Data Specification

Each LLM call will capture:

| Category | Data Captured | Source |
|----------|---------------|--------|
| **Identity** | trace_id, span_id, name | Auto-generated |
| **Model** | model name (gemini-2.5-flash, claude-3.5-sonnet) | Adapter config |
| **Prompt** | Full prompt text with schema | prompt parameter |
| **Response** | LLM output text | response.text |
| **Tokens** | input_tokens, output_tokens | Response usage |
| **Cost** | Calculated from tokens × model pricing | LangFuse auto |
| **Latency** | End-to-end call time (ms) | Already tracked |
| **Metadata** | provider, retry_count, image_count | Adapter state |
| **Score** | extraction_confidence (0.0-1.0) | Schema validation |

---

## Suggested Requirements for /define

Based on this brainstorm session, the following should be captured in the DEFINE phase:

### Problem Statement (Draft)
LLM calls in the invoice extraction pipeline lack observability for cost tracking, quality monitoring, and debugging, making it difficult to meet the $0.01/invoice cost target and 90% accuracy requirement.

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Data Engineers | Cannot debug extraction failures without logs |
| FinOps | Cannot track LLM costs per invoice |
| ML Engineers | Cannot measure extraction accuracy over time |

### Success Criteria (Draft)
- [ ] All Gemini and OpenRouter calls traced in LangFuse
- [ ] Token usage and cost visible per extraction
- [ ] P95 latency measurable via LangFuse dashboard
- [ ] Confidence scores attached to each extraction
- [ ] Zero impact on extraction if LangFuse unavailable

### Constraints Identified
- April 1, 2026 production deadline
- Secret Manager for credential management
- Must not block invoice processing
- Extraction-only scope (not full pipeline)

### Out of Scope (Confirmed)
- Full pipeline tracing (tiff_to_png, classifier, bigquery_writer)
- Prompt management in LangFuse (keep files)
- LLM-as-Judge evaluation
- Custom alerting rules
- Session/conversation linking
- Image capture in traces

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 5 |
| Approaches Explored | 2 |
| Features Removed (YAGNI) | 6 |
| Validations Completed | 5 |
| Duration | ~10 minutes |

---

## Next Step

**Ready for:** `/define .claude/sdd/features/BRAINSTORM_LANGFUSE_OBSERVABILITY.md`
