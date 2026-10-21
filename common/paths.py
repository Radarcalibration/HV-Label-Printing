 

import sys
from pathlib import Path


def get_common_base_dir() -> Path:
    
    if getattr(sys, "frozen", False): # frozen = True (applicable to .exe file)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent # resolve()--> absulute path