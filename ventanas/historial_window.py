import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import database
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import database

def open_history_window(parent):
    try:
        win = ctk.CTkToplevel(parent)
        win.title('Historial')
        try:
            from utils.window_utils import enforce_custom_titlebar
            content = enforce_custom_titlebar(win, title='Historial', colors=getattr(parent, 'colors', {}), fonts=getattr(parent, 'fonts', {}))
        except Exception:
            content = win

        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Simple Treeview showing basic historial records (placeholder for real implementation)
        cols = ('fecha', 'usuario', 'accion', 'detalle')
        tree = ttk.Treeview(content, columns=cols, show='headings')
        tree.heading('fecha', text='Fecha')
        tree.heading('usuario', text='Usuario')
        tree.heading('accion', text='Acción')
        tree.heading('detalle', text='Detalle')
        tree.pack(fill='both', expand=True, padx=8, pady=8)

        # load historial from DB if available (placeholder function `get_history` may not exist)
        try:
            if hasattr(database, 'get_history'):
                rows = database.get_history()
            else:
                # fallback: build a small sample from product changes (if available)
                rows = []
        except Exception:
            rows = []

        for r in rows:
            try:
                tree.insert('', 'end', values=r)
            except Exception:
                pass

        # center small window
        try:
            parent._center_window(win, dw=700, dh=400)
        except Exception:
            pass

        try:
            win.transient(parent)
            win.grab_set()
        except Exception:
            pass
        return win
    except Exception:
        return None
