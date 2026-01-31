"""Stage 4: Validate extracted data against ground truth."""

from tests.smoke.config import load_config
from tests.smoke.models import SmokeContext
from tests.smoke.stages.base import Stage, StageResult
from tests.smoke.validators import CRITICAL_FIELDS, match_fields


class ValidateStage(Stage):
    """Validate extraction accuracy against ground truth.

    This stage:
    1. Compares extracted data with the original invoice_data (ground truth)
    2. Enforces exact match on critical fields
    3. Reports all mismatches for debugging
    """

    name = "validate"

    def run(self, context: SmokeContext) -> StageResult:
        """Compare extraction output with ground truth."""
        if not context.invoice_data:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="No ground truth (invoice_data) in context",
            )

        if not context.extracted_data:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="No extracted_data in context. Process stage must complete first.",
            )

        # Load critical fields from config or use defaults
        config = load_config()
        stage_config = config.get_stage("validate")
        critical_fields_list = stage_config.critical_fields

        if critical_fields_list:
            critical_fields = set(critical_fields_list)
        else:
            critical_fields = CRITICAL_FIELDS

        # Perform field matching
        all_passed, results = match_fields(
            expected=context.invoice_data,
            actual=context.extracted_data,
            critical_fields=critical_fields,
        )

        # Store results in context
        context.validation_passed = all_passed
        context.field_mismatches = [
            f"{r.field_name}: expected={r.expected}, actual={r.actual}"
            for r in results
            if not r.matched
        ]

        # Build result data
        matched_count = sum(1 for r in results if r.matched)
        total_count = len(results)

        result_data = {
            "matched": matched_count,
            "total": total_count,
            "accuracy": f"{matched_count}/{total_count}",
        }

        if context.field_mismatches:
            result_data["mismatches"] = context.field_mismatches

        return StageResult(
            stage_name=self.name,
            passed=all_passed,
            data=result_data,
            error=f"{len(context.field_mismatches)} critical field(s) mismatched"
            if not all_passed
            else None,
        )
