from opentariff.Enums.base_enums import EnumBase


class ProductEnums:
    """Group product-related enums"""

    class TariffType(str, EnumBase):
        FIXED = "fixed"
        VARIABLE = "variable"

    class OtherProductsType(str, EnumBase):
        UTILITY = "utility"
        PHYSICAL_ASSET = "physical_asset"

    class Tracker(str, EnumBase):
        non_commodity = "non_commodity"
        day_ahead = "day_ahead"
        intraday = "intraday"
        price_cap = "price_cap"

