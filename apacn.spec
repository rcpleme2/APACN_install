# apacn.spec
# ----------
# Spec do PyInstaller para empacotar o APACN – Nota Paraná.
#
# Execute na máquina Windows de build com:
#   pyinstaller apacn.spec --clean
#
# Pré-requisitos no ambiente de build:
#   pip install -r requirements.txt
#   playwright install chromium

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Localiza o driver do Playwright (Node.js embutido + pacote JS)
# O caminho varia conforme a versão do Playwright:
#   >= 1.40 : playwright/driver/
#   antigas : playwright/_impl/_driver/
# ---------------------------------------------------------------------------
import playwright as _pw
_pw_pkg = Path(_pw.__file__).parent

_driver_candidates = [
    _pw_pkg / "driver",
    _pw_pkg / "_impl" / "_driver",
]
_pw_driver = next((p for p in _driver_candidates if p.exists()), None)

if _pw_driver is None:
    _found = [str(p) for p in _pw_pkg.iterdir()]
    raise SystemExit(
        f"[apacn.spec] Driver do Playwright nao encontrado.\n"
        f"Conteudo do pacote: {_found}\n"
        "Certifique-se de que 'playwright' esta instalado no ambiente de build."
    )
print(f"[apacn.spec] Driver Playwright: {_pw_driver}")

# ---------------------------------------------------------------------------
# Localiza o Chromium instalado pelo Playwright
# ---------------------------------------------------------------------------
_localappdata = os.environ.get("LOCALAPPDATA", "")
if not _localappdata:
    raise SystemExit("[apacn.spec] Variável LOCALAPPDATA não encontrada.")

_ms_playwright = Path(_localappdata) / "ms-playwright"
_chromium_dirs = sorted(_ms_playwright.glob("chromium-*"))
if not _chromium_dirs:
    raise SystemExit(
        f"[apacn.spec] Chromium não encontrado em {_ms_playwright}.\n"
        "Execute: playwright install chromium"
    )
_chromium_path = _chromium_dirs[-1]
print(f"[apacn.spec] Chromium: {_chromium_path}")

# ---------------------------------------------------------------------------
# Ícone (opcional — coloque apacn.ico na raiz do projeto)
# ---------------------------------------------------------------------------
_icon = "apacn.ico" if Path("apacn.ico").exists() else None

# ---------------------------------------------------------------------------
# Definição do build
# ---------------------------------------------------------------------------
block_cipher = None

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Driver do Playwright (Node.js + pacote JS)
        # Mantém a mesma estrutura relativa que tem no site-packages
        (str(_pw_driver), f"playwright/{_pw_driver.relative_to(_pw_pkg)}"),
        # Chromium embutido
        (str(_chromium_path), f"pw-browsers/{_chromium_path.name}"),
    ],
    hiddenimports=[
        "playwright",
        "playwright.sync_api",
        "playwright._impl._sync_api",
        "playwright._impl._browser",
        "playwright._impl._page",
        "playwright._impl._network",
        "pyee",
        "pyee.base",
        "pyee.asyncio",
        "greenlet",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "wx"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="APACN",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,          # Aplicação de terminal — mantém janela do console
    icon=_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="APACN",
)
