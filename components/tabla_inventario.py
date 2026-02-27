import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from . import __init__  # ensure package
import database
import unicodedata
import re


class TablaInventario(ctk.CTkFrame):
    """Componente de tabla de inventario.

    Usa un ttk.Treeview dentro de un CTkScrollableFrame para mostrar los productos.
    Provee métodos públicos para recargar, agregar y eliminar.
    """

    def __init__(self, master, colors=None, fonts=None, **kwargs):
        # allow frame background from colors
        fg = None
        if colors:
            fg = colors.get('frame')
        if fg is not None:
            super().__init__(master, fg_color=fg, **kwargs)
        else:
            super().__init__(master, **kwargs)
        self.colors = colors or {}
        self.fonts = fonts or {}
        self._build()

    def _build(self):
        # Contenedor simple (sin CTkScrollableFrame para evitar doble barra de scroll:
        # el Treeview ya tiene su propia scrollbar vertical; un ScrollableFrame añadía una segunda)
        self.scroll_frame = ctk.CTkFrame(self, fg_color=self.colors.get('frame'))
        self.scroll_frame.pack(expand=True, fill='both')

        # Treeview (ttk) para mostrar columnas: Código, Nombre, Precio Bs, Precio (USD/EUR), Stock
        container = tk.Frame(self.scroll_frame, bg=self.colors.get('frame'))
        container.pack(expand=True, fill='both')

        style = ttk.Style()
        # configurar estilo oscuro básico
        try:
            style.theme_use('clam')
        except Exception:
            pass

        self.tree = ttk.Treeview(container, columns=("code","name", "price_bs", "price_usd", "stock"), show='headings', selectmode='browse')
        try:
            self.tree.configure(highlightbackground='#4a4a4f', highlightcolor='#4a4a4f', highlightthickness=1)
        except Exception:
            pass
        # Ensure heading text aligns with column contents (left-aligned)
        self.tree.heading("code", text="Código", anchor='w')
        self.tree.heading("name", text="Nombre", anchor='w')
        self.tree.heading("price_bs", text="Precio Bs")
        # heading for foreign currency will be set dynamically
        symbol = '$'
        try:
            cur = database.get_setting('currency', 'USD')
            symbol = '$' if str(cur) == 'USD' else '€'
        except Exception:
            symbol = '$'
        self.tree.heading("price_usd", text=f"Precio {symbol}")
        self.tree.heading("stock", text="Stock")
        self.tree.column("code", anchor='w', width=80)
        self.tree.column("name", anchor='w', width=180)
        self.tree.column("price_bs", anchor='center', width=90)
        self.tree.column("price_usd", anchor='center', width=90)
        self.tree.column("stock", anchor='center', width=80)

        self._vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)

        def _on_yscroll(first, last):
            self._vsb.set(first, last)
            try:
                if first <= 0 and last >= 0.9999:
                    self._vsb.pack_forget()
                else:
                    self._vsb.pack(side='right', fill='y')
            except Exception:
                pass

        self.tree.configure(yscrollcommand=_on_yscroll)
        self.tree.pack(expand=True, fill='both', side='left')
        # Mostrar scrollbar solo si hay contenido que desborde (se actualiza en reload)
        self.after_idle(lambda: _on_yscroll(*(self.tree.yview())))

        # Popup menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Eliminar", command=self._delete_selected)

        self.tree.bind("<Button-3>", self._on_right_click)

        # Inicializar datos
        self.reload()

    def _on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()

    def reload(self, query: str = None):
        for r in self.tree.get_children():
            self.tree.delete(r)
        q = (query or '').strip() if query is not None else None

        def normalize_text(s: str) -> str:
            if s is None:
                return ''
            s = str(s)
            # remove diacritics
            s = unicodedata.normalize('NFD', s)
            s = ''.join(ch for ch in s if not unicodedata.combining(ch))
            # remove non-alphanumeric
            s = re.sub(r'[^\w\s]', '', s)
            return s.lower()

        nq = normalize_text(q) if q else None
        for row in database.get_products():
            # id, code, name, price_bs, price_usd, quantity
            pid, code, name, price_bs, price_usd, qty = row
            # normalize/format product code: if numeric, pad to 4 digits (0001)
            try:
                if code and str(code).isdigit():
                    display_code = str(code).zfill(4)
                elif code:
                    display_code = str(code)
                else:
                    display_code = str(pid).zfill(4)
            except Exception:
                display_code = str(code or pid)
            if nq:
                if nq not in normalize_text(display_code) and nq not in normalize_text(name):
                    continue
            # price_usd column stores price in selected foreign currency (USD or EUR)
            self.tree.insert("", "end", iid=str(pid), values=(display_code, name, f"{price_bs:.2f}", f"{price_usd:.2f}", qty))
        # Mostrar/ocultar scrollbar según si hay contenido que desborde
        try:
            first, last = self.tree.yview()
            if first <= 0 and last >= 0.9999:
                self._vsb.pack_forget()
            else:
                self._vsb.pack(side='right', fill='y')
        except Exception:
            pass

    def update_currency_heading(self):
        """Update the foreign-currency column heading symbol according to settings."""
        try:
            cur = database.get_setting('currency', 'USD')
            symbol = '$' if str(cur) == 'USD' else '€'
            self.tree.heading("price_usd", text=f"Precio {symbol}")
        except Exception:
            try:
                self.tree.heading("price_usd", text="Precio $")
            except Exception:
                pass

    def add_product(self, code: str, name: str, price_bs: float, price_usd: float, quantity: int):
        database.add_product_full(code=code, name=name, price_bs=price_bs, price_usd=price_usd, quantity=quantity)
        self.reload()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        database.delete_product(pid)
        self.reload()
