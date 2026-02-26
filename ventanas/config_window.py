import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import database
from styles import apply_styles
try:
    from utils.window_utils import set_native_titlebar_black
except Exception:
    set_native_titlebar_black = lambda win: None


class ConfigWindow(ctk.CTkToplevel):
    def __init__(self, master=None, is_admin: bool = False, current_user: str = None, **kwargs):
        super().__init__(master=master, **kwargs)
        self.title('Configuración')
        self.current_user = current_user
        colors, fonts = apply_styles()
        self.colors = colors
        self.fonts = fonts

        # aplicar barra de título personalizada y obtener content frame
        try:
            from utils.window_utils import enforce_custom_titlebar
            content = enforce_custom_titlebar(self, title='Configuración', colors=colors, fonts=fonts)
        except Exception:
            content = self

        # tamaño solicitado obligatorio: 23.71cm x 15.74cm (ancho x alto) convertido a píxeles y centrar
        try:
            try:
                self.update_idletasks()
                px = self.winfo_fpixels('1c')
            except Exception:
                # fallback: assume 96 DPI
                px = 96 / 2.54
            w = int(23.71 * px)
            h = int(15.74 * px)
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = int((sw - w) / 2)
            y = int((sh - h) / 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
            # hacer obligatorio el tamaño: impedir cambiarlo
            try:
                self.resizable(False, False)
                self.minsize(w, h)
                self.maxsize(w, h)
            except Exception:
                pass
        except Exception:
            # fallback to 800x600 centered and non-resizable
            try:
                w, h = 800, 600
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                x = int((sw - w) / 2)
                y = int((sh - h) / 2)
                self.geometry(f"{w}x{h}+{x}+{y}")
                try:
                    self.resizable(False, False)
                    self.minsize(w, h)
                    self.maxsize(w, h)
                except Exception:
                    pass
            except Exception:
                pass

        # Tabview
        try:
            tabview = ctk.CTkTabview(content)
        except Exception:
            # fallback: use ttk.Notebook inside a frame
            frame = tk.Frame(self, bg=colors.get('frame'))
            frame.pack(fill='both', expand=True)
            tabview = None

        if tabview is not None:
            tabview.pack(fill='both', expand=True, padx=10, pady=10)
            # Orden lógico: Resolucion, Gestion de moneda, Cuentas (si admin), Cierre
            tabview.add('Resolucion')
            tabview.add('Gestion de moneda')
            if is_admin:
                tabview.add('Cuentas')
            # rename Cierre tab to 'Formato de impresión' to configure printing options
            tabview.add('Formato de impresión')

            # Resolucion tab
            f_res = tabview.tab('Resolucion')
            ctk.CTkLabel(f_res, text='Resolución y display', font=self.fonts.get('heading')).pack(anchor='w', pady=6)
            ctk.CTkLabel(f_res, text='(Opciones de resolución - placeholder)').pack(anchor='w', pady=6)

            # Gestion de moneda tab
            f_mon = tabview.tab('Gestion de moneda')
            ctk.CTkLabel(f_mon, text='Configuración de moneda', font=self.fonts.get('heading')).pack(anchor='w', pady=6)
            # Moneda base (fixed)
            ctk.CTkLabel(f_mon, text='Moneda base: VES (Bolívar)').pack(anchor='w', pady=(2,8))

            # Tasa de cambio USD -> VES
            rate_frame = ctk.CTkFrame(f_mon, fg_color=self.colors.get('frame'))
            rate_frame.pack(fill='x', padx=6, pady=6)
            ctk.CTkLabel(rate_frame, text='Tasa de cambio (1 USD = ? VES):').grid(row=0, column=0, sticky='w', padx=6, pady=6)
            mode_var = tk.StringVar(value='Manual')
            mode_menu = ctk.CTkOptionMenu(rate_frame, values=['Manual', 'Automático'], variable=mode_var)
            mode_menu.grid(row=0, column=1, sticky='e', padx=6, pady=6)

            ctk.CTkLabel(rate_frame, text='Tasa:').grid(row=1, column=0, sticky='e', padx=6, pady=6)
            rate_entry = ctk.CTkEntry(rate_frame)
            rate_entry.grid(row=1, column=1, sticky='ew', padx=6, pady=6)

            # Selección de moneda extranjera (USD o EUR). La app almacenará la moneda seleccionada
            # en la llave 'currency' y la tasa en 'exchange_rate' significa 1 [currency] = ? VES.
            ctk.CTkLabel(rate_frame, text='Moneda extranjera:').grid(row=1, column=2, sticky='e', padx=6, pady=6)
            currency_var = tk.StringVar(value='USD')
            currency_menu = ctk.CTkOptionMenu(rate_frame, values=['USD', 'EUR'], variable=currency_var)
            currency_menu.grid(row=1, column=3, sticky='ew', padx=6, pady=6)

            rate_status = ctk.CTkLabel(rate_frame, text='')
            rate_status.grid(row=2, column=0, columnspan=2, sticky='w', padx=6, pady=(4,0))

            # IVA management
            iva_frame = ctk.CTkFrame(f_mon, fg_color=self.colors.get('frame'))
            iva_frame.pack(fill='x', padx=6, pady=6)
            ctk.CTkLabel(iva_frame, text='Gestión de IVA', font=self.fonts.get('heading')).grid(row=0, column=0, sticky='w', padx=6, pady=6)
            iva_var = tk.BooleanVar(value=False)
            iva_switch = ctk.CTkSwitch(iva_frame, text='Habilitar IVA', variable=iva_var)
            iva_switch.grid(row=0, column=1, sticky='e', padx=6, pady=6)

            ctk.CTkLabel(iva_frame, text='Porcentaje (%):').grid(row=1, column=0, sticky='e', padx=6, pady=6)
            iva_entry = ctk.CTkEntry(iva_frame)
            iva_entry.grid(row=1, column=1, sticky='ew', padx=6, pady=6)

            iva_status = ctk.CTkLabel(iva_frame, text='')
            iva_status.grid(row=2, column=0, columnspan=2, sticky='w', padx=6, pady=(4,0))

            # load existing settings if available
            try:
                from database import get_setting, set_setting, update_prices_by_rate
                cur_rate = get_setting('exchange_rate', '1.0')
                rate_entry.delete(0, 'end')
                rate_entry.insert(0, str(cur_rate))
                cur_currency = get_setting('currency', 'USD')
                currency_var.set(cur_currency if cur_currency in ('USD','EUR') else 'USD')
                cur_mode = get_setting('exchange_mode', 'Manual')
                mode_var.set(cur_mode if cur_mode in ('Manual', 'Automático') else 'Manual')
                iva_enabled = get_setting('vat_enabled', '0')
                iva_var.set(True if str(iva_enabled) == '1' else False)
                iva_pct = get_setting('vat_percent', '16')
                iva_entry.delete(0, 'end')
                iva_entry.insert(0, str(iva_pct))
            except Exception:
                try:
                    rate_entry.insert(0, '1.0')
                except Exception:
                    pass

            def on_mode_change(val):
                # enable rate entry only for manual mode
                try:
                    if val == 'Manual':
                        rate_entry.configure(state='normal')
                    else:
                        rate_entry.configure(state='disabled')
                except Exception:
                    pass

            try:
                mode_menu.configure(command=on_mode_change)
            except Exception:
                pass
            # ensure entry state reflects current mode on load
            try:
                on_mode_change(mode_var.get())
            except Exception:
                try:
                    rate_entry.configure(state='normal')
                except Exception:
                    pass

            def show_temporary(lbl, text, timeout=5000):
                try:
                    lbl.configure(text=text)
                    lbl.after(timeout, lambda: lbl.configure(text=''))
                except Exception:
                    pass

            def save_rate():
                try:
                    mode = mode_var.get()
                    # persist mode selection
                    try:
                        set_setting('exchange_mode', mode)
                    except Exception:
                        pass
                    if mode == 'Manual':
                        try:
                            rate_val = float(rate_entry.get())
                        except Exception:
                            show_temporary(rate_status, 'Tasa inválida')
                            return
                    else:
                        # Automático not implemented: just read current entry
                        try:
                            rate_val = float(rate_entry.get())
                        except Exception:
                            show_temporary(rate_status, 'Tasa inválida')
                            return
                    ok = set_setting('exchange_rate', str(rate_val))
                    # save selected currency
                    try:
                        curc = currency_var.get()
                        if curc in ('USD', 'EUR'):
                            set_setting('currency', curc)
                    except Exception:
                        pass
                    # Update product prices in DB using price_usd * rate -> price_bs
                    try:
                        update_prices_by_rate(float(rate_val))
                    except Exception:
                        pass
                    # refresh parent UI product list if possible
                    try:
                        if hasattr(self.master, '_reload'):
                            self.master._reload()
                        # apply currency change immediately in-place
                        if hasattr(self.master, '_apply_currency_change') and callable(self.master._apply_currency_change):
                            try:
                                self.master._apply_currency_change()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    if ok:
                        show_temporary(rate_status, 'Tasa cambiada exitosamente', timeout=5000)
                    else:
                        show_temporary(rate_status, 'Error al guardar tasa', timeout=5000)
                except Exception:
                    show_temporary(rate_status, 'Error al guardar tasa', timeout=5000)

            def save_iva():
                try:
                    enabled = 1 if iva_var.get() else 0
                    try:
                        pct = float(iva_entry.get())
                    except Exception:
                        show_temporary(iva_status, 'Porcentaje inválido')
                        return
                    ok1 = set_setting('vat_enabled', str(enabled))
                    ok2 = set_setting('vat_percent', str(pct))
                    if ok1 and ok2:
                        show_temporary(iva_status, 'IVA actualizado', timeout=5000)
                    else:
                        show_temporary(iva_status, 'Error al guardar IVA', timeout=5000)
                except Exception:
                    show_temporary(iva_status, 'Error al guardar IVA', timeout=5000)

            rate_btn = ctk.CTkButton(rate_frame, text='Guardar tasa', command=save_rate)
            rate_btn.grid(row=3, column=0, padx=6, pady=8)
            # Button to fetch BCV and update the rate immediately (manual trigger)
            def update_bcv_action():
                try:
                    from utils.bcv_fetch import obtener_bcv
                except Exception:
                    show_temporary(rate_status, 'Módulo BCV no disponible', timeout=5000)
                    return
                try:
                    res = obtener_bcv()
                    if not res or 'error' in res:
                        show_temporary(rate_status, f"Error BCV: {res.get('error','sin datos')}")
                        return
                    curc = currency_var.get()
                    key = 'dolar' if curc == 'USD' else 'euro'
                    val = res.get(key)
                    if val is None:
                        show_temporary(rate_status, 'BCV no devolvió valor para moneda')
                        return
                    # set entry and save
                    try:
                        rate_entry.configure(state='normal')
                        rate_entry.delete(0, 'end')
                        rate_entry.insert(0, str(val))
                        rate_entry.configure(state='disabled' if mode_var.get() != 'Manual' else 'normal')
                    except Exception:
                        pass
                    # persist and apply
                    try:
                        set_setting('exchange_rate', str(val))
                        set_setting('currency', curc)
                        update_prices_by_rate(float(val))
                    except Exception:
                        pass
                    # refresh UI and quick restart
                    try:
                        if hasattr(self.master, '_reload'):
                            self.master._reload()
                        if hasattr(self.master, '_apply_currency_change') and callable(self.master._apply_currency_change):
                            try:
                                self.master._apply_currency_change()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    show_temporary(rate_status, 'Tasa BCV aplicada', timeout=5000)
                except Exception as e:
                    show_temporary(rate_status, f'Error BCV: {e}')

            bcv_btn = ctk.CTkButton(rate_frame, text='Actualizar precio BCV', command=update_bcv_action)
            bcv_btn.grid(row=3, column=1, padx=6, pady=8)
            iva_btn = ctk.CTkButton(iva_frame, text='Guardar IVA', command=save_iva)
            iva_btn.grid(row=3, column=0, padx=6, pady=8)

            # Formato de impresión tab (antiguo Cierre)
            f_cierre = tabview.tab('Formato de impresión')
            ctk.CTkLabel(f_cierre, text='Formato de impresión', font=self.fonts.get('heading')).pack(anchor='w', pady=6)
            ctk.CTkLabel(f_cierre, text='Configura la impresora predeterminada y el formato de ticket').pack(anchor='w', pady=6)

            # Colores del área de impresión (grises, sin azul)
            print_fg = self.colors.get('frame', '#1b1b1f')
            print_btn = '#4a4a4f'
            print_dropdown_bg = '#2b2b2f'
            print_border_gray = '#5a5a5f'

            # Printing settings frame
            pf = ctk.CTkFrame(f_cierre, fg_color=print_fg)
            pf.pack(fill='x', padx=6, pady=6)

            ctk.CTkLabel(pf, text='Impresora predeterminada:', anchor='w').grid(row=0, column=0, sticky='w', padx=6, pady=6)
            printer_var = tk.StringVar(value='')
            # Try to populate available printers (best-effort)
            printers_list = []
            # Try multiple strategies to list installed Windows printers (best-effort)
            try:
                import win32print
                try:
                    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                    raw = win32print.EnumPrinters(flags)
                    printers_list = [p[2] for p in raw]
                except Exception:
                    try:
                        raw = win32print.EnumPrinters()
                        printers_list = [p[2] for p in raw]
                    except Exception:
                        printers_list = []
            except Exception:
                # fallback: try PowerShell (Get-Printer) then WMIC
                try:
                    import subprocess, shlex
                    # Use PowerShell to get printer names if available
                    ps_cmd = 'powershell -NoProfile -Command "Get-Printer | Select-Object -ExpandProperty Name"'
                    p = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, timeout=3)
                    out = p.stdout.strip()
                    if out:
                        printers_list = [line.strip() for line in out.splitlines() if line.strip()]
                    else:
                        # fallback to wmic
                        try:
                            wm = subprocess.run('wmic printer get name', shell=True, capture_output=True, text=True, timeout=3)
                            lines = [l.strip() for l in wm.stdout.splitlines()]
                            # drop header if present
                            if lines and any('Name' in x for x in lines[:2]):
                                lines = [l for l in lines if l and 'Name' not in l]
                            printers_list = [l for l in lines if l]
                        except Exception:
                            printers_list = []
                except Exception:
                    printers_list = []

            try:
                # Ensure the frame expands the second column
                try:
                    pf.grid_columnconfigure(1, weight=1)
                except Exception:
                    pass
                # If we have printers, show option menu; otherwise show option menu with placeholder
                menu_values = printers_list if printers_list else ['(ninguna detectada)']
                try:
                    printer_menu = ctk.CTkOptionMenu(
                        pf, values=menu_values, variable=printer_var,
                        width=220, fg_color=print_dropdown_bg, button_color=print_btn,
                        dropdown_fg_color=print_dropdown_bg, dropdown_hover_color=print_btn,
                        button_hover_color=print_border_gray
                    )
                    printer_menu.grid(row=0, column=1, sticky='w', padx=6, pady=6)
                except Exception:
                    # fallback to entry if option menu not available
                    printer_menu = ctk.CTkEntry(pf, textvariable=printer_var, placeholder_text='Nombre de impresora')
                    printer_menu.grid(row=0, column=1, sticky='ew', padx=6, pady=6)
            except Exception:
                try:
                    printer_menu = ttk.Combobox(pf, values=printers_list or ['(ninguna detectada)'], textvariable=printer_var)
                    printer_menu.grid(row=0, column=1, sticky='ew', padx=6, pady=6)
                except Exception:
                    try:
                        printer_menu = ttk.Entry(pf, textvariable=printer_var)
                        printer_menu.grid(row=0, column=1, sticky='ew', padx=6, pady=6)
                    except Exception:
                        pass

            ctk.CTkLabel(pf, text='Formato papel (ancho):').grid(row=1, column=0, sticky='w', padx=6, pady=6)
            paper_var = tk.StringVar(value='58mm')
            try:
                paper_menu = ctk.CTkOptionMenu(
                    pf, values=['58mm', '80mm'], variable=paper_var,
                    width=120, fg_color=print_dropdown_bg, button_color=print_btn,
                    dropdown_fg_color=print_dropdown_bg, dropdown_hover_color=print_btn,
                    button_hover_color=print_border_gray
                )
                paper_menu.grid(row=1, column=1, sticky='w', padx=6, pady=6)
            except Exception:
                try:
                    paper_menu = ttk.Combobox(pf, values=['58mm', '80mm'], textvariable=paper_var)
                    paper_menu.grid(row=1, column=1, sticky='ew', padx=6, pady=6)
                except Exception:
                    pass

            # status label for saving
            print_status = ctk.CTkLabel(pf, text='')
            print_status.grid(row=2, column=0, columnspan=2, sticky='w', padx=6, pady=(4,0))

            # load existing settings
            try:
                from database import get_setting, set_setting
                cur_printer = get_setting('default_printer', '')
                if cur_printer:
                    try:
                        printer_var.set(cur_printer)
                    except Exception:
                        pass
                cur_paper = get_setting('receipt_paper_size', '58mm')
                if cur_paper in ('58mm', '80mm'):
                    paper_var.set(cur_paper)
            except Exception:
                pass

            def show_temporary_print(lbl, text, timeout=4000):
                try:
                    lbl.configure(text=text)
                    lbl.after(timeout, lambda: lbl.configure(text=''))
                except Exception:
                    pass

            def save_print_settings():
                try:
                    p = printer_var.get() if hasattr(printer_var, 'get') else ''
                    s = paper_var.get() if hasattr(paper_var, 'get') else '58mm'
                    try:
                        set_setting('default_printer', str(p))
                    except Exception:
                        pass
                    try:
                        set_setting('receipt_paper_size', str(s))
                    except Exception:
                        pass
                    show_temporary_print(print_status, 'Formato de impresión guardado', timeout=4000)
                except Exception:
                    show_temporary_print(print_status, 'Error al guardar formato', timeout=4000)

            # Add a button to re-detect printers
            def detect_printers_action():
                try:
                    # replicate detection logic: try win32print then PowerShell/WMIC
                    new_list = []
                    try:
                        import win32print
                        try:
                            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                            raw = win32print.EnumPrinters(flags)
                            new_list = [p[2] for p in raw]
                        except Exception:
                            try:
                                raw = win32print.EnumPrinters()
                                new_list = [p[2] for p in raw]
                            except Exception:
                                new_list = []
                    except Exception:
                        try:
                            import subprocess
                            ps_cmd = 'powershell -NoProfile -Command "Get-Printer | Select-Object -ExpandProperty Name"'
                            p = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, timeout=3)
                            out = p.stdout.strip()
                            if out:
                                new_list = [line.strip() for line in out.splitlines() if line.strip()]
                            else:
                                wm = subprocess.run('wmic printer get name', shell=True, capture_output=True, text=True, timeout=3)
                                lines = [l.strip() for l in wm.stdout.splitlines()]
                                if lines and any('Name' in x for x in lines[:2]):
                                    lines = [l for l in lines if l and 'Name' not in l]
                                new_list = [l for l in lines if l]
                        except Exception:
                            new_list = []
                    # update menu or combobox
                    try:
                        if hasattr(printer_menu, 'configure') and hasattr(printer_menu, 'set'):
                            # CTkOptionMenu supports values update via configure
                            try:
                                printer_menu.configure(values=new_list or ['(ninguna detectada)'])
                            except Exception:
                                pass
                        elif isinstance(printer_menu, ttk.Combobox):
                            printer_menu['values'] = new_list or ['(ninguna detectada)']
                    except Exception:
                        pass
                    # set variable to first detected if currently empty
                    try:
                        if new_list and (not printer_var.get() or printer_var.get() in ('', '(ninguna detectada)')):
                            printer_var.set(new_list[0])
                    except Exception:
                        pass
                    show_temporary_print(print_status, 'Detección completada', timeout=2000)
                except Exception:
                    show_temporary_print(print_status, 'Error al detectar impresoras', timeout=2000)

            try:
                detect_btn = ctk.CTkButton(pf, text='Detectar impresoras', command=detect_printers_action)
                detect_btn.grid(row=3, column=1, padx=6, pady=8, sticky='e')
            except Exception:
                try:
                    ttk.Button(pf, text='Detectar impresoras', command=detect_printers_action).grid(row=3, column=1, padx=6, pady=8, sticky='e')
                except Exception:
                    pass

            try:
                save_btn = ctk.CTkButton(pf, text='Guardar formato', command=save_print_settings)
                save_btn.grid(row=3, column=0, padx=6, pady=8)
            except Exception:
                try:
                    ttk.Button(pf, text='Guardar formato', command=save_print_settings).grid(row=3, column=0, padx=6, pady=8)
                except Exception:
                    pass

            # Cuentas tab (solo admin)
            if is_admin:
                f_cuentas = tabview.tab('Cuentas')
                f_cuentas.grid_columnconfigure(0, weight=1)
                # Treeview listing users
                tree_frame = tk.Frame(f_cuentas, bg=self.colors.get('frame'))
                tree_frame.pack(fill='both', expand=True, padx=6, pady=6)
                cols = ('id', 'username', 'role', 'nombre', 'apellido', 'cedula', 'telefono')
                tree = ttk.Treeview(tree_frame, columns=cols, show='headings')
                headings = {'id':'ID','username':'Usuario','role':'Rol','nombre':'Nombre','apellido':'Apellido','cedula':'Cédula','telefono':'Teléfono'}
                for c in cols:
                    tree.heading(c, text=headings.get(c, c.capitalize()))
                    tree.column(c, anchor='center')
                vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview, style='Vertical.TScrollbar')
                tree.configure(yscrollcommand=vsb.set)
                vsb.pack(side='right', fill='y')
                tree.pack(fill='both', expand=True)

                # load users
                role_display_map = {'admin':'Administrador', 'employee':'Empleado'}
                for r in database.get_all_users():
                    # r = (id, username, role, nombre, apellido, cedula, telefono)
                    rid, uname, irole, nombre, apellido, cedula, telefono = r
                    tree.insert('', 'end', values=(rid, uname, role_display_map.get(irole, irole), nombre, apellido, cedula, telefono))
                # botón para abrir un diálogo separado de creación de cuenta
                status_lbl = ctk.CTkLabel(f_cuentas, text='', text_color=self.colors.get('text'))
                status_lbl.pack(anchor='w', padx=6, pady=(0,4))

                def refresh_users():
                    try:
                        for r in tree.get_children():
                            tree.delete(r)
                        for rr in database.get_all_users():
                            rid, uname, irole, nombre, apellido, cedula, telefono = rr
                            tree.insert('', 'end', values=(rid, uname, {'admin':'Administrador','employee':'Empleado'}.get(irole, irole), nombre, apellido, cedula, telefono))
                    except Exception as e:
                        try:
                            import traceback
                            traceback.print_exc()
                        except Exception:
                            pass

                def open_add_user_dialog():
                    dlg = ctk.CTkToplevel(self)
                    dlg.title('Agregar cuenta')
                    try:
                        dlg.resizable(True, True)
                        dlg.minsize(400, 380)
                    except Exception:
                        pass
                    try:
                        self.update_idletasks()
                        pwx = self.winfo_rootx()
                        pwy = self.winfo_rooty()
                        pww = self.winfo_width()
                        pwh = self.winfo_height()
                    except Exception:
                        pwx = pwy = 0
                        pww = dlg.winfo_screenwidth()
                        pwh = dlg.winfo_screenheight()
                    dw, dh = 520, 460
                    dx = pwx + max(0, int((pww - dw) / 2))
                    dy = pwy + max(0, int((pwh - dh) / 2))
                    try:
                        dlg.geometry(f"{dw}x{dh}+{dx}+{dy}")
                    except Exception:
                        pass
                    try:
                        dlg.transient(self)
                        dlg.grab_set()
                    except Exception:
                        pass
                    # Outer frame and scrollable area so all fields are accessible on small screens
                    outer = ctk.CTkFrame(dlg, fg_color=self.colors.get('frame'))
                    outer.pack(fill='both', expand=True, padx=12, pady=12)
                    try:
                        scroll = ctk.CTkScrollableFrame(outer, fg_color=self.colors.get('frame'))
                        scroll.pack(fill='both', expand=True)
                        fdlg = scroll
                    except Exception:
                        fdlg = outer
                    # campos alineados verticalmente, más espacio
                    enombre = ctk.CTkEntry(fdlg, placeholder_text='Nombre')
                    enombre.pack(fill='x', pady=6)
                    eapellido = ctk.CTkEntry(fdlg, placeholder_text='Apellido')
                    eapellido.pack(fill='x', pady=6)
                    eced = ctk.CTkEntry(fdlg, placeholder_text='Cédula')
                    eced.pack(fill='x', pady=6)
                    etel = ctk.CTkEntry(fdlg, placeholder_text='Teléfono')
                    etel.pack(fill='x', pady=6)
                    euser = ctk.CTkEntry(fdlg, placeholder_text='Usuario')
                    euser.pack(fill='x', pady=6)
                    epass = ctk.CTkEntry(fdlg, placeholder_text='Contraseña', show='*')
                    epass.pack(fill='x', pady=6)
                    role_opt = ctk.CTkOptionMenu(fdlg, values=['Administrador', 'Empleado'])
                    role_opt.set('Empleado')
                    role_opt.pack(pady=8)
                    msg = ctk.CTkLabel(fdlg, text='')
                    msg.pack(anchor='w', pady=(4,0))

                    def save_new():
                        try:
                            nombre = enombre.get().strip()
                            apellido = eapellido.get().strip()
                            ced = eced.get().strip()
                            tel = etel.get().strip()
                            uname = euser.get().strip()
                            pwd = epass.get().strip()
                            role_map = {'Administrador':'admin', 'Empleado':'employee'}
                            role = role_map.get(role_opt.get(), 'employee')
                            if not (nombre and apellido and ced and tel and uname and pwd):
                                msg.configure(text='Complete todos los campos requeridos')
                                return
                            try:
                                ok = database.create_user(uname, pwd, role, nombre=nombre, apellido=apellido, cedula=ced, telefono=tel)
                            except Exception as e:
                                msg.configure(text=f'Error al crear usuario: {e}')
                                return
                            if not ok:
                                msg.configure(text='Error: usuario ya existe')
                            else:
                                # cerrar diálogo de forma segura: liberar grab y ocultar/destruir
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
                                status_lbl.configure(text='Usuario creado')
                                refresh_users()
                        except Exception as e:
                            # evitar que errores inesperados cierren la app; mostrar en etiqueta
                            try:
                                import traceback
                                traceback.print_exc()
                            except Exception:
                                pass
                            msg.configure(text=f'Error inesperado: {e}')

                    ctk.CTkButton(fdlg, text='Crear cuenta', command=save_new, fg_color=self.colors.get('primary')).pack(pady=12)

                add_btn = ctk.CTkButton(f_cuentas, text='Agregar cuenta', command=open_add_user_dialog, fg_color=self.colors.get('primary'))
                add_btn.pack(anchor='e', padx=6, pady=(0,6))
                # botones editar/eliminar
                btns = ctk.CTkFrame(f_cuentas, fg_color=self.colors.get('frame'))
                btns.pack(fill='x', padx=6, pady=(2, 6))

                def do_edit_user():
                    sel = tree.selection()
                    if not sel:
                        status_lbl.configure(text='Seleccione una cuenta para editar')
                        return
                    iid = sel[0]
                    vals = tree.item(iid, 'values')
                    if not vals:
                        status_lbl.configure(text='Selección inválida')
                        return
                    # vals: id, username, role_display, nombre, apellido, cedula, telefono
                    uid, uname, role_disp, nombre_v, apellido_v, ced_v, tel_v = vals

                    dlg = ctk.CTkToplevel(self)
                    dlg.title('Editar cuenta')
                    try:
                        dlg.resizable(False, False)
                    except Exception:
                        pass
                    # centrar
                    try:
                        self.update_idletasks()
                        pwx = self.winfo_rootx()
                        pwy = self.winfo_rooty()
                        pww = self.winfo_width()
                        pwh = self.winfo_height()
                    except Exception:
                        pwx = pwy = 0
                        pww = dlg.winfo_screenwidth()
                        pwh = dlg.winfo_screenheight()
                    dw, dh = 520, 380
                    dx = pwx + max(0, int((pww - dw) / 2))
                    dy = pwy + max(0, int((pwh - dh) / 2))
                    try:
                        dlg.geometry(f"{dw}x{dh}+{dx}+{dy}")
                    except Exception:
                        pass
                    try:
                        dlg.transient(self)
                        dlg.grab_set()
                    except Exception:
                        pass
                    fdlg = ctk.CTkFrame(dlg, fg_color=self.colors.get('frame'))
                    fdlg.pack(fill='both', expand=True, padx=12, pady=12)
                    ctk.CTkLabel(fdlg, text=f'Usuario: {uname}', anchor='w').pack(anchor='w')
                    pwd = ctk.CTkEntry(fdlg, placeholder_text='Nueva contraseña (opcional)', show='*')
                    pwd.pack(fill='x', pady=8)
                    role_opt = ctk.CTkOptionMenu(fdlg, values=['Administrador', 'Empleado'])
                    role_opt.set(role_disp)
                    role_opt.pack(pady=8)
                    # personal fields
                    entry_n = ctk.CTkEntry(fdlg, placeholder_text='Nombre')
                    entry_n.insert(0, nombre_v)
                    entry_n.pack(fill='x', pady=6)
                    entry_a = ctk.CTkEntry(fdlg, placeholder_text='Apellido')
                    entry_a.insert(0, apellido_v)
                    entry_a.pack(fill='x', pady=6)
                    entry_c = ctk.CTkEntry(fdlg, placeholder_text='Cédula')
                    entry_c.insert(0, ced_v)
                    entry_c.pack(fill='x', pady=6)
                    entry_t = ctk.CTkEntry(fdlg, placeholder_text='Teléfono')
                    entry_t.insert(0, tel_v)
                    entry_t.pack(fill='x', pady=6)
                    msg = ctk.CTkLabel(fdlg, text='')
                    msg.pack(anchor='w', pady=(4,0))

                    def save_edit():
                        try:
                            new_pwd = pwd.get().strip()
                            new_role_disp = role_opt.get()
                            role_map = {'Administrador':'admin', 'Empleado':'employee'}
                            new_role = role_map.get(new_role_disp, 'employee')
                            new_nombre = entry_n.get().strip()
                            new_apellido = entry_a.get().strip()
                            new_ced = entry_c.get().strip()
                            new_tel = entry_t.get().strip()
                            try:
                                ok = database.update_user(int(uid), password=new_pwd if new_pwd else None, role=new_role, nombre=new_nombre, apellido=new_apellido, cedula=new_ced, telefono=new_tel)
                            except Exception as e:
                                msg.configure(text=f'Error al actualizar: {e}')
                                return
                            if not ok:
                                msg.configure(text='Error actualizando la cuenta')
                            else:
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
                                refresh_users()
                        except Exception as e:
                            try:
                                import traceback
                                traceback.print_exc()
                            except Exception:
                                pass
                            msg.configure(text=f'Error inesperado: {e}')

                    ctk.CTkButton(fdlg, text='Guardar', command=save_edit, fg_color=self.colors.get('primary')).pack(pady=10)

                def do_delete_user():
                    sel = tree.selection()
                    if not sel:
                        status_lbl.configure(text='Seleccione una cuenta para eliminar')
                        return
                    iid = sel[0]
                    vals = tree.item(iid, 'values')
                    if not vals:
                        status_lbl.configure(text='Selección inválida')
                        return
                    uid, uname = vals[0], vals[1]
                    # prevenir eliminación del usuario actualmente conectado
                    if self.current_user and uname == self.current_user:
                        status_lbl.configure(text='No puede eliminar la cuenta actualmente activa')
                        return
                    ok = database.delete_user(int(uid))
                    if not ok:
                        status_lbl.configure(text='Error eliminando usuario')
                    else:
                        status_lbl.configure(text='Usuario eliminado')
                        refresh_users()

                edit_btn = ctk.CTkButton(btns, text='Editar', command=do_edit_user, fg_color=self.colors.get('primary'))
                edit_btn.grid(row=0, column=0, padx=6, pady=6)
                del_btn = ctk.CTkButton(btns, text='Eliminar', command=do_delete_user, fg_color='#c53030')
                del_btn.grid(row=0, column=1, padx=6, pady=6)

        else:
            # fallback use ttk.Notebook
            nb = ttk.Notebook(frame)
            nb.pack(fill='both', expand=True, padx=10, pady=10)
            f1 = tk.Frame(nb, bg=colors.get('frame'))
            f2 = tk.Frame(nb, bg=colors.get('frame'))
            f3 = tk.Frame(nb, bg=colors.get('frame'))
            nb.add(f1, text='Resolucion')
            nb.add(f2, text='Gestion de moneda')
            nb.add(f3, text='Cierre')
            if is_admin:
                f4 = tk.Frame(nb, bg=colors.get('frame'))
                nb.add(f4, text='Cuentas')
                # fill accounts
                tree = ttk.Treeview(f4, columns=('id','username','role','nombre','apellido','cedula','telefono'), show='headings')
                headings = {'id':'ID','username':'Usuario','role':'Rol','nombre':'Nombre','apellido':'Apellido','cedula':'Cédula','telefono':'Teléfono'}
                for c in ('id','username','role','nombre','apellido','cedula','telefono'):
                    tree.heading(c, text=headings.get(c, c.capitalize()))
                tree.pack(fill='both', expand=True, padx=6, pady=6)
                for r in database.get_all_users():
                    rid, uname, irole, nombre, apellido, cedula, telefono = r
                    tree.insert('', 'end', values=(rid, uname, {'admin':'Administrador','employee':'Empleado'}.get(irole, irole), nombre, apellido, cedula, telefono))
                # botón para abrir diálogo de alta en fallback
                status = ctk.CTkLabel(f4, text='')
                status.pack(anchor='w', padx=6, pady=(2,4))

                def refresh_fallback():
                    try:
                        for i in tree.get_children():
                            tree.delete(i)
                        for rr in database.get_all_users():
                            rid, uname, irole, nombre, apellido, cedula, telefono = rr
                            tree.insert('', 'end', values=(rid, uname, {'admin':'Administrador','employee':'Empleado'}.get(irole, irole), nombre, apellido, cedula, telefono))
                    except Exception:
                        try:
                            import traceback
                            traceback.print_exc()
                        except Exception:
                            pass

                def open_add_fallback_dialog():
                    dlg = tk.Toplevel(self)
                    dlg.title('Agregar cuenta')
                    try:
                        dlg.resizable(True, True)
                        dlg.minsize(400, 380)
                    except Exception:
                        pass
                    # centrar sobre padre
                    try:
                        self.update_idletasks()
                        pwx = self.winfo_rootx()
                        pwy = self.winfo_rooty()
                        pww = self.winfo_width()
                        pwh = self.winfo_height()
                    except Exception:
                        pwx = pwy = 0
                        pww = dlg.winfo_screenwidth()
                        pwh = dlg.winfo_screenheight()
                    dw, dh = 520, 460
                    dx = pwx + max(0, int((pww - dw) / 2))
                    dy = pwy + max(0, int((pwh - dh) / 2))
                    try:
                        dlg.geometry(f"{dw}x{dh}+{dx}+{dy}")
                    except Exception:
                        pass
                    try:
                        dlg.transient(self)
                        dlg.grab_set()
                    except Exception:
                        pass
                    frame = tk.Frame(dlg, bg=colors.get('frame'))
                    frame.pack(fill='both', expand=True, padx=12, pady=12)
                    tk.Label(frame, text='Nombre').pack(anchor='w', padx=6, pady=(6,0))
                    en = tk.Entry(frame)
                    en.pack(fill='x', padx=6, pady=4)
                    tk.Label(frame, text='Apellido').pack(anchor='w', padx=6, pady=(6,0))
                    ea = tk.Entry(frame)
                    ea.pack(fill='x', padx=6, pady=4)
                    tk.Label(frame, text='Cédula').pack(anchor='w', padx=6, pady=(6,0))
                    ec = tk.Entry(frame)
                    ec.pack(fill='x', padx=6, pady=4)
                    tk.Label(frame, text='Teléfono').pack(anchor='w', padx=6, pady=(6,0))
                    et = tk.Entry(frame)
                    et.pack(fill='x', padx=6, pady=4)
                    tk.Label(frame, text='Usuario').pack(anchor='w', padx=6, pady=(6,0))
                    eu = tk.Entry(frame)
                    eu.pack(fill='x', padx=6, pady=4)
                    tk.Label(frame, text='Contraseña').pack(anchor='w', padx=6, pady=(6,0))
                    ep = tk.Entry(frame, show='*')
                    ep.pack(fill='x', padx=6, pady=4)
                    role_var2 = tk.StringVar(value='Empleado')
                    ttk.Label(frame, text='Rol').pack(anchor='w', padx=6, pady=(6,0))
                    role_c = ttk.Combobox(frame, textvariable=role_var2, values=['Empleado','Administrador'], state='readonly')
                    role_c.pack(padx=6, pady=6)
                    lbl = tk.Label(frame, text='')
                    lbl.pack(anchor='w', padx=6)

                    def save_fallback():
                        try:
                            nombre = en.get().strip()
                            apellido = ea.get().strip()
                            ced = ec.get().strip()
                            tel = et.get().strip()
                            uname = eu.get().strip()
                            pwd = ep.get().strip()
                            role_map = {'Administrador':'admin','Empleado':'employee'}
                            role = role_map.get(role_var2.get(), 'employee')
                            if not (nombre and apellido and ced and tel and uname and pwd):
                                lbl.configure(text='Complete usuario y todos los campos requeridos')
                                return
                            try:
                                ok = database.create_user(uname, pwd, role, nombre=nombre, apellido=apellido, cedula=ced, telefono=tel)
                            except Exception as e:
                                lbl.configure(text=f'Error al crear usuario: {e}')
                                return
                            if not ok:
                                lbl.configure(text='Error: usuario ya existe')
                            else:
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
                                status.configure(text='Usuario creado')
                                refresh_fallback()
                        except Exception as e:
                            try:
                                import traceback
                                traceback.print_exc()
                            except Exception:
                                pass
                            lbl.configure(text=f'Error inesperado: {e}')

                    tk.Button(frame, text='Crear cuenta', command=save_fallback).pack(pady=8)

                addb = ctk.CTkButton(f4, text='Agregar cuenta', command=open_add_fallback_dialog, fg_color=colors.get('primary'))
                addb.pack(anchor='e', padx=6, pady=(0,6))
                # botones editar/eliminar en fallback
                btnsf = tk.Frame(f4, bg=colors.get('frame'))
                btnsf.pack(fill='x', padx=6, pady=(2,6))

                def do_edit_fallback():
                    sel = tree.selection()
                    if not sel:
                        status.configure(text='Seleccione una cuenta para editar')
                        return
                    iid = sel[0]
                    vals = tree.item(iid, 'values')
                    if not vals:
                        status.configure(text='Selección inválida')
                        return
                    # vals: id, username, role_display, nombre, apellido, cedula, telefono
                    uid, uname, role_disp, nombre_v, apellido_v, ced_v, tel_v = vals
                    dlg = tk.Toplevel(self)
                    dlg.title('Editar cuenta')
                    dlg.transient(self)
                    tk.Label(dlg, text=f'Usuario: {uname}').pack(anchor='w', padx=6, pady=6)
                    ep = tk.Entry(dlg, show='*')
                    ep.pack(fill='x', padx=6, pady=6)
                    role_var2 = tk.StringVar(value=role_disp)
                    role_c = ttk.Combobox(dlg, textvariable=role_var2, values=['Empleado','Administrador'], state='readonly')
                    role_c.pack(padx=6, pady=6)
                    # personal fields
                    en = tk.Entry(dlg)
                    en.insert(0, nombre_v)
                    en.pack(fill='x', padx=6, pady=4)
                    ea = tk.Entry(dlg)
                    ea.insert(0, apellido_v)
                    ea.pack(fill='x', padx=6, pady=4)
                    ec = tk.Entry(dlg)
                    ec.insert(0, ced_v)
                    ec.pack(fill='x', padx=6, pady=4)
                    et = tk.Entry(dlg)
                    et.insert(0, tel_v)
                    et.pack(fill='x', padx=6, pady=4)
                    lbl = tk.Label(dlg, text='')
                    lbl.pack(anchor='w', padx=6)

                    def save_fallback():
                        new_pwd = ep.get().strip()
                        new_role_disp = role_var2.get()
                        role_map = {'Administrador':'admin','Empleado':'employee'}
                        new_role = role_map.get(new_role_disp, 'employee')
                        new_nombre = en.get().strip()
                        new_apellido = ea.get().strip()
                        new_ced = ec.get().strip()
                        new_tel = et.get().strip()
                        ok = database.update_user(int(uid), password=new_pwd if new_pwd else None, role=new_role, nombre=new_nombre, apellido=new_apellido, cedula=new_ced, telefono=new_tel)
                        if not ok:
                            lbl.configure(text='Error actualizando')
                        else:
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
                            refresh_fallback()

                    btnsave = tk.Button(dlg, text='Guardar', command=save_fallback)
                    btnsave.pack(pady=6)

                def do_del_fallback():
                    sel = tree.selection()
                    if not sel:
                        status.configure(text='Seleccione una cuenta para eliminar')
                        return
                    iid = sel[0]
                    vals = tree.item(iid, 'values')
                    if not vals:
                        status.configure(text='Selección inválida')
                        return
                    uid, uname = vals[0], vals[1]
                    # prevenir eliminación del usuario actualmente conectado
                    if self.current_user and uname == self.current_user:
                        status.configure(text='No puede eliminar la cuenta actualmente activa')
                        return
                    ok = database.delete_user(int(uid))
                    if not ok:
                        status.configure(text='Error eliminando')
                    else:
                        status.configure(text='Usuario eliminado')
                        refresh_fallback()

                editbf = ctk.CTkButton(btnsf, text='Editar', command=do_edit_fallback, fg_color=colors.get('primary'))
                editbf.grid(row=0, column=0, padx=6, pady=6)
                delbf = ctk.CTkButton(btnsf, text='Eliminar', command=do_del_fallback, fg_color='#c53030')
                delbf.grid(row=0, column=1, padx=6, pady=6)

            ctk.CTkLabel(f1, text='Resolución y display', font=self.fonts.get('heading')).pack(anchor='w', pady=6)
            ctk.CTkLabel(f2, text='Configuración de moneda', font=self.fonts.get('heading')).pack(anchor='w', pady=6)
            ctk.CTkLabel(f3, text='Cierre de caja y opciones', font=self.fonts.get('heading')).pack(anchor='w', pady=6)

        # intentar colorear la barra nativa a negro (Windows) tras mapear
        try:
            self.after(80, lambda: set_native_titlebar_black(self))
        except Exception:
            pass

        # No automatic fitting: ConfigWindow debe mantener la resolución obligatoria
        # No global grab here: child dialogs will use grab_set() modalmente para evitar cerrar la ventana padre inadvertidamente
