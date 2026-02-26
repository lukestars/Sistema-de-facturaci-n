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
    bg_main = getattr(app, 'theme_colors', {}).get('bg_main', '#212121')
    panel = getattr(app, 'theme_colors', {}).get('panel', '#323232')
    border = getattr(app, 'theme_colors', {}).get('border', '#2f2f2f')
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


def center_window(app: Any, win: tk.Toplevel | tk.Tk, w: int, h: int) -> None:
    try:
        app.root.update_idletasks()
        x = app.root.winfo_x() + (app.root.winfo_width() - w) // 2
        y = app.root.winfo_y() + (app.root.winfo_height() - h) // 2
        win.geometry(f'{w}x{h}+{x}+{y}')
    except Exception:
        try:
            # fallback: center on screen
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            nx = (sw - w) // 2
            ny = (sh - h) // 2
            win.geometry(f'{w}x{h}+{nx}+{ny}')
        except Exception:
            pass
