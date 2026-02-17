# PROMPT: EXAMPLE_FEATURE

> Example PROMPT for AgentLoop — Building a Python utility

---

## Goal

Create a date parsing utility that handles multiple date formats and outputs ISO 8601.

---

## Quality Tier

**Tier:** production

---

## Context

- Target location: `src/utils/date_parser.py`
- Test location: `tests/test_date_parser.py`
- Must handle: ISO, US format (MM/DD/YYYY), EU format (DD/MM/YYYY)
- Use Python 3.10+ with type hints

---

## Tasks (Prioritized)

### 🔴 RISKY (Do First)

- [ ] Decide on date parsing library (dateutil vs manual): Document decision in Notes
- [ ] Create directory structure if needed: Verify: `mkdir -p src/utils tests`

### 🟡 CORE

- [ ] Create `src/utils/__init__.py`: Verify: `ls src/utils/__init__.py`
- [ ] @python-developer: Implement date_parser.py with parse_date() function
- [ ] Implement format detection logic: Verify: `python -c "from src.utils.date_parser import parse_date; print('Import OK')"`
- [ ] @test-generator: Create comprehensive tests for date_parser
- [ ] Run tests: Verify: `pytest tests/test_date_parser.py -v`

### 🟢 POLISH (Do Last)

- [ ] Add docstrings and type hints: Verify: `python -c "from src.utils.date_parser import parse_date; print(parse_date.__doc__)"`
- [ ] @code-reviewer: Review implementation for edge cases

---

## Exit Criteria

- [ ] Module imports successfully: `python -c "from src.utils.date_parser import parse_date; print('OK')"`
- [ ] All tests pass: `pytest tests/test_date_parser.py --tb=short`
- [ ] Type hints present: `grep -q "def parse_date.*->.*:" src/utils/date_parser.py && echo "OK"`
- [ ] Handles ISO format: `python -c "from src.utils.date_parser import parse_date; assert parse_date('2026-01-25') == '2026-01-25'"`
- [ ] Handles US format: `python -c "from src.utils.date_parser import parse_date; assert parse_date('01/25/2026') == '2026-01-25'"`

---

## Progress

**Status:** NOT_STARTED

| Iteration | Timestamp | Task Completed | Key Decision | Files Changed |
|-----------|-----------|----------------|--------------|---------------|
| - | - | - | - | - |

---

## Config

```yaml
mode: hitl
quality_tier: production
max_iterations: 20
max_retries: 3
circuit_breaker: 3
small_steps: true
feedback_loops:
  - pytest tests/test_date_parser.py --tb=short
  - python -c "from src.utils.date_parser import parse_date"
```

---

## Notes

**Decision Log:**
- [ ] Library choice: [TBD - dateutil or manual parsing?]

This is an example PROMPT file demonstrating how to build a simple feature using AgentLoop.
Copy this file to `.claude/dev/tasks/` and customize it for your use case.

---

## References

- [Python Best Practices](.claude/kb/pydantic/)
- [PROMPT Template](.claude/dev/templates/PROMPT_TEMPLATE.md)
