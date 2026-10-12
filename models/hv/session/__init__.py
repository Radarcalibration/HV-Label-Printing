from __future__ import annotations

from typing import Any

__all__ = ["load_pack_serial", "save_pack_serial"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from models.hv.session import pack_store

        return getattr(pack_store, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
