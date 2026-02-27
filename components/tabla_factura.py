import customtkinter as ctk
import tkinter as tk
from tkinter import ttk


class TablaFactura(ctk.CTkFrame):
    """Panel para productos seleccionados (factura).

    Similar a TablaInventario pero muestra Nombre, Precio, Cantidad y Subtotal.
    Provee métodos para añadir, eliminar y obtener los ítems seleccionados.
    """

    def __init__(self, master, colors=None, fonts=None, **kwargs):
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
        container = tk.Frame(self, bg=self.colors.get('frame'))
        container.pack(expand=True, fill='both')

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # add a remove column (acts as an 'X' button)
        # columns: Nombre | Precio (Bs) | IVA | Cantidad | Subtotal (Bs) | Remove
        self.tree = ttk.Treeview(container, columns=("name", "price", "iva", "quantity", "subtotal", "remove"), show='headings')
        try:
            self.tree.configure(highlightbackground='#4a4a4f', highlightcolor='#4a4a4f', highlightthickness=1)
        except Exception:
            pass
        self.tree.heading('name', text='Nombre', anchor='w')
        self.tree.heading('price', text='Precio Bs', anchor='e')
        self.tree.heading('iva', text='IVA', anchor='e')
        self.tree.heading('quantity', text='Cantidad', anchor='e')
        self.tree.heading('subtotal', text='Subtotal Bs', anchor='e')
        self.tree.heading('remove', text='', anchor='center')
        self.tree.column('name', anchor='w', width=140)
        self.tree.column('price', anchor='e', width=90)
        self.tree.column('iva', anchor='e', width=80)
        self.tree.column('quantity', anchor='e', width=80)
        self.tree.column('subtotal', anchor='e', width=110)
        self.tree.column('remove', anchor='center', width=30)

        self._vsb = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview)

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
        self.after_idle(lambda: _on_yscroll(*(self.tree.yview())))

        # popup menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label='Eliminar', command=self._delete_selected)
        self.tree.bind('<Button-3>', self._on_right_click)
        # bind left-click to detect remove column clicks
        self.tree.bind('<Button-1>', self._on_left_click)

        # internal store: map pid -> (name, price, qty)
        self._items = {}

    def _on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                try:
                    self.menu.grab_release()
                except Exception:
                    pass

    def add_item(self, pid: int, name: str, price: float, quantity: int = 1):
        pid = int(pid)
        qty = int(quantity)
        if pid in self._items:
            cur_name, cur_price, cur_qty = self._items[pid]
            cur_qty += qty
            self._items[pid] = (cur_name, cur_price, cur_qty)
        else:
            self._items[pid] = (name, float(price), qty)
        self._refresh()

    def _refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        # determine VAT settings
        try:
            import database
            vat_enabled = True if str(database.get_setting('vat_enabled', '0')) == '1' else False
            vat_pct = float(database.get_setting('vat_percent', '0') or 0.0)
        except Exception:
            vat_enabled = False
            vat_pct = 0.0
        for pid, (name, price, qty) in self._items.items():
            subtotal = price * qty
            iva_amount = (subtotal * vat_pct / 100.0) if vat_enabled else 0.0
            iva_text = f"{iva_amount:.2f} Bs" if vat_enabled else "-"
            # show prices in Bs in the invoice table
            self.tree.insert('', 'end', iid=str(pid), values=(name, f"{price:.2f} Bs", iva_text, qty, f"{subtotal:.2f} Bs", 'X'))
        # Mostrar/ocultar scrollbar según si hay contenido que desborde
        try:
            first, last = self.tree.yview()
            if first <= 0 and last >= 0.9999:
                self._vsb.pack_forget()
            else:
                self._vsb.pack(side='right', fill='y')
        except Exception:
            pass

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            pid = int(iid)
            if pid in self._items:
                # restore stock in DB for removed qty
                name, price, qty = self._items[pid]
                try:
                    import database
                    database.increase_product_quantity(int(pid), int(qty))
                except Exception:
                    pass
                del self._items[pid]
            self._refresh()
            # notify parent to reload inventory if a callback was provided
            try:
                if hasattr(self, '_on_remove_callback') and callable(self._on_remove_callback):
                    self._on_remove_callback()
            except Exception:
                pass
        except Exception:
            pass

    def _on_left_click(self, event):
        # identify column and row; if remove column (X) clicked, delete that item and return qty to stock
        try:
            col = self.tree.identify_column(event.x)
            row = self.tree.identify_row(event.y)
            if not row:
                return
            # columns: #1=name, #2=price, #3=iva, #4=quantity, #5=subtotal, #6=remove
            if col == '#6':
                self.tree.selection_set(row)
                self._delete_selected()
        except Exception:
            pass

    def clear(self):
        # restore stock for all items before clearing
        try:
            import database
            for pid, (_name, _price, qty) in list(self._items.items()):
                try:
                    database.increase_product_quantity(int(pid), int(qty))
                except Exception:
                    pass
        except Exception:
            pass
        self._items.clear()
        self._refresh()

    def finalize(self):
        """Finalize the invoice: clear internal items without restoring stock (sale committed)."""
        try:
            self._items.clear()
            self._refresh()
        except Exception:
            pass

    def get_items(self):
        # return list of dicts suitable for factura processing
        out = []
        for pid, (name, price, qty) in self._items.items():
            # compute VAT amount per item
            try:
                import database
                vat_enabled = True if str(database.get_setting('vat_enabled', '0')) == '1' else False
                vat_pct = float(database.get_setting('vat_percent', '0') or 0.0)
            except Exception:
                vat_enabled = False
                vat_pct = 0.0
            subtotal = price * qty
            iva = (subtotal * vat_pct / 100.0) if vat_enabled else 0.0
            out.append({'id': pid, 'name': name, 'price': price, 'quantity': qty, 'subtotal': subtotal, 'vat': iva})
        return out
