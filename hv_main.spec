# hv_label_printer.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('models/hv/assets/logo.png', 'models/hv/assets'),
        ('models/hv/assets/logo.ico', 'models/hv/assets'),
    ],
    hiddenimports=[
        'openpyxl'
    ],
    excludes=[
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'pytest',
        'tkinter.test'
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HV Label Printer',
    console=False,
    icon='models/hv/assets/logo.ico',
    upx=True,
)