import customtkinter as ctk
import tkinter as tk
from typing import Optional


class ClienteHeader(ctk.CTkFrame):
    """Header simple que muestra el cliente seleccionado y un botón de logout.

    Provee set_client/get_selected_client y un botón para abrir la ventana de
    gestión de clientes si está disponible.
    """

    def __init__(self, master, colors: dict = None, fonts: dict = None, on_logout: Optional[callable] = None, on_config: Optional[callable] = None, is_admin: bool = False, **kwargs):
        super().__init__(master, **kwargs)
        self.colors = colors or {}
        self.fonts = fonts or {}
        self.on_logout = on_logout
        self.on_config = on_config
        self.is_admin = is_admin
        self.selected_client = None

        # Layout
        # Layout principal: sel_btn (left), prefijo 'Cliente', box con columnas, logout (right)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=0)
        self.grid_columnconfigure(4, weight=0)

        # Botón de gestión a la izquierda, antes del prefijo 'Cliente:'
        sel_btn = ctk.CTkButton(self, text="Gestion de cliente", command=self._open_client_selector,
                    fg_color=self.colors.get('primary'), text_color=self.colors.get('text'))
        sel_btn.grid(row=0, column=0, sticky='w', padx=(6, 6), pady=6)

        # Prefijo 'Cliente:' a la izquierda del recuadro
        ctk.CTkLabel(self, text="Cliente:", font=self.fonts.get('small')).grid(row=0, column=1, sticky='w', padx=(0, 6), pady=6)

        # Crear un recuadro que contiene la sección de columnas (Nombre|Apellido|Cédula)
        box = ctk.CTkFrame(self, corner_radius=8, fg_color=self.colors.get('frame'), border_width=1, border_color=self.colors.get('primary'))
        box.grid(row=0, column=2, sticky='w', padx=6, pady=6)
        box.grid_columnconfigure(0, weight=1)
        box.grid_columnconfigure(1, weight=1)
        box.grid_columnconfigure(2, weight=1)

        # Encabezados por columna: Nombre | Apellido | Cédula
        ctk.CTkLabel(box, text="Nombre", font=self.fonts.get('small')).grid(row=0, column=0, sticky='w', padx=8, pady=(6, 2))
        ctk.CTkLabel(box, text="Apellido", font=self.fonts.get('small')).grid(row=0, column=1, sticky='w', padx=8, pady=(6, 2))
        ctk.CTkLabel(box, text="Cédula", font=self.fonts.get('small')).grid(row=0, column=2, sticky='w', padx=8, pady=(6, 2))

        # Campos individuales alineados con encabezados
        self.client_name_label = ctk.CTkLabel(box, text="-", font=self.fonts.get('small'))
        self.client_name_label.grid(row=1, column=0, sticky='w', padx=8, pady=(2, 8))
        self.client_apellido_label = ctk.CTkLabel(box, text="-", font=self.fonts.get('small'))
        self.client_apellido_label.grid(row=1, column=1, sticky='w', padx=8, pady=(2, 8))
        self.client_ci_label = ctk.CTkLabel(box, text="-", font=self.fonts.get('small'))
        self.client_ci_label.grid(row=1, column=2, sticky='w', padx=8, pady=(2, 8))

        # Botón de configuración (engranaje) y logout a la derecha
        if callable(self.on_config):
            cfg_btn = ctk.CTkButton(self, text='⚙', width=36, height=28, command=self.on_config,
                                    fg_color=self.colors.get('frame'), text_color=self.colors.get('text'))
            cfg_btn.grid(row=0, column=3, sticky='e', padx=(0, 6), pady=6)

        logout_btn = ctk.CTkButton(self, text="Cerrar Sesión", command=self._on_logout,
                       fg_color=self.colors.get('primary'), text_color=self.colors.get('text'))
        logout_btn.grid(row=0, column=4, sticky='e', padx=(0, 6), pady=6)

    def _open_client_selector(self):
        try:
            from gestion_clientes import GestionClientes
            win = GestionClientes(self.winfo_toplevel(), on_select=self.set_client)
            win.transient(self.winfo_toplevel())
            win.grab_set()
        except Exception:
            # Fallback simple
            # usar CTkToplevel para que el dialogo respete el tema
            try:
                dlg = ctk.CTkToplevel(self)
            except Exception:
                dlg = tk.Toplevel(self)
            dlg.title("Seleccionar Cliente")
            dlg.transient(self)
            # build dialog contents then size it

            ctk.CTkLabel(dlg, text="Nombre:").grid(row=0, column=0, sticky='e', padx=6, pady=6)
            e_name = ctk.CTkEntry(dlg)
            e_name.grid(row=0, column=1, padx=6, pady=6)

            ctk.CTkLabel(dlg, text="Apellido:").grid(row=1, column=0, sticky='e', padx=6, pady=6)
            e_last = ctk.CTkEntry(dlg)
            e_last.grid(row=1, column=1, padx=6, pady=6)

            ctk.CTkLabel(dlg, text="C.I:").grid(row=2, column=0, sticky='e', padx=6, pady=6)
            e_ci = ctk.CTkEntry(dlg)
            e_ci.grid(row=2, column=1, padx=6, pady=6)

            status_local = ctk.CTkLabel(dlg, text='', text_color=self.colors.get('text'))
            status_local.grid(row=4, column=0, columnspan=2, pady=(4, 6))

            def do_select():
                nombre = e_name.get().strip()
                apellido = e_last.get().strip()
                ci = e_ci.get().strip()
                if not nombre or not apellido or not ci:
                    status_local.configure(text='Complete todos los campos para seleccionar un cliente.')
                    return
                try:
                    ci_int = int(ci)
                    formatted_ci = f"{ci_int:,}".replace(',', '.')
                except Exception:
                    formatted_ci = ci
                client = {"nombre": nombre, "apellido": apellido, "ci": formatted_ci}
                self.set_client(client)
                dlg.destroy()

            btn_sel = ctk.CTkButton(dlg, text="Seleccionar", command=do_select, fg_color=self.colors.get('primary'))
            btn_sel.grid(row=3, column=0, columnspan=2, pady=(6, 10))

            # Ajustar tamaño del diálogo para que muestre todo y sea un poco más grande
            try:
                from utils.window_utils import fit_window
                fit_window(dlg)
            except Exception:
                pass

            dlg.grab_set()

    def set_client(self, client: dict | None):
        self.selected_client = client
        if client:
            nombre = client.get('nombre') or '-'
            apellido = client.get('apellido') or '-'
            ci_raw = client.get('ci') or '-'
            # formatear cédula: mantener solo dígitos, máximo 8, y mostrar con puntos
            digits = ''.join(ch for ch in str(ci_raw) if ch.isdigit())[:8]
            if digits:
                try:
                    ci = f"{int(digits):,}".replace(',', '.')
                except Exception:
                    ci = digits
            else:
                ci = str(ci_raw)
            self.client_name_label.configure(text=nombre)
            self.client_apellido_label.configure(text=apellido)
            self.client_ci_label.configure(text=ci)
        else:
            self.client_name_label.configure(text='-')
            self.client_apellido_label.configure(text='-')
            self.client_ci_label.configure(text='-')

    def get_selected_client(self):
        return self.selected_client

    def _on_logout(self):
        if callable(self.on_logout):
            try:
                self.on_logout()
                return
            except Exception:
                pass
        try:
            root = self.winfo_toplevel()
            root.destroy()
        except Exception:
            pass
