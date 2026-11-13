from __future__ import annotations

import io
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
import warnings
from pathlib import Path
from tkinter import filedialog, messagebox

warnings.filterwarnings("ignore", category=UserWarning, module="customtkinter")

if len(sys.argv) > 1 and sys.argv[1] == "--login":
    try:
        from login import run_login
        run_login()
    except Exception as e:
        print(f"Erro no login: {e}")
    sys.exit(0)

import customtkinter as ctk
from PIL import Image

try:
    import yt_dlp
    from yt_dlp.utils import DownloadCancelled
except ImportError:
    ctk.CTk().withdraw()
    messagebox.showerror(
        "All Down",
        "O pacote yt-dlp não está instalado.\nRode run.bat para instalar as dependências.",
    )
    sys.exit(1)

APP_NAME = "All Down"
SETTINGS_FILE = Path.home() / ".alldown.json"
BEST = "Melhor disponível"
NO_COOKIES = "Não usar"
COOKIE_FILE = "Arquivo cookies.txt…"
BROWSERS = {"Chrome": "chrome", "Edge": "edge", "Firefox": "firefox", "Brave": "brave", "Opera": "opera"}
AUDIO_QUALITY_MAP = {
    "320 kbps (Máxima Fidelidade)": "320",
    "256 kbps (Muito Alta)": "256",
    "192 kbps (Alta Qualidade)": "192",
    "128 kbps (Padrão)": "128",
}
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

COLOR_BG = "#0D0D11"
COLOR_CARD = "#17171D"
COLOR_CARD_BORDER = "#2A2A36"
COLOR_CARD_ALT = "#1F1F27"
COLOR_ACCENT = "#E50914"
COLOR_ACCENT_HOVER = "#B80710"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_MUTED = "#9CA3AF"
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def find_ffmpeg() -> str | None:
    base = get_base_dir()
    for candidate in [
        base / "_internal" / "bin" / "ffmpeg.exe",
        base / "bin" / "ffmpeg.exe",
        base / "ffmpeg.exe",
        base / ".venv" / "Scripts" / "ffmpeg.exe",
    ]:
        if candidate.is_file():
            return str(candidate)

    exe = shutil.which("ffmpeg")
    if exe:
        return exe

    try:
        import imageio_ffmpeg
        img_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if img_exe and os.path.isfile(img_exe):
            target = Path(img_exe).parent / "ffmpeg.exe"
            if not target.is_file():
                try:
                    shutil.copy2(img_exe, target)
                except Exception:
                    pass
            if target.is_file():
                return str(target)
            return img_exe
    except Exception:
        pass
    return None


def find_node() -> str | None:
    base = get_base_dir()
    for candidate in [
        base / "_internal" / "bin" / "node.exe",
        base / "bin" / "node.exe",
        base / "node.exe",
        Path(r"C:\Program Files\nodejs\node.exe"),
    ]:
        if candidate.is_file():
            return str(candidate)

    return shutil.which("node")


def find_bgutil_server() -> str | None:
    base = get_base_dir()
    candidates = [
        base / "_internal" / "bgutil_provider" / "server",
        base / "bgutil_provider" / "server",
        Path.home() / "bgutil-ytdlp-pot-provider" / "server",
    ]
    for c in candidates:
        if (c / "build" / "generate_once.js").is_file():
            return str(c)
    return None


def find_js_runtimes() -> dict:
    runtimes = {}
    node = find_node()
    if node:
        runtimes["node"] = {"path": node}
    for name in ("deno", "bun"):
        path = shutil.which(name)
        if path:
            runtimes[name] = {"path": path}
    return runtimes


def tier_name(width: int, height: int) -> str:
    side = max(width or 0, height or 0)
    if side >= 7680:
        return "8K Ultra HD"
    if side >= 3840:
        return "4K Ultra HD"
    if side >= 2560:
        return "2K Quad HD"
    if side >= 1920:
        return "Full HD 1080p"
    if side >= 1280:
        return "HD 720p"
    return ""


def human_bytes(n: float | None) -> str:
    if not n:
        return "0 MB"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def human_time(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def clean_error(exc: Exception) -> str:
    msg = ANSI_RE.sub("", str(exc)).strip()
    return msg.removeprefix("ERROR:").strip() or exc.__class__.__name__


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    try:
        SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def default_download_dir() -> str:
    downloads = Path.home() / "Downloads"
    return str(downloads if downloads.exists() else Path.home())


def open_in_explorer(path: str) -> None:
    if sys.platform.startswith("win"):
        if os.path.isfile(path):
            subprocess.run(["explorer", "/select,", os.path.normpath(path)])
        else:
            os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", "-R" if os.path.isfile(path) else "", path])
    else:
        subprocess.run(["xdg-open", os.path.dirname(path) if os.path.isfile(path) else path])


def check_cookie_auth(path: Path | str | None) -> bool:
    if not path:
        return False
    p = Path(path)
    if not p.is_file():
        return False
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
        auth_markers = ("LOGIN_INFO", "SAPISID", "SID", "SSID", "HSID", "__Secure-1PSID", "__Secure-3PSID")
        return any(marker in content for marker in auth_markers)
    except Exception:
        return False


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(f"{APP_NAME} — YouTube 4K Downloader")
        self.geometry("820x760")
        self.minsize(780, 700)
        self.configure(fg_color=COLOR_BG)

        self.base_dir = get_base_dir()
        icon_ico = self.base_dir / "assets" / "icon.ico"
        icon_png = self.base_dir / "assets" / "icon.png"
        if not icon_ico.is_file():
            icon_ico = self.base_dir / "_internal" / "assets" / "icon.ico"
        if not icon_png.is_file():
            icon_png = self.base_dir / "_internal" / "assets" / "icon.png"
        if icon_ico.is_file():
            try:
                self.iconbitmap(str(icon_ico))
            except Exception:
                pass

        self.events: queue.Queue = queue.Queue()
        self.cancel_flag = threading.Event()
        self.busy = False
        self.info: dict | None = None
        self.quality_map: dict[str, int | None] = {}
        self.last_file: str | None = None

        self.is_playlist = False
        self.playlist_count = 1
        self.ffmpeg = find_ffmpeg()
        self.js_runtimes = find_js_runtimes()
        self.bgutil_server = find_bgutil_server()
        self.settings = load_settings()

        self.url_var = ctk.StringVar()
        self.quality_var = ctk.StringVar(value=BEST)
        self.container_var = ctk.StringVar(value=self.settings.get("container", "MP4"))
        self.folder_var = ctk.StringVar(value=self.settings.get("folder", default_download_dir()))

        default_cookie_file = self.base_dir / "cookies.txt"
        self.cookie_file = self.settings.get("cookie_file", "")
        if default_cookie_file.is_file() and not self.cookie_file:
            self.cookie_file = str(default_cookie_file)
            self.settings["cookie_file"] = self.cookie_file

        saved_cookies = self.settings.get("cookies")
        if not saved_cookies:
            if check_cookie_auth(self.cookie_file) or check_cookie_auth(default_cookie_file):
                saved_cookies = COOKIE_FILE
            else:
                saved_cookies = NO_COOKIES
        self.cookies_var = ctk.StringVar(value=saved_cookies)

        self.status_var = ctk.StringVar(value="Cole o link de um vídeo do YouTube e clique em Analisar.")
        self.progress_detail_var = ctk.StringVar(value="")

        self.thumb_image: ctk.CTkImage | None = None
        self._build_ui(icon_png)
        self._set_state()
        self._update_auth_ui()
        self._on_format_changed(self.container_var.get())
        self.after(100, self._poll_events)
        self.after(600, self._check_login_on_startup)

    def _build_ui(self, icon_png: Path) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 12), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        if icon_png.is_file():
            try:
                logo_pil = Image.open(icon_png).resize((52, 52), Image.Resampling.LANCZOS)
                self.logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(52, 52))
                logo_label = ctk.CTkLabel(header, image=self.logo_img, text="")
                logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 14), sticky="w")
            except Exception:
                pass

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=1, rowspan=2, sticky="w")

        title_row = ctk.CTkFrame(title_box, fg_color="transparent")
        title_row.pack(anchor="w")

        title_lbl = ctk.CTkLabel(
            title_row,
            text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(side="left")

        badge_4k = ctk.CTkLabel(
            title_row,
            text=" 4K ULTRA HD ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#D97706",
            text_color="#FFFFFF",
            corner_radius=6,
        )
        badge_4k.pack(side="left", padx=10)

        sub_lbl = ctk.CTkLabel(
            title_box,
            text="Baixe vídeos, playlists e áudios do YouTube na resolução máxima sem restrições",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        tutorial_btn = ctk.CTkButton(
            header,
            text="📖 Como Usar",
            width=115,
            height=36,
            corner_radius=8,
            fg_color=COLOR_CARD_ALT,
            hover_color=COLOR_CARD_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.open_tutorial,
        )
        tutorial_btn.grid(row=0, column=2, rowspan=2, padx=(10, 0), sticky="e")

        main_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLOR_CARD_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT,
        )
        main_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        card_url = ctk.CTkFrame(main_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card_url.pack(fill="x", pady=8, padx=4)
        card_url.grid_columnconfigure(0, weight=1)

        url_lbl = ctk.CTkLabel(
            card_url,
            text="Link do Vídeo ou Playlist:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        url_lbl.grid(row=0, column=0, columnspan=3, padx=18, pady=(14, 6), sticky="w")

        self.url_entry = ctk.CTkEntry(
            card_url,
            textvariable=self.url_var,
            placeholder_text="Cole o link do YouTube aqui (vídeo ou playlist)...",
            height=44,
            corner_radius=8,
            border_color=COLOR_CARD_BORDER,
            fg_color=COLOR_CARD_ALT,
            text_color=COLOR_TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.url_entry.grid(row=1, column=0, padx=(18, 10), pady=(0, 16), sticky="ew")
        self.url_entry.bind("<Return>", lambda _e: self.analyze())

        paste_btn = ctk.CTkButton(
            card_url,
            text="📋 Colar",
            width=85,
            height=44,
            corner_radius=8,
            fg_color=COLOR_CARD_ALT,
            hover_color=COLOR_CARD_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.paste_from_clipboard,
        )
        paste_btn.grid(row=1, column=1, padx=(0, 10), pady=(0, 16))

        self.analyze_btn = ctk.CTkButton(
            card_url,
            text="Analisar Vídeo",
            width=135,
            height=44,
            corner_radius=8,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.analyze,
        )
        self.analyze_btn.grid(row=1, column=2, padx=(0, 18), pady=(0, 16))

        self.card_info = ctk.CTkFrame(main_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        self.card_info.grid_columnconfigure(1, weight=1)

        self.thumb_label = ctk.CTkLabel(self.card_info, text="", width=180, height=101, fg_color=COLOR_CARD_ALT, corner_radius=8)
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=16, pady=16, sticky="nw")

        self.video_title_lbl = ctk.CTkLabel(
            self.card_info,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
            wraplength=480,
            justify="left",
            anchor="w",
        )
        self.video_title_lbl.grid(row=0, column=1, padx=(0, 16), pady=(16, 4), sticky="nw")

        self.video_meta_lbl = ctk.CTkLabel(
            self.card_info,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
            justify="left",
            anchor="w",
        )
        self.video_meta_lbl.grid(row=1, column=1, padx=(0, 16), pady=(0, 4), sticky="nw")

        self.video_tier_badge = ctk.CTkLabel(
            self.card_info,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_ACCENT,
            text_color="#FFFFFF",
            corner_radius=6,
        )
        self.video_tier_badge.grid(row=2, column=1, padx=(0, 16), pady=(0, 16), sticky="w")

        card_settings = ctk.CTkFrame(main_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card_settings.pack(fill="x", pady=8, padx=4)
        card_settings.grid_columnconfigure((0, 1), weight=1)

        self.q_label = ctk.CTkLabel(
            card_settings,
            text="Qualidade Desejada:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.q_label.grid(row=0, column=0, padx=18, pady=(14, 6), sticky="w")

        self.quality_menu = ctk.CTkOptionMenu(
            card_settings,
            variable=self.quality_var,
            values=[BEST],
            height=38,
            corner_radius=8,
            fg_color=COLOR_CARD_ALT,
            button_color=COLOR_CARD_BORDER,
            button_hover_color=COLOR_ACCENT,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color=COLOR_ACCENT,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.quality_menu.grid(row=1, column=0, padx=(18, 12), pady=(0, 16), sticky="ew")

        fmt_label = ctk.CTkLabel(
            card_settings,
            text="Formato Final:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        fmt_label.grid(row=0, column=1, padx=12, pady=(14, 6), sticky="w")

        self.format_menu = ctk.CTkSegmentedButton(
            card_settings,
            variable=self.container_var,
            values=["MP4", "MKV", "MP3"],
            height=38,
            corner_radius=8,
            selected_color=COLOR_ACCENT,
            selected_hover_color=COLOR_ACCENT_HOVER,
            unselected_color=COLOR_CARD_ALT,
            unselected_hover_color=COLOR_CARD_BORDER,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._on_format_changed,
        )
        self.format_menu.grid(row=1, column=1, padx=(12, 18), pady=(0, 16), sticky="ew")

        dest_label = ctk.CTkLabel(
            card_settings,
            text="Salvar na Pasta:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        dest_label.grid(row=2, column=0, columnspan=2, padx=18, pady=(0, 6), sticky="w")

        self.folder_entry = ctk.CTkEntry(
            card_settings,
            textvariable=self.folder_var,
            height=38,
            corner_radius=8,
            state="readonly",
            border_color=COLOR_CARD_BORDER,
            fg_color=COLOR_CARD_ALT,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.folder_entry.grid(row=3, column=0, padx=(18, 12), pady=(0, 16), sticky="ew")

        self.folder_btn = ctk.CTkButton(
            card_settings,
            text="📁 Escolher Pasta",
            height=38,
            corner_radius=8,
            fg_color=COLOR_CARD_ALT,
            hover_color=COLOR_CARD_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.choose_folder,
        )
        self.folder_btn.grid(row=3, column=1, padx=(12, 18), pady=(0, 16), sticky="ew")

        card_auth = ctk.CTkFrame(main_frame, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=12)
        card_auth.pack(fill="x", pady=8, padx=4)
        card_auth.grid_columnconfigure(0, weight=1)

        auth_header = ctk.CTkFrame(card_auth, fg_color="transparent")
        auth_header.grid(row=0, column=0, columnspan=3, padx=18, pady=(14, 8), sticky="ew")
        auth_header.grid_columnconfigure(1, weight=1)

        auth_title = ctk.CTkLabel(
            auth_header,
            text="Autenticação do YouTube (Anti-Robô):",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        auth_title.grid(row=0, column=0, sticky="w")

        self.auth_badge = ctk.CTkLabel(
            auth_header,
            text="  Não conectado  ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_CARD_ALT,
            text_color=COLOR_TEXT_MUTED,
            corner_radius=6,
        )
        self.auth_badge.grid(row=0, column=2, sticky="e")

        self.login_btn = ctk.CTkButton(
            card_auth,
            text="🔑 Fazer Login no YouTube",
            height=38,
            corner_radius=8,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.open_embedded_login,
        )
        self.login_btn.grid(row=1, column=0, padx=(18, 12), pady=(0, 14), sticky="w")

        cookie_opts_frame = ctk.CTkFrame(card_auth, fg_color="transparent")
        cookie_opts_frame.grid(row=1, column=1, columnspan=2, padx=(0, 18), pady=(0, 14), sticky="e")

        ctk.CTkLabel(
            cookie_opts_frame,
            text="Ou usar cookies de:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
        ).pack(side="left", padx=(0, 8))

        self.cookies_box = ctk.CTkOptionMenu(
            cookie_opts_frame,
            variable=self.cookies_var,
            values=[NO_COOKIES, COOKIE_FILE, *BROWSERS],
            height=34,
            corner_radius=8,
            fg_color=COLOR_CARD_ALT,
            button_color=COLOR_CARD_BORDER,
            button_hover_color=COLOR_ACCENT,
            dropdown_fg_color=COLOR_CARD,
            command=lambda _val: self._on_cookies_selected(),
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self.cookies_box.pack(side="left")

        bottom = ctk.CTkFrame(self, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=16)
        bottom.grid(row=2, column=0, padx=20, pady=(6, 18), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(16, 12))
        actions.grid_columnconfigure(0, weight=1)

        self.download_btn = ctk.CTkButton(
            actions,
            text="⬇ BAIXAR VÍDEO",
            height=46,
            corner_radius=10,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.download,
        )
        self.download_btn.grid(row=0, column=0, sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            actions,
            text="Cancelar",
            height=46,
            width=100,
            corner_radius=10,
            fg_color=COLOR_CARD_ALT,
            hover_color=COLOR_CARD_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.cancel,
        )
        self.cancel_btn.grid(row=0, column=1, padx=(10, 0))

        self.open_btn = ctk.CTkButton(
            actions,
            text="📂 Abrir Pasta",
            height=46,
            width=120,
            corner_radius=10,
            fg_color=COLOR_CARD_ALT,
            hover_color=COLOR_CARD_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.open_folder,
        )
        self.open_btn.grid(row=0, column=2, padx=(10, 0))

        self.progress = ctk.CTkProgressBar(
            bottom,
            height=10,
            corner_radius=5,
            progress_color=COLOR_ACCENT,
            fg_color=COLOR_CARD_ALT,
        )
        self.progress.pack(fill="x", padx=18, pady=(0, 6))
        self.progress.set(0)

        status_box = ctk.CTkFrame(bottom, fg_color="transparent")
        status_box.pack(fill="x", padx=18, pady=(0, 14))
        status_box.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            status_box,
            textvariable=self.status_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.status_lbl.grid(row=0, column=0, sticky="w")

        self.progress_detail_lbl = ctk.CTkLabel(
            status_box,
            textvariable=self.progress_detail_var,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
            anchor="e",
        )
        self.progress_detail_lbl.grid(row=0, column=1, sticky="e")

        if not self.ffmpeg:
            self.status_var.set("⚠ ffmpeg não detectado: downloads serão limitados a 720p.")

    def paste_from_clipboard(self) -> None:
        try:
            text = self.clipboard_get()
            if text:
                self.url_var.set(text.strip())
                self.analyze()
        except Exception:
            pass

    def is_logged_in(self) -> bool:
        if self.cookies_var.get() in BROWSERS:
            return True
        if self.cookies_var.get() == NO_COOKIES:
            return False
        target = self.cookie_file if (self.cookie_file and os.path.isfile(self.cookie_file)) else (self.base_dir / "cookies.txt")
        return check_cookie_auth(target)

    def _check_login_on_startup(self) -> None:
        if not self.is_logged_in():
            ans = messagebox.askyesno(
                APP_NAME,
                "Você ainda não conectou sua conta do YouTube.\n\n"
                "Fazer login evita o erro 403 (Forbidden), bloqueios anti-robô e permite baixar em 4K e resoluções máximas.\n\n"
                "Deseja fazer login na sua conta do YouTube agora?",
            )
            if ans:
                self.open_embedded_login()

    def prompt_login_if_not_logged(self, action_desc: str = "esta ação") -> bool:
        if self.is_logged_in():
            return True
        resp = messagebox.askyesnocancel(
            APP_NAME,
            f"Você ainda não fez login no YouTube.\n\n"
            f"Para {action_desc} com segurança (evitando bloqueios de robô e erro 403), é recomendado conectar sua conta.\n\n"
            f"• Sim: Fazer login agora no YouTube\n"
            f"• Não: Continuar sem login\n"
            f"• Cancelar: Voltar",
        )
        if resp is True:
            self.open_embedded_login()
            return False
        elif resp is False:
            return True
        return False

    def _update_auth_ui(self) -> None:
        if self.is_logged_in():
            if self.cookies_var.get() in BROWSERS:
                self.auth_badge.configure(
                    text=f"  ✔ Navegador {self.cookies_var.get()}  ",
                    fg_color=COLOR_SUCCESS,
                    text_color="#FFFFFF",
                )
            else:
                self.auth_badge.configure(
                    text="  ✔ Conta Conectada  ",
                    fg_color=COLOR_SUCCESS,
                    text_color="#FFFFFF",
                )
            self.login_btn.configure(
                text="🔄 Trocar Conta",
                fg_color=COLOR_CARD_ALT,
                hover_color=COLOR_CARD_BORDER,
            )
        else:
            self.auth_badge.configure(
                text="  ⚠ Não Conectado (Exigido p/ 4K)  ",
                fg_color=COLOR_WARNING,
                text_color="#000000",
            )
            self.login_btn.configure(
                text="🔑 Fazer Login no YouTube",
                fg_color="#2563EB",
                hover_color="#1D4ED8",
            )

    def _on_format_changed(self, value: str | None = None) -> None:
        val = (value or self.container_var.get()).upper()
        if val == "MP3":
            self.q_label.configure(text="Qualidade do Áudio (Bitrate):")
            self.quality_menu.configure(values=list(AUDIO_QUALITY_MAP.keys()))
            if self.quality_var.get() not in AUDIO_QUALITY_MAP:
                self.quality_var.set(list(AUDIO_QUALITY_MAP.keys())[0])
            if getattr(self, "is_playlist", False):
                self.download_btn.configure(text=f"⬇ BAIXAR PLAYLIST EM MP3 ({self.playlist_count} faixas)")
            else:
                self.download_btn.configure(text="⬇ BAIXAR ÁUDIO (MP3)")
        else:
            self.q_label.configure(text="Qualidade Desejada:")
            values = list(self.quality_map.keys()) if self.quality_map else [BEST]
            self.quality_menu.configure(values=values)
            if self.quality_var.get() not in values:
                self.quality_var.set(values[0] if getattr(self, "is_playlist", False) else (values[1] if len(values) > 1 else BEST))
            if getattr(self, "is_playlist", False):
                self.download_btn.configure(text=f"⬇ BAIXAR PLAYLIST COMPLETA ({self.playlist_count} vídeos)")
            else:
                self.download_btn.configure(text="⬇ BAIXAR VÍDEO")
        self._persist()

    def _set_state(self) -> None:
        busy = self.busy
        self.analyze_btn.configure(state="disabled" if busy else "normal")
        self.url_entry.configure(state="disabled" if busy else "normal")
        self.folder_btn.configure(state="disabled" if busy else "normal")
        can_download = not busy and self.info is not None
        self.download_btn.configure(state="normal" if can_download else "disabled")
        if getattr(self, "is_playlist", False):
            if self.container_var.get().upper() == "MP3":
                self.download_btn.configure(text=f"⬇ BAIXAR PLAYLIST EM MP3 ({self.playlist_count} faixas)")
            else:
                self.download_btn.configure(text=f"⬇ BAIXAR PLAYLIST COMPLETA ({self.playlist_count} vídeos)")
        else:
            if self.container_var.get().upper() == "MP3":
                self.download_btn.configure(text="⬇ BAIXAR ÁUDIO (MP3)")
            else:
                self.download_btn.configure(text="⬇ BAIXAR VÍDEO")
        self.quality_menu.configure(state="normal" if can_download else "disabled")
        self.format_menu.configure(state="normal" if not busy else "disabled")
        self.cookies_box.configure(state="normal" if not busy else "disabled")
        self.login_btn.configure(state="disabled" if busy else "normal")
        self.cancel_btn.configure(state="normal" if busy else "disabled")

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.folder_var.get(), title="Escolha onde salvar")
        if folder:
            self.folder_var.set(folder)
            self._persist()

    def open_folder(self) -> None:
        target = self.last_file if self.last_file and os.path.exists(self.last_file) else self.folder_var.get()
        open_in_explorer(target)

    def cancel(self) -> None:
        self.cancel_flag.set()
        self.status_var.set("Cancelando download…")

    def analyze(self) -> None:
        url = self.url_var.get().strip()
        if not url or self.busy:
            return
        if ("watch?" in url or "watch/" in url) and "list=" in url:
            ans = messagebox.askyesno(
                APP_NAME,
                "O link informado contém um vídeo que pertence a uma Playlist.\n\n"
                "Deseja carregar a PLAYLIST COMPLETA?\n\n"
                "• Sim: Analisar e baixar todos os vídeos da Playlist\n"
                "• Não: Analisar e baixar apenas este vídeo individual",
            )
            if not ans:
                url = re.sub(r"[&?]list=[^&]+", "", url)
                self.url_var.set(url)

        if not self.prompt_login_if_not_logged("analisar este conteúdo"):
            return
        self.info = None
        self.is_playlist = False
        self.playlist_count = 1
        self.card_info.pack_forget()
        self.quality_menu.configure(values=[BEST])
        self.quality_var.set(BEST)
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status_var.set("Buscando informações do vídeo/playlist e resoluções disponíveis…")
        self.progress_detail_var.set("")
        self._run_worker(self._analyze_worker, url)

    def download(self) -> None:
        if self.busy or not self.info:
            return
        folder = self.folder_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror(APP_NAME, "A pasta de destino não existe.")
            return
        is_audio = self.container_var.get().upper() == "MP3"
        item_type = "a playlist" if getattr(self, "is_playlist", False) else "o vídeo"
        action_desc = f"baixar {item_type} em MP3" if is_audio else f"baixar {item_type} em alta qualidade"
        if not self.prompt_login_if_not_logged(action_desc):
            return
        self._persist()
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        container = self.container_var.get().lower()
        playlist_title = self.info.get("title") or "Playlist"
        webpage_url = self.info.get("webpage_url") or self.url_var.get().strip()
        is_pl = getattr(self, "is_playlist", False)

        if is_audio:
            bitrate = AUDIO_QUALITY_MAP.get(self.quality_var.get(), "320")
            msg = f"Iniciando download da playlist em MP3 ({bitrate} kbps)…" if is_pl else f"Iniciando download do áudio em MP3 ({bitrate} kbps)…"
            self.status_var.set(msg)
            self.progress_detail_var.set("0%")
            self._run_worker(self._download_worker, webpage_url, None, "mp3", folder, bitrate, is_pl, playlist_title)
        else:
            height = self.quality_map.get(self.quality_var.get())
            msg = "Iniciando download da playlist completa…" if is_pl else "Iniciando download em alta qualidade…"
            self.status_var.set(msg)
            self.progress_detail_var.set("0%")
            self._run_worker(self._download_worker, webpage_url, height, container, folder, "320", is_pl, playlist_title)

    def _persist(self) -> None:
        self.settings.update(
            folder=self.folder_var.get(),
            container=self.container_var.get(),
            cookies=self.cookies_var.get(),
            cookie_file=self.cookie_file,
        )
        save_settings(self.settings)

    def open_tutorial(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("All Down — Como Usar")
        win.geometry("640x620")
        win.minsize(580, 520)
        win.configure(fg_color=COLOR_BG)
        win.transient(self)
        win.grab_set()

        top_bar = ctk.CTkFrame(win, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(20, 10))

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="📖 Guia Rápido de Uso",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            top_bar,
            text="Aprenda a aproveitar o máximo do All Down em poucos passos simples.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        scroll = ctk.CTkScrollableFrame(
            win,
            fg_color="transparent",
            scrollbar_button_color=COLOR_CARD_BORDER,
            scrollbar_button_hover_color=COLOR_ACCENT,
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        steps = [
            (
                "🔑 1. Conectar sua Conta do YouTube (Anti-Bloqueio)",
                "O YouTube impõe restrições contra robôs (erro HTTP 403 Forbidden) e bloqueia streams 4K/8K para quem não está logado.\n\n"
                "• Clique no botão '🔑 Fazer Login no YouTube' e entre com sua conta na janela oficial do Google.\n"
                "• Ao concluir, o badge verde '✔ Conta Conectada' confirma que você tem acesso total e velocidade máxima.",
                "#10B981",
            ),
            (
                "📋 2. Colar o Link do Vídeo ou Playlist",
                "Copie a URL de qualquer vídeo ou playlist do YouTube (ex: https://www.youtube.com/watch?v=... ou https://www.youtube.com/playlist?list=...).\n\n"
                "• No All Down, clique no botão '📋 Colar' ou use o atalho Ctrl + V.\n"
                "• Se colar um vídeo que pertence a uma playlist, o app perguntará se você quer baixar a playlist inteira ou só aquele vídeo.",
                "#3B82F6",
            ),
            (
                "🔍 3. Analisar o Conteúdo",
                "Clique em 'Analisar Vídeo' (ou pressione Enter no campo de link).\n\n"
                "• O app consulta o YouTube e exibe thumbnail, título, canal, duração e todas as resoluções reais disponíveis.",
                "#8B5CF6",
            ),
            (
                "⚙️ 4. Escolher o Formato e a Qualidade",
                "Você escolhe exatamente como quer salvar:\n\n"
                "• MP4: Vídeo com máxima compatibilidade com TVs, celulares e editores.\n"
                "• MKV: Vídeo preservando codecs originais de alta definição.\n"
                "• MP3: Baixa somente o áudio convertido em MP3 (bitrate de até 320 kbps de altíssima fidelidade) com tags e metadados inclusos.\n"
                "• Escolha a resolução desejada (ex: 4K Ultra HD, 1080p Full HD) ou a taxa de bits do áudio.",
                "#F59E0B",
            ),
            (
                "📁 5. Playlists Organizadas Automaticamente",
                "Ao baixar uma playlist completa, o All Down cria automaticamente uma subpasta com o nome da playlist dentro da sua pasta de destino.\n\n"
                "• Todos os arquivos são numerados sequencialmente (ex: '01 - Nome [1080p].mp4' ou '01 - Faixa.mp3').\n"
                "• Vídeos indisponíveis ou privados são pulados automaticamente sem travar a lista.",
                "#EC4899",
            ),
            (
                "⬇️ 6. Baixar e Abrir Pasta",
                "Clique no botão vermelho '⬇ BAIXAR VÍDEO' (ou '⬇ BAIXAR PLAYLIST' / '⬇ BAIXAR ÁUDIO (MP3)').\n\n"
                "• Acompanhe em tempo real o progresso percentual, velocidade de download e tempo restante.\n"
                "• Ao finalizar, clique em '📂 Abrir Pasta' para ir direto até os arquivos prontos!",
                COLOR_ACCENT,
            ),
        ]

        for title, desc, color in steps:
            card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=10)
            card.pack(fill="x", pady=6, padx=4)

            header_step = ctk.CTkFrame(card, fg_color="transparent")
            header_step.pack(fill="x", padx=16, pady=(12, 6))

            ctk.CTkLabel(
                header_step,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=color,
            ).pack(side="left")

            ctk.CTkLabel(
                card,
                text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLOR_TEXT_PRIMARY,
                wraplength=520,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 14))

        close_btn = ctk.CTkButton(
            win,
            text="Entendi, Fechar Guia",
            height=42,
            corner_radius=8,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=win.destroy,
        )
        close_btn.pack(fill="x", padx=24, pady=16)

    def open_embedded_login(self) -> None:
        self.login_btn.configure(state="disabled")
        self.status_var.set("Abrindo janela de login no YouTube… Entre na sua conta e aguarde a confirmação.")

        def _worker():
            try:
                if getattr(sys, "frozen", False):
                    cmd = [sys.executable, "--login"]
                else:
                    cmd = [sys.executable, str(self.base_dir / "login.py")]

                proc = subprocess.run(cmd, capture_output=True, text=True)
                cookie_target = self.base_dir / "cookies.txt"
                if "SUCCESS:" in proc.stdout or cookie_target.is_file():
                    self.events.put(("login_success", str(cookie_target)))
                else:
                    self.events.put(("login_cancelled", None))
            except Exception as e:
                self.events.put(("login_error", str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_cookies_selected(self) -> None:
        if self.cookies_var.get() == COOKIE_FILE:
            path = filedialog.askopenfilename(
                title="Escolha o arquivo cookies.txt exportado do navegador",
                filetypes=[("Cookies (Netscape)", "*.txt"), ("Todos os arquivos", "*.*")],
                initialdir=os.path.dirname(self.cookie_file) if self.cookie_file else default_download_dir(),
            )
            if path:
                self.cookie_file = path
            elif not os.path.isfile(self.cookie_file):
                self.cookies_var.set(NO_COOKIES)
        self._update_auth_ui()
        self._persist()

    def _run_worker(self, target, *args) -> None:
        self.busy = True
        self.cancel_flag.clear()
        self._set_state()
        threading.Thread(target=target, args=args, daemon=True).start()

    def _base_opts(self, is_playlist: bool = False) -> dict:
        extractor_args = {
            "youtube": {
                "player_client": ["mweb", "web_embedded", "web"]
            }
        }
        if self.bgutil_server and os.path.isdir(self.bgutil_server):
            extractor_args["youtubepot-bgutilscript"] = {
                "server_home": [str(self.bgutil_server)]
            }

        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": not is_playlist,
            "noprogress": True,
            "extractor_args": extractor_args,
        }
        if self.ffmpeg:
            opts["ffmpeg_location"] = self.ffmpeg
        if self.js_runtimes:
            opts["js_runtimes"] = self.js_runtimes

        browser = BROWSERS.get(self.cookies_var.get())
        if browser:
            opts["cookiesfrombrowser"] = (browser,)
        elif self.cookies_var.get() == COOKIE_FILE:
            target = self.cookie_file if (self.cookie_file and os.path.isfile(self.cookie_file)) else str(self.base_dir / "cookies.txt")
            if os.path.isfile(target):
                opts["cookiefile"] = target
        elif self.cookies_var.get() != NO_COOKIES:
            default_cookie = self.base_dir / "cookies.txt"
            if default_cookie.is_file():
                opts["cookiefile"] = str(default_cookie)

        return opts

    def _analyze_worker(self, url: str) -> None:
        try:
            is_plist_url = ("playlist?list=" in url) or ("list=" in url and "watch" not in url) or ("list=" in url)
            analyze_opts = self._base_opts(is_playlist=is_plist_url) | {"extract_flat": "in_playlist"}
            with yt_dlp.YoutubeDL(analyze_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            is_playlist = info.get("_type") == "playlist" or "entries" in info
            thumb_pil = None
            thumb_url = None

            if is_playlist:
                entries = list(info.get("entries") or [])
                thumb_url = info.get("thumbnail")
                if not thumb_url:
                    for e in entries:
                        if isinstance(e, dict):
                            if e.get("thumbnail"):
                                thumb_url = e.get("thumbnail")
                                break
                            elif e.get("thumbnails"):
                                thumb_url = e.get("thumbnails")[-1].get("url")
                                break
            else:
                thumb_url = info.get("thumbnail")

            if thumb_url:
                try:
                    req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        img_bytes = resp.read()
                        raw_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                        thumb_pil = raw_pil.resize((180, 101), Image.Resampling.LANCZOS)
                except Exception:
                    pass

            self.events.put(("info", (info, thumb_pil, is_playlist)))
        except Exception as exc:
            self.events.put(("error", clean_error(exc)))

    def _download_worker(self, url: str, height: int | None, container: str, folder: str, bitrate: str = "320", is_playlist: bool = False, playlist_title: str = "") -> None:
        target_folder = folder
        if is_playlist:
            clean_title = re.sub(r'[<>:"/\\|?*]', "_", playlist_title).strip() or "Playlist"
            target_folder = os.path.join(folder, clean_title)
            os.makedirs(target_folder, exist_ok=True)

        if container == "mp3":
            fmt = "ba/b"
            if is_playlist:
                outtmpl = os.path.join(target_folder, "%(playlist_index)02d - %(title)s.%(ext)s")
            else:
                outtmpl = os.path.join(target_folder, "%(title)s.%(ext)s")
            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate,
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ]
            opts = self._base_opts(is_playlist=is_playlist) | {
                "format": fmt,
                "outtmpl": outtmpl,
                "postprocessors": postprocessors,
                "windowsfilenames": True,
                "concurrent_fragment_downloads": 4,
                "ignoreerrors": is_playlist,
                "progress_hooks": [self._progress_hook],
                "postprocessor_hooks": [self._postprocessor_hook],
            }
        else:
            if height is None:
                fmt = "bv*+ba/b"
            elif container == "mp4":
                fmt = (
                    f"bv*[height={height}]+ba[ext=m4a]/bv*[height={height}]+ba/b[height={height}]"
                    f"/bv*[height<={height}]+ba/b"
                )
            else:
                fmt = f"bv*[height={height}]+ba/b[height={height}]/bv*[height<={height}]+ba/b"

            if is_playlist:
                outtmpl = os.path.join(target_folder, "%(playlist_index)02d - %(title)s [%(height)sp].%(ext)s")
            else:
                outtmpl = os.path.join(target_folder, "%(title)s [%(height)sp].%(ext)s")

            opts = self._base_opts(is_playlist=is_playlist) | {
                "format": fmt,
                "merge_output_format": container,
                "outtmpl": outtmpl,
                "windowsfilenames": True,
                "concurrent_fragment_downloads": 4,
                "ignoreerrors": is_playlist,
                "progress_hooks": [self._progress_hook],
                "postprocessor_hooks": [self._postprocessor_hook],
            }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            if is_playlist:
                self.events.put(("done", target_folder))
            else:
                downloads = info.get("requested_downloads") or [{}]
                path = downloads[0].get("filepath") or downloads[0].get("_filename")
                if container == "mp3" and path:
                    mp3_candidate = os.path.splitext(path)[0] + ".mp3"
                    if os.path.isfile(mp3_candidate):
                        path = mp3_candidate
                self.events.put(("done", path))
        except DownloadCancelled:
            self.events.put(("cancelled", None))
        except Exception as exc:
            if self.cancel_flag.is_set():
                self.events.put(("cancelled", None))
            else:
                self.events.put(("error", clean_error(exc)))

    def _progress_hook(self, d: dict) -> None:
        if self.cancel_flag.is_set():
            raise DownloadCancelled()
        fmt = d.get("info_dict") or {}
        kind = "áudio" if fmt.get("vcodec") == "none" else "vídeo"
        idx = fmt.get("playlist_index")
        total_items = fmt.get("n_entries") or fmt.get("playlist_count")
        prefix = f"[{idx}/{total_items}] " if (idx and total_items) else ""

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            pct = (done / total) if total else 0
            pct_val = pct * 100
            eta = human_time(d.get("eta"))
            speed = f"{human_bytes(d.get('speed'))}/s"
            status_text = f"{prefix}Baixando {kind}: {human_bytes(done)} de {human_bytes(total)}  •  Velocidade: {speed}  •  Restante: {eta}"
            self.events.put(("progress", (pct, f"{pct_val:.0f}%", status_text)))
        elif d["status"] == "finished":
            self.events.put(("progress", (1.0, "100%", f"{prefix}Download do {kind} concluído com sucesso.")))

    def _postprocessor_hook(self, d: dict) -> None:
        if d["status"] == "started":
            pp = d.get("postprocessor")
            if pp == "Merger":
                self.events.put(("merging", None))
            elif pp in ("ExtractAudio", "FFmpegExtractAudio"):
                self.events.put(("converting_audio", None))

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                getattr(self, f"_on_{kind}")(payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _finish(self, status: str) -> None:
        self.busy = False
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.status_var.set(status)
        self._set_state()

    def _on_info(self, payload: tuple) -> None:
        info, thumb_pil, is_playlist = payload
        self.info = info
        self.is_playlist = is_playlist

        if thumb_pil:
            self.thumb_image = ctk.CTkImage(light_image=thumb_pil, dark_image=thumb_pil, size=(180, 101))
            self.thumb_label.configure(image=self.thumb_image, text="")
        else:
            self.thumb_label.configure(image=None, text="Sem Prévia")

        if is_playlist:
            entries = list(info.get("entries") or [])
            self.playlist_count = len(entries)
            title = info.get("title") or "Playlist"
            channel = info.get("uploader") or info.get("channel") or "YouTube"

            self.video_title_lbl.configure(text=f"📋 {title}")
            self.video_meta_lbl.configure(text=f"📺 {channel}   •   📋 {self.playlist_count} vídeos na playlist")
            self.video_tier_badge.configure(text=f"  PLAYLIST ({self.playlist_count} VÍDEOS)  ", fg_color="#8B5CF6")

            self.quality_map = {
                BEST: None,
                "4K Ultra HD (2160p)": 2160,
                "2K Quad HD (1440p)": 1440,
                "Full HD (1080p)": 1080,
                "HD (720p)": 720,
                "SD (480p)": 480,
            }
        else:
            self.playlist_count = 1
            title = info.get("title", "Sem título")
            channel = info.get("uploader") or info.get("channel") or "Canal Desconhecido"
            duration = human_time(info.get("duration"))

            self.video_title_lbl.configure(text=title)
            self.video_meta_lbl.configure(text=f"📺 {channel}   •   ⏱ Duração: {duration}")

            best: dict[int, tuple[float, int]] = {}
            for f in info.get("formats") or []:
                h = f.get("height")
                if not h or f.get("vcodec") == "none" or f.get("ext") == "mhtml":
                    continue
                fps = f.get("fps") or 0
                prev = best.get(h, (0, 0))
                best[h] = (max(prev[0], fps), max(prev[1], f.get("width") or 0))

            max_h = None if self.ffmpeg else 720
            self.quality_map = {BEST: None}
            for h in sorted(best, reverse=True):
                if max_h and h > max_h:
                    continue
                fps, width = best[h]
                label = f"{h}p"
                tier = tier_name(width, h)
                if tier:
                    label += f" ({tier})"
                if fps > 30:
                    label += f" {int(round(fps))}fps"
                self.quality_map[label] = h

            has_4k = any(h >= 2160 for h in best)
            if has_4k:
                self.video_tier_badge.configure(text="  DISPONÍVEL EM 4K ULTRA HD  ", fg_color="#D97706")
            else:
                top_h = max(best.keys()) if best else 0
                self.video_tier_badge.configure(text=f"  MÁXIMA RESOLUÇÃO: {top_h}p  ", fg_color="#2563EB")

        if self.container_var.get().upper() == "MP3":
            self.q_label.configure(text="Qualidade do Áudio (Bitrate):")
            self.quality_menu.configure(values=list(AUDIO_QUALITY_MAP.keys()))
            if self.quality_var.get() not in AUDIO_QUALITY_MAP:
                self.quality_var.set(list(AUDIO_QUALITY_MAP.keys())[0])
            self.download_btn.configure(
                text=f"⬇ BAIXAR PLAYLIST EM MP3 ({self.playlist_count} faixas)" if is_playlist else "⬇ BAIXAR ÁUDIO (MP3)"
            )
        else:
            self.q_label.configure(text="Qualidade Desejada:")
            values = list(self.quality_map)
            self.quality_menu.configure(values=values)
            self.quality_var.set(values[0] if is_playlist else (values[1] if len(values) > 1 else BEST))
            self.download_btn.configure(
                text=f"⬇ BAIXAR PLAYLIST COMPLETA ({self.playlist_count} vídeos)" if is_playlist else "⬇ BAIXAR VÍDEO"
            )

        self.card_info.pack(fill="x", pady=8, padx=4, before=self.folder_entry.master)
        msg = f"Playlist com {self.playlist_count} vídeos identificada!" if is_playlist else "Vídeo identificado! Escolha o formato e a qualidade para baixar."
        self._finish(msg)
        self.progress.set(0)
        self.progress_detail_var.set("")

    def _on_progress(self, payload: tuple) -> None:
        pct, pct_text, text = payload
        self.progress.configure(mode="determinate")
        self.progress.set(pct)
        self.progress_detail_var.set(pct_text)
        self.status_var.set(text)

    def _on_merging(self, _payload) -> None:
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status_var.set("Juntando áudio e vídeo de alta fidelidade via FFmpeg…")
        self.progress_detail_var.set("Processando...")

    def _on_converting_audio(self, _payload) -> None:
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status_var.set("Extraindo e convertendo áudio para MP3 via FFmpeg…")
        self.progress_detail_var.set("Convertendo MP3...")

    def _on_done(self, path: str | None) -> None:
        self.last_file = path
        if getattr(self, "is_playlist", False):
            self._finish(f"✅ Playlist baixada com sucesso! Salva em: {path}")
        else:
            self._finish(f"✅ Download finalizado com sucesso! Arquivo salvo em: {path}" if path else "✅ Download concluído!")
        self.progress.set(1.0)
        self.progress_detail_var.set("100%")

    def _on_cancelled(self, _payload) -> None:
        self._finish("Operação cancelada pelo usuário.")
        self.progress.set(0)
        self.progress_detail_var.set("")

    def _on_login_success(self, path: str) -> None:
        self.login_btn.configure(state="normal")
        self.cookie_file = path
        self.cookies_var.set(COOKIE_FILE)
        self._update_auth_ui()
        self._persist()
        self.status_var.set("✅ Login realizado com sucesso! Sua conta está autenticada no YouTube.")
        messagebox.showinfo(APP_NAME, "Login realizado com sucesso!\nO YouTube agora reconhece sua conta.")

    def _on_login_cancelled(self, _payload) -> None:
        self.login_btn.configure(state="normal")
        self.status_var.set("Janela de login fechada.")

    def _on_login_error(self, err: str) -> None:
        self.login_btn.configure(state="normal")
        self.status_var.set(f"Erro ao autenticar: {err}")
        messagebox.showerror(APP_NAME, f"Erro ao abrir janela de login:\n{err}")

    def _on_error(self, message: str) -> None:
        self._finish(f"❌ Erro: {message}")
        self.progress.set(0)
        self.progress_detail_var.set("")
        lower = message.lower()
        if "not a bot" in lower or "sign in" in lower:
            message = (
                "O YouTube pediu confirmação anti-robô.\n\n"
                "Clique no botão '🔑 Fazer Login no YouTube' abaixo para entrar na sua conta."
            )
        messagebox.showerror(APP_NAME, message)


if __name__ == "__main__":
    app = App()
    app.mainloop()
