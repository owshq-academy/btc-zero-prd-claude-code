"""Click CLI for smoke test execution."""

import json
import sys
from datetime import datetime

import click

from tests.smoke.runner import run_smoke_test
from tests.smoke.stages import StageResult


def _print_stage_result(result: StageResult, verbose: bool = False) -> None:
    """Print stage result with colored output."""
    if result.passed:
        status = click.style("✓ PASS", fg="green", bold=True)
    elif result.error and "Skipped" in result.error:
        status = click.style("○ SKIP", fg="yellow")
    else:
        status = click.style("✗ FAIL", fg="red", bold=True)

    click.echo(f"  {status} {result.stage_name} ({result.duration_ms}ms)")

    # Show stage data in verbose mode
    if verbose and result.data:
        for key, value in result.data.items():
            if key not in ("error",):
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 60:
                    str_value = str_value[:57] + "..."
                click.echo(f"       │ {click.style(key, fg='blue')}: {str_value}")

    if result.error and "Skipped" not in result.error:
        # Truncate very long errors
        error_msg = result.error
        if len(error_msg) > 100:
            error_msg = error_msg[:97] + "..."
        click.echo(f"       └─ {click.style(error_msg, fg='red')}")


def _create_verbose_callback(verbose: bool):
    """Create a callback with verbose flag bound."""
    def callback(result: StageResult) -> None:
        _print_stage_result(result, verbose)
    return callback


@click.command()
@click.option(
    "--env",
    "-e",
    type=click.Choice(["dev", "prod"]),
    default="dev",
    help="Target environment",
)
@click.option(
    "--vendor",
    "-v",
    type=click.Choice(["ubereats", "doordash", "grubhub", "ifood", "rappi"]),
    default="ubereats",
    help="Vendor type for test invoice",
)
@click.option(
    "--fail-fast/--no-fail-fast",
    default=True,
    help="Stop on first failure (default: true)",
)
@click.option(
    "--skip-logging",
    is_flag=True,
    default=False,
    help="Skip Cloud Logging check",
)
@click.option(
    "--json-output",
    is_flag=True,
    default=False,
    help="Output results as JSON",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output with stage details",
)
def main(
    env: str,
    vendor: str,
    fail_fast: bool,
    skip_logging: bool,
    json_output: bool,
    verbose: bool,
) -> None:
    """Run smoke tests for the invoice processing pipeline.

    This CLI executes an end-to-end test that:
    \b
    1. Generates a synthetic invoice
    2. Uploads it to GCS
    3. Waits for pipeline processing
    4. Validates extraction accuracy
    5. Verifies BigQuery output
    6. Checks for pipeline errors

    Exit codes:
    \b
      0 = All stages passed
      1 = One or more stages failed

    Examples:
    \b
      smoke-test --env dev --vendor ubereats
      smoke-test --env dev --vendor rappi --verbose
      smoke-test --json-output --no-fail-fast
    """
    start_time = datetime.now()

    if not json_output:
        click.echo()
        click.echo(click.style("🔬 Invoice Pipeline Smoke Test", fg="cyan", bold=True))
        click.echo(click.style("─" * 50, fg="cyan"))
        click.echo(f"   Environment: {click.style(env, fg='yellow')}")
        click.echo(f"   Vendor:      {click.style(vendor, fg='yellow')}")
        click.echo(f"   Fail-fast:   {click.style(str(fail_fast), fg='yellow')}")
        click.echo(f"   Started:     {click.style(start_time.strftime('%H:%M:%S'), fg='yellow')}")
        click.echo(click.style("─" * 50, fg="cyan"))
        click.echo()
        click.echo("Running stages:")
        if verbose:
            click.echo(click.style("  (verbose mode - showing stage details)", dim=True))
        click.echo()

    # Run the smoke test
    callback = _create_verbose_callback(verbose) if not json_output else None

    result = run_smoke_test(
        env=env,
        vendor=vendor,
        fail_fast=fail_fast,
        skip_logging=skip_logging,
        verbose=verbose,
        on_stage_complete=callback,
    )

    if json_output:
        # JSON output mode
        output = result.model_dump()
        output["timestamp"] = start_time.isoformat()
        click.echo(json.dumps(output, indent=2, default=str))
    else:
        # Human-readable output
        click.echo()
        click.echo(click.style("─" * 50, fg="cyan"))

        if result.success:
            click.echo(
                click.style("✓ SMOKE TEST PASSED", fg="green", bold=True)
                + click.style(f" ({result.total_duration_ms}ms)", dim=True)
            )
        else:
            click.echo(
                click.style("✗ SMOKE TEST FAILED", fg="red", bold=True)
                + click.style(f" ({result.total_duration_ms}ms)", dim=True)
            )

        click.echo()

        # Summary box
        click.echo(click.style("  ┌─ Summary ─────────────────────────────────┐", fg="cyan"))
        click.echo(f"  │  Passed:  {click.style(str(result.stages_passed), fg='green', bold=True):>3}                              │")
        click.echo(f"  │  Failed:  {click.style(str(result.stages_failed), fg='red' if result.stages_failed else 'white', bold=True):>3}                              │")
        click.echo(f"  │  Skipped: {click.style(str(result.stages_skipped), fg='yellow' if result.stages_skipped else 'white'):>3}                              │")
        click.echo(click.style("  └───────────────────────────────────────────┘", fg="cyan"))

        if result.invoice_id:
            click.echo()
            click.echo(f"  Invoice ID: {click.style(result.invoice_id, fg='cyan', bold=True)}")

        if result.error_summary and not result.success:
            click.echo()
            click.echo(click.style("  Error Summary:", fg="red", bold=True))
            # Split long errors into multiple lines
            error = result.error_summary
            if len(error) > 70:
                error = error[:67] + "..."
            click.echo(f"  {error}")

        click.echo()

        # Helpful hints for failures
        if not result.success:
            click.echo(click.style("  💡 Debugging tips:", dim=True))
            click.echo(click.style("     • Run with --verbose for more details", dim=True))
            click.echo(click.style("     • Run with --json-output for full data", dim=True))
            click.echo(click.style("     • Check Cloud Logging for pipeline errors", dim=True))
            if result.invoice_id:
                click.echo(click.style(f"     • Search logs: jsonPayload.invoice_id:\"{result.invoice_id}\"", dim=True))
            click.echo()

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
