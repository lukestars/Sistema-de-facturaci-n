import customtkinter as ctk
import tkinter as tk
from styles import apply_styles
try:
    from utils.window_utils import set_native_titlebar_black
except Exception:
    try:
        from ..utils.window_utils import set_native_titlebar_black
    except Exception:
        set_native_titlebar_black = lambda win: None
from components.tabla_inventario import TablaInventario
from components.tabla_factura import TablaFactura
from components.panel_resumen import PanelResumen
from components.cliente_header import ClienteHeader
import database

# Aplicar estilos globales al importar el módulo para asegurar el modo/tema
try:
    apply_styles()
except Exception:
    pass


class VentanaPrincipal(ctk.CTkToplevel):
    def __init__(self, master=None, user: str = "", invoice_items: dict = None):
        super().__init__(master=master)
        self.user = user
        self.title(f"Venta - Principal ({user})")

        colors, fonts = apply_styles()
        self.colors = colors
        self.fonts = fonts
        # Backwards-compat aliases expected by historial modules
        try:
            self.theme_colors = colors
        except Exception:
            self.theme_colors = {}
        try:
            self.theme_fonts = fonts
        except Exception:
            self.theme_fonts = {}
        # sensible defaults used by historial modules
        import os
        try:
            self._ui_scale = getattr(self, '_ui_scale', 1.15)
        except Exception:
            self._ui_scale = 1.15
        try:
            self._data_dir = getattr(self, '_data_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
        except Exception:
            self._data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        try:
            self._facturas_dir = getattr(self, '_facturas_dir', os.path.join(self._data_dir, 'facturas'))
        except Exception:
            self._facturas_dir = os.path.join(self._data_dir, 'facturas')
        try:
            self._backups_dir = getattr(self, '_backups_dir', os.path.join(self._data_dir, 'backups'))
        except Exception:
            self._backups_dir = os.path.join(self._data_dir, 'backups')
        # lightweight placeholders for lists used by historial
        self.products = getattr(self, 'products', [])
        self.paused_invoices = getattr(self, 'paused_invoices', [])
        self.facturas = getattr(self, 'facturas', [])
        # id generator for dynamically added invoice items (used by add_to_cart_no_reserve)
        try:
            self._next_item_iid = getattr(self, '_next_item_iid', 1)
        except Exception:
            self._next_item_iid = 1
        # ensure root attribute exists (many migrated dialogs expect app.root)
        self.root = getattr(self, 'root', self)

        # usar la barra de título nativa (no aplicar titlebar custom)
        content = self

        # determinar rol del usuario
        try:
            u = database.get_user(user)
            if u and len(u) >= 4:
                self.user_role = u[3]
            else:
                self.user_role = 'employee'
        except Exception:
            self.user_role = 'employee'
        self.is_admin = (self.user_role == 'admin')

            # Solicitar resolución 1366x768 y centrar, permitir redimensionar (ventana, no fullscreen)
        try:
            w, h = 1360, 768
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = int((sw - w) / 2)
            y = int((sh - h) / 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
            try:
                # Forzar tamaño fijo 1360x768 y no permitir redimensionar
                self.resizable(False, False)
                self.minsize(w, h)
            except Exception:
                pass
        except Exception:
            try:
                self.geometry("1000x600")
                try:
                    self.minsize(800, 600)
                except Exception:
                    pass
            except Exception:
                pass

        # intentar colorear la barra nativa (Windows)
        try:
            set_native_titlebar_black(self)
        except Exception:
            pass
        # Nota: se fuerza tamaño absoluto; no aplicar fit_window ni reajustes

        # Layout: use content frame returned by the titlebar helper
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=0)  # header
        content.grid_rowconfigure(1, weight=1)  # contenido

        # Header superior (ocupando todo el ancho)
        self.header = ClienteHeader(content, colors=colors, fonts=fonts, on_logout=self._logout, on_config=self._open_config, is_admin=self.is_admin)
        self.header.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=(10, 0))
        # track open product dialogs so we can update their currency label live
        self._open_product_dialogs = []

        # Panel izquierdo
        left_frame = ctk.CTkFrame(content, fg_color=colors.get('frame'))
        left_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        # Barra de búsqueda sobre la tabla
        search_frame = ctk.CTkFrame(left_frame, fg_color=colors.get('frame'))
        search_frame.pack(fill='x', padx=8, pady=(8, 4))
        ctk.CTkLabel(search_frame, text='Buscar:').pack(side='left', padx=(6,4))
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text='Código o nombre')
        self.search_entry.pack(side='left', fill='x', expand=True, padx=6)
        try:
            self.search_entry.bind('<KeyRelease>', lambda e: self.tabla.reload(self.search_entry.get()))
        except Exception:
            pass

        # Controles sobre la tabla (Agregar / Editar / Stock)
        ctrl_frame = ctk.CTkFrame(left_frame, fg_color=colors.get('frame'))
        ctrl_frame.pack(fill='x', padx=8, pady=(4, 4))

        add_btn = ctk.CTkButton(ctrl_frame, text="Agregar", command=self._open_add_product_dialog)
        add_btn.pack(side='left', padx=6)

        edit_btn = ctk.CTkButton(ctrl_frame, text="Editar", command=self._open_edit_product_dialog)
        edit_btn.pack(side='left', padx=6)

        stock_btn = ctk.CTkButton(ctrl_frame, text="Stock", command=self._open_stock_dialog)
        stock_btn.pack(side='left', padx=6)

        # status label for quick messages
        self.status_lbl = ctk.CTkLabel(ctrl_frame, text='', text_color=colors.get('text'))
        self.status_lbl.pack(side='left', padx=6)
        # status message management
        self._status_after_id = None
        def _clear_status_internal():
            try:
                self.status_lbl.configure(text='')
            except Exception:
                pass
            self._status_after_id = None
        self._clear_status_internal = _clear_status_internal

        def show_status(message: str, timeout: int = 4000):
            """Show a non-obstructive status message in the header for `timeout` ms."""
            try:
                # cancel previous clear if pending
                if self._status_after_id:
                    try:
                        self.after_cancel(self._status_after_id)
                    except Exception:
                        pass
                self.status_lbl.configure(text=message)
                if message and timeout and timeout > 0:
                    try:
                        self._status_after_id = self.after(timeout, self._clear_status_internal)
                    except Exception:
                        self._status_after_id = None
            except Exception:
                # best-effort: if status cannot be shown, print to console
                try:
                    print('[STATUS]', message)
                except Exception:
                    pass

        self.show_status = show_status
        self.clear_status = lambda: self.show_status('', 0)

        refresh_btn = ctk.CTkButton(ctrl_frame, text="Historial", command=lambda: self._open_history())
        refresh_btn.pack(side='left', padx=6)

        # Tabla de inventario
        self.tabla = TablaInventario(left_frame, colors=colors, fonts=fonts)
        self.tabla.pack(expand=True, fill='both', padx=8, pady=8)

        # Panel derecho
        right_frame = ctk.CTkFrame(content, fg_color=colors.get('frame'))
        right_frame.grid(row=1, column=1, sticky='nsew', padx=10, pady=10)
        right_frame.grid_rowconfigure(1, weight=1)

        # Total panel (reemplaza el resumen): muestra subtotal, IVA y total (incluye IVA) en Bs y en la divisa seleccionada
        total_frame = ctk.CTkFrame(right_frame, fg_color=colors.get('frame'))
        total_frame.grid(row=0, column=0, sticky='new', padx=6, pady=6)
        # boxed area for totals with highlighted main total
        # use a gray that harmonizes with the palette (use 'frame' color as base)
        box_bg = colors.get('frame', '#1b1b1f')
        # slightly lighten the frame color for inner box if possible
        box_border = colors.get('accent', '#00A3FF')
        totals_box = ctk.CTkFrame(total_frame, fg_color=box_bg, corner_radius=8, border_width=1, border_color=box_border)
        totals_box.pack(fill='x', padx=8, pady=8)

        self.subtotal_label = ctk.CTkLabel(totals_box, text="Subtotal Bs: 0.00", font=self.fonts.get('normal'))
        self.subtotal_label.pack(anchor='w', padx=8, pady=(8,2))
        self.iva_label = ctk.CTkLabel(totals_box, text="IVA: 0.00 Bs", font=self.fonts.get('normal'))
        self.iva_label.pack(anchor='w', padx=8, pady=(0,2))
        # main total styled in electric blue to stand out
        electric_blue = '#00A3FF'
        try:
            # prefer a heading font if available
            tf = self.fonts.get('heading') or self.fonts.get('normal')
        except Exception:
            tf = None
        self.total_bs_label = ctk.CTkLabel(totals_box, text="Total Bs: 0.00", font=tf, text_color=electric_blue)
        self.total_bs_label.pack(anchor='w', padx=8, pady=(4,4))
        self.total_foreign_label = ctk.CTkLabel(totals_box, text="Total moneda: 0.00", font=self.fonts.get('normal'), text_color=electric_blue)
        self.total_foreign_label.pack(anchor='w', padx=8, pady=(0,8))

        # Panel de productos seleccionados para la factura (se parece a la lista de productos)
        # pass a callback so factura panel can request inventory reload when items are removed
        self.factura_panel = TablaFactura(right_frame, colors=colors, fonts=fonts)
        # set callback
        try:
            self.factura_panel._on_remove_callback = lambda: (self._reload(), self.show_status('Item eliminado, stock restaurado'))
        except Exception:
            # best-effort: keep going
            pass
        self.factura_panel.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)

        # Actions under invoice panel: Imprimir
        try:
            actions_frame = ctk.CTkFrame(right_frame, fg_color=colors.get('frame'))
            actions_frame.grid(row=2, column=0, sticky='ew', padx=6, pady=(4,6))
            print_btn = ctk.CTkButton(actions_frame, text='Imprimir', command=lambda: self._open_print())
            print_btn.pack(side='left', padx=6)
        except Exception:
            pass

        # restore invoice items if provided (transfer state across quick restart)
        try:
            if invoice_items and isinstance(invoice_items, dict):
                # shallow copy items into the factura panel without touching DB
                self.factura_panel._items = {int(k): (v[0], float(v[1]), int(v[2])) for k, v in invoice_items.items()}
                try:
                    self.factura_panel._refresh()
                except Exception:
                    pass
        except Exception:
            pass

        # (Logout ahora mostrado en el header)

        # bind double-click on inventory rows to add automatically to factura
        try:
            self.tabla.tree.bind('<Double-1>', lambda e: self._add_selected_to_invoice(e))
        except Exception:
            pass

        self._reload()

        # main window geometry is set during initialization; avoid extra re-centering hacks

        # ensure window close restores invoice stock
        try:
            self.protocol('WM_DELETE_WINDOW', self._on_close)
        except Exception:
            pass

    def _restore_invoice_stock(self):
        """Restore stock for all items currently in the invoice panel."""
        try:
            # Prefer using the factura panel's clear() since it already restores stock
            try:
                self.factura_panel.clear()
                return
            except Exception:
                pass
            # Fallback: manually restore from internal items dict (robust casting)
            items = getattr(self.factura_panel, '_items', {}) or {}
            for pid, (_name, _price, qty) in list(items.items()):
                try:
                    database.increase_product_quantity(int(pid), int(qty))
                except Exception:
                    pass
            try:
                self.factura_panel._items.clear()
                self.factura_panel._refresh()
            except Exception:
                pass
        except Exception:
            pass

    # -- Minimal compatibility helpers used by migrated historial modules --
    def paused_registry_path(self):
        import os
        try:
            d = getattr(self, '_data_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
        except Exception:
            d = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return os.path.join(d, 'paused.json')

    def save_paused_to_disk(self):
        import json
        try:
            path = self.paused_registry_path()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.paused_invoices or [], f, ensure_ascii=False, indent=2)
        except Exception:
            try:
                print('Warning: could not save paused invoices')
            except Exception:
                pass

    def request_get(self, url, timeout=5, **kwargs):
        try:
            import requests
            return requests.get(url, timeout=timeout, **kwargs)
        except Exception:
            return None

    def request_post(self, url, json=None, timeout=5, **kwargs):
        try:
            import requests
            return requests.post(url, json=json, timeout=timeout, **kwargs)
        except Exception:
            return None

    def add_to_cart_no_reserve(self, name, price, qty=1):
        """Add an item to the factura panel without touching DB stock (used by paused invoices)."""
        try:
            pid = -int(self._next_item_iid or 1)
            try:
                self._next_item_iid += 1
            except Exception:
                self._next_item_iid = (getattr(self, '_next_item_iid', 1) or 1) + 1
            try:
                # TablaFactura expects (pid, name, price, qty)
                self.factura_panel.add_item(pid, name, float(price or 0.0), int(qty or 1))
            except Exception:
                try:
                    # fallback: mutate internal items dict
                    items = getattr(self.factura_panel, '_items', {})
                    items[pid] = (name, float(price or 0.0), int(qty or 1))
                    try:
                        self.factura_panel._refresh()
                    except Exception:
                        pass
                except Exception:
                    pass
            try:
                self.update_totals()
            except Exception:
                pass
        except Exception:
            pass

    def set_active_client(self, client):
        try:
            self.active_client = client
            # try to update header if supported
            try:
                if hasattr(self, 'header') and hasattr(self.header, 'set_client'):
                    self.header.set_client(client)
            except Exception:
                pass
        except Exception:
            pass

    def clear_selected_items(self, restore_stock=True):
        try:
            # prefer factura_panel.clear which restores stock when appropriate
            try:
                if hasattr(self.factura_panel, 'clear'):
                    self.factura_panel.clear()
                else:
                    self.factura_panel._items = {}
                    try:
                        self.factura_panel._refresh()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if restore_stock:
                    # attempt to restore stock for cleared items
                    self._restore_invoice_stock()
            except Exception:
                pass
            try:
                self.update_totals()
            except Exception:
                pass
        except Exception:
            pass

    def _log_stock_change(self, codigo, producto, cantidad_anterior, cantidad_nueva, motivo):
        """Append a simple stock change record to stock_history.json in data dir."""
        import json, os, datetime
        try:
            d = getattr(self, '_data_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, 'stock_history.json')
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        arr = json.load(f) or []
                else:
                    arr = []
            except Exception:
                arr = []
            rec = {
                'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
                'codigo': codigo,
                'producto': producto,
                'cantidad_anterior': cantidad_anterior,
                'cantidad_nueva': cantidad_nueva,
                'motivo': motivo,
                'usuario': getattr(self, 'user', '')
            }
            arr.append(rec)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(arr, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_products(self):
        """Populate self.products from the sqlite database to a list of dicts expected by historial modules."""
        try:
            rows = database.get_products()
        except Exception:
            rows = []
        prods = []
        try:
            for r in rows:
                try:
                    pid = int(r[0])
                    code = r[1] or str(pid)
                    name = r[2] or ''
                    price_bs = float(r[3] or 0.0)
                    price_usd = float(r[4] or 0.0)
                    qty = int(r[5] or 0)
                    prods.append({'id': pid, 'codigo': code, 'producto': name, 'precio_bs': price_bs, 'precio_usd': price_usd, 'cantidad_disponible': qty})
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.products = prods
        except Exception:
            pass

    def _center_window(self, win, dw=520, dh=420):
        try:
            win.update_idletasks()
        except Exception:
            pass
        try:
            pwx = self.winfo_rootx()
            pwy = self.winfo_rooty()
            pww = self.winfo_width()
            pwh = self.winfo_height()
            dx = pwx + max(0, int((pww - dw) / 2))
            dy = pwy + max(0, int((pwh - dh) / 2))
            win.geometry(f"{dw}x{dh}+{dx}+{dy}")
        except Exception:
            try:
                # fallback center on screen
                sw = win.winfo_screenwidth()
                sh = win.winfo_screenheight()
                dx = int((sw - dw) / 2)
                dy = int((sh - dh) / 2)
                win.geometry(f"{dw}x{dh}+{dx}+{dy}")
            except Exception:
                pass

    def _on_close(self):
        """Handler for window close: restore invoice stock, destroy window and return to login if present."""
        try:
            # restore any reserved stock
            try:
                self._restore_invoice_stock()
            except Exception:
                pass
            # destroy and show master login if present
            m = getattr(self, 'master', None)
            try:
                self.destroy()
            except Exception:
                pass
            if m is not None:
                try:
                    m.deiconify()
                except Exception:
                    try:
                        from ventanas.login_window import LoginWindow
                        login = LoginWindow()
                        login.mainloop()
                    except Exception:
                        pass
        except Exception:
            try:
                self.destroy()
            except Exception:
                pass

    def _apply_currency_change(self):
        """Apply visual currency settings (update headings and any visible labels)."""
        try:
            # update inventory table heading
            try:
                self.tabla.update_currency_heading()
            except Exception:
                pass
            # refresh views
            try:
                self._reload()
            except Exception:
                pass
            # update open product dialogs' currency label
            try:
                import database as _db
                cur = _db.get_setting('currency', 'USD')
                symbol = '$' if str(cur) == 'USD' else '€'
                for dlg in list(getattr(self, '_open_product_dialogs', []) or []):
                    try:
                        # if dialog stored a price_label, update its text
                        if hasattr(dlg, 'price_label'):
                            try:
                                dlg.price_label.configure(text=f"Precio {symbol}:")
                            except Exception:
                                pass
                        else:
                            # try to find a child label with 'Precio ' prefix
                            try:
                                for child in dlg.winfo_children():
                                    try:
                                        if hasattr(child, 'cget') and isinstance(child.cget('text'), str) and child.cget('text').startswith('Precio'):
                                            child.configure(text=f"Precio {symbol}:")
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def _quick_restart(self):
        """Quick restart: recreate the main window instance to apply UI-wide changes
        without logging out or losing DB data. This will create a new VentanaPrincipal and
        destroy the current one. The login/master window remains hidden (not logged out).
        """
        try:
            master = getattr(self, 'master', None)
            user = getattr(self, 'user', '')
            geom = None
            try:
                geom = self.geometry()
            except Exception:
                geom = None
            # transfer current invoice items to the new window so state is preserved
            try:
                items_to_transfer = getattr(self.factura_panel, '_items', {}) or {}
            except Exception:
                items_to_transfer = {}
            # Import class and create a new window before destroying this one
            try:
                from ventanas.ventana_principal import VentanaPrincipal as VP
                new_win = VP(master=master, user=user, invoice_items=items_to_transfer)
                if geom:
                    try:
                        new_win.geometry(geom)
                    except Exception:
                        pass
                try:
                    # ensure same close behavior with login
                    if master is not None:
                        new_win.protocol('WM_DELETE_WINDOW', lambda: (new_win.destroy(), master.deiconify()))
                except Exception:
                    pass
            except Exception:
                new_win = None
            # destroy old window
            try:
                self.destroy()
            except Exception:
                pass
        except Exception:
            pass

    def _close_dialog(self, dlg):
        """Safely release grab and destroy or withdraw a dialog to avoid leaving a global grab."""
        try:
            dlg.grab_release()
        except Exception:
            pass
        try:
            dlg.destroy()
        except Exception:
            try:
                dlg.withdraw()
            except Exception:
                pass

    def _add_product(self):
        # deprecated: use dialogs instead
        return

    def _add_selected_to_invoice(self, event=None):
        # tomar la selección de la tabla de inventario y añadir al panel de factura
        try:
            # si viene un evento (doble-click), seleccionar la fila bajo el cursor
            if event is not None:
                try:
                    iid = self.tabla.tree.identify_row(event.y)
                    if iid:
                        self.tabla.tree.selection_set(iid)
                except Exception:
                    pass

            sel = self.tabla.tree.selection()
            if not sel:
                return
            item_id = sel[0]
            # iid es product id
            pid = int(item_id)
            vals = self.tabla.tree.item(item_id, 'values')
            if not vals:
                return
            # vals: code, name, price_bs, price_usd, stock
            try:
                code = vals[0]
                name = vals[1]
                price = float(vals[2])
            except Exception:
                # fallback: try previous layout
                try:
                    name = vals[0]
                    price = float(vals[1])
                except Exception:
                    name = vals[0] if vals else ''
                    price = 0.0
            # usar la cantidad indicada en entry_qty si es válida, sino 1
            try:
                qty = int(self.entry_qty.get()) if self.entry_qty.get().strip() else 1
            except Exception:
                qty = 1
            # intentar decrementar stock en DB antes de añadir
            try:
                ok = database.decrease_product_quantity(pid, qty)
            except Exception:
                ok = False
            if not ok:
                # no hay stock suficiente
                self.show_status('Stock insuficiente')
                return
            # stock decremented, refresh inventory and add to factura
            try:
                self._reload()
            except Exception:
                pass
            self.factura_panel.add_item(pid, name, price, qty)
            try:
                # update totals display
                self.update_totals()
            except Exception:
                pass
            # clear status
            try:
                self.clear_status()
            except Exception:
                pass
        except Exception:
            try:
                import traceback
                traceback.print_exc()
            except Exception:
                pass

    

    def _reload(self):
        self.tabla.reload()
        # refresh totals and inventory
        try:
            products = database.get_products()
        except Exception:
            products = []
        try:
            self.update_totals()
        except Exception:
            pass

    def _logout(self):
        try:
            # Si esta ventana fue creada con un master (login), devolver el focus al login
            m = getattr(self, 'master', None)
            try:
                self.destroy()
            except Exception:
                pass
            if m is not None:
                try:
                    m.deiconify()
                except Exception:
                    try:
                        from ventanas.login_window import LoginWindow
                        login = LoginWindow()
                        login.mainloop()
                    except Exception:
                        pass
            else:
                try:
                    from ventanas.login_window import LoginWindow
                    login = LoginWindow()
                    login.mainloop()
                except Exception:
                    pass
        except Exception:
            try:
                self.destroy()
            except Exception:
                pass

    def _open_config(self):
        try:
            from ventanas.config_window import ConfigWindow
            win = ConfigWindow(self, is_admin=self.is_admin, current_user=self.user)
            win.transient(self)
            win.grab_set()
        except Exception:
            pass

    def _open_history(self):
        # Open a compact Historial menu that delegates to the new venta.historial modules
        try:
            import tkinter as tk
            from tkinter import ttk
            try:
                win = ctk.CTkToplevel(self)
            except Exception:
                win = tk.Toplevel(self)
            win.title('Historial')
            try:
                win.transient(self)
                win.resizable(False, False)
            except Exception:
                pass
            pad = 12
            try:
                # center using existing helper
                self._center_window(win, dw=380, dh=320)
            except Exception:
                pass
            try:
                frm = ttk.Frame(win, padding=pad)
                frm.pack(fill=tk.BOTH, expand=True)
            except Exception:
                frm = tk.Frame(win, padx=pad, pady=pad)
                frm.pack(fill=tk.BOTH, expand=True)

            ttk.Label(frm, text='Historial', font=(self.fonts.get('heading') if hasattr(self, 'fonts') else None)).pack(pady=(0, pad))

            def _open_and_close(cmd):
                try:
                    win.destroy()
                except Exception:
                    pass
                try:
                    cmd(self)
                except Exception:
                    pass

            # try to import new historial handlers
            try:
                from historial.listado import show_facturas
            except Exception:
                try:
                    from venta.historial.listado import show_facturas
                except Exception:
                    show_facturas = None
            try:
                from historial.pausadas import show_paused_invoices
            except Exception:
                try:
                    from venta.historial.pausadas import show_paused_invoices
                except Exception:
                    show_paused_invoices = None
            try:
                from historial.stock_history import show_stock_history_window
            except Exception:
                try:
                    from venta.historial.stock_history import show_stock_history_window
                except Exception:
                    show_stock_history_window = None
            try:
                from historial.cierre_caja import show_cierre_caja
            except Exception:
                try:
                    from venta.historial.cierre_caja import show_cierre_caja
                except Exception:
                    show_cierre_caja = None
            try:
                from historial.export import show_export_menu
            except Exception:
                try:
                    from venta.historial.export import show_export_menu
                except Exception:
                    show_export_menu = None

            b1 = ttk.Button(frm, text='  Facturas finalizadas', command=lambda: _open_and_close(show_facturas), width=28)
            b1.pack(fill=tk.X, pady=6)
            b2 = ttk.Button(frm, text='  Facturas en pausa', command=lambda: _open_and_close(show_paused_invoices), width=28)
            b2.pack(fill=tk.X, pady=6)
            b3 = ttk.Button(frm, text='  Historial de stock', command=lambda: _open_and_close(show_stock_history_window), width=28)
            b3.pack(fill=tk.X, pady=6)
            b4 = ttk.Button(frm, text='  Cierre de caja', command=lambda: _open_and_close(show_cierre_caja), width=28)
            b4.pack(fill=tk.X, pady=6)
            b5 = ttk.Button(frm, text='  Exportar (CSV)', command=lambda: _open_and_close(show_export_menu), width=28)
            b5.pack(fill=tk.X, pady=6)

            ttk.Separator(frm, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=pad)
            ttk.Button(frm, text='Cerrar', command=win.destroy).pack(pady=4)
        except Exception:
            # fallback to old historial window if present
            try:
                from ventanas.historial_window import open_history_window
                open_history_window(self)
            except Exception:
                try:
                    from ventanas.historial_window import open_history_window as _f
                    _f(self)
                except Exception:
                    pass


    def _open_print(self):
        """Open the print/impresion window (safe import and fallback)."""
        try:
            from ventanas.impresion import open_print_window
            open_print_window(self)
        except Exception:
            try:
                from ventanas.impresion import open_print_window as _f
                _f(self)
            except Exception:
                try:
                    # best-effort: show status
                    self.show_status('No se pudo abrir la ventana de impresión')
                except Exception:
                    pass


    def update_totals(self):
        try:
            items = self.factura_panel.get_items()
        except Exception:
            items = []
        subtotal_bs = 0.0
        total_vat = 0.0
        for it in items:
            try:
                subtotal_bs += float(it.get('subtotal', 0.0))
            except Exception:
                pass
            try:
                total_vat += float(it.get('vat', 0.0))
            except Exception:
                pass
        total_with_vat = subtotal_bs + total_vat
        try:
            rate = float(database.get_setting('exchange_rate', '1.0') or 1.0)
        except Exception:
            rate = 1.0
        try:
            cur = database.get_setting('currency', 'USD')
            symbol = '$' if str(cur) == 'USD' else '€'
        except Exception:
            symbol = '$'
        try:
            total_foreign = (total_with_vat / rate) if rate and rate != 0 else 0.0
        except Exception:
            total_foreign = 0.0
        try:
            # update labels: subtotal, iva, total (highlighted), and foreign total
            try:
                self.subtotal_label.configure(text=f"Subtotal Bs: {subtotal_bs:.2f}")
            except Exception:
                pass
            try:
                self.iva_label.configure(text=f"IVA: {total_vat:.2f} Bs")
            except Exception:
                pass
            try:
                self.total_bs_label.configure(text=f"Total Bs: {total_with_vat:.2f}")
            except Exception:
                pass
            try:
                self.total_foreign_label.configure(text=f"Total {symbol}: {total_foreign:.2f}")
            except Exception:
                pass
        except Exception:
            pass

    # --- Product dialogs (basic implementations to avoid AttributeError) ---
    def _open_add_product_dialog(self):
        try:
            from ventanas.add_product_dialog import open_add_product_dialog
            open_add_product_dialog(self)
        except Exception:
            try:
                # best-effort fallback: import and call, or silently ignore
                from ventanas.add_product_dialog import open_add_product_dialog as _f
                _f(self)
            except Exception:
                pass

    def _open_edit_product_dialog(self):
        try:
            from ventanas.edit_product_dialog import open_edit_product_dialog
            open_edit_product_dialog(self)
        except Exception:
            try:
                from ventanas.edit_product_dialog import open_edit_product_dialog as _f
                _f(self)
            except Exception:
                pass

    def _open_stock_dialog(self):
        try:
            from ventanas.stock_dialog import open_stock_dialog
            open_stock_dialog(self)
        except Exception:
            try:
                from ventanas.stock_dialog import open_stock_dialog as _f
                _f(self)
            except Exception:
                pass
