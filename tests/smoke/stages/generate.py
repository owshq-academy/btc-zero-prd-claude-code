"""Stage 1: Generate synthetic invoice via invoice-gen library."""

from pathlib import Path
from tempfile import TemporaryDirectory

from tests.smoke.models import SmokeContext
from tests.smoke.stages.base import Stage, StageResult

try:
    from invoice_gen import InvoiceGenerator, VendorType

    INVOICE_GEN_AVAILABLE = True
except ImportError:
    INVOICE_GEN_AVAILABLE = False
    VendorType = None


class GenerateStage(Stage):
    """Generate a synthetic invoice using invoice-gen library.

    This stage:
    1. Creates an InvoiceGenerator for the specified vendor
    2. Generates a synthetic invoice with random but valid data
    3. Stores the invoice_data (ground truth) and tiff_path in context
    """

    name = "generate"

    def __init__(self, output_dir: Path | None = None):
        """Initialize the generate stage.

        Args:
            output_dir: Directory for generated files. If None, uses temp dir.
        """
        self._output_dir = output_dir
        self._temp_dir: TemporaryDirectory | None = None

    def run(self, context: SmokeContext) -> StageResult:
        """Generate a synthetic invoice for the specified vendor."""
        if not INVOICE_GEN_AVAILABLE:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error="invoice-gen library not installed. Run: pip install -e gen/synthetic-invoice-gen",
            )

        # Map vendor string to VendorType enum
        vendor_map = {
            "ubereats": VendorType.UBEREATS,
            "doordash": VendorType.DOORDASH,
            "grubhub": VendorType.GRUBHUB,
            "ifood": VendorType.IFOOD,
            "rappi": VendorType.RAPPI,
        }

        vendor_type = vendor_map.get(context.vendor.lower())
        if not vendor_type:
            return StageResult(
                stage_name=self.name,
                passed=False,
                error=f"Unknown vendor: {context.vendor}. Valid: {list(vendor_map.keys())}",
            )

        # Set up output directory
        if self._output_dir:
            output_path = self._output_dir
        else:
            self._temp_dir = TemporaryDirectory()
            output_path = Path(self._temp_dir.name)

        # Generate the TIFF invoice
        generator = InvoiceGenerator(output_dir=output_path)
        generated = generator.generate_tiff(vendor_type)

        # Convert InvoiceData to dict for ground truth comparison
        invoice_dict = generated.invoice_data.model_dump(mode="json")

        # Store ground truth and file path in context
        context.invoice_data = invoice_dict
        context.tiff_path = generated.tiff_path

        return StageResult(
            stage_name=self.name,
            passed=True,
            data={
                "invoice_id": invoice_dict.get("invoice_id"),
                "vendor": context.vendor,
                "tiff_path": str(generated.tiff_path),
                "total_amount": str(invoice_dict.get("total_amount")),
            },
        )

    def cleanup(self) -> None:
        """Clean up temporary directory if created."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
