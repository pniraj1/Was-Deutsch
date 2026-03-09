"""
pipeline/fonts.py — Cross-platform font detection.
Works on: macOS, Windows, Linux, Google Colab, GitHub Actions.
Installs Poppins automatically on Linux/Colab if missing.
"""

import glob
import os
import platform
import subprocess
import urllib.request
from pathlib import Path
from PIL import ImageFont

_POPPINS_GITHUB = "https://github.com/google/fonts/raw/main/ofl/poppins/"
_POPPINS_FILES  = ["Poppins-Bold.ttf", "Poppins-Medium.ttf", "Poppins-Regular.ttf"]
_INSTALL_DIR    = Path("/usr/local/share/fonts/poppins")

_SEARCH_DIRS = [
    # Linux / Colab
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/usr/share/fonts/truetype",
    str(_INSTALL_DIR),
    os.path.expanduser("~/.fonts"),
    # macOS
    "/Library/Fonts",
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    os.path.expanduser("~/Library/Fonts"),
    # Windows
    "C:/Windows/Fonts",
    os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts"),
]


def _find(names: list[str]) -> str | None:
    for name in names:
        for d in _SEARCH_DIRS:
            matches = glob.glob(f"{d}/**/{name}", recursive=True)
            if matches:
                return matches[0]
        try:
            r = subprocess.run(
                ["fc-match", "--format=%{file}", name.replace(".ttf", "")],
                capture_output=True, text=True, timeout=3
            )
            path = r.stdout.strip()
            if path and os.path.exists(path):
                return path
        except Exception:
            pass
    return None


def _install_poppins_linux():
    """Download Poppins from Google Fonts GitHub on Linux/Colab."""
    _INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    for fname in _POPPINS_FILES:
        dest = _INSTALL_DIR / fname
        if dest.exists():
            continue
        try:
            print(f"  Downloading {fname}...")
            urllib.request.urlretrieve(_POPPINS_GITHUB + fname, str(dest))
        except Exception as e:
            print(f"  Could not download {fname}: {e}")
    try:
        subprocess.run(["fc-cache", "-f"], capture_output=True, timeout=15)
    except Exception:
        pass


def _maybe_install():
    if platform.system() != "Linux":
        return
    if _find(["Poppins-Bold.ttf"]):
        return  # already installed
    print("  Poppins not found — installing...")
    # Try apt first (fast on Colab)
    try:
        subprocess.run(
            ["apt-get", "install", "-y", "-q", "fonts-open-sans"],
            capture_output=True, timeout=30
        )
    except Exception:
        pass
    _install_poppins_linux()


# ── PUBLIC INTERFACE ──────────────────────────────────────────────────────────
_BOLD: str | None = None
_MED:  str | None = None
_REG:  str | None = None


def init_fonts(verbose: bool = True) -> dict:
    """Detect and cache font paths. Call once at startup."""
    global _BOLD, _MED, _REG
    _maybe_install()

    _BOLD = _find(["Poppins-Bold.ttf",   "OpenSans-Bold.ttf",   "LiberationSans-Bold.ttf",
                   "FreeSansBold.ttf",    "DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"])
    _MED  = _find(["Poppins-Medium.ttf",  "Poppins-Regular.ttf", "OpenSans-Regular.ttf",
                   "LiberationSans-Regular.ttf", "FreeSans.ttf",  "DejaVuSans.ttf"])
    _REG  = _find(["Poppins-Regular.ttf", "OpenSans-Regular.ttf","LiberationSans-Regular.ttf",
                   "FreeSans.ttf",         "DejaVuSans.ttf"])

    if verbose:
        print(f"  Bold: {_BOLD or 'PIL default'}")
        print(f"  Med:  {_MED  or 'PIL default'}")
        print(f"  Reg:  {_REG  or 'PIL default'}")

    return {"bold": _BOLD, "med": _MED, "reg": _REG}


def get(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    """
    Load a font at the given size. Full fallback chain — never crashes.
    Always call init_fonts() before using this.
    """
    for candidate in [path, _BOLD, _MED, _REG]:
        if not candidate:
            continue
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()
