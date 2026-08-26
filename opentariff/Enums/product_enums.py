from opentariff.Enums.base_enums import EnumBase


class ProductEnums:
    """Group product-related enums"""

    class TariffType(str, EnumBase):
        FIXED = "fixed"
        VARIABLE = "variable"

    class BundledWithType(str, EnumBase):
        """What a bundled product is bundled with: an asset
        (solar panels, battery) or a service (boiler care insurance)."""

        ASSET = "asset"
        SERVICE = "service"

    class Direction(str, EnumBase):
        IMPORT = "import"
        EXPORT = "export"
        BI_DIRECTIONAL = "bi_directional"
