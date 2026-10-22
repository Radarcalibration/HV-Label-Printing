""" Accepts bmb_cmb ID formats
  1. "VQ150720-REV-A-S26250061" 
  2. "VQ150710-2v2S26250082"   
  3. "VQ150720_1.0X26030083"   

  VQ150720- → BMB ID 
  VQ150710- → CMB ID 
"""
 

import re
from dataclasses import dataclass

BMB_MODEL = "VQ150720"
CMB_MODEL = "VQ150710"
MODEL_TO_KIND = {BMB_MODEL: "BMB", CMB_MODEL: "CMB"}

FULL_BMB_CMB_PATTERN = re.compile(
    r"^(?P<model>VQ150720|VQ150710)[-_](?P<middle>.*?)[-_]?(?P<marker>[SX])(?P<serial>\d+)$",
    re.IGNORECASE,
)

@dataclass(frozen=True)
class ParsedBmbCmbId:
    kind: str
    model: str
    middle: str        
    serial: str
    raw: str           

    @property
    def short_id(self) -> str:
       
        return self.raw[-9:]  # last 9 digits of each bmb/cmb id (string type)


def parse_bmb_cmb_id(value: str) -> ParsedBmbCmbId | None:
    cleaned = value.strip().upper()
    match = FULL_BMB_CMB_PATTERN.match(cleaned)
    if not match:
        return None
    model = match.group("model").upper()
    return ParsedBmbCmbId(
        kind=MODEL_TO_KIND[model],
        model=model,
        middle=match.group("middle").upper(),
        serial=match.group("serial"),
        raw=cleaned,
    )


def short_bmb_cmb_id(raw: str) -> str:
    
    return raw.strip().upper()[-9:]