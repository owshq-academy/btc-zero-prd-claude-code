"""Click CLI entry point for invoice generation."""

import time
from pathlib import Path

import click

from invoice_gen.generator import InvoiceGenerator
from invoice_gen.schemas.invoice import VendorType


@click.command()
@click.option(
    "--partner",
    "-p",
    type=click.Choice([v.value for v in VendorType], case_sensitive=False),
    help="Partner brand to generate invoices for",
)
@click.option(
    "--all-partners",
    is_flag=True,
    default=False,
    help="Generate invoices for all 5 partners",
)
@click.option(
    "--count",
    "-n",
    default=1,
    type=int,
    help="Number of invoices per partner",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="./output",
    help="Output directory for TIFF files",
)
@click.option(
    "--seed",
    type=int,
    default=None,
    help="Random seed for reproducibility",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["tiff", "pdf"], case_sensitive=False),
    default="tiff",
    help="Output format (default: tiff)",
)
@click.option(
    "--dpi",
    type=int,
    default=200,
    help="DPI for TIFF output (default: 200)",
)
@click.option(
    "--no-delivery",
    is_flag=True,
    default=False,
    help="Exclude delivery information from invoices",
)
@click.option(
    "--no-payment",
    is_flag=True,
    default=False,
    help="Exclude payment information from invoices",
)
@click.option(
    "--failure-rate",
    type=float,
    default=0.0,
    help="Rate (0.0-1.0) of invoices with intentionally wrong totals for validation testing",
)
@click.option(
    "--keep-intermediates",
    is_flag=True,
    default=False,
    help="Keep HTML and PDF intermediate files (useful for debugging)",
)
@click.option(
    "--gcs-bucket",
    type=str,
    default=None,
    help="GCS bucket to upload generated files (requires gcloud auth)",
)
def main(
    partner: str | None,
    all_partners: bool,
    count: int,
    output: str,
    seed: int | None,
    format: str,
    dpi: int,
    no_delivery: bool,
    no_payment: bool,
    failure_rate: float,
    keep_intermediates: bool,
    gcs_bucket: str | None,
) -> None:
    if not partner and not all_partners:
        raise click.UsageError("Either --partner or --all-partners must be specified")

    if partner and all_partners:
        raise click.UsageError("Cannot use both --partner and --all-partners")

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    vendors = list(VendorType) if all_partners else [VendorType(partner)]

    total_invoices = len(vendors) * count
    click.echo(f"Generating {total_invoices} invoice(s)...")
    click.echo(f"  Partners: {', '.join(v.value for v in vendors)}")
    click.echo(f"  Count per partner: {count}")
    click.echo(f"  Output: {output_path.absolute()}")
    click.echo(f"  Format: {format.upper()}")
    if seed is not None:
        click.echo(f"  Seed: {seed}")
    if failure_rate > 0:
        click.echo(click.style(f"  ⚠ Failure injection: {failure_rate:.0%} of invoices will have wrong totals", fg="yellow"))
    if keep_intermediates:
        click.echo(click.style("  📁 Keeping intermediate files (HTML, PDF)", fg="cyan"))

    uploader = None
    if gcs_bucket:
        try:
            from invoice_gen.gcs import GCSUploader

            uploader = GCSUploader(gcs_bucket)
            click.echo(click.style(f"  ☁️  GCS bucket: gs://{gcs_bucket}/", fg="cyan"))
        except Exception as e:
            raise click.ClickException(f"GCS access failed: {e}") from e

    click.echo()

    generator = InvoiceGenerator(
        seed=seed,
        output_dir=output_path,
        dpi=dpi,
        include_delivery=not no_delivery,
        include_payment=not no_payment,
        failure_rate=failure_rate,
        keep_intermediates=keep_intermediates,
    )

    start_time = time.time()
    generated_files: list[Path] = []
    errors: list[str] = []

    with click.progressbar(
        length=total_invoices,
        label="Generating invoices",
        show_pos=True,
        show_eta=True,
        show_percent=True,
    ) as bar:
        for vendor in vendors:
            for i in range(count):
                try:
                    if format.lower() == "pdf":
                        result = generator.generate_pdf(vendor)
                    else:
                        result = generator.generate_tiff(vendor)
                    generated_files.append(result.tiff_path)
                except Exception as e:
                    errors.append(f"{vendor.value} #{i + 1}: {e}")
                finally:
                    bar.update(1)

    elapsed = time.time() - start_time

    click.echo()
    click.echo(click.style("✅ Generation Complete!", fg="green", bold=True))
    click.echo(f"  Generated: {len(generated_files)} invoices")
    click.echo(f"  Time: {elapsed:.2f} seconds")
    click.echo(f"  Average: {elapsed / max(len(generated_files), 1):.2f} seconds per invoice")
    click.echo(f"  Output: {output_path.absolute()}")

    if keep_intermediates:
        html_count = len(list(output_path.glob("*.html")))
        pdf_count = len(list(output_path.glob("*.pdf")))
        click.echo(f"  Intermediates: {html_count} HTML, {pdf_count} PDF files")

    if errors:
        click.echo()
        click.echo(click.style(f"⚠ Errors ({len(errors)}):", fg="yellow"))
        for error in errors:
            click.echo(f"  - {error}")

    if uploader and generated_files:
        upload_success = 0
        upload_failed = 0
        upload_errors: list[str] = []

        click.echo()
        with click.progressbar(
            generated_files,
            label="Uploading to GCS",
            show_pos=True,
            show_percent=True,
        ) as bar:
            for file_path in bar:
                result = uploader.upload_file(file_path)
                if result.success:
                    upload_success += 1
                else:
                    upload_failed += 1
                    upload_errors.append(f"{file_path.name}: {result.error}")

        click.echo()
        if upload_failed == 0:
            click.echo(
                click.style(
                    f"☁️  Uploaded: {upload_success}/{len(generated_files)} files to gs://{gcs_bucket}/",
                    fg="green",
                )
            )
        else:
            click.echo(
                click.style(
                    f"☁️  Uploaded: {upload_success}/{len(generated_files)} files ({upload_failed} failed)",
                    fg="yellow",
                )
            )
            for error in upload_errors:
                click.echo(click.style(f"  ⚠ {error}", fg="yellow"))


if __name__ == "__main__":
    main()
