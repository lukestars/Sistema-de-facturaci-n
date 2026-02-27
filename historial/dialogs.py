"""Diálogos genéricos para ventanas del historial en la carpeta venta."""
import tkinter as tk
from typing import Any


class Tooltip:
    def __init__(self, widget, text):
        try:
            widget.bind('<Enter>', lambda e: None)
            widget.bind('<Leave>', lambda e: None)
        except Exception:
            pass


def style_window(app: Any, win: tk.Toplevel | tk.Tk) -> tk.Frame:
    colors = getattr(app, 'colors', None) or getattr(app, 'theme_colors', {})
    bg_main = colors.get('bg', colors.get('bg_main', '#121212'))
    panel = colors.get('frame', colors.get('panel', '#1b1b1f'))
    border = colors.get('muted', colors.get('border', '#4a4a4f'))
    try:
        win.configure(bg=bg_main)
    except Exception:
        pass
    try:
        outer = tk.Frame(win, bg=border, padx=1, pady=1)
        outer.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(outer, bg=panel)
        inner.pack(fill=tk.BOTH, expand=True)
        return inner
    except Exception:
        return win


# Reuse central centering helper from utils to keep behavior consistent across app
try:
    from utils.window_utils import center_window
except Exception:
    try:
        from venta.utils.window_utils import center_window
    except Exception:
        # fallback: minimal local implementation
        def center_window(app: Any, win: tk.Toplevel | tk.Tk, w: int, h: int) -> None:
            try:
                win.update_idletasks()
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                nx = (sw - w) // 2
                ny = (sh - h) // 2
                win.geometry(f'{w}x{h}+{nx}+{ny}')
            except Exception:
                pass
