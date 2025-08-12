from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from opentariff.Enums.product_enums import ProductEnums


class BundledProduct(BaseModel):
    """Represents additional products that can be bundled with tariffs"""

    model_config = ConfigDict(frozen=True)

    type: ProductEnums.OtherProductsType
    name: str
    description: Optional[str] = None


class Product(BaseModel):
    """Core product information"""

    model_config = ConfigDict(frozen=True)

    name: str
    domestic: bool
    description: Optional[str] = None
    type: ProductEnums.TariffType
    available_from: datetime
    available_to: Optional[datetime] = None
    supplier_name: Optional[str] = None

    # Optional Attributes
    smart: Optional[bool] = None
    ev: Optional[bool] = None
    exclusive: Optional[bool] = None
    retention: Optional[bool] = None
    acquisition: Optional[bool] = None
    collective_switch: Optional[bool] = None
    green_percentage: Optional[float] = Field(None, ge=0, le=100)
    bundled_products: Optional[list[BundledProduct]] = None
    tracker: ProductEnums.Tracker | None = None
    creditTracker: bool | None = None

    @field_validator("available_to")
    @classmethod
    def validate_available_to(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v and info.data.get("available_from") and v <= info.data["available_from"]:
            raise ValueError("available_to must be after available_from")
        return v
