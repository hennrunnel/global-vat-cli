from pydantic import BaseModel, Field


class DataRecord(BaseModel):
    region_code: str = Field(..., description="e.g., EU-AT, UK-GB, CA-ON")
    country_iso: str = Field(..., description="ISO 3166-1 alpha-2")
    country_name: str
    jurisdiction_level: str
    jurisdiction_name: str
    tax_authority_name: str
    tax_authority_url: str
    tax_type: str  # VAT, GST, HST, PST
    rate_type: str  # Standard, Reduced, Zero
    rate_percent: float
    category_source_label: str
    category_ui_label: str
    primary_source_url: str
    last_validated_utc: str


