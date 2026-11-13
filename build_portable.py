import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DIST_DIR = BASE_DIR / "dist"
PORTABLE_DIR = DIST_DIR / "AllDown-Portable"


def remove_readonly(func, path, _excinfo):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def safe_rmtree(path: Path) -> None:
    if not path.exists():
        return
    try:
        shutil.rmtree(path, onexc=remove_readonly)
    except TypeError:
        shutil.rmtree(path, onerror=remove_readonly)


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

safe_rmtree(PORTABLE_DIR)
shutil.copytree(build_output, PORTABLE_DIR, dirs_exist_ok=True)
safe_rmtree(build_output)

internal_dir = PORTABLE_DIR / "_internal"

bin_dest = internal_dir / "bin"
bin_dest.mkdir(parents=True, exist_ok=True)
if (BASE_DIR / "bin" / "ffmpeg.exe").is_file():
    shutil.copy2(BASE_DIR / "bin" / "ffmpeg.exe", bin_dest / "ffmpeg.exe")
if (BASE_DIR / "bin" / "node.exe").is_file():
    shutil.copy2(BASE_DIR / "bin" / "node.exe", bin_dest / "node.exe")

bgutil_dest = internal_dir / "bgutil_provider" / "server"
if (BASE_DIR / "bgutil_provider" / "server").is_dir():
    shutil.copytree(
        BASE_DIR / "bgutil_provider" / "server",
        bgutil_dest,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git*", ".devcontainer", "src", "types", "scripts", "*.ts",
            "*.tsbuildinfo", "eslint*", "prettier*", "Dockerfile", "deno*", "*.md"
        ),
    )

if (BASE_DIR / "cookies.txt").is_file():
    shutil.copy2(BASE_DIR / "cookies.txt", PORTABLE_DIR / "cookies.txt")

readme_content = """===============================================================
  ALL DOWN — BAIXADOR DE VÍDEOS E PLAYLISTS EM 4K / MP3 (PORTÁTIL)
===============================================================

COMO USAR:
1. Dê um duplo clique em "AllDown.exe" para abrir o aplicativo.
2. Cole o link do vídeo ou playlist do YouTube.
3. Clique em "Analisar Vídeo".
4. Escolha a resolução (até 4K/8K) ou selecione MP3 para baixar áudio.
5. Clique em "BAIXAR VÍDEO" (ou "BAIXAR PLAYLIST").

DENTRO DO APLICATIVO:
- Clique no botão "📖 Como Usar" no topo para o tutorial interativo completo.
- Clique em "🔑 Fazer Login no YouTube" para conectar sua conta e evitar bloqueios.

REQUISITOS:
- Windows 10 ou 11 (64 bits).
- Nenhuma instalação necessária (FFmpeg e Node.js já inclusos na pasta _internal).
"""
(PORTABLE_DIR / "LEIA-ME.txt").write_text(readme_content, encoding="utf-8")

print("\n" + "=" * 60)
print(f"SUCESSO! Aplicativo portátil gerado em: {PORTABLE_DIR.resolve()}")
print(f"Executável: {PORTABLE_DIR / 'AllDown.exe'}")
print("=" * 60)
