"""Calculate the annual cost of a tariff for a given consumption time-series."""

from datetime import time
from decimal import Decimal

from opentariff.Enums.base_enums import DayOfWeek
from opentariff.Enums.tariff_enums import TariffEnums
from opentariff.models.consumption_models import EnergyReading
from opentariff.models.tariff_models import Rate, StandingCharge, Tariff

PENCE_PER_POUND = Decimal("100")

# rate_types with cost calculation logic implemented so far
SUPPORTED_RATE_TYPES = {
    TariffEnums.RateType.SINGLE_RATE,
    TariffEnums.RateType.TIME_OF_USE_STATIC,
}


def calculate_annual_cost(tariff: Tariff, consumption: list[EnergyReading]) -> Decimal:
    """Calculate the cost (in pounds) of a tariff over a consumption time-series.

    The result covers whatever period the time-series spans (the number of
    distinct calendar days present is used to pro-rate standing charges), so
    passing a full year of readings gives an annual cost.
    """
    if not consumption:
        raise ValueError("consumption time-series must not be empty")

    if tariff.rate_type not in SUPPORTED_RATE_TYPES:
        raise NotImplementedError(
            f"annual cost calculation is not implemented for rate_type={tariff.rate_type}"
        )

    total_pence = Decimal("0")

    for fuel in {reading.fuel for reading in consumption}:
        fuel_readings = [reading for reading in consumption if reading.fuel == fuel]
        fuel_rates = [rate for rate in tariff.rates if rate.fuel == fuel]
        fuel_standing_charges = [
            charge for charge in tariff.standing_charges if charge.fuel == fuel
        ]

        if not fuel_rates:
            raise ValueError(f"tariff has no rates for fuel={fuel}")
        if not fuel_standing_charges:
            raise ValueError(f"tariff has no standing charges for fuel={fuel}")

        total_pence += _unit_cost_pence(tariff.rate_type, fuel_rates, fuel_readings)
        total_pence += _standing_charge_cost_pence(fuel_standing_charges, fuel_readings)

    return (total_pence / PENCE_PER_POUND).quantize(Decimal("0.01"))


def _unit_cost_pence(
    rate_type: TariffEnums.RateType,
    rates: list[Rate],
    readings: list[EnergyReading],
) -> Decimal:
    """Sum consumption_kwh * unit_rate (pence/kWh) across a time-series."""

    if rate_type == TariffEnums.RateType.SINGLE_RATE:
        if len(rates) != 1:
            raise ValueError("single_rate tariffs must have exactly one rate per fuel")
        rate = rates[0]
        return sum((reading.consumption_kwh * rate.unit_rate for reading in readings), Decimal("0"))

    if rate_type == TariffEnums.RateType.TIME_OF_USE_STATIC:
        total = Decimal("0")
        for reading in readings:
            rate = _assign_static_tou_rate(rates, reading)
            total += reading.consumption_kwh * rate.unit_rate
        return total

    raise NotImplementedError(
        f"annual cost calculation is not implemented for rate_type={rate_type}"
    )


def _assign_static_tou_rate(rates: list[Rate], reading: EnergyReading) -> Rate:
    """Assign the single time_of_use_static rate whose bands cover a reading's timestamp."""

    matches = [rate for rate in rates if _static_tou_rate_matches(rate, reading)]

    if not matches:
        raise ValueError(f"no time_of_use_static rate matches timestamp {reading.timestamp}")
    if len(matches) > 1:
        raise ValueError(
            f"multiple time_of_use_static rates match timestamp {reading.timestamp}: "
            "overlapping rate bands"
        )

    return matches[0]


def _static_tou_rate_matches(rate: Rate, reading: EnergyReading) -> bool:
    """Match a reading against a static_tou rate's time/day/month bands.

    Rate.validate_static_tou_rate_fields() guarantees each *_from/*_to pair is
    either both set or both None, so a *_to is safe to use once its *_from is checked.
    """
    timestamp = reading.timestamp

    if rate.time_from is not None:
        assert rate.time_to is not None
        if not _time_in_band(timestamp.time(), rate.time_from, rate.time_to):
            return False

    if rate.day_from is not None:
        assert rate.day_to is not None
        if not _day_in_band(DayOfWeek(timestamp.weekday()), rate.day_from, rate.day_to):
            return False

    if rate.month_from is not None:
        assert rate.month_to is not None
        if not _month_in_band(timestamp.month, rate.month_from, rate.month_to):
            return False

    return True


def _time_in_band(t: time, time_from: time, time_to: time) -> bool:
    # midnight as time_to means "end of day" rather than a wraparound band
    if time_to == time(0, 0):
        return t >= time_from
    if time_from <= time_to:
        return time_from <= t < time_to
    return t >= time_from or t < time_to


def _day_in_band(day: DayOfWeek, day_from: DayOfWeek, day_to: DayOfWeek) -> bool:
    if day_from <= day_to:
        return day_from <= day <= day_to
    return day >= day_from or day <= day_to


def _month_in_band(month: int, month_from: int, month_to: int) -> bool:
    if month_from <= month_to:
        return month_from <= month <= month_to
    return month >= month_from or month <= month_to


def _standing_charge_cost_pence(
    standing_charges: list[StandingCharge], readings: list[EnergyReading]
) -> Decimal:
    num_days = len({reading.timestamp.date() for reading in readings})
    total_kwh = sum((reading.consumption_kwh for reading in readings), Decimal("0"))

    applicable_charges = _select_standing_charges(standing_charges, total_kwh)
    daily_rate_pence = sum((charge.standing_charge for charge in applicable_charges), Decimal("0"))

    return daily_rate_pence * num_days


def _select_standing_charges(
    standing_charges: list[StandingCharge], total_kwh: Decimal
) -> list[StandingCharge]:
    """Select the standing charges that apply for a given total consumption.

    Charges without a consumption band always apply. Banded charges (e.g. TCR
    bands) apply only when total_kwh falls within [min_consumption, max_consumption].
    """
    unbanded = [
        charge
        for charge in standing_charges
        if charge.min_consumption is None and charge.max_consumption is None
    ]
    banded = [
        charge
        for charge in standing_charges
        if charge.min_consumption is not None or charge.max_consumption is not None
    ]

    if not banded:
        return unbanded

    matching_bands = [
        charge
        for charge in banded
        if (charge.min_consumption is None or total_kwh >= charge.min_consumption)
        and (charge.max_consumption is None or total_kwh <= charge.max_consumption)
    ]

    if not matching_bands:
        raise ValueError(f"no standing charge band matches total consumption of {total_kwh} kWh")

    return unbanded + matching_bands
