import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

# Configuraciones globales de estilo y tema para la app

def apply_styles():
    """Aplica configuración global de CustomTkinter y devuelve diccionarios de estilos.

    También configura estilos de ttk (Treeview/Heading) para que todas las tablas
    usen la paleta de colores de la aplicación.
    """
    # Tema oscuro global para customtkinter
    ctk.set_appearance_mode("dark")
    try:
        ctk.set_default_color_theme("dark-blue")
    except Exception:
        pass

    COLORS = {
        "bg": "#121212",
        "primary": "#1f6feb",
        "accent": "#2dd4bf",
        "text": "#e6eef8",
        "muted": "#9aa6bf",
            # color de recuadros / marcos discretos
            "frame": "#1b1b1f",
        "table_header": "#2b2b2b",
        "table_row_alt_lighten": "#1a1a1a",
    }

    FONTS = {
        "heading": ("Segoe UI", 16, "bold"),
        "normal": ("Segoe UI", 12),
        "small": ("Segoe UI", 10),
    }

    # Configurar estilos ttk (Treeview) para que coincidan con la paleta
    try:
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        tree_bg = COLORS.get('bg')
        tree_fg = COLORS.get('text')
        head_bg = COLORS.get('table_header')
        head_fg = COLORS.get('text')
        active_bg = COLORS.get('primary')
        frame_col = COLORS.get('frame')

        # Treeview base styles (also configure a Custom.Treeview name some components use)
        style.configure('Treeview', background=tree_bg, fieldbackground=tree_bg, foreground=tree_fg, rowheight=22)
        style.configure('Custom.Treeview', background=tree_bg, fieldbackground=tree_bg, foreground=tree_fg, rowheight=22)
        style.configure('Treeview.Heading', background=head_bg, foreground=head_fg, relief='flat')
        style.configure('Custom.Treeview.Heading', background=head_bg, foreground=head_fg, relief='flat')
        # al iluminar (active/pressed) usar color primary
        style.map('Treeview.Heading', background=[('active', active_bg), ('pressed', active_bg)])
        style.map('Custom.Treeview.Heading', background=[('active', active_bg), ('pressed', active_bg)])

        # Scrollbar styling to better match the app palette (uses clam theme tokens)
        try:
            # compute a hover/active gray derived from the frame color
            def _lighten(hexcol, amount=16):
                try:
                    hexcol = hexcol.lstrip('#')
                    r = int(hexcol[0:2], 16)
                    g = int(hexcol[2:4], 16)
                    b = int(hexcol[4:6], 16)
                    r = min(255, r + amount)
                    g = min(255, g + amount)
                    b = min(255, b + amount)
                    return f"#{r:02x}{g:02x}{b:02x}"
                except Exception:
                    return hexcol

            hover_col = _lighten(frame_col, amount=16)
            style.configure('Vertical.TScrollbar', troughcolor=frame_col, background=hover_col, arrowcolor=head_fg, troughrelief='flat')
            style.configure('Horizontal.TScrollbar', troughcolor=frame_col, background=hover_col, arrowcolor=head_fg, troughrelief='flat')
            # map to change background on active/hover to a gray harmonized with the palette
            style.map('Vertical.TScrollbar', background=[('active', hover_col), ('!active', hover_col)])
            style.map('Horizontal.TScrollbar', background=[('active', hover_col), ('!active', hover_col)])
        except Exception:
            pass
        # Tema oscuro para TFrame, TLabel, TButton, TEntry (ventanas historial, cierre, export)
        try:
            style.configure('TFrame', background=frame_col)
            style.configure('TLabel', background=frame_col, foreground=tree_fg)
            style.configure('TButton', background=hover_col, foreground=tree_fg)
            style.map('TButton', background=[('active', frame_col), ('pressed', head_bg)])
            style.configure('TEntry', fieldbackground=tree_bg, foreground=tree_fg)
        except Exception:
            pass
    except Exception:
        pass

    return COLORS, FONTS
