import pandas as pd
import numpy as np
import pprint

def calc_annual_cost_tou(tariff: dict, energy_df: pd.DataFrame):
    # TODO we could turn this tarrif parser into a useful class
    band_edges = [0] # seconds after midnight
    rates = []

    # make sure bands are processed in chronological order
    bands = sorted(tariff["unit_rates"],
                key=lambda b: b["time_from"])
    
    for rate_dict in bands:
        rates.append(rate_dict["unit_rate"]) # p/kWh

        h, m, s = map(int, rate_dict["time_to"].split(":"))
        band_edges.append(h * 3600 + m * 60 + s)

    # convert 00:00 to 24:00 for integer logic
    if band_edges[-1] == 0:
        band_edges[-1] = 24 * 3600
    
    # ensure we end exactly at 24:00:00 (86 400 s)
    if band_edges[-1] != 24 * 3600:
        band_edges.append(24 * 3600)

    # Calculate the seconds since midnight for every row (vectorised)
    secs = (energy_df.index.hour*3600
            + energy_df.index.minute*60
            + energy_df.index.second).to_numpy()
    
    # print(band_edges)
    # find the index in band_edges where each timestamp would have been
    # subtract 1 since if it is in the 1st place we need to use rate[0]
    band_indexes = np.searchsorted(band_edges, secs, side="right") - 1

    # print(band_indexes)
    rates = np.asarray(rates, dtype=float) /100 # convert to Pounds/kWh
    energy_df["unit_rate"] = rates[band_indexes] # this is now a vector of each timestamps rate
    
    # calculate cost
    energy_df["cost_pounds"] = energy_df["kWh"] * energy_df["unit_rate"]
    usage_cost = energy_df["cost_pounds"].sum()

    standing_charge = np.float64(tariff["standing_charges"][0]["value"]) * 365/100
    
    return usage_cost + standing_charge

def calc_annual_cost_single_rate(tariff: dict, energy_df: pd.DataFrame):
    kWh_used = energy_df["kWh"].sum()
    rate = np.float64(tariff["unit_rates"][0]["unit_rate"])
    usage_cost = kWh_used*rate/100

    standing_rate = np.float64(tariff["standing_charges"][0]["value"])
    standing_cost = standing_rate * 365/100 # TODO decide how to account for leap years etc

    return usage_cost + standing_cost


def calculate_annual_cost_for_tarrif(tariff: dict, energy_df: pd.DataFrame):
    """Calculate the annual cost of the tarriff given a year worth of energy timeseries data.

    Args:
        energy_df (pd.DataFrame): Timeseries with timestamps and kWh for one year.
        tariff (dict): The tarrif as a dict.
    """
    if tariff["rate_type"] == "single_rate":
        return calc_annual_cost_single_rate(tariff, energy_df)
    elif tariff["rate_type"] == "static_tou":
        return calc_annual_cost_tou(tariff, energy_df)
    else:
        raise NotImplementedError("Invalid rate_type, only single_rate and static_tou implimented.")

    
    


if __name__ == "__main__":
    import tests.test_annualcost as test_annualcost
    t = test_annualcost.tou_tariff()
    df = test_annualcost.smart_meter_readings()
    calculate_annual_cost_for_tarrif(df, t)