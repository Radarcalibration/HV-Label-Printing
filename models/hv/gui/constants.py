VARIANT_OPTIONS = ["12P", "16P", "24P", "27P", "SW_LH_8P"] #1

VARIANT_TO_MODEL_BY_CELL_MFR = {
    "Ten Power": {
        "12P": "VX156590",
        "16P": "VX156600",
        "24P": "VX156610",
        "27P": "VX155480",
        "SW_LH_8P": "BP00000140" #2
    },
    "BAK": {
        "12P": "VQ150040",
        "16P": "VQ150050",
        "24P": "VQ150060",
        "27P": "VQ150070",
        "SW_LH_8P": "BP00000140" #3
    },
}

REESS_BY_MODEL_BY_CELL_MFR = {
    "Ten Power": {
        "VX155480": "VX155800", #27p
        "VX156610": "VX156060", #24p
        "VX156600": "VX156070", #16p
        "VX156590": "VX156080", #12p
        "BP00000140": "BP00000129", #SW_LH_8P
    },
    "BAK": {
        "VQ150040": "VQ150000", #12P
        "VQ150070": "VQ150030", #27P
        "VQ150060": "VQ150020", #24P
        "VQ150050": "VQ150010", #16P
        "BP00000140": "BP00000129", #SW_LH_8P
    },
}

# Keep the original single-manufacturer maps available for existing callers.
VARIANT_TO_MODEL = VARIANT_TO_MODEL_BY_CELL_MFR["BAK"]
MODEL_TO_VARIANT = {model: variant for variant, model in VARIANT_TO_MODEL.items()}
REESS_BY_MODEL = REESS_BY_MODEL_BY_CELL_MFR["BAK"]
REESS_TO_VARIANT = {}
for _cell_mfr, _models in VARIANT_TO_MODEL_BY_CELL_MFR.items():
    _reess_by_model = REESS_BY_MODEL_BY_CELL_MFR[_cell_mfr]
    for _variant, _model in _models.items():
        REESS_TO_VARIANT[_reess_by_model[_model]] = _variant
CELL_MFR_BY_REESS = {
    reess: cell_mfr
    for cell_mfr, model_map in REESS_BY_MODEL_BY_CELL_MFR.items()
    for reess in model_map.values()
}

VARIANT_PARAMS = {
    "low voltage": {},
    "high voltage": {
        "12P": {
            "rated_capacity": "6 kWh",
            "max_voltage": "116.2 V",
            "srb_code": "SRB05",
            "tac_number": "AS8318",
            "emark": "E11*136R01/00*0113*00",
        },
        "16P": {
            "rated_capacity": "8.1 kWh",
            "max_voltage": "116.2 V",
            "srb_code": "SRB07",
            "tac_number": "AS8317",
            "emark": "E11*136R01/00*0112*00",
        },
        "24P": {
            "rated_capacity": "12.1 kWh",
            "max_voltage": "116.2 V",
            "srb_code": "SRB10",
            "tac_number": "AS8316",
            "emark": "E11*136R01/00*0110*00",
        },
        "27P": {
            "rated_capacity": "13.6 kWh",
            "max_voltage": "116.2 V",
            "srb_code": "SRB12",
            "tac_number": "AS8315",
            "emark": "E11*136R01/00*0111*00",
        },
    },
    "shockwave": {
        "SW_LH_8P": {
            "rated_capacity": "4 kWh",
            "max_voltage": "116.2 V",
            "srb_code": "SRB04",
            "tac_number": "XXXXXX",
            "emark": "E11*136R01/00*0119*00",
        },
    },
    "tesseract": {},
}


MODULE_VARIANT_CODES = {
    "12P": "C",
    "16P": "D",
    "24P": "E",
    "27P": "F",
    "SW_LH_8P": "G",    #9
    # "SW_RH_8P": "H",
    # "SW_LH_10P": "I",
    # "SW_RH_10P": "J",
    # "TS_8P": "K",
    # "TS_10P": "L",
}
VARIANT_BY_CODE = {v: k for k, v in MODULE_VARIANT_CODES.items()}

GROUP_CODES = {f"G{i}": str(i) for i in range(1, 4)}
GROUP_BY_CODE = {v: k for k, v in GROUP_CODES.items()}
GROUP_OPTIONS = [f"G{i}" for i in range(1, 4)]

CELL_MFR_CODES = {
    "Molical":   "1",
    "Samsung":   "2",
    "BAK":       "3",
    "EVE":       "4",
    "LG":        "5",
    "Ten Power": "6",
}
CELL_MFR_BY_CODE = {v: k for k, v in CELL_MFR_CODES.items()}
CELL_MFR_OPTIONS = list(CELL_MFR_CODES.keys())

PLANT_CODES_HV = {
    "Jigani": ("1"),
    "Domlur": ("2"),
    "Plant_c": ("3"),
}
PLANT_BY_CODE_HV = {
    "1": "Jigani",
    "A": "Jigani",

    "2": "Domlur",
    "B": "Domlur",

    "3": "Plant_c",
    "C": "Plant_c",
}
PLANT_OPTIONS = list(PLANT_CODES_HV.keys())

LINE_CODES = {"Line 1": "1", "Line 2": "2", "Line 3": "3"}
LINE_OPTIONS = list(LINE_CODES.keys())

SHIFT_CODES_HV = {"Shift 1": "1", "Shift 2": "2", "Shift 3": "3"}
SHIFT_OPTIONS = list(SHIFT_CODES_HV.keys())

MONTH_CODES = {
    1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F",
    7: "G", 8: "H", 9: "I", 10: "J", 11: "K", 12: "L",
}
MONTH_BY_CODE = {v: k for k, v in MONTH_CODES.items()}

def year_code(year: int) -> str:
    return str(year % 100).zfill(2)

def year_from_code(code: str) -> int:
    return 2000 + int(code)

CATEGORY_OPTIONS = ["Domestic", "Export"]

RANGE_CODES = {variant: str(i) for i, variant in enumerate(VARIANT_OPTIONS, start=1)}
RANGE_OPTIONS = list(RANGE_CODES.values())


def get_range(variant: str) -> str:
    return RANGE_CODES.get(variant.strip(), "")

BATTERY_PARAM_ROWS = [
    ("Rated Capacity", "rated_capacity", False),
    ("Max Voltage",     "max_voltage",    False),
    ("Model Number",    "model_number",   False),
    ("TAC Number",      "tac_number",     False),
    ("Serial Number",   "serial_number",  False),
]


def variants_for_category(category: str) -> list[str]:
    if category.strip().lower() == "export":
        return [
            variant for variant in VARIANT_OPTIONS
            if get_variant_params(variant).get("emark", "NA") != "NA"
        ]
    return list(VARIANT_OPTIONS)


def get_variant_params(variant: str) -> dict[str, str]:
    variant = variant.strip()
    for model_params in VARIANT_PARAMS.values():
        if variant in model_params:
            return model_params[variant]
    return {}


def format_pack_qr_data(*, variant: str, serial_number: str, cell_mfr: str) -> str:
    reess = get_type_of_reess(variant, cell_mfr)
    return f"{reess}:{serial_number.strip()}"


def get_model_number(variant: str, cell_mfr: str) -> str:
    return VARIANT_TO_MODEL_BY_CELL_MFR.get(cell_mfr.strip(), {}).get(variant.strip(), "")


def get_part_number(variant: str, cell_mfr: str) -> str:
    return get_model_number(variant, cell_mfr)


def get_full_model_number(variant: str, revision: str, cell_mfr: str) -> str:
    part = get_part_number(variant, cell_mfr)
    revision = (revision or "").strip().upper()
    return f"{part}-{revision}" if part and revision else part


def get_type_of_reess(variant: str, cell_mfr: str) -> str:
    model = get_model_number(variant, cell_mfr)
    return REESS_BY_MODEL_BY_CELL_MFR.get(cell_mfr.strip(), {}).get(model, "NA")


def get_cell_mfr_from_reess(reess: str) -> str | None:
    return CELL_MFR_BY_REESS.get(reess.strip().upper())


def get_variant_from_reess(reess: str) -> str | None:
    return REESS_TO_VARIANT.get(reess.strip().upper())


def get_tac_number(variant: str) -> str:
    return get_variant_params(variant).get("tac_number", "NA")


def get_emark(variant: str) -> str:
    return get_variant_params(variant).get("emark", "NA")


def get_rated_capacity(variant: str) -> str:
    return get_variant_params(variant).get("rated_capacity", "NA")


def get_max_voltage(variant: str) -> str:
    return get_variant_params(variant).get("max_voltage", "NA")


def get_emark_res_code(variant: str) -> str:
    import re as _re
    raw = get_emark(variant)
    match = _re.match(r"E(\d+)\*(\d+)R(\d+)/\d+\*(\d+)\*\d+", raw) #E11*136R01/00*0112*00
    if not match: 
        return "NA" 
    _e_num, prefix, r_num, suffix = match.groups()
    return f"{prefix}RES-{r_num}{suffix}"


def get_srb_code(variant: str) -> str:
    return get_variant_params(variant).get("srb_code", "NA")