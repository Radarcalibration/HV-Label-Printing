from models.hv.gui.constants import (
    get_emark,
    get_emark_res_code,
    get_srb_code,
    get_tac_number,
    get_cell_mfr_from_reess,
    get_type_of_reess,
    get_variant_from_reess,
)
from models.hv.nomenclature.serial_number import parse_serial_number

from models.hv.printing.zpl import (
    build_hv_bms_id_zpl,
    build_hv_dummy_id_zpl,
    build_hv_pack_id_zpl,
)


def _reess_for_pack_qr(*, variant: str, cell_mfr: str, pack_qr_data: str) -> str:
    qr_reess = pack_qr_data.split(":", 1)[0].strip().upper() # extract part number from Dummy ID
    qr_serial = pack_qr_data.split(":", 1)[1] if ":" in pack_qr_data else ""
    parsed_serial = parse_serial_number(qr_serial)
    if not cell_mfr and qr_reess:
        cell_mfr = (
            parsed_serial.cell_mfr
            if parsed_serial is not None
            else get_cell_mfr_from_reess(qr_reess) or ""
        )
    reess = get_type_of_reess(variant, cell_mfr) # get part number from battery parameters
    if reess == "NA":
        raise ValueError(f"part number of pack id does not match variant/cell manufacturer: {pack_qr_data}")
    if qr_reess and reess != qr_reess:
        qr_cell_mfr = get_cell_mfr_from_reess(qr_reess)
        if (
            get_variant_from_reess(qr_reess) != variant
            or (qr_cell_mfr and cell_mfr and qr_cell_mfr != cell_mfr)
        ):
            raise ValueError(
                f"part number of pack id does not match variant/cell manufacturer: {pack_qr_data}"
            )
        return qr_reess
    return reess


def build_hv_dummy_id_label(
    *,
    pack_qr_data: str,
    serial_number: str,
    tac_number: str,
    mfg_date: str,
    variant: str,
    category: str,
    cell_mfr: str,
) -> str:
    is_export = category.strip().lower() == "export"
    tac_value= get_emark(variant) if (is_export and variant) else tac_number
    tac_label = "E-Marking No" if (is_export and variant) else "TAC Number"
    model_number = _reess_for_pack_qr(
        variant=variant, cell_mfr=cell_mfr, pack_qr_data=pack_qr_data
    )
    tac_number = tac_value
    return build_hv_dummy_id_zpl(
        pack_qr_data=pack_qr_data,
        model_number=model_number,
        serial_number=serial_number,
        tac_number=tac_number,
        tac_label=tac_label,
        category=category,
        mfg_date=mfg_date,
    )


def build_hv_pack_id_label(
    *,
    serial_number: str,
    rated_capacity: str,
    max_voltage: str,
    type_of_reess: str,
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
    qr_serial = pack_qr_data.split(":", 1)[1] if ":" in pack_qr_data else ""
    parsed_serial = parse_serial_number(qr_serial)
    qr_data = pack_qr_data or serial_number
    return build_hv_pack_id_zpl(
        rated_capacity=rated_capacity,
        max_voltage=max_voltage,
        type_of_reess=type_of_reess,
        serial_number=serial_number,
        tac_number=tac_number or get_tac_number(variant),
        emark_res=get_emark_res_code(variant),
        srb_code=get_srb_code(variant),
        made_in=made_in,
        mfg_date=mfg_date,
        qr_data=qr_data,
        category=category,
        cell_mfr=cell_mfr or (
            parsed_serial.cell_mfr
            if parsed_serial is not None
            else get_cell_mfr_from_reess(
                pack_qr_data.split(":", 1)[0]
            ) or ""
        ),
    )
    
    
def build_hv_bms_id_label(*, bmb_serial: str, cmb_serial: str, pack_qr_data: str = "") -> str: #3
    return build_hv_bms_id_zpl(
        bmb_serial=bmb_serial,
        cmb_serial=cmb_serial,
        pack_qr_data=pack_qr_data,
    )