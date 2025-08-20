import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from opentariff.models.product_models import Product
from opentariff.Enums.product_enums import ProductEnums
from opentariff.models.tariff_models import Rate
from opentariff.Enums.tariff_enums import TariffEnums


def test_validate_rate_type():
    """Test the field validator for rate_type works correctly"""
    
    # Test 1: Static tou rate with time_from and time_to
    rate_dict = {
        "rate_type": TariffEnums.RateType.TIME_OF_USE_STATIC,
        "fuel": "electricity",
        "unit_rate": 0.15,
        "time_from": "00:00",
        "time_to": "06:00",
    }
    static_tou_rate = Rate.model_validate(rate_dict)
    assert static_tou_rate.rate_type == "time_of_use_static"

    # Now remove the time_to and check for validation error
    rate_dict.pop("time_to")
    with pytest.raises(ValidationError) as exc_info:
        Rate.model_validate(rate_dict)

    # Test 2: Dynamic rate with rate_datetime
    rate_dict = {
        "rate_type": TariffEnums.RateType.TIME_OF_USE_DYNAMIC,
        "fuel": "electricity",
        "unit_rate": 0.15,
        "datetime_from": datetime.now() - timedelta(hours=0.5),
        "datetime_to": datetime.now(),
    }
    dynamic_rate = Rate.model_validate(rate_dict)
    assert dynamic_rate.rate_type == "time_of_use_dynamic"
    

    # Now remove the datetime_from and check for validation error
    rate_dict.pop("datetime_from")
    with pytest.raises(ValidationError) as exc_info:
        Rate.model_validate(rate_dict)

    assert f"{rate_dict['rate_type']} rates require" in str(exc_info.value)

    # Test 3: Consumption-based rate with consumption_from and consumption_to
    rate_dict = {
        "rate_type": TariffEnums.RateType.DEMAND_TIERED,
        "fuel": "electricity",
        "unit_rate": 0.15,
        "consumption_from": 100,
        "consumption_to": 200,
    }
    consumption_rate = Rate.model_validate(rate_dict)
    assert consumption_rate.rate_type == "demand_tiered"

    assert consumption_rate.consumption_from == 100
    assert consumption_rate.consumption_to == 200

    # Now remove the consumption_to and check for validation error
    rate_dict.pop("consumption_to")
    with pytest.raises(ValidationError) as exc_info:
        Rate.model_validate(rate_dict)

    # Test 4: Type of use rate with consumption_type
    rate_dict = {
        "rate_type": TariffEnums.RateType.TYPE_OF_USE,
        "fuel": "electricity",
        "unit_rate": 0.15,
        "consumption_type": TariffEnums.ConsumptionType.ELECTRIC_VEHICLE,
    }
    type_of_use_rate = Rate.model_validate(rate_dict)
    assert type_of_use_rate.rate_type == "type_of_use"

    # Now remove the consumption_type and check for validation error
    rate_dict.pop("consumption_type")
    with pytest.raises(ValidationError) as exc_info:
        Rate.model_validate(rate_dict)
        
    assert f"{rate_dict['rate_type']} rates require" in str(exc_info.value)
    