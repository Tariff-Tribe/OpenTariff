import json
import pandas as pd
from datetime import datetime

def calculate_annual_cost(tariff, energy_data):
    df = pd.DataFrame(energy_data)
    
    df['timestamp'] = pd.to_datetime(df['reading_timestamp'])
    df['time'] = df['timestamp'].dt.time
    
    daily_standing_charge = float(tariff['standing_charges'][0]['value']) / 100
    
    rate_periods = []
    for rate in tariff['unit_rates']:
        start = datetime.strptime(rate['time_from'], '%H:%M:%S').time()
        end = datetime.strptime(rate['time_to'], '%H:%M:%S').time()
        rate_periods.append({
            'start': start,
            'end': end,
            'rate': float(rate['unit_rate']) / 100
        })
    
    def get_rate_for_time(t):
        for period in rate_periods:
            if period['start'] <= period['end']:
                if period['start'] <= t <= period['end']:
                    return period['rate']
            else:
                if t >= period['start'] or t <= period['end']:
                    return period['rate']
        return max(p['rate'] for p in rate_periods)
    
    df['unit_rate'] = df['time'].apply(get_rate_for_time)
    df['cost'] = df['kwh_value'] * df['unit_rate']
    
    total_unit_cost = df['cost'].sum()
    total_days = (df['timestamp'].max() - df['timestamp'].min()).days + 1
    total_standing_charge = daily_standing_charge * total_days
    
    total_cost = total_unit_cost + total_standing_charge
    return round(total_cost, 2)



if __name__ == "__main__":
    example_tariff = {
        "supplier_name": "Good Energy",
        "supplier_id": "08920056-69ce-4fd4-9a65-cee2c351a73d",
        "name": "Good Energy Heat Pump",
        "tariff_id": "3373791a-3a1e-46c0-bfc8-3e9c731abf0e",
        "available_from": "2025-01-04T00:00:00",
        "available_to": None,
        "rate_type": "static_tou",
        "dno_region_id": 7,
        "dno_region": "Norweb",
        "description": "Good Energy heat pump tariffs are fixed for 12 months...",
        "unit_rates": [
            {
                "time_to": "05:00:00",
                "added_ts": "2025-06-01T23:30:32.864670",
                "day_to": None,
                "month_to": None,
                "unit_rate_id": 534,
                "tariff_id": "3373791a-3a1e-46c0-bfc8-3e9c731abf0e",
                "unit_rate": "30.66",
                "time_from": "00:00:00",
                "day_from": None,
                "month_from": None,
                "rate_datetime": None,
                "rate_type": "static_tou"
            },
            {
                "time_to": "09:00:00",
                "added_ts": "2025-06-01T23:30:32.864670",
                "day_to": None,
                "month_to": None,
                "unit_rate_id": 535,
                "tariff_id": "3373791a-3a1e-46c0-bfc8-3e9c731abf0e",
                "unit_rate": "12",
                "time_from": "05:00:00",
                "day_from": None,
                "month_from": None,
                "rate_datetime": None,
                "rate_type": "static_tou"
            },
            {
                "time_to": "13:00:00",
                "added_ts": "2025-06-01T23:30:32.864670",
                "day_to": None,
                "month_to": None,
                "unit_rate_id": 536,
                "tariff_id": "3373791a-3a1e-46c0-bfc8-3e9c731abf0e",
                "unit_rate": "30.66",
                "time_from": "09:00:00",
                "day_from": None,
                "month_from": None,
                "rate_datetime": None,
                "rate_type": "static_tou"
            },
            {
                "time_to": "16:00:00",
                "added_ts": "2025-06-01T23:30:32.864670",
                "day_to": None,
                "month_to": None,
                "unit_rate_id": 537,
                "tariff_id": "3373791a-3a1e-46c0-bfc8-3e9c731abf0e",
                "unit_rate": "12",
                "time_from": "13:00:00",
                "day_from": None,
                "month_from": None,
                "rate_datetime": None,
                "rate_type": "static_tou"
            },
            {
                "time_to": "00:00:00",
                "added_ts": "2025-06-01T23:30:32.864670",
                "day_to": None,
                "month_to": None,
                "unit_rate_id": 538,
                "tariff_id": "3373791a-3a1e-46c0-bfc8-3e9c731abf0e",
                "unit_rate": "30.66",
                "time_from": "16:00:00",
                "day_from": None,
                "month_from": None,
                "rate_datetime": None,
                "rate_type": "static_tou"
            }
        ],
    "standing_charges": [
            {
                "added_ts": "2025-06-01T23:30:32.864670",
                "max_consumption": None,
                "line_loss": None,
                "standing_charge_id": 534,
                "tcrbandtype": None,
                "tcr_band": None,
                "min_consumption": None,
                "value": "52.82",
                "tariff_id": "3373791a-3a1e-46c0-bfc8-3e9c731abf0e"
            }
        ]
    }

    energy_data = [
        {
            "reading_timestamp": "2025-01-01T22:00:00+00:00",
            "kwh_value": 2.0
        },
        {
            "reading_timestamp": "2025-01-02T04:00:00+00:00",
            "kwh_value": 1.5
        },
        {
            "reading_timestamp": "2025-01-01T12:00:00+00:00",
            "kwh_value": 3.0
        }
    ]

    total_cost = calculate_annual_cost(example_tariff, energy_data)
    print(f"Total annual cost: {total_cost}")
