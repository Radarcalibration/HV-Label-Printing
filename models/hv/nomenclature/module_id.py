""" VX156610-E1611109G260076 VQ150060-E1311109G260078 """

import re
from dataclasses import dataclass
from datetime import date, datetime

from models.hv.gui.constants import (
    MODULE_VARIANT_CODES, VARIANT_BY_CODE,
    GROUP_CODES, GROUP_BY_CODE,
    CELL_MFR_CODES, CELL_MFR_BY_CODE,
    PLANT_CODES_HV, PLANT_BY_CODE_HV,
    SHIFT_CODES_HV,
    MONTH_CODES, MONTH_BY_CODE,
    get_model_number,
)

_SUB_PATTERN = re.compile(
    r"^(?P<variant>[C-F])"
    r"(?P<group>[1-3])"
    r"(?P<cell_mfr>[1-6])"
    r"(?P<plant>[123ABC])" #plant encoded (either 123 and ABC)
    r"(?P<line>[123])"
    r"(?P<shift>[123])"
    r"(?P<dd>\d{2})"
    r"(?P<month>[A-L])"
    r"(?P<yy>\d{2})"
    r"(?P<serial>\d{4})$"
)
# VX156600-D1611105J260303 (valid module id, from robot cell sorting machine) -> accept this type
# VQ156610-E2A1116J26009759 (invalid module id, from manual cell sorting machine) -> can't accept this type
_FULL_PATTERN = re.compile(
    r"^(?P<part_number>V[QX][0-9]{6})-(?P<sub>[C-F][1-3][1-6][123ABC][123][123]\d{2}[A-L]\d{2}\d{4})$"
)
@dataclass(frozen=True)
class ParsedModuleId:
    variant: str
    part_number: str   
    group: str        
    cell_mfr: str
    plant: str
    line: str
    day: int
    month: int
    year: int
    shift: str
    serial: str
    sub_id: str         
    raw: str          

    @property
    def as_date(self) -> date:
        return date(self.year, self.month, self.day)


def build_module_sub_id(
    *,
    variant: str,
    group: str,
    cell_mfr: str,
    plant: str,
    line: str,
    when: date | datetime,
    shift: str,
    serial: str,
) -> str:
    if isinstance(when, datetime):
        when = when.date()

    v_code  = MODULE_VARIANT_CODES.get(variant.strip())
    g_code  = GROUP_CODES.get(group.strip())
    cm_code = CELL_MFR_CODES.get(cell_mfr.strip())
    p_code  = PLANT_CODES_HV.get(plant.strip())
    sh_code = SHIFT_CODES_HV.get(shift.strip())
    m_code  = MONTH_CODES.get(when.month)

    if not all([v_code, g_code, cm_code, p_code, sh_code, m_code]):
        raise ValueError(
            f"Invalid code: variant={variant}, group={group}, "
            f"cell_mfr={cell_mfr}, plant={plant}, shift={shift}, month={when.month}"
        )
    if line not in ("1", "2", "3"):
        raise ValueError(f"Invalid line: {line}")

    count = re.sub(r"\D", "", serial).zfill(4)[-4:] # \D removes non-numeric keys. (4) converts to len(4) and (-4) returns last 4 digits. 

    return (
        f"{v_code}"
        f"{g_code}"
        f"{cm_code}"
        f"{p_code}"
        f"{line}"
        f"{sh_code}"
        f"{when.day:02d}"
        f"{m_code}"
        f"{when.year % 100:02d}"
        f"{count}"
    )


def build_full_module_id(
    *,
    variant: str,
    group: str,
    cell_mfr: str,
    plant: str,
    line: str,
    when: date | datetime,
    shift: str,
    serial: str,
) -> str:
    part_number = get_model_number(variant, cell_mfr)
    if not part_number:
        raise ValueError(f"Unsupported variant/cell manufacturer: {variant}/{cell_mfr}")
    sub = build_module_sub_id(
        variant=variant, group=group, cell_mfr=cell_mfr,
        plant=plant, line=line, when=when, shift=shift, serial=serial,
    )
    return f"{part_number}-{sub}"


def build_all_module_ids(
    *, # to specify parameters insted of values.
    variant: str,
    group: str,
    cell_mfr: str,
    plant: str,
    line: str,
    when: date | datetime,
    shift: str,
    start_serial: str,
    count: int = 4,
) -> list[str]:
    start = int(re.sub(r"\D", "", start_serial or "0") or "0")
    ids: list[str] = []
    for offset in range(count): # count 4 (m1-m4)
        serial = str(start + offset).zfill(4)[-4:] # store last 4 digit and compares with other modules
        ids.append(
            build_full_module_id(
                variant=variant, group=group, cell_mfr=cell_mfr,
                plant=plant, line=line, when=when, shift=shift, serial=serial,
            )
        )
    return ids


build_module_id = build_full_module_id


def parse_module_id(value: str) -> ParsedModuleId | None:
    cleaned = value.strip().upper()
    m = _FULL_PATTERN.match(cleaned)
    if not m:
        return None

    part_number = m.group("part_number")
    sub   = m.group("sub")
    sm    = _SUB_PATTERN.match(sub)
    if not sm:
        return None

    g = sm.groupdict()
    variant  = VARIANT_BY_CODE.get(g["variant"])
    cell_mfr = CELL_MFR_BY_CODE.get(g["cell_mfr"])
    plant    = PLANT_BY_CODE_HV.get(g["plant"])
    group    = GROUP_BY_CODE.get(g["group"])
    month    = MONTH_BY_CODE.get(g["month"])

    if (
        variant is None
        or cell_mfr is None
        or plant is None
        or group is None
        or month is None
    ):
        return None

    if get_model_number(variant, cell_mfr) != part_number:
        return None

    year  = 2000 + int(g["yy"])
    day   = int(g["dd"])
    try:
        date(year, month, day)
    except ValueError:
        return None

    shift_map = {"1": "Shift 1", "2": "Shift 2", "3": "Shift 3"}

    return ParsedModuleId(
        variant=variant,
        part_number=part_number,
        group=group,
        cell_mfr=cell_mfr,
        plant=plant,
        line=g["line"],
        day=day, month=month, year=year,
        shift=shift_map[g["shift"]],
        serial=g["serial"],
        sub_id=sub,
        raw=cleaned,
    )