from opentariff.Enums.base_enums import EnumBase


class TariffEnums:
    """Group tariff-related enums"""

    class FuelType(str, EnumBase):
        ELECTRICITY = "electricity"
        GAS = "gas"
        BOTH = "both"

    class Fuel(str, EnumBase):
        ELECTRICITY = "electricity"
        GAS = "gas"

    class RateType(str, EnumBase):
        SINGLE_RATE = "single_rate"
        TIME_OF_USE_STATIC = "time_of_use_static"
        TIME_OF_USE_DYNAMIC = "time_of_use_dynamic"
        DEMAND_TIERED = "demand_tiered"
        TYPE_OF_USE = "type_of_use"
        
        @classmethod
        def get_required_fields(cls, rate_type) -> list[str]:
            """Return a list of the fields required on a rate of rate_type.

            TIME_OF_USE_STATIC rates are handled seperately. Look in the 
            Rate.validate_static_tou_rate_fields() for TIME_OF_USE_STATIC behaviour.
            """
            requirements = {
                cls.SINGLE_RATE: [],
                cls.TIME_OF_USE_DYNAMIC: ["datetime_from", "datetime_to"],
                cls.DEMAND_TIERED: ["consumption_from", "consumption_to"],
                cls.TYPE_OF_USE: ["consumption_type"],
            }
            return requirements.get(rate_type, [])

    class TCRBand(str, EnumBase):
        BAND_1 = "1"
        BAND_2 = "2"
        BAND_3 = "3"
        BAND_4 = "4"

    class ExitFeeType(str, EnumBase):
        FIXED = "fixed"
        PERC_OF_BALANCE = "perc_of_contract_balance"

    class PaymentMethod(str, EnumBase):
        DIRECT_DEBIT = "direct_debit"
        PREPAYMENT = "prepayment"
        CASH_CHEQUE = "cash_cheque"

    class TCRBandType(str, EnumBase):
        line_loss = "line_loss"
        consumption = "consumption"

    class ConsumptionType(str, EnumBase):
        ELECTRIC_VEHICLE = "electric_vehicle"
        HEAT_PUMP = "heat_pump"
        ANY = "any"

    class RateDirection(str, EnumBase):
        IMPORT = "import"
        EXPORT = "export"
