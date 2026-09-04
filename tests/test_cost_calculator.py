import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from opentariff.cost_calculator import calculate_annual_cost
from opentariff.Enums.tariff_enums import TariffEnums
from opentariff.models.consumption_models import EnergyReading
from opentariff.models.tariff_models import Rate, StandingCharge, Tariff


def _half_hourly_consumption(
    num_days: int, kwh_per_interval: Decimal, start: datetime = datetime(2025, 1, 1)
) -> list[EnergyReading]:
    """Mock a half-hourly consumption time-series of constant usage."""
    num_intervals = num_days * 48
    return [
        EnergyReading(
            timestamp=start + timedelta(minutes=30 * i),
            consumption_kwh=kwh_per_interval,
        )
        for i in range(num_intervals)
    ]


def _single_rate_tariff(unit_rate: Decimal, standing_charge: Decimal) -> Tariff:
    return Tariff(
        dno_region=16,
        rate_type=TariffEnums.RateType.SINGLE_RATE,
        fuel_type=TariffEnums.FuelType.ELECTRICITY,
        payment_method=TariffEnums.PaymentMethod.DIRECT_DEBIT,
        rates=[
            Rate(
                rate_type=TariffEnums.RateType.SINGLE_RATE,
                fuel=TariffEnums.Fuel.ELECTRICITY,
                unit_rate=unit_rate,
            )
        ],
        standing_charges=[
            StandingCharge(standing_charge=standing_charge, fuel=TariffEnums.Fuel.ELECTRICITY)
        ],
    )


def _good_energy_heat_pump_tariff() -> Tariff:
    """Recreate the example static_tou tariff from the ticket, using the current schema.

    Off-peak (12p/kWh) 05:00-09:00 and 13:00-16:00, on-peak (30.66p/kWh) the rest.
    Standing charge is 52.82p/day.
    """
    off_peak_bands = [("05:00:00", "09:00:00"), ("13:00:00", "16:00:00")]
    on_peak_bands = [("00:00:00", "05:00:00"), ("09:00:00", "13:00:00"), ("16:00:00", "00:00:00")]

    rates = [
        Rate(
            rate_type=TariffEnums.RateType.TIME_OF_USE_STATIC,
            fuel=TariffEnums.Fuel.ELECTRICITY,
            unit_rate=Decimal("12"),
            time_from=time_from,
            time_to=time_to,
        )
        for time_from, time_to in off_peak_bands
    ] + [
        Rate(
            rate_type=TariffEnums.RateType.TIME_OF_USE_STATIC,
            fuel=TariffEnums.Fuel.ELECTRICITY,
            unit_rate=Decimal("30.66"),
            time_from=time_from,
            time_to=time_to,
        )
        for time_from, time_to in on_peak_bands
    ]

    return Tariff(
        dno_region=16,
        rate_type=TariffEnums.RateType.TIME_OF_USE_STATIC,
        fuel_type=TariffEnums.FuelType.ELECTRICITY,
        payment_method=TariffEnums.PaymentMethod.DIRECT_DEBIT,
        rates=rates,
        standing_charges=[
            StandingCharge(standing_charge=Decimal("52.82"), fuel=TariffEnums.Fuel.ELECTRICITY)
        ],
    )


def test_calculate_annual_cost_single_rate():
    """1 day of half-hourly readings at 1kWh/interval (48kWh/day), 20p/kWh, 50p/day standing charge."""
    tariff = _single_rate_tariff(unit_rate=Decimal("20"), standing_charge=Decimal("50"))
    consumption = _half_hourly_consumption(num_days=1, kwh_per_interval=Decimal("1"))

    cost = calculate_annual_cost(tariff, consumption)

    # unit cost: 48 kWh * 20p = 960p, standing charge: 50p * 1 day = 50p, total = 1010p = £10.10
    assert cost == Decimal("10.10")


def test_calculate_annual_cost_single_rate_scales_with_days():
    tariff = _single_rate_tariff(unit_rate=Decimal("20"), standing_charge=Decimal("50"))
    consumption = _half_hourly_consumption(num_days=365, kwh_per_interval=Decimal("1"))

    cost = calculate_annual_cost(tariff, consumption)

    # unit cost: 365 * 48 kWh * 20p = 350400p, standing charge: 50p * 365 = 18250p
    assert cost == Decimal("3686.50")


def test_calculate_annual_cost_time_of_use_static():
    tariff = _good_energy_heat_pump_tariff()
    consumption = _half_hourly_consumption(num_days=1, kwh_per_interval=Decimal("1"))

    cost = calculate_annual_cost(tariff, consumption)

    # off-peak: 8 (05-09) + 6 (13-16) = 14 intervals @ 12p = 168p
    # on-peak: 48 - 14 = 34 intervals @ 30.66p = 1042.44p
    # standing charge: 52.82p
    # total = 168 + 1042.44 + 52.82 = 1263.26p = £12.63
    assert cost == Decimal("12.63")


def test_calculate_annual_cost_time_of_use_static_midnight_boundary():
    """A reading exactly at midnight should fall in the 00:00-05:00 band, not 16:00-00:00."""
    tariff = _good_energy_heat_pump_tariff()
    consumption = [
        EnergyReading(timestamp=datetime(2025, 1, 1, 0, 0), consumption_kwh=Decimal("1")),
    ]

    cost = calculate_annual_cost(tariff, consumption)

    # unit cost: 1 kWh * 30.66p = 30.66p, standing charge: 52.82p * 1 day, total = 83.48p = £0.83
    assert cost == Decimal("0.83")


def test_calculate_annual_cost_empty_consumption_raises():
    tariff = _single_rate_tariff(unit_rate=Decimal("20"), standing_charge=Decimal("50"))

    with pytest.raises(ValueError, match="must not be empty"):
        calculate_annual_cost(tariff, [])


def test_calculate_annual_cost_unsupported_rate_type_raises():
    tariff = Tariff(
        dno_region=16,
        rate_type=TariffEnums.RateType.TIME_OF_USE_DYNAMIC,
        fuel_type=TariffEnums.FuelType.ELECTRICITY,
        payment_method=TariffEnums.PaymentMethod.DIRECT_DEBIT,
        rates=[
            Rate(
                rate_type=TariffEnums.RateType.TIME_OF_USE_DYNAMIC,
                fuel=TariffEnums.Fuel.ELECTRICITY,
                unit_rate=Decimal("20"),
                datetime_from=datetime(2025, 1, 1),
                datetime_to=datetime(2025, 1, 1, 0, 30),
            )
        ],
        standing_charges=[
            StandingCharge(standing_charge=Decimal("50"), fuel=TariffEnums.Fuel.ELECTRICITY)
        ],
    )
    consumption = _half_hourly_consumption(num_days=1, kwh_per_interval=Decimal("1"))

    with pytest.raises(NotImplementedError):
        calculate_annual_cost(tariff, consumption)


def test_calculate_annual_cost_no_matching_fuel_raises():
    tariff = _single_rate_tariff(unit_rate=Decimal("20"), standing_charge=Decimal("50"))
    consumption = [
        EnergyReading(
            timestamp=datetime(2025, 1, 1),
            consumption_kwh=Decimal("1"),
            fuel=TariffEnums.Fuel.GAS,
        )
    ]

    with pytest.raises(ValueError, match="no rates for fuel"):
        calculate_annual_cost(tariff, consumption)


def test_calculate_annual_cost_standing_charge_band_selection():
    """Banded standing charges (e.g. TCR bands) should be selected by total consumption."""
    tariff = Tariff(
        dno_region=16,
        rate_type=TariffEnums.RateType.SINGLE_RATE,
        fuel_type=TariffEnums.FuelType.ELECTRICITY,
        payment_method=TariffEnums.PaymentMethod.DIRECT_DEBIT,
        rates=[
            Rate(
                rate_type=TariffEnums.RateType.SINGLE_RATE,
                fuel=TariffEnums.Fuel.ELECTRICITY,
                unit_rate=Decimal("20"),
            )
        ],
        standing_charges=[
            StandingCharge(
                standing_charge=Decimal("30"),
                fuel=TariffEnums.Fuel.ELECTRICITY,
                min_consumption=Decimal("0"),
                max_consumption=Decimal("10"),
            ),
            StandingCharge(
                standing_charge=Decimal("60"),
                fuel=TariffEnums.Fuel.ELECTRICITY,
                min_consumption=Decimal("10.01"),
                max_consumption=Decimal("1000"),
            ),
        ],
    )
    # 1 day at 1kWh/interval * 48 intervals = 48 kWh -> falls in the second band
    consumption = _half_hourly_consumption(num_days=1, kwh_per_interval=Decimal("1"))

    cost = calculate_annual_cost(tariff, consumption)

    # unit cost: 48 kWh * 20p = 960p, standing charge: 60p * 1 day = 60p, total = 1020p = £10.20
    assert cost == Decimal("10.20")
