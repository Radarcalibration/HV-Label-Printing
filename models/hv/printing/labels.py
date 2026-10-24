from datetime import datetime

from models.hv.gui.constants import (
    get_emark,
    get_emark_res_code,
    get_max_voltage,
    get_model_number,
    get_rated_capacity,
    get_srb_code,
    get_tac_number,
    get_cell_mfr_from_reess,
    get_type_of_reess,
)
from models.hv.nomenclature.module_id import parse_module_id
from models.hv.printing.zpl import (
    build_bmb_cmb_zpl,
    build_hv_pack_label_domestic,
    build_hv_pack_label_export,
    build_hv_bms_id_zpl,
    build_hv_dummy_id_zpl,
    build_hv_pack_id_zpl,
)


def _reess_for_pack_qr(*, variant: str, cell_mfr: str, pack_qr_data: str) -> str:
    qr_reess = pack_qr_data.split(":", 1)[0].strip().upper() if ":" in pack_qr_data else ""
    if not cell_mfr and qr_reess:
        cell_mfr = get_cell_mfr_from_reess(qr_reess) or ""
    reess = get_type_of_reess(variant, cell_mfr)
    if reess == "NA" or (qr_reess and reess != qr_reess):
        raise ValueError(f"part number of pack id does not match variant/cell manufacturer: {pack_qr_data}")
    return reess


def _manufacturing_year(mfg_date: str, mfg_year: str | None = None) -> str:
    if mfg_year and mfg_year.strip().isdigit() and len(mfg_year.strip()) == 4:
        return mfg_year.strip()
    value = mfg_date.strip()
    if value.isdigit() and len(value) == 4:
        return value
    for date_format in ("%d %b %Y", "%d %B %Y", "%d %m %Y", "%d/%m/%Y", "%d/%B/%Y"):
        try:
            return datetime.strptime(value, date_format).strftime("%Y")
        except ValueError:
            continue
    raise ValueError(f"Could not determine manufacturing year from {mfg_date!r}.")


def _pack_manufacturing_value(
    *, category: str, mfg_date: str, mfg_year: str | None = None
) -> str:
    if category.strip().lower() == "export":
        return _manufacturing_year(mfg_date, mfg_year)
    for date_format in ("%d %b %Y", "%d %B %Y", "%d %m %Y", "%d/%m/%Y", "%d/%B/%Y"):
        try:
            return datetime.strptime(mfg_date.strip(), date_format).strftime("%d %m %Y")
        except ValueError:
            continue
    raise ValueError(f"Could not parse manufacturing date {mfg_date!r}.")


def build_hv_pack_label(
    *,
    module_id: str,
    variant: str,
    model_number: str,
    mfg_date: str,
    mfg_year: str,
    category: str,
) -> str:
    is_export = category.strip().lower() == "export"
    module = parse_module_id(module_id)
    if module is None or module.cell_mfr is None:
        raise ValueError("Invalid module ID")
    cell_mfr = module.cell_mfr
    params = dict(
        module_id=module_id,
        variant=variant,
        model_number=get_model_number(variant, cell_mfr),
        type_of_reess=get_type_of_reess(variant, cell_mfr),
        rated_capacity=get_rated_capacity(variant),
    )
    if is_export:
        return build_hv_pack_label_export(
            rated_capacity=params["rated_capacity"],
            max_voltage=get_max_voltage(variant),
            type_of_reess=params["type_of_reess"],
            serial_number=module_id,
            tac_number=get_tac_number(variant),
            emark_res=get_emark_res_code(variant),
            srb_code=get_srb_code(variant),
            made_in="India",
            mfg_year=mfg_year,
            qr_data=module_id,
        )
    return build_hv_pack_label_domestic(
        tac_number=get_tac_number(variant),
        mfg_date=mfg_date,
        **params,
    )


def build_hv_dummy_id_label(
    *,
    pack_qr_data: str,
    serial_number: str,
    tac_number: str,
    mfg_date: str,
    variant: str,
    category: str,
    cell_mfr: str,
    mfg_year: str | None = None,
) -> str:
    is_export = category.strip().lower() == "export"
    value = get_emark(variant) if (is_export and variant) else tac_number
    tac_label = "E-Marking No" if (is_export and variant) else "TAC Number"
    model_number = _reess_for_pack_qr(
        variant=variant, cell_mfr=cell_mfr, pack_qr_data=pack_qr_data
    )
    mfg_value = (
        _manufacturing_year(mfg_date, mfg_year)
        if is_export
        else mfg_date.strip()
    )
    tac_number = value
    return build_hv_dummy_id_zpl(
        pack_qr_data=pack_qr_data,
        model_number=model_number,
        serial_number=serial_number,
        tac_number=tac_number,
        tac_label=tac_label,
        category=category,
        mfg_value=mfg_value,
    )


def build_pack_qr_label(
    *,
    pack_qr_data: str,
    model_number: str,
    serial_number: str,
    tac_number: str,
    mfg_date: str,
    variant: str = "",
    category: str = "Domestic",
    cell_mfr: str = "",
    mfg_year: str | None = None,
) -> str:
    return build_hv_dummy_id_label(
        pack_qr_data=pack_qr_data,
        serial_number=serial_number,
        tac_number=tac_number,
        mfg_date=mfg_date,
        variant=variant,
        category=category,
        cell_mfr=cell_mfr,
        mfg_year=mfg_year,
    )


def build_hv_bms_id_label(*, bmb_serial: str, cmb_serial: str, pack_qr_data: str = "") -> str:
    return build_hv_bms_id_zpl(
        bmb_serial=bmb_serial,
        cmb_serial=cmb_serial,
        pack_qr_data=pack_qr_data,
    )


def build_bmb_cmb_combined_label(*, bmb_serial: str, cmb_serial: str, pack_qr_data: str = "") -> str:
    return build_hv_bms_id_label(
        bmb_serial=bmb_serial,
        cmb_serial=cmb_serial,
        pack_qr_data=pack_qr_data,
    )


def build_bmb_cmb_label(*, kind: str, value: str, pack_qr_data: str = "") -> str:
    return build_bmb_cmb_zpl(kind=kind, value=value, pack_qr_data=pack_qr_data)



# def _emark_res(variant: str) -> str:
#     full = get_emark(variant)
#     if not full or "*" not in full:
#         return full
#     return full.split("*", 1)[1]


def build_hv_pack_id_label(
    *,
    serial_number: str,
    rated_capacity: str,
    max_voltage: str,
    model_number: str,
    tac_number: str,
    variant: str,
    category: str,
    mfg_date: str,
    pack_qr_data: str = "",
    made_in: str = "India",
    cell_mfr: str = "",
    mfg_year: str | None = None,
) -> str:
    type_of_reess = _reess_for_pack_qr(
        variant=variant, cell_mfr=cell_mfr, pack_qr_data=pack_qr_data
    )
    qr_data = pack_qr_data or serial_number
    mfg_value = _pack_manufacturing_value(
        category=category,
        mfg_date=mfg_date,
        mfg_year=mfg_year,
    )
    return build_hv_pack_id_zpl(
        rated_capacity=rated_capacity,
        max_voltage=max_voltage,
        type_of_reess=type_of_reess,
        serial_number=serial_number,
        tac_number=tac_number or get_tac_number(variant),
        emark_res=get_emark_res_code(variant),
        srb_code=get_srb_code(variant),
        made_in=made_in,
        mfg_value=mfg_value,
        qr_data=qr_data,
        category=category,
    )


def build_battery_pack_id_label(
    *,
    serial_number: str,
    rated_capacity: str,
    max_voltage: str,
    model_number: str,
    tac_number: str,
    variant: str,
    category: str,
    mfg_date: str,
    pack_qr_data: str = "",
    made_in: str = "India",
    cell_mfr: str = "",
    mfg_year: str | None = None,
) -> str:
    return build_hv_pack_id_label(
        serial_number=serial_number,
        rated_capacity=rated_capacity,
        max_voltage=max_voltage,
        model_number=model_number,
        tac_number=tac_number,
        variant=variant,
        category=category,
        mfg_date=mfg_date,
        pack_qr_data=pack_qr_data,
        made_in=made_in,
        cell_mfr=cell_mfr,
        mfg_year=mfg_year,
    )


def get_model_number_for_label(variant: str, cell_mfr: str) -> str:
    from models.hv.gui.constants import get_model_number
    return get_model_number(variant, cell_mfr)