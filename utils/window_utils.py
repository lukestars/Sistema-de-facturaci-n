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

    This should be called early in a window's __init__ before adding other widgets.
    It will attempt to call overrideredirect(True) and create a title bar with
    minimize/maximize/close buttons and drag-to-move behavior. Returns a Tk Frame
    that the caller should use as the main content parent.
    """
    try:
        # prefer to make a custom titlebar
        # Avoid forcing overrideredirect on the root Tk window (or CTk)
        try:
            is_root = isinstance(win, tk.Tk) or win.__class__.__name__.endswith('CTk')
        except Exception:
            is_root = False
        try:
            if not is_root:
                win.overrideredirect(True)
        except Exception:
            pass

        # create title bar
        try:
            tb = tk.Frame(win, bg='black', relief='flat', height=30)
            tb.pack(side='top', fill='x')
        except Exception:
            tb = None

        # title label
        if tb is not None:
            try:
                lbl_txt = title if title is not None else win.title() or ''
                lbl = tk.Label(tb, text=lbl_txt, bg='black', fg=(colors.get('text') if colors else 'white'))
                lbl.pack(side='left', padx=8)
            except Exception:
                lbl = None

            # control buttons
            def _min():
                try:
                    win.iconify()
                except Exception:
                    pass

            def _toggle_max():
                try:
                    if getattr(win, '_is_maximized', False):
                        try:
                            win.state('normal')
                        except Exception:
                            if getattr(win, '_normal_geometry', None):
                                win.geometry(win._normal_geometry)
                        win._is_maximized = False
                    else:
                        try:
                            win._normal_geometry = win.geometry()
                        except Exception:
                            win._normal_geometry = None
                        try:
                            win.state('zoomed')
                        except Exception:
                            sw = win.winfo_screenwidth()
                            sh = win.winfo_screenheight()
                            win.geometry(f"{sw}x{sh}+0+0")
                        win._is_maximized = True
                except Exception:
                    pass

            def _close():
                try:
                    win.destroy()
                except Exception:
                    pass

            try:
                btn_min = tk.Button(tb, text='🗕', bg='black', fg=(colors.get('text') if colors else 'white'), bd=0, activebackground='black', activeforeground=(colors.get('text') if colors else 'white'), command=_min)
                btn_min.pack(side='right', padx=2)
                btn_max = tk.Button(tb, text='🗖', bg='black', fg=(colors.get('text') if colors else 'white'), bd=0, activebackground='black', activeforeground=(colors.get('text') if colors else 'white'), command=_toggle_max)
                btn_max.pack(side='right', padx=2)
                btn_close = tk.Button(tb, text='✕', bg='black', fg=(colors.get('text') if colors else 'white'), bd=0, activebackground='black', activeforeground=(colors.get('text') if colors else 'white'), command=_close)
                btn_close.pack(side='right', padx=6)
            except Exception:
                pass

            # dragging
            def _start(event):
                win._drag_x = event.x
                win._drag_y = event.y

            def _drag(event):
                try:
                    x = event.x_root - getattr(win, '_drag_x', 0)
                    y = event.y_root - getattr(win, '_drag_y', 0)
                    win.geometry(f'+{x}+{y}')
                except Exception:
                    pass

            try:
                tb.bind('<Button-1>', _start)
                tb.bind('<B1-Motion>', _drag)
                if lbl is not None:
                    lbl.bind('<Button-1>', _start)
                    lbl.bind('<B1-Motion>', _drag)
            except Exception:
                pass

        # content frame
        try:
            content = tk.Frame(win, bg=(colors.get('bg') if colors else win.cget('bg')))
            content.pack(side='top', fill='both', expand=True)
        except Exception:
            content = win

        # attempt to apply native coloring as well
        try:
            set_native_titlebar_black(win)
        except Exception:
            pass

        return content
    except Exception:
        return win
