import customtkinter as ctk
import database


class LoginForm(ctk.CTkFrame):
    def __init__(self, master, on_success=None, colors=None, fonts=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_success = on_success
        self.colors = colors or {}
        self.fonts = fonts or {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(
            self, text="Iniciar Sesión", font=self.fonts.get("heading"),
            text_color=self.colors.get("text", "#e6eef8")
        )
        self.label.grid(row=0, column=0, pady=(16, 24))

        self.username = ctk.CTkEntry(
            self, placeholder_text="Usuario", height=40,
            border_width=1, fg_color=self.colors.get("bg", "#121212"),
            text_color=self.colors.get("text", "#e6eef8")
        )
        self.username.grid(row=1, column=0, padx=24, pady=8, sticky="ew")

        self.password = ctk.CTkEntry(
            self, placeholder_text="Contraseña", show="*", height=40,
            border_width=1, fg_color=self.colors.get("bg", "#121212"),
            text_color=self.colors.get("text", "#e6eef8")
        )
        self.password.grid(row=2, column=0, padx=24, pady=8, sticky="ew")

        self.login_btn = ctk.CTkButton(
            self, text="Entrar", command=self._on_login,
            fg_color=self.colors.get("primary"), height=40,
            font=self.fonts.get("normal"), corner_radius=8
        )
        self.login_btn.grid(row=3, column=0, padx=24, pady=(16, 10), sticky="ew")

        self.message = ctk.CTkLabel(
            self, text="", font=self.fonts.get("small"),
            text_color=self.colors.get("muted", "#9aa6bf")
        )
        self.message.grid(row=4, column=0, pady=(4, 12))

        # Enter en cualquier campo o en el formulario ejecuta Entrar
        self.bind("<Return>", lambda e: self._on_login())
        self.username.bind("<Return>", lambda e: self._on_login())
        self.password.bind("<Return>", lambda e: self._on_login())

    def _show_message(self, title, message, kind="info"):
        # Mostrar el mensaje en la etiqueta dentro del formulario en lugar de abrir ventanas
        if kind == 'error':
            self.message.configure(text=message)
        else:
            self.message.configure(text=message)

    def _on_login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()
        if not user or not pwd:
            self.message.configure(text="Por favor complete los campos.")
            return

        if database.verify_user(user, pwd):
            self._show_message("Éxito", f"Bienvenido {user}")
            if callable(self.on_success):
                self.on_success(user)
        else:
            self.message.configure(text="Usuario o contraseña incorrectos.")
            self._show_message("Error", "Usuario o contraseña incorrectos.", kind="error")
