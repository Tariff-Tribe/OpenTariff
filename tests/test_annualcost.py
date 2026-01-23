import numpy as np
import pandas as pd
import math
import pytest
from annualcost import calculate_annual_cost_for_tarrif

# ------------------------------------------------------------------
# Fixtures ─ reproducible half‑hourly data and two example tariffs
# ------------------------------------------------------------------

BASE_RATE = 5  # multiplier for random kWh data


@pytest.fixture(scope="module")
def smart_meter_readings():
    """
    Deterministic 1‑year DataFrame of half‑hourly kWh values.
    The index spans 365 consecutive days (365 × 48 = 17 520 half‑hour periods).
    """
    np.random.seed(42)                                   # repeatability
    idx = pd.date_range(
        "2024-01-01",                      # start of the year (non‑leap)
        periods=365 * 48,                   # full year of half‑hours
        freq="30min",
        tz="UTC",
    )
    return pd.DataFrame(
        {"kWh": (np.random.random(len(idx)).round(3) * BASE_RATE)},
        index=idx,
    )


@pytest.fixture(scope="module")
def tou_tariff():
    """
    Static TOU tariff copied (and trimmed) from the brief.
    """
    return {
        "rate_type": "static_tou",
        "unit_rates": [
            {"time_from": "00:00:00", "time_to": "05:00:00", "unit_rate": "30.66"},
            {"time_from": "05:00:00", "time_to": "09:00:00", "unit_rate": "12"},
            {"time_from": "09:00:00", "time_to": "13:00:00", "unit_rate": "30.66"},
            {"time_from": "13:00:00", "time_to": "16:00:00", "unit_rate": "12"},
            {"time_from": "16:00:00", "time_to": "00:00:00", "unit_rate": "30.66"},
        ],
        "standing_charges": [{"value": "52.82"}],        # pence / day
    }


@pytest.fixture(scope="module")
def single_rate_tariff():
    """
    Simple flat‑rate tariff used as a control case.
    """
    return {
        "rate_type": "single_rate",
        "unit_rates": [{"unit_rate": "30.00"}],           # pence / kWh
        "standing_charges": [{"value": "50"}],            # pence / day
    }

# ------------------------------------------------------------------
# Helpers – tiny reference implementations to produce expected £
# ------------------------------------------------------------------

def _annualise(sample_days: int, cost_pence: float) -> float:
    """Scale *cost_pence* from *sample_days* up to a 365‑day year."""
    return cost_pence * (365 / sample_days)


def _calc_expected_tou_cost(df: pd.DataFrame, tariff: dict) -> float:
    """
    Naïve pure‑Python replication of the TOU pricing logic.
    Returns annual cost in pounds.
    """
    import datetime as dt

    # Build (start, end, rate) tuples
    intervals = [
        (
            dt.time.fromisoformat(tr["time_from"]),
            dt.time.fromisoformat(tr["time_to"]),
            float(tr["unit_rate"]),
        )
        for tr in tariff["unit_rates"]
    ]

    def rate_for(ts: pd.Timestamp) -> float:
        t = ts.time()
        for start, end, r in intervals:
            if (start <= end and start <= t < end) or (start > end and (t >= start or t < end)):
                return r
        raise RuntimeError("No rate matched")

    energy_cost_p = sum(kwh * rate_for(ts) for ts, kwh in df.itertuples())
    standing_p = float(tariff["standing_charges"][0]["value"])
    total_p = _annualise(df.index.normalize().nunique(), energy_cost_p) + standing_p * 365
    return total_p / 100  # convert pence → £


def _calc_expected_single_rate_cost(df: pd.DataFrame, tariff: dict) -> float:
    """Annual £ for a flat‑rate tariff."""
    rate_p = float(tariff["unit_rates"][0]["unit_rate"])
    energy_cost_p = df["kWh"].sum() * rate_p
    standing_p = float(tariff["standing_charges"][0]["value"])
    total_p = _annualise(df.index.normalize().nunique(), energy_cost_p) + standing_p * 365
    return total_p / 100

# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "tariff_fixture, expected_fn",
    [
        ("tou_tariff", _calc_expected_tou_cost),
        ("single_rate_tariff", _calc_expected_single_rate_cost),
    ],
)
def test_calculate_annual_costs(tariff_fixture, expected_fn, smart_meter_readings, request):
    """
    Main happy‑path test for both supported rate types.
    """
    tariff = request.getfixturevalue(tariff_fixture)
    expected = expected_fn(smart_meter_readings, tariff)
    actual = calculate_annual_cost_for_tarrif(tariff, smart_meter_readings)

    # Accept either 1 % relative error or £0.01 absolute, whichever is larger
    assert math.isclose(actual, expected, rel_tol=0.01, abs_tol=0.01), (
        f"{tariff['rate_type']} mismatch: expected £{expected:.2f}, got £{actual:.2f}"
    )


def test_unsupported_rate_type_raises(smart_meter_readings):
    """
    The function should reject a tariff whose rate_type it does not know about.
    """
    bogus_tariff = {"rate_type": "seasonal", "unit_rates": [], "standing_charges": []}
    with pytest.raises((ValueError, NotImplementedError)):
        calculate_annual_cost_for_tarrif(bogus_tariff, smart_meter_readings)
