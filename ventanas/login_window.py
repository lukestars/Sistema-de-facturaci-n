import customtkinter as ctk
from styles import apply_styles
from components.login_form import LoginForm
import database
try:
    from utils.window_utils import set_native_titlebar_black
except Exception:
    set_native_titlebar_black = lambda win: None


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Venta - Login")

        # Aplicar estilos y obtener diccionarios
        colors, fonts = apply_styles()
        self.colors = colors
        self.fonts = fonts

        # usar el content frame raíz (no barra de título personalizada en login)
        content = self

        # Asegurar que la geometría y ppi estén disponibles
        self.update_idletasks()
        try:
            # winfo_fpixels('1c') devuelve píxeles por centímetro en la pantalla
            px_per_cm = self.winfo_fpixels('1c')
        except Exception:
            # fallback a 96 dpi
            px_per_cm = 96 / 2.54

        w = int(12 * px_per_cm)
        h = int(16 * px_per_cm)

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = int((sw - w) / 2)
        y = int((sh - h) / 2)

        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)

        # intentar colorear la barra nativa (Windows)
        try:
            set_native_titlebar_black(self)
        except Exception:
            pass

        # Fondo único: ventana y área del formulario con el mismo color
        bg = colors.get("bg", "#121212")
        try:
            self.configure(fg_color=bg)
        except Exception:
            pass

        container = ctk.CTkFrame(
            content, corner_radius=0, fg_color=bg,
            border_width=0
        )
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.82)

        self.login = LoginForm(container, on_success=self._on_success, colors=colors, fonts=fonts, fg_color=bg)
        self.login.pack(expand=True, fill='both', padx=24, pady=24)

    def _on_success(self, username: str):
        # No mostrar popups; continuar con la apertura de la ventana principal

        # Abrir la ventana principal de la aplicación
        try:
            from ventanas.ventana_principal import VentanaPrincipal
            # Crear la ventana principal como Toplevel y ocultar el login (no destruir la raíz)
            try:
                self.withdraw()
            except Exception:
                pass
            main_win = VentanaPrincipal(master=self, user=username)
            # cuando se cierre la ventana principal, devolver el login
            try:
                main_win.protocol('WM_DELETE_WINDOW', lambda: (main_win.destroy(), self.deiconify()))
            except Exception:
                pass
        except Exception as e:
            # Mostrar la excepción en consola para diagnóstico y avisar al usuario
            import traceback
            traceback.print_exc()
            try:
                import tkinter.messagebox as mb
                mb.showerror("Error", f"No se pudo abrir la ventana principal: {e}")
            except Exception:
                pass
