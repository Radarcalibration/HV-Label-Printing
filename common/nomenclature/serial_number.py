import re
from dataclasses import dataclass
from datetime import date, datetime

# Serial number codes
NEW_PLANT_CODES = {
    "Jigani": "A",
    "Domlur": "B",
    "Plant_c": "C",  
}
NEW_PLANT_BY_CODE = {code: name for name, code in NEW_PLANT_CODES.items()}

MODEL_CODES = {
    "low voltage": "A",
    "high voltage": "B",
    "shockwave": "C",
    "tesseract": "D",
}
MODEL_BY_CODE = {code: name for name, code in MODEL_CODES.items()}
MODEL_BY_VARIANT = {
    "12P": "high voltage",
    "16P": "high voltage",
    "24P": "high voltage",
    "27P": "high voltage",
    "SW_LH_8P": "shockwave",
}

MODULE_VARIANT_CODES_NEW = {
    # "33P": "A1",  # low voltage
    # "48P": "A2",  # low voltage
    "12P": "A3",  # high voltage
    "16P": "A4",  # high voltage
    "24P": "A5",  # high voltage
    "27P": "A6",  # high voltage
    "SW_LH_8P": "S1",   # Shockwave #1
    # "SW RH 8P": "S2",
    # "SW LH 10P": "S3",
    # "SW LH 10P": "S4",
    # "TS 8P": "T1",  #tesseract
    # "TS 10P" : "T2"
}
VARIANT_BY_CODE_NEW = {code: name for name, code in MODULE_VARIANT_CODES_NEW.items()}

# Category code.
CATEGORY_CODES_NEW = {
    "domestic": "1",
    "export": "2",
}
CATEGORY_BY_CODE_NEW = {code: name for name, code in CATEGORY_CODES_NEW.items()}

# Cell manufacturer code.
CELL_MFR_CODES_NEW = {
    "molical": "P",
    "samsung": "Q",
    "bak": "R",
    "eve": "S",
    "lg": "T",
    "ten power": "U",
}
CELL_MFR_BY_CODE_NEW = {
    "P": "Molical",
    "Q": "Samsung",
    "R": "BAK",
    "S": "EVE",
    "T": "LG",
    "U": "Ten Power",
}


NEW_SERIAL_NUMBER_PATTERN = re.compile(
    r"^(?P<plant>[ABC])(?P<model>[ABCD])(?P<variant>A[1-6]|S[1-4]|T[1-4])(?P<line>[123])"
    r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
    r"(?P<category>[12])(?P<cell_mfr>[P-U])(?P<serial_count>\d{5})$"
)

# New approach for serial_count logic, 99999- A0000, Z9999- AA000, ZZ999- AAA00 and so on total (7,363,359 possible counts)
# NEW_SERIAL_NUMBER_PATTERN = re.compile(
#     r"^(?P<plant>[ABC])(?P<model>[ABCD])(?P<variant>A[3-6])(?P<line>[123])"
#     r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
#     r"(?P<category>[12])(?P<cell_mfr>[P-U])"
#     r"(?P<serial_count>[A-Z]{0,4}\d{1,5})$"
# )



@dataclass(frozen=True)
class ParsedSerialNumber:
    plant: str
    line: str
    year: int
    month: int
    day: int
    serial_count: str
    raw: str
    model: str
    variant: str
    cell_mfr: str
    category: str

    @property
    def is_export(self) -> bool:
        return (self.category or "").strip().lower() == "export"

    @property
    def as_date(self) -> date:
        return date(self.year, self.month, self.day)

    def format_date(self) -> str:
        return self.as_date.strftime("%d %b %Y")


def build_serial_number(
    *,
    plant: str,
    line: str,
    when: datetime | date,
    serial_count: str,
    model: str | None = None,
    variant: str | None = None,
    cell_mfr: str | None = None,
    category: str | None = None,
) -> str:
    
    plant_key = plant.strip().capitalize()
    if isinstance(when, datetime):
        when = when.date()

    # Build the supported serial number format.
    if plant_key not in NEW_PLANT_CODES:
        raise ValueError(f"Unsupported plant: {plant}")
    if line not in {"1", "2", "3"}:
        raise ValueError(f"Unsupported line: {line}")

    variant_key = (variant or "").strip().upper()
    if variant_key not in MODULE_VARIANT_CODES_NEW:
        raise ValueError(f"Unsupported variant: {variant}")

    model_key = MODEL_BY_VARIANT.get(variant_key)
    if model_key is None:
        raise ValueError(f"No serial-number model is configured for variant: {variant}")
    requested_model = (model or "").strip().lower()
    if requested_model and requested_model != model_key:
        raise ValueError(
            f"Variant {variant_key} requires model {model_key}, not {requested_model}."
        )

    cell_mfr_key = (cell_mfr or "").strip().lower()
    if cell_mfr_key not in CELL_MFR_CODES_NEW:
        raise ValueError(f"Unsupported cell manufacturer: {cell_mfr}")

    category_key = (category or "").strip().lower()
    if category_key not in CATEGORY_CODES_NEW:
        raise ValueError(f"Unsupported category: {category}")

    count_digits = re.sub(r"\D", "", serial_count or "")
    if count_digits and int(count_digits) > 99999:
        raise ValueError("Serial count cannot exceed 99999.")
    count = count_digits.zfill(5)

    #for new approach serial_count logic
    # count = (serial_count or "").strip().upper()

    # if not re.fullmatch(r"[A-Z]{0,4}\d{1,5}", count):
    #     raise ValueError(
    #         "Invalid serial count format."
    #     )
    # if len(count) != 5:
    #     raise ValueError(
    #         "Serial count must be exactly 5 characters."
    #     )
        
    return (
        f"{NEW_PLANT_CODES[plant_key]}"
        f"{MODEL_CODES[model_key]}"
        f"{MODULE_VARIANT_CODES_NEW[variant_key]}"
        f"{line}"
        f"{when:%Y%m%d}"
        f"{CATEGORY_CODES_NEW[category_key]}"
        f"{CELL_MFR_CODES_NEW[cell_mfr_key]}"
        f"{count}"
    )


def build_serial_number_for_model(
    model: str,
    *,
    plant: str,
    line: str,
    when: datetime | date,
    serial_count: str,
    variant: str,
    cell_mfr: str,
    category: str,
) -> str:
    
    return build_serial_number(
        plant=plant,
        line=line,
        when=when,
        serial_count=serial_count,
        model=model,
        variant=variant,
        cell_mfr=cell_mfr,
        category=category,
    )


def _parse_serial_number(cleaned: str) -> ParsedSerialNumber | None:
    match = NEW_SERIAL_NUMBER_PATTERN.match(cleaned)
    if not match:
        return None

    g = match.groupdict()
    plant_code = g["plant"]
    model_code = g["model"]
    variant_code = g["variant"]
    category_code = g["category"]
    manufacturer_code = g["cell_mfr"]

    if (
        plant_code not in NEW_PLANT_BY_CODE
        or model_code not in MODEL_BY_CODE
        or variant_code not in VARIANT_BY_CODE_NEW
        or manufacturer_code not in CELL_MFR_BY_CODE_NEW
        or category_code not in CATEGORY_BY_CODE_NEW
    ):
        return None

    try:
        date(int(g["year"]), int(g["month"]), int(g["day"]))
    except ValueError:
        return None

    return ParsedSerialNumber(
        plant=NEW_PLANT_BY_CODE[plant_code],
        line=g["line"],
        year=int(g["year"]),
        month=int(g["month"]),
        day=int(g["day"]),
        serial_count=g["serial_count"],
        raw=cleaned,
        model=MODEL_BY_CODE[model_code],
        variant=VARIANT_BY_CODE_NEW[variant_code],
        cell_mfr=CELL_MFR_BY_CODE_NEW[manufacturer_code],
        category=CATEGORY_BY_CODE_NEW[category_code],
    )


def parse_serial_number(value: str) -> ParsedSerialNumber | None:
    cleaned = value.strip().upper()

    return _parse_serial_number(cleaned)