import sys
import tkinter as tk
from typing import Union


def fit_window(win: Union[tk.Toplevel, tk.Tk], padding: int = 40, enlarge_factor: float = 1.08):
    """Resize and center a window so it shows all its content and is slightly larger.

    win: the Toplevel or Tk instance
    padding: extra pixels to add to width/height
    enlarge_factor: multiplicative factor to make window a bit larger than required
    """
    try:
        # Ensure layout measured
        win.update_idletasks()
        req_w = win.winfo_reqwidth()
        req_h = win.winfo_reqheight()

        w = max(200, int(req_w * enlarge_factor) + padding)
        h = max(120, int(req_h * enlarge_factor) + padding)

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = max(0, int((sw - w) / 2))
        y = max(0, int((sh - h) / 2))

        win.geometry(f"{w}x{h}+{x}+{y}")
        try:
            win.minsize(req_w, req_h)
        except Exception:
            pass
    except Exception:
        # best-effort, ignore failures
        pass


def center_window(parent: Union[tk.Toplevel, tk.Tk, object], win: Union[tk.Toplevel, tk.Tk], w: int = None, h: int = None):
    """Center `win` relative to `parent` when possible, otherwise center on screen.

    parent may be the application object (having `root`) or a window instance.
    If w/h are provided, they are used to set the geometry size before centering.
    """
    try:
        try:
            win.update_idletasks()
        except Exception:
            pass

        # determine target size
        tw = w if (w and int(w) > 0) else win.winfo_reqwidth()
        th = h if (h and int(h) > 0) else win.winfo_reqheight()

        # attempt to center relative to parent.root or parent window
        px = py = None
        pw = ph = None
        try:
            # if parent exposes root (app object), use it
            root = getattr(parent, 'root', None) or parent
            root.update_idletasks()
            px = root.winfo_rootx()
            py = root.winfo_rooty()
            pw = root.winfo_width()
            ph = root.winfo_height()
        except Exception:
            px = py = pw = ph = None

        if px is not None and pw is not None:
            x = px + max(0, int((pw - tw) / 2))
            y = py + max(0, int((ph - th) / 2))
        else:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = max(0, int((sw - tw) / 2))
            y = max(0, int((sh - th) / 2))

        try:
            win.geometry(f"{int(tw)}x{int(th)}+{x}+{y}")
        except Exception:
            try:
                win.geometry(f"+{x}+{y}")
            except Exception:
                pass
    except Exception:
        # never raise from centering helper
        pass


def set_native_titlebar_black(win: Union[tk.Toplevel, tk.Tk]):
    """Try to set the native titlebar color to black on Windows.

    This uses DWM attributes where available. Fails silently on non-Windows
    platforms or older Windows versions where attributes are unsupported.
    """
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        from ctypes import wintypes

        # ensure window is realized and has an HWND
        try:
            win.update_idletasks()
        except Exception:
            pass

        hwnd = wintypes.HWND(win.winfo_id())

        # prepare functions
        dwmapi = ctypes.windll.dwmapi

        # constants (may vary by Windows version)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # try common value
        DWMWA_CAPTION_COLOR = 35
        DWMWA_TEXT_COLOR = 36

        # set caption color to black (COLORREF 0x00BBGGRR -> 0x000000)
        col_black = wintypes.DWORD(0x000000)
        try:
            dwmapi.DwmSetWindowAttribute(hwnd, ctypes.c_uint(DWMWA_CAPTION_COLOR), ctypes.byref(col_black), ctypes.sizeof(col_black))
        except Exception:
            pass

        # set text color to white
        col_white = wintypes.DWORD(0x00FFFFFF)
        try:
            dwmapi.DwmSetWindowAttribute(hwnd, ctypes.c_uint(DWMWA_TEXT_COLOR), ctypes.byref(col_white), ctypes.sizeof(col_white))
        except Exception:
            pass

        # enable immersive dark mode if possible (try a couple of attribute ids)
        val = ctypes.c_int(1)
        for attr in (DWMWA_USE_IMMERSIVE_DARK_MODE, 19):
            try:
                dwmapi.DwmSetWindowAttribute(hwnd, ctypes.c_uint(attr), ctypes.byref(val), ctypes.sizeof(val))
            except Exception:
                pass
    except Exception:
        # silent fallback
        return


def enforce_custom_titlebar(win: Union[tk.Toplevel, tk.Tk], title: str = None, colors: dict = None, fonts: dict = None):
    """Replace native decorations with a custom black titlebar and return a content frame.

    On macOS and Linux uses the system default title bar (no custom bar) to avoid
    visual issues. On Windows uses a custom title bar with minimize and close buttons.
    """
    # Use native titlebar for all platforms to ensure minimize/maximize are available.
    try:
        content = tk.Frame(win, bg=(colors.get('bg') if colors else win.cget('bg')))
        content.pack(side='top', fill='both', expand=True)
        try:
            set_native_titlebar_black(win)
        except Exception:
            pass
        return content
    except Exception:
        return win
