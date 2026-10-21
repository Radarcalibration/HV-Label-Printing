 

from datetime import datetime

from models.hv.gui.constants import (
    get_emark,
    get_emark_res_code,
    get_model_number,
    get_rated_capacity,
    get_srb_code,
    get_tac_number,
    get_cell_mfr_from_reess,
    get_type_of_reess,
)
from models.hv.nomenclature.module_id import parse_module_id
from models.hv.printing.zpl import (
    build_battery_pack_id_zpl_unified,
    build_bmb_cmb_combined_zpl,
    build_bmb_cmb_zpl,
    # build_hv_module_label_domestic,
    # build_hv_module_label_export,
    build_hv_pack_label_domestic,
    build_hv_pack_label_export,
    build_pack_qr_zpl,
)


def _reess_for_pack_qr(*, variant: str, cell_mfr: str, pack_qr_data: str) -> str:
    qr_reess = pack_qr_data.split(":", 1)[0].strip().upper() if ":" in pack_qr_data else ""
    if not cell_mfr and qr_reess:
        cell_mfr = get_cell_mfr_from_reess(qr_reess) or ""
    reess = get_type_of_reess(variant, cell_mfr)
    if reess == "NA" or (qr_reess and reess != qr_reess):
        raise ValueError(f"part number of pack id does not match variant/cell manufacturer: {pack_qr_data}")
    return reess


# def build_hv_module_label(
#     *,
#     full_module_id: str,
#     # variant: str,
#     # model_number: str,
#     # mfg_date: str,
#     # mfg_year: str,
#     category: str,
# ) -> str:
#     is_export = category.strip().lower() == "export"
#     module = parse_module_id(full_module_id)
#     if module is None:
#         raise ValueError("Invalid module ID")
#     if is_export:
#         return build_hv_module_label_export(full_module_id=full_module_id)
#     return build_hv_module_label_domestic(full_module_id=full_module_id)


def build_hv_pack_label(
    *,
    module_id: str,
    variant: str,
    # model_number: str,
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
            emark=get_emark(variant),
            mfg_year=mfg_year,
            **params,
        )
    return build_hv_pack_label_domestic(
        tac_number=get_tac_number(variant),
        mfg_date=mfg_date,
        **params,
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
) -> str:
    is_export = category.strip().lower() == "export"
    value = get_emark(variant) if (is_export and variant) else tac_number
    tac_label = "E-Marking No" if (is_export and variant) else "TAC Number"
    model_number = _reess_for_pack_qr(
        variant=variant, cell_mfr=cell_mfr, pack_qr_data=pack_qr_data
    )
    return build_pack_qr_zpl(
        pack_qr_data=pack_qr_data,
        model_number=model_number,
        serial_number=serial_number,
        tac_number=value,
        tac_label=tac_label,
        mfg_date=mfg_date,
    )


def build_bmb_cmb_combined_label(*, bmb_serial: str, cmb_serial: str, pack_qr_data: str = "") -> str:
    return build_bmb_cmb_combined_zpl(bmb_serial=bmb_serial, cmb_serial=cmb_serial, pack_qr_data=pack_qr_data)


def build_bmb_cmb_label(*, kind: str, value: str, pack_qr_data: str = "") -> str:
    return build_bmb_cmb_zpl(kind=kind, value=value, pack_qr_data=pack_qr_data)



def _emark_res(variant: str) -> str:
    full = get_emark(variant)
    if not full or "*" not in full:
        return full
    return full.split("*", 1)[1]


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
) -> str:
    type_of_reess = _reess_for_pack_qr(
        variant=variant, cell_mfr=cell_mfr, pack_qr_data=pack_qr_data
    )
    qr_data = pack_qr_data or serial_number
    # mfg_year = mfg_date[-4:] if len(mfg_date) >= 4 else mfg_date # mfg_date
    mfg_date_new = datetime.strptime(mfg_date, "%d %b %Y").strftime("%d %m %Y")
    return build_battery_pack_id_zpl_unified(
        rated_capacity=rated_capacity,
        max_voltage=max_voltage,
        type_of_reess=type_of_reess,
        serial_number=serial_number,
        tac_number=tac_number or get_tac_number(variant),
        emark_res=get_emark_res_code(variant),
        srb_code=get_srb_code(variant),
        made_in=made_in,
        mfg_date_new=mfg_date_new, # mfg_date
        qr_data=qr_data,
    )


# def build_scanned_module_label(*, full_module_id: str, variant: str, category: str) -> str:
#     module = parse_module_id(full_module_id)
#     return build_hv_module_label(
#         full_module_id=full_module_id,
#         variant=variant,
#         model_number=get_model_number_for_label(variant, module.cell_mfr if module else ""),
#         mfg_date="",
#         mfg_year="",
#         category=category,
#     )


def get_model_number_for_label(variant: str, cell_mfr: str) -> str:
    from models.hv.gui.constants import get_model_number
    return get_model_number(variant, cell_mfr)