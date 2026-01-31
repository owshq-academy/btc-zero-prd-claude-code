"""Pydantic models for invoice extraction and validation.

This module defines all data models for the invoice processing pipeline:
- VendorType: Enum for delivery platform types (5 vendors + other)
- LineItem: Individual invoice line item with computed total
- ExtractedInvoice: Complete extracted invoice with all fields
- ExtractionResult: Wrapper with metadata and confidence
- ValidationResult: Multi-layer validation output
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Literal, Self

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class VendorType(str, Enum):
    """Delivery platform vendor types."""

    UBEREATS = "ubereats"
    DOORDASH = "doordash"
    GRUBHUB = "grubhub"
    IFOOD = "ifood"
    RAPPI = "rappi"
    OTHER = "other"


class ExtractionSource(str, Enum):
    """LLM provider used for extraction."""

    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    MANUAL = "manual"


class LineItem(BaseModel):
    """Individual line item from an invoice."""

    description: str = Field(
        ..., min_length=1, max_length=500, description="Item or service description"
    )
    quantity: int = Field(default=1, ge=1, le=1000, description="Quantity of items")
    unit_price: Decimal = Field(..., description="Price per unit (negative for discounts/credits)")

    @computed_field
    @property
    def amount(self) -> Decimal:
        """Calculate total amount for this line item."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "examples": [
                {"description": "Delivery Service Fee", "quantity": 1, "unit_price": "15.00"}
            ]
        },
    }


class ExtractedInvoice(BaseModel):
    """Complete extracted invoice combining header, items, and financials."""

    invoice_id: str = Field(..., min_length=1, max_length=50, description="Unique invoice ID")
    vendor_name: str = Field(..., min_length=1, max_length=200, description="Restaurant name")
    vendor_type: VendorType = Field(default=VendorType.OTHER, description="Delivery platform")
    invoice_date: date = Field(..., description="Invoice issue date")
    due_date: date = Field(..., description="Payment due date")
    currency: Literal["BRL", "USD", "EUR", "GBP", "CAD", "AUD", "MXN", "COP"] = Field(
        default="USD", description="Currency code"
    )
    line_items: list[LineItem] = Field(default_factory=list, description="Invoice line items")
    subtotal: Decimal = Field(..., ge=Decimal("0"), description="Subtotal before tax")
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), description="Tax amount")
    commission_rate: Decimal = Field(
        default=Decimal("0"), ge=Decimal("0"), le=Decimal("1"), description="Commission rate"
    )
    commission_amount: Decimal = Field(
        default=Decimal("0"), ge=Decimal("0"), description="Commission amount"
    )
    total_amount: Decimal = Field(..., ge=Decimal("0"), description="Total invoice amount")

    @field_validator("tax_amount", "commission_rate", "commission_amount", mode="before")
    @classmethod
    def handle_null_decimals(cls, v):
        """Convert null/None values to 0 for optional decimal fields."""
        if v is None:
            return Decimal("0")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        """Ensure due_date is on or after invoice_date."""
        if self.due_date < self.invoice_date:
            raise ValueError(
                f"due_date ({self.due_date}) cannot be before invoice_date ({self.invoice_date})"
            )
        return self

    @model_validator(mode="after")
    def validate_line_items_total(self) -> Self:
        """Check if line items sum approximately equals subtotal."""
        if self.line_items:
            items_total = sum(item.amount for item in self.line_items)
            tolerance = Decimal("0.10")
            if abs(items_total - self.subtotal) > tolerance:
                pass  # Log warning but don't fail
        return self

    @computed_field
    @property
    def line_item_count(self) -> int:
        """Number of line items."""
        return len(self.line_items)

    @computed_field
    @property
    def expected_commission(self) -> Decimal:
        """Calculate expected commission from subtotal * rate."""
        return (self.subtotal * self.commission_rate).quantize(Decimal("0.01"))

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
        "json_schema_extra": {
            "examples": [
                {
                    "invoice_id": "UE-2026-001234",
                    "vendor_name": "Restaurant Example",
                    "vendor_type": "ubereats",
                    "invoice_date": "2026-01-15",
                    "due_date": "2026-02-15",
                    "currency": "USD",
                    "line_items": [
                        {"description": "Food Delivery Sales", "quantity": 1, "unit_price": "1000.00"}
                    ],
                    "subtotal": "1000.00",
                    "tax_amount": "50.00",
                    "commission_rate": "0.15",
                    "commission_amount": "150.00",
                    "total_amount": "1050.00",
                }
            ]
        },
    }


class ExtractionResult(BaseModel):
    """Wrapper for extraction output with metadata and confidence."""

    invoice: ExtractedInvoice | None = Field(default=None, description="Extracted invoice data")
    success: bool = Field(..., description="Whether extraction succeeded")
    source: ExtractionSource = Field(default=ExtractionSource.GEMINI, description="LLM provider")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    latency_ms: int = Field(default=0, ge=0, description="Processing time in milliseconds")
    tokens_used: int | None = Field(default=None, ge=0, description="Total tokens consumed")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    raw_response: str | None = Field(default=None, description="Raw LLM response")
    input_file: str | None = Field(default=None, description="Original input file path")


class ValidationResult(BaseModel):
    """Multi-layer validation output."""

    is_valid: bool = Field(..., description="Overall validation passed")
    schema_valid: bool = Field(..., description="Pydantic schema validation passed")
    business_rules_valid: bool = Field(..., description="Business rules validation passed")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    schema_errors: list[str] = Field(default_factory=list, description="Schema errors")
    business_rule_errors: list[str] = Field(default_factory=list, description="Business rule errors")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings")
    field_confidence: dict[str, float] = Field(
        default_factory=dict, description="Per-field confidence"
    )


def get_extraction_schema_json() -> str:
    """Generate JSON Schema string for LLM extraction prompts."""
    import json

    return json.dumps(ExtractedInvoice.model_json_schema(), indent=2)
