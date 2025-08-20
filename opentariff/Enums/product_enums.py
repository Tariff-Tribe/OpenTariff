from opentariff.Enums.base_enums import EnumBase


class ProductEnums:
    """Group product-related enums"""

    class TariffType(str, EnumBase):
        FIXED = "fixed"
        VARIABLE = "variable"

    class OtherProductsType(str, EnumBase):
        UTILITY = "utility"
        PHYSICAL_ASSET = "physical_asset"

    class Direction(str, EnumBase):
        IMPORT = "import"
        EXPORT = "export"
        BI_DIRECTIONAL = "bi_directional"
