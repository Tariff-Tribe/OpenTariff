from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo

from opentariff.Enums.product_enums import ProductEnums


class BundledProduct(BaseModel):
    """Represents additional products that can be bundled with tariffs"""

    model_config = ConfigDict(frozen=True)

    type: ProductEnums.BundledWithType
    name: str
    description: str | None = None


class Product(BaseModel):
    """Core product information"""

    model_config = ConfigDict(frozen=True)

    name: str
    domestic: bool
    description: str | None = None
    type: ProductEnums.TariffType
    available_from: datetime
    available_to: datetime | None = None
    supplier_name: str | None = None
    direction: ProductEnums.Direction = ProductEnums.Direction.IMPORT

    # Optional Attributes
    smart: bool | None = None
    ev: bool | None = None
    exclusive: bool | None = None
    retention: bool | None = None
    acquisition: bool | None = None
    collective_switch: bool | None = None
    green_percentage: float | None = Field(None, ge=0, le=100)
    bundled_products: list[BundledProduct] | None = None

    @field_validator("available_to")
    @classmethod
    def validate_available_to(cls, v: datetime | None, info: ValidationInfo) -> datetime | None:
        if v and info.data.get("available_from") and v <= info.data["available_from"]:
            raise ValueError("available_to must be after available_from")
        return v
