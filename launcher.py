"""
launcher.py
-----------
Ponto de entrada para o executável gerado pelo PyInstaller.

Define PLAYWRIGHT_BROWSERS_PATH apontando para o Chromium embutido no
pacote ANTES de qualquer importação de playwright, depois delega para main().
"""

import os
import sys


def _configurar_playwright() -> None:
    """Aponta Playwright para o Chromium incluído no bundle."""
    if not getattr(sys, "frozen", False):
        return  # Execução normal em desenvolvimento — usa o Chromium do sistema

    # sys._MEIPASS é o diretório onde PyInstaller extrai os arquivos do bundle.
    # Funciona tanto no modo onefile (diretório temporário) quanto no modo
    # onedir/COLLECT (subdiretório _internal gerado pelo PyInstaller 6+).
    base = sys._MEIPASS
    browsers_path = os.path.join(base, "pw-browsers")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path


# Configurar ANTES de qualquer import que carregue playwright
_configurar_playwright()

# Só agora é seguro importar módulos que dependem de playwright
from main import main  # noqa: E402


if __name__ == "__main__":
    main()
