from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from opentariff.Enums.tariff_enums import TariffEnums


class EnergyReading(BaseModel):
    """A single point in a consumption time-series.

    Represents the energy consumed in the interval ending at `timestamp`
    (e.g. a half-hourly meter reading), in kWh.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    consumption_kwh: Decimal = Field(..., ge=0)
    fuel: TariffEnums.Fuel = TariffEnums.Fuel.ELECTRICITY
