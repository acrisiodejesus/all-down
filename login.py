from __future__ import annotations

import sys
import threading
import time
from email.utils import parsedate_to_datetime
from pathlib import Path
import webview

LOGIN_URL = "https://accounts.google.com/ServiceLogin?service=youtube&continue=https%3A%2F%2Fwww.youtube.com"
COOKIE_TARGET = Path(__file__).parent / "cookies.txt"
STORAGE_DIR = Path.home() / ".alldown_webview"

AUTH_COOKIE_KEYS = {
    "LOGIN_INFO",
    "SID",
    "SSID",
    "HSID",
    "SAPISID",
    "APISID",
    "__Secure-1PAPISID",
    "__Secure-3PAPISID",
    "__Secure-1PSID",
    "__Secure-3PSID",
}


def cookies_to_netscape(cookie_list: list, output_file: Path) -> int:
    lines = [
        "# Netscape HTTP Cookie File",
        "# http://curl.haxx.se/rfc/cookie_spec.html",
        "# This file was generated automatically by All Down via WebView2",
        "",
    ]
    count = 0
    for cookie in cookie_list:
        for name, morsel in cookie.items():
            domain = morsel["domain"] or ".youtube.com"
            flag = "TRUE" if domain.startswith(".") else "FALSE"
            path = morsel["path"] or "/"
            secure = "TRUE" if morsel["secure"] else "FALSE"

            expires = morsel["expires"]
            if expires:
                try:
                    dt = parsedate_to_datetime(expires)
                    expiry = int(dt.timestamp())
                except Exception:
                    expiry = int(time.time() + 86400 * 365)
            else:
                expiry = int(time.time() + 86400 * 365)

            value = morsel.value
            lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")
            count += 1

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count


def has_auth_cookies(cookies: list) -> bool:
    for c in cookies:
        for k in c.keys():
            if k in AUTH_COOKIE_KEYS:
                return True
    return False


def monitor(window: webview.Window) -> None:
    time.sleep(2)
    saved = False
    for _ in range(360):
        try:
            url = window.get_current_url() or ""
            if "youtube.com" in url and "accounts.google.com" not in url:
                cookies = window.get_cookies()
                if cookies and has_auth_cookies(cookies):
                    count = cookies_to_netscape(cookies, COOKIE_TARGET)
                    print(f"SUCCESS:{count}:{COOKIE_TARGET}")
                    sys.stdout.flush()
                    saved = True
                    try:
                        window.set_title("All Down — Login Concluído! Fechando...")
                    except Exception:
                        pass
                    time.sleep(1.5)
                    window.destroy()
                    break
        except Exception:
            pass
        time.sleep(2)

    if not saved:
        try:
            cookies = window.get_cookies()
            if cookies and has_auth_cookies(cookies):
                count = cookies_to_netscape(cookies, COOKIE_TARGET)
                print(f"SUCCESS:{count}:{COOKIE_TARGET}")
                sys.stdout.flush()
        except Exception:
            pass


def main() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    window = webview.create_window(
        title="All Down — Faça login com sua conta do YouTube/Google",
        url=LOGIN_URL,
        width=580,
        height=740,
        resizable=True,
    )

    t = threading.Thread(target=monitor, args=(window,), daemon=True)
    t.start()
    webview.start(storage_path=str(STORAGE_DIR))


def run_login() -> None:
    main()


if __name__ == "__main__":
    main()
