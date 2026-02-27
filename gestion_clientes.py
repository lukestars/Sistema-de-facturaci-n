import sys
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import database
from styles import apply_styles


class GestionClientes(ctk.CTkToplevel):
    """Ventana para gestionar clientes: formulario a la izquierda y lista a la derecha.

    Provee seleccionar cliente que cierra la ventana y ejecuta un callback.
    """

    def __init__(self, master=None, on_select=None, **kwargs):
        super().__init__(master=master, **kwargs)
        self.title("Gestión de Clientes")
        self.on_select = on_select
        colors, fonts = apply_styles()
        self.colors = colors
        self.fonts = fonts

        # Use native titlebar on all platforms to preserve minimize/maximize buttons
        use_native_titlebar = True

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        content_row = 0 if use_native_titlebar else 1
        self.grid_rowconfigure(content_row, weight=1)
        if not use_native_titlebar:
            self.grid_rowconfigure(0, weight=0)

        # Barra de título personalizada solo en Windows
        if not use_native_titlebar:
            try:
                title_bar = tk.Frame(self, bg='black', relief='flat')
                title_bar.grid(row=0, column=0, columnspan=2, sticky='ew')
                title_bar.grid_columnconfigure(0, weight=1)
                title_lbl = tk.Label(title_bar, text='Gestión de Clientes', bg='black', fg=self.colors.get('text'), font=self.fonts.get('heading'))
                title_lbl.grid(row=0, column=0, sticky='w', padx=(8, 0), pady=4)

                def _minimize():
                    try:
                        self.iconify()
                    except Exception:
                        pass

                def _toggle_maximize():
                    try:
                        if getattr(self, '_is_maximized', False):
                            try:
                                self.state('normal')
                            except Exception:
                                if getattr(self, '_normal_geometry', None):
                                    self.geometry(self._normal_geometry)
                            self._is_maximized = False
                            max_btn.configure(text='🗖')
                        else:
                            try:
                                self._normal_geometry = self.geometry()
                            except Exception:
                                self._normal_geometry = None
                            try:
                                self.state('zoomed')
                            except Exception:
                                sw = self.winfo_screenwidth()
                                sh = self.winfo_screenheight()
                                self.geometry(f"{sw}x{sh}+0+0")
                            self._is_maximized = True
                            max_btn.configure(text='🗗')
                    except Exception:
                        pass

                min_btn = tk.Button(title_bar, text='🗕', bg='black', fg=self.colors.get('text'), bd=0, activebackground='black', activeforeground=self.colors.get('text'), command=_minimize)
                min_btn.grid(row=0, column=1, sticky='e', padx=2)
                max_btn = tk.Button(title_bar, text='🗖', bg='black', fg=self.colors.get('text'), bd=0, activebackground='black', activeforeground=self.colors.get('text'), command=_toggle_maximize)
                max_btn.grid(row=0, column=2, sticky='e', padx=2)
                close_btn = tk.Button(title_bar, text='✕', bg='black', fg=self.colors.get('text'), bd=0, activebackground='black', activeforeground=self.colors.get('text'), command=self.destroy)
                close_btn.grid(row=0, column=3, sticky='e', padx=6)

                def _start_move(event):
                    self._drag_offset_x = event.x
                    self._drag_offset_y = event.y

                def _on_move(event):
                    try:
                        x = event.x_root - getattr(self, '_drag_offset_x', 0)
                        y = event.y_root - getattr(self, '_drag_offset_y', 0)
                        self.geometry(f'+{x}+{y}')
                    except Exception:
                        pass

                title_bar.bind('<Button-1>', _start_move)
                title_bar.bind('<B1-Motion>', _on_move)
                title_lbl.bind('<Button-1>', _start_move)
                title_lbl.bind('<B1-Motion>', _on_move)
                title_lbl.bind('<Double-1>', lambda e: _toggle_maximize())
            except Exception:
                pass

        # Reorganizar: lista a la izquierda, registro a la derecha en su propio recuadro
        left = ctk.CTkFrame(self, fg_color=self.colors.get('frame'))
        left.grid(row=content_row, column=0, sticky='nsew', padx=8, pady=8)
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)
        right = ctk.CTkFrame(self, fg_color=self.colors.get('frame'))
        right.grid(row=content_row, column=1, sticky='nsew', padx=8, pady=8)
        right.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Tabla (ttk.Treeview estilizado) en la izquierda
        container = tk.Frame(left, bg=self.colors.get('frame'))
        container.grid(row=0, column=0, sticky='nsew')
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(container, columns=('nombre', 'apellido', 'cedula', 'telefono'), show='headings', selectmode='browse', style='Custom.Treeview')
        self.tree.heading('nombre', text='Nombre')
        self.tree.heading('apellido', text='Apellido')
        self.tree.heading('cedula', text='Cédula')
        self.tree.heading('telefono', text='Teléfono')
        self.tree.column('nombre', width=160, anchor='w')
        self.tree.column('apellido', width=140, anchor='w')
        self.tree.column('cedula', width=120, anchor='center')
        self.tree.column('telefono', width=120, anchor='center')

        # usar style configurado globalmente para scrolbars
        vsb = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview, style='Vertical.TScrollbar')
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky='ns')
        self.tree.grid(row=0, column=0, sticky='nsew')

        # Botones de acción para filas (editar/eliminar)
        btns_frame = ctk.CTkFrame(left, fg_color=self.colors.get('frame'))
        btns_frame.grid(row=1, column=0, sticky='ew', pady=(8, 0))
        btns_frame.grid_columnconfigure(0, weight=1)
        # Seleccionar, Editar, Eliminar
        select_btn = ctk.CTkButton(btns_frame, text='Seleccionar', fg_color=self.colors.get('primary'), command=self._seleccionar_desde_menu)
        select_btn.grid(row=0, column=0, sticky='w', padx=6)
        edit_btn = ctk.CTkButton(btns_frame, text='Editar', fg_color=self.colors.get('primary'), command=self._abrir_editor_seleccionado)
        edit_btn.grid(row=0, column=1, sticky='w', padx=6)
        del_btn = ctk.CTkButton(btns_frame, text='Eliminar', fg_color='#c53030', command=self._eliminar_seleccionado)
        del_btn.grid(row=0, column=2, sticky='w', padx=6)

        # Popup menu para acciones por fila
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label='Seleccionar', command=self._seleccionar_desde_menu)
        self.menu.add_command(label='Editar', command=self._abrir_editor_seleccionado)
        self.menu.add_command(label='Eliminar', command=self._eliminar_seleccionado)

        self.tree.bind('<Button-3>', self._on_right_click)
        self.tree.bind('<Double-1>', self._on_double_click)

        # Sección Derecha - Registro (reubicada)
        ctk.CTkLabel(right, text="Registrar cliente", font=self.fonts.get('heading')).grid(row=0, column=0, pady=(6, 12))

        f = ctk.CTkFrame(right, fg_color=self.colors.get('frame'))
        f.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)
        f.grid_columnconfigure(0, weight=1)

        self.e_nombre = ctk.CTkEntry(f, placeholder_text='Nombre')
        self.e_nombre.grid(row=0, column=0, sticky='ew', padx=6, pady=6)
        self.e_apellido = ctk.CTkEntry(f, placeholder_text='Apellido')
        self.e_apellido.grid(row=1, column=0, sticky='ew', padx=6, pady=6)
        self.e_cedula = ctk.CTkEntry(f, placeholder_text='Cédula')
        self.e_cedula.grid(row=2, column=0, sticky='ew', padx=6, pady=6)
        self.e_telefono = ctk.CTkEntry(f, placeholder_text='Teléfono')
        self.e_telefono.grid(row=3, column=0, sticky='ew', padx=6, pady=6)

        # Attach live formatter for cedula entry (show dots while typing)
        try:
            self._attach_cedula_formatter(self.e_cedula)
        except Exception:
            pass

        save_btn = ctk.CTkButton(f, text='Aceptar', fg_color=self.colors.get('primary'), command=self._guardar_cliente)
        save_btn.grid(row=4, column=0, sticky='ew', padx=6, pady=(8, 6))

        # Mensaje
        self.msg = ctk.CTkLabel(f, text='', font=self.fonts.get('small'))
        self.msg.grid(row=5, column=0, sticky='w', padx=6, pady=(4, 6))

        # Cargar
        self.cargar_clientes()

        # Ajustar tamaño para que se muestre todo y ser un poco más grande
        try:
            from utils.window_utils import fit_window
            fit_window(self)
        except Exception:
            pass

    # ---------- lógica de clientes ----------
    def cargar_clientes(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for row in database.get_clients():
            cid, nombre, apellido, cedula, telefono = row
            # mostrar cedula formateada con puntos
            try:
                digits = ''.join(ch for ch in str(cedula) if ch.isdigit())[:8]
                if digits:
                    ced_display = f"{int(digits):,}".replace(',', '.')
                else:
                    ced_display = str(cedula)
            except Exception:
                ced_display = str(cedula)
            self.tree.insert('', 'end', iid=str(cid), values=(nombre, apellido, ced_display, telefono))

        # aplicar colores simples (fila zebra) usando tags, con la paleta global
        colors, _ = apply_styles()
        odd_bg = colors.get('bg', '#1a1a1a')
        # generar un color alterno ligero para filas pares
        def _lighten(hexcol, amount=20):
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
                return '#000000'

        even_bg = _lighten(odd_bg, amount=12)
        fg = colors.get('text', '#ffffff')
        for i, iid in enumerate(self.tree.get_children()):
            tag = 'odd' if i % 2 == 0 else 'even'
            self.tree.item(iid, tags=(tag,))
        self.tree.tag_configure('odd', background=odd_bg, foreground=fg)
        self.tree.tag_configure('even', background=even_bg, foreground=fg)

    def _guardar_cliente(self):
        nombre = self.e_nombre.get().strip()
        apellido = self.e_apellido.get().strip()
        cedula = self.e_cedula.get().strip()
        telefono = self.e_telefono.get().strip()
        # Normalizar cedula a solo dígitos y máximo 8
        ced_digits = ''.join(ch for ch in cedula if ch.isdigit())[:8]
        if ced_digits:
            cedula = ced_digits
        # Normalizar teléfono: solo dígitos, máximo 11
        tel_digits = ''.join(ch for ch in telefono if ch.isdigit())[:11]
        telefono = tel_digits
        if not nombre or not apellido or not cedula:
            self.msg.configure(text='Complete Nombre, Apellido y Cédula')
            return
        res = database.add_client(nombre, apellido, cedula, telefono)
        if res == -1:
            self.msg.configure(text='Cédula ya registrada')
        else:
            self.msg.configure(text='Cliente guardado')
            self.e_nombre.delete(0, 'end')
            self.e_apellido.delete(0, 'end')
            self.e_cedula.delete(0, 'end')
            self.e_telefono.delete(0, 'end')
            self.cargar_clientes()

    def _on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()

    # ---------- util: cedula formatter ----------
    def _format_cedula_display(self, digits: str) -> str:
        if not digits:
            return ''
        try:
            d = digits[:8]
            return f"{int(d):,}".replace(',', '.')
        except Exception:
            return digits

    def _attach_cedula_formatter(self, entry_widget):
        # Bind key release to format cedula while typing
        def _on_key(e):
            val = entry_widget.get()
            # keep only digits and limit to 8
            digits = ''.join(ch for ch in val if ch.isdigit())[:8]
            formatted = self._format_cedula_display(digits)
            # update entry without moving cursor too much (set to end)
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, formatted)

        entry_widget.bind('<KeyRelease>', _on_key)

    def _on_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        # doble click = seleccionar
        self.seleccionar_cliente(iid)

    def _seleccionar_desde_menu(self):
        sel = self.tree.selection()
        if not sel:
            return
        self.seleccionar_cliente(sel[0])

    def seleccionar_cliente(self, iid):
        # obtener datos y llamar callback, luego cerrar
        row = database.get_client(int(iid))
        if not row:
            return
        cid, nombre, apellido, cedula, telefono = row
        # formatear cedula
        try:
            ced_int = int(cedula)
            formatted = f"{ced_int:,}".replace(',', '.')
        except Exception:
            formatted = cedula
        client = {"nombre": nombre, "apellido": apellido, "ci": formatted}
        if callable(self.on_select):
            try:
                self.on_select(client)
            except Exception:
                pass
        self.destroy()

    def _abrir_editor_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        row = database.get_client(int(iid))
        if not row:
            return
        cid, nombre, apellido, cedula, telefono = row
        self.abrir_editor({'id': cid, 'nombre': nombre, 'apellido': apellido, 'cedula': cedula, 'telefono': telefono})

    def abrir_editor(self, datos: dict):
        # ventana de edición
        dlg = ctk.CTkToplevel(self)
        dlg.title('Editar Cliente')
        # marcar como transitorio para la ventana principal y manejar cierre propio
        try:
            dlg.transient(self)
        except Exception:
            pass
        try:
            dlg.protocol('WM_DELETE_WINDOW', dlg.destroy)
        except Exception:
            pass
        try:
            from utils.window_utils import set_native_titlebar_black
            try:
                # aplicar al diálogo tras un pequeño delay
                dlg.after(40, lambda: set_native_titlebar_black(dlg))
            except Exception:
                pass
        except Exception:
            pass
        dlg.grab_set()
        # Fijar tamaño de la ventana de edición a 7x11 cm y centrarla
        try:
            dlg.update_idletasks()
            try:
                px_per_cm = dlg.winfo_fpixels('1c')
            except Exception:
                px_per_cm = 96 / 2.54
            w = int(7 * px_per_cm)
            h = int(11 * px_per_cm)
            sw = dlg.winfo_screenwidth()
            sh = dlg.winfo_screenheight()
            x = max(0, int((sw - w) / 2))
            y = max(0, int((sh - h) / 2))
            dlg.geometry(f"{w}x{h}+{x}+{y}")
            try:
                dlg.minsize(w, h)
            except Exception:
                pass
        except Exception:
            try:
                dlg.geometry('380x220')
            except Exception:
                pass

        ctk.CTkLabel(dlg, text='Editar cliente', font=self.fonts.get('heading')).pack(pady=(10, 6))
        f = ctk.CTkFrame(dlg, fg_color=self.colors.get('frame'))
        f.pack(fill='both', expand=True, padx=10, pady=6)

        e_nombre = ctk.CTkEntry(f, placeholder_text='Nombre')
        e_nombre.pack(fill='x', pady=6)
        e_nombre.insert(0, datos.get('nombre'))
        e_apellido = ctk.CTkEntry(f, placeholder_text='Apellido')
        e_apellido.pack(fill='x', pady=6)
        e_apellido.insert(0, datos.get('apellido'))
        e_cedula = ctk.CTkEntry(f, placeholder_text='Cédula')
        e_cedula.pack(fill='x', pady=6)
        # mostrar cedula formateada
        try:
            ced_digits = ''.join(ch for ch in str(datos.get('cedula') or '') if ch.isdigit())[:8]
            if ced_digits:
                e_cedula.insert(0, f"{int(ced_digits):,}".replace(',', '.'))
            else:
                e_cedula.insert(0, datos.get('cedula') or '')
        except Exception:
            e_cedula.insert(0, datos.get('cedula') or '')

        # Teléfono (ahora editable)
        e_telefono = ctk.CTkEntry(f, placeholder_text='Teléfono')
        e_telefono.pack(fill='x', pady=6)
        e_telefono.insert(0, datos.get('telefono') or '')

        # attach formatter so editing shows dots
        try:
            self._attach_cedula_formatter(e_cedula)
        except Exception:
            pass

        msg = ctk.CTkLabel(f, text='')
        msg.pack(pady=(4, 0))

        def do_save():
            nombre = e_nombre.get().strip()
            apellido = e_apellido.get().strip()
            cedula = e_cedula.get().strip()
            telefono = e_telefono.get().strip()
            if not nombre or not apellido or not cedula:
                msg.configure(text='Complete los campos obligatorios')
                return
            # aplicar mismas normalizaciones que en registro
            ced_digits = ''.join(ch for ch in cedula if ch.isdigit())[:8]
            if ced_digits:
                cedula = ced_digits
            tel_digits = ''.join(ch for ch in telefono if ch.isdigit())[:11]
            telefono = tel_digits
            ok = database.update_client(datos.get('id'), nombre, apellido, cedula, telefono)
            if not ok:
                msg.configure(text='Error: cédula duplicada u otro error')
            else:
                dlg.destroy()
                self.cargar_clientes()

        btn = ctk.CTkButton(f, text='Guardar', fg_color=self.colors.get('primary'), command=do_save)
        btn.pack(pady=(6, 8))

    def _eliminar_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        database.delete_client(int(iid))
        self.cargar_clientes()
        # Removed accidental footer that caused syntax error