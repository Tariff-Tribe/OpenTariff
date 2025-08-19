from datetime import datetime, date, time
from decimal import Decimal
from typing import Self
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator, ValidationInfo

from opentariff.Enums.base_enums import DayOfWeek
from opentariff.Enums.tariff_enums import TariffEnums


class StandingCharge(BaseModel):
    tcr_band: TariffEnums.TCRBand | None = Field(default=None, ge=1, le=4)
    tcrbandtype: TariffEnums.TCRBandType | None = Field(default=None)
    max_consumption: Decimal | None = Field(default=None, gt=0)
    min_consumption: Decimal | None = Field(default=None, ge=0)
    line_loss: Decimal | None = Field(default=None, ge=0)
    standing_charge: Decimal


class Rate(BaseModel):
    """Unified rate model for all rate types"""

    model_config = ConfigDict(frozen=True)

    rate_type: TariffEnums.RateType
    fuel: TariffEnums.Fuel
    unit_rate: Decimal = Field(..., gt=0, lt=100)

    # Fields for time-of-use static rates
    time_from: time | None = None
    time_to: time | None = None
    day_from: DayOfWeek | None = None
    day_to: DayOfWeek | None = None
    month_from: int | None = Field(None, ge=1, le=12)
    month_to: int | None = Field(None, ge=1, le=12)

    # Fields for dynamic rates
    rate_datetime: datetime | None = None

    # Fields for consumption-based rates
    consumption_from: Decimal | None = None
    consumption_to: Decimal | None = None

    # type of use static rates
    consumption_type: TariffEnums.ConsumptionType | None = None

    @field_validator("time_to")
    @classmethod
    def validate_time_to(cls, v: time | None, info: ValidationInfo) -> time | None:
        if v and info.data.get("time_from") and v == info.data["time_from"]:
            raise ValueError("time_to must not equal time_from")
        
        return v

    @field_validator("day_to")
    @classmethod
    def validate_day_to(cls, v: time | None, info: ValidationInfo) -> time | None:
        if v and info.data.get("day_from") and v == info.data["day_from"]:
            raise ValueError("day_to must not equal day_from")
        
        return v

    @field_validator("month_to")
    @classmethod
    def validate_month_to(cls, v: int | None, info: ValidationInfo) -> int | None:
        if v and info.data.get("month_from") and v == info.data["month_from"]:
            raise ValueError("month_to must not equal to month_from")
        return v

    @field_validator("consumption_to")
    @classmethod
    def validate_consumption_to(cls, v: Decimal | None, info: ValidationInfo) -> Decimal| None:
        if (
            v
            and info.data.get("consumption_from")
            and v < info.data["consumption_from"]
        ):
            raise ValueError(
                "consumption_to must be equal to or greater than consumption_from"
            )
        return v

    @model_validator(mode="after")
    def validate_rate_fields(self) -> Self:
        """Validate that required fields are present based on rate type"""
        rate_type = self.rate_type
        required_fields = TariffEnums.RateType.get_required_fields(rate_type)

        if required_fields and not all(
            getattr(self, field, None) is not None for field in required_fields
        ):
            raise ValueError(f"{rate_type} rates require {', '.join(required_fields)}")

        return self


class Tariff(BaseModel):
    """Core tariff information"""

    model_config = ConfigDict(frozen=True)

    dno_region: int = Field(..., ge=10, le=23)
    rate_type: TariffEnums.RateType
    fuel_type: TariffEnums.FuelType
    payment_method: TariffEnums.PaymentMethod
    contract_length_months: int | None = Field(None, gt=0)
    contract_end_date: date | None = None
    on_supply_from: datetime | None = None
    on_supply_to: datetime | None = None
    exit_fee_type: TariffEnums.ExitFeeType | None = None
    exit_fee_value: Decimal | None = Field(None, ge=0)
    supplier_tariff_code: str | None = None
    annual_cost: Decimal | None = None
    standing_charges: list[StandingCharge]
    rates: list[Rate]

    @field_validator("rates")
    @classmethod
    def validate_rates(cls, v: list[Rate], info: ValidationInfo) -> list[Rate]:
        if not v:
            raise ValueError("tariff must have at least one rate")
        if "rate_type" in info.data:
            for rate in v:
                if rate.rate_type != info.data["rate_type"]:
                    raise ValueError("all rates must match tariff rate_type")
        return v

    @field_validator("exit_fee_value")
    @classmethod
    def validate_exit_fee(cls, v: Decimal | None, info: ValidationInfo) -> Decimal | None:
        if v is not None and not info.data.get("exit_fee_type"):
            raise ValueError(
                "exit_fee_type is required when exit_fee_value is provided"
            )
        return v
