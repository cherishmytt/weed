SYNC_AREA_PRESETS = {
    "world": {
        "label": "全球",
        "bbox": "world",
    },
    "seasia": {
        "label": "东南亚",
        "bbox": "90,-15,150,30",
    },
    "australia": {
        "label": "澳大利亚",
        "bbox": "110,-45,155,-10",
    },
    "south_america": {
        "label": "南美",
        "bbox": "-85,-57,-32,14",
    },
}

SYNC_SOURCE_PRESETS = {
    "VIIRS_NOAA20_NRT": {
        "label": "NOAA-20",
    },
    "VIIRS_SNPP_NRT": {
        "label": "S-NPP",
    },
}

DEFAULT_SYNC_TARGETS = [
    {"area_label": area_label, "source_product": source_product}
    for area_label in SYNC_AREA_PRESETS
    for source_product in SYNC_SOURCE_PRESETS
]


def resolve_area_preset(area_label: str) -> dict:
    return SYNC_AREA_PRESETS[area_label]


def resolve_source_preset(source_product: str) -> dict:
    return SYNC_SOURCE_PRESETS[source_product]
