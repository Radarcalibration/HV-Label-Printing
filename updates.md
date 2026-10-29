# test cases for pack id

VQ150000:ABA31202609241R00295
VQ150010:ABA41202609251R00297
VQ150020:ABA51202609261R00299
VQ150030:ABA61202609151R00277
VQ150030:ABA61202610121R00330
VQ150030:ABA61202609151R00276

VQ150000:ABA31202609242R00295

1) i have given the SW_LH_8P variant for everywhere to add, check with serial number pattern (it should accept) all MODULE_VARIANT_CODES_NEW
2) i have commented build_hv_pack_id_zpl same below this function in zpl.py (if cell mfr is BAK) TAC Number = XXXXXXXX and no values after 136RES (E-Marking number) write this directly in that function only.