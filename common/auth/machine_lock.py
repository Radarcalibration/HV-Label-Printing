from __future__ import annotations

import hashlib
import platform
import sys

AUTHORIZED_HASHES = {"3871a77f1b1180d3a8c4fa9e1f71a0b32cf164e6d8cd5f9792c9a8986bc43f7b","0300cac0dfe775b53c6ee8ed0a35a22e1e5b8db8b8712aa44f7e34435233e767", "542208c237138aafade60a7190238712faa9a7683c567701dd026338fecf9e7d", "a9cd7d93c0388e793fb35cfdd708ca04c33a7975b8eb72a9d816fa012064aa70", "2e4d2fa6c54b82a39f2ee81d71ff7441f6ea666335bce7199fbecea4330c7a86"}


def _raw_machine_id() -> str:
    if platform.system() != "Windows":
        return "NON-WINDOWS-DEV-ENVIRONMENT"

    try:
        import winreg # windows registry api (built-in lib)
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography"
        )
        value= winreg.QueryValueEx(key, "MachineGuid") # ,_type is unnecessary
        winreg.CloseKey(key)
        return str(value)
    except OSError:
        return "UNREADABLE-MACHINE-GUID"


def get_machine_hash() -> str:
    raw = _raw_machine_id()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest() # encode("utf-8") converts raw str into bytes # and then converted to hexadecimal


def is_authorized() -> bool:
    if not AUTHORIZED_HASHES:
        return False
    return get_machine_hash() in AUTHORIZED_HASHES


if __name__ == "__main__":
    # python -m auth.machine_lock
    print("This machine's hash:")
    print(get_machine_hash())
    print()
    print("Add this to AUTHORIZED_HASHES in auth/machine_lock.py to authorize it.")
    sys.exit(0) # sys.exit(1) due to errors