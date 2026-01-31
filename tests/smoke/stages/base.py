"""Base class for all smoke test stages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tests.smoke.models import SmokeContext


@dataclass
class StageResult:
    """Result from a single stage execution."""

    stage_name: str
    passed: bool
    duration_ms: int = 0
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "stage": self.stage_name,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
        }
        if self.error:
            result["error"] = self.error
        if self.data:
            result.update(self.data)
        return result


class Stage(ABC):
    """Abstract base class for smoke test stages.

    All stages must implement the `run` method and set a `name` attribute.
    Use `execute` instead of `run` directly to get automatic timing.
    """

    name: str = "unnamed"

    @abstractmethod
    def run(self, context: "SmokeContext") -> StageResult:
        """Execute the stage logic.

        Args:
            context: Mutable context with inputs from previous stages

        Returns:
            StageResult with pass/fail status and any output data
        """
        pass

    def execute(self, context: "SmokeContext") -> StageResult:
        """Execute the stage with timing and error handling.

        This is the main entry point for running a stage. It wraps the
        `run` method with timing and exception handling.
        """
        start = datetime.now()
        try:
            result = self.run(context)
            result.duration_ms = int((datetime.now() - start).total_seconds() * 1000)
            return result
        except Exception as e:
            duration = int((datetime.now() - start).total_seconds() * 1000)
            return StageResult(
                stage_name=self.name,
                passed=False,
                duration_ms=duration,
                error=str(e),
            )
