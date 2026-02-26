Aplicación de facturación (esqueleto)

Este proyecto contiene la estructura inicial de una app de facturación en Python usando CustomTkinter.

Estructura creada:
- `styles.py` — Colores, fuentes y aplicar tema.
- `database.py` — Inicialización SQLite y funciones de usuario (init_db, create_user, verify_user).
- `components/login_form.py` — Componente de formulario de login (CTkFrame reutilizable).
- `ventanas/login_window.py` — Ventana de login centrada con tamaño 12x16 cm en tema oscuro.
- `main.py` — Punto de entrada mínimo.
- `requirements.txt` — Dependencias sugeridas.

Instalación rápida:

1. Crear un entorno virtual (recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Ejecutar:

```powershell
python main.py
```

Notas:
- El proyecto crea una base de datos en `data/app.db` y un usuario por defecto `admin` con contraseña `admin`.
- Sigue la estructura pedida: separé estilos, DB, componentes y ventanas.
- Próximo paso: crear la ventana principal, tabla de inventario, y demás componentes en archivos separados.
