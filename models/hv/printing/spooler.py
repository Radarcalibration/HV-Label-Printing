import ctypes
from ctypes import wintypes
from pathlib import Path

from models.hv.printing.constants import  PRINTER_PACK_ID #, PRINTER_NAME


class DOCINFO1(ctypes.Structure):
    _fields_ = [
        ("pDocName",    wintypes.LPWSTR),
        ("pOutputFile", wintypes.LPWSTR),
        ("pDatatype",   wintypes.LPWSTR),
    ]


def _resolve_printer_name(printer_name: str) -> str:
    return printer_name

def send_zpl(zpl: str, printer_name: str = PRINTER_PACK_ID) -> None:
    resolved_name = _resolve_printer_name(printer_name)
    payload = zpl.encode("utf-8")

    winspool = ctypes.WinDLL("winspool.drv")  

    winspool.OpenPrinterW.argtypes  = [wintypes.LPWSTR, ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p]
    winspool.OpenPrinterW.restype   = wintypes.BOOL
    winspool.StartDocPrinterW.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(DOCINFO1)]
    winspool.StartDocPrinterW.restype  = wintypes.DWORD
    winspool.StartPagePrinter.argtypes = [wintypes.HANDLE]
    winspool.StartPagePrinter.restype  = wintypes.BOOL
    winspool.WritePrinter.argtypes  = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    winspool.WritePrinter.restype   = wintypes.BOOL
    winspool.EndPagePrinter.argtypes  = [wintypes.HANDLE]
    winspool.EndPagePrinter.restype   = wintypes.BOOL
    winspool.EndDocPrinter.argtypes   = [wintypes.HANDLE]
    winspool.EndDocPrinter.restype    = wintypes.BOOL
    winspool.ClosePrinter.argtypes    = [wintypes.HANDLE]
    winspool.ClosePrinter.restype     = wintypes.BOOL

    hprinter = wintypes.HANDLE()
    if not winspool.OpenPrinterW(resolved_name, ctypes.byref(hprinter), None):
        raise OSError(f'Could not open printer "{resolved_name}" (check with printer name is correct or not, error {ctypes.GetLastError()}).')

    try:
        job_id = 0
        last_error = 0
        for datatype in ("RAW", None):
            doc_info = DOCINFO1("BMS Label", None, datatype)
            job_id = winspool.StartDocPrinterW(hprinter, 1, ctypes.byref(doc_info))
            if job_id != 0:
                break
            last_error = ctypes.GetLastError()

        if job_id == 0:
            raise OSError(
                f'StartDocPrinterW failed (error {last_error}). '
                f'This usually means the printer driver for "{resolved_name}" is missing '
                f'or corrupted — try restarting the Print Spooler service or '
                f'reinstalling the ZDesigner driver.'
            )

        try:
            if not winspool.StartPagePrinter(hprinter):
                raise OSError(f'StartPagePrinter failed (error {ctypes.GetLastError()}).')

            written = wintypes.DWORD(0)
            buf = ctypes.create_string_buffer(payload)
            if not winspool.WritePrinter(hprinter, buf, len(payload), ctypes.byref(written)):
                raise OSError(f'WritePrinter failed (error {ctypes.GetLastError()}).')
            if written.value != len(payload):
                raise OSError(f'WritePrinter wrote {written.value}/{len(payload)} bytes.')
        finally:
            winspool.EndPagePrinter(hprinter)
            winspool.EndDocPrinter(hprinter)
    finally:
        winspool.ClosePrinter(hprinter)


def save_zpl(zpl: str, path: str | Path) -> Path:
    output = Path(path)
    output.write_text(zpl, encoding="utf-8")
    return output