import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"
PORTABLE_DIR = DIST_DIR / "AllDown-Portable"

print("=" * 60)
print("Construindo All Down Executável Portátil...")
print("=" * 60)

pyinstaller_args = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", "AllDown",
    "--icon", str(BASE_DIR / "assets" / "icon.ico"),
    "--add-data", f"{BASE_DIR / 'assets'};assets",
    "--collect-all", "customtkinter",
    "--collect-all", "yt_dlp",
    "--collect-all", "yt_dlp_plugins",
    "--collect-all", "webview",
    "--collect-all", "PIL",
    "--hidden-import", "webview.platforms.edgechromium",
    "--hidden-import", "webview.platforms.winforms",
    "--hidden-import", "pythonnet",
    "--hidden-import", "clr",
    str(BASE_DIR / "app.py"),
]

res = subprocess.run(pyinstaller_args, cwd=str(BASE_DIR))
if res.returncode != 0:
    print("ERRO: PyInstaller falhou!")
    sys.exit(res.returncode)

build_output = DIST_DIR / "AllDown"
if not build_output.exists():
    print(f"ERRO: Pasta de saída {build_output} não encontrada!")
    sys.exit(1)

if PORTABLE_DIR.exists():
    shutil.rmtree(PORTABLE_DIR)

shutil.move(str(build_output), str(PORTABLE_DIR))

bin_dest = PORTABLE_DIR / "bin"
bin_dest.mkdir(exist_ok=True)
if (BASE_DIR / "bin" / "ffmpeg.exe").is_file():
    shutil.copy2(BASE_DIR / "bin" / "ffmpeg.exe", bin_dest / "ffmpeg.exe")
if (BASE_DIR / "bin" / "node.exe").is_file():
    shutil.copy2(BASE_DIR / "bin" / "node.exe", bin_dest / "node.exe")

bgutil_dest = PORTABLE_DIR / "bgutil_provider"
if (BASE_DIR / "bgutil_provider").is_dir():
    shutil.copytree(BASE_DIR / "bgutil_provider", bgutil_dest, dirs_exist_ok=True)

assets_dest = PORTABLE_DIR / "assets"
shutil.copytree(BASE_DIR / "assets", assets_dest, dirs_exist_ok=True)
if (BASE_DIR / "cookies.txt").is_file():
    shutil.copy2(BASE_DIR / "cookies.txt", PORTABLE_DIR / "cookies.txt")

if (BASE_DIR / "login.py").is_file():
    shutil.copy2(BASE_DIR / "login.py", PORTABLE_DIR / "login.py")

readme_content = """===============================================================
  ALL DOWN — BAIXADOR DE VÍDEOS DO YOUTUBE EM 4K / 8K (PORTÁTIL)
===============================================================

COMO USAR:
1. Dê um duplo clique em "AllDown.exe" para abrir o aplicativo.
2. Cole o link do vídeo do YouTube que deseja baixar.
3. Clique em "Analisar Vídeo".
4. Selecione a resolução desejada (ex: 4K Ultra HD) e clique em "BAIXAR VÍDEO".

LOGIN NO YOUTUBE:
Se o YouTube solicitar confirmação de que você não é um robô:
- Clique no botão "🔑 Fazer Login no YouTube" dentro do aplicativo.
- Entre na sua conta normalmente na janela segura que abrir.
- O aplicativo salvará seus cookies automaticamente para liberar todos os downloads.

REQUISITOS:
- Windows 10 ou 11 (64 bits).
- Nenhum software adicional precisa ser instalado.
"""
(PORTABLE_DIR / "LEIA-ME.txt").write_text(readme_content, encoding="utf-8")

print("\n" + "=" * 60)
print(f"SUCESSO! Aplicativo portátil gerado em: {PORTABLE_DIR.resolve()}")
print(f"Executável: {PORTABLE_DIR / 'AllDown.exe'}")
print("=" * 60)
