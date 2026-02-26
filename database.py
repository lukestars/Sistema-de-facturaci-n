import sqlite3
from pathlib import Path
import hashlib

BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "app.db"


def _get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Crea las tablas necesarias y un usuario administrador por defecto si no existe."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            nombre TEXT DEFAULT '',
            apellido TEXT DEFAULT '',
            cedula TEXT DEFAULT '',
            telefono TEXT DEFAULT ''
        )
        """
    )
    # Tabla de productos para inventario
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT DEFAULT '',
            name TEXT NOT NULL,
            price_bs REAL NOT NULL DEFAULT 0,
            price_usd REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    # Tabla de clientes
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            cedula TEXT NOT NULL UNIQUE,
            telefono TEXT
        )
        """
    )
    conn.commit()

    # Migración: si la columna 'role' no existe (BD antigua), agregarla
    # Add missing columns if they don't exist
    try:
        cur.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cur.fetchall()]
        for col, ddl in (
            ('role', "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'employee'"),
            ('nombre', "ALTER TABLE users ADD COLUMN nombre TEXT DEFAULT ''"),
            ('apellido', "ALTER TABLE users ADD COLUMN apellido TEXT DEFAULT ''"),
            ('cedula', "ALTER TABLE users ADD COLUMN cedula TEXT DEFAULT ''"),
            ('telefono', "ALTER TABLE users ADD COLUMN telefono TEXT DEFAULT ''"),
            # products migrations
            ('code', "ALTER TABLE products ADD COLUMN code TEXT DEFAULT ''"),
            ('price_bs', "ALTER TABLE products ADD COLUMN price_bs REAL NOT NULL DEFAULT 0"),
            ('price_usd', "ALTER TABLE products ADD COLUMN price_usd REAL NOT NULL DEFAULT 0"),
        ):
            if col not in cols:
                try:
                    cur.execute(ddl)
                    conn.commit()
                except Exception:
                    pass
    except Exception:
        pass
    # Asegurar que el usuario 'admin' tenga rol admin (en caso de migración)
    try:
        cur.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")
        conn.commit()
    except Exception:
        pass

    # Asegurar usuario por defecto: admin / admin
    if not get_user("admin"):
        create_user("admin", "admin", role='admin')

    conn.close()


    # Ensure settings table exists
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.commit()
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username: str, password: str, role: str = 'employee', nombre: str = '', apellido: str = '', cedula: str = '', telefono: str = '') -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, role, nombre, apellido, cedula, telefono) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, _hash_password(password), role, nombre, apellido, cedula, telefono),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user(username: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, role, nombre, apellido, cedula, telefono FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def verify_user(username: str, password: str) -> bool:
    user = get_user(username)
    if not user:
        return False
    # password_hash is at index 2
    return user[2] == _hash_password(password)


def get_all_users():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, nombre, apellido, cedula, telefono FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def update_user(user_id: int, username: str | None = None, password: str | None = None, role: str | None = None, nombre: str | None = None, apellido: str | None = None, cedula: str | None = None, telefono: str | None = None) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        fields = []
        params = []
        if username is not None:
            fields.append('username = ?')
            params.append(username)
        if password is not None:
            fields.append('password_hash = ?')
            params.append(_hash_password(password))
        if role is not None:
            fields.append('role = ?')
            params.append(role)
        if nombre is not None:
            fields.append('nombre = ?')
            params.append(nombre)
        if apellido is not None:
            fields.append('apellido = ?')
            params.append(apellido)
        if cedula is not None:
            fields.append('cedula = ?')
            params.append(cedula)
        if telefono is not None:
            fields.append('telefono = ?')
            params.append(telefono)
        if not fields:
            return False
        params.append(int(user_id))
        sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        cur.execute(sql, params)
        conn.commit()
        changed = cur.rowcount > 0
        return changed
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_user(user_id: int) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id = ?", (int(user_id),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# Funciones para productos (inventario)
def add_product(name: str, price: float, quantity: int) -> int:
    # backward-compatible: simple call that writes into new schema using price_bs
    return add_product_full(code='', name=name, price_bs=price, price_usd=0.0, quantity=quantity)


def get_products():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, code, name, price_bs, price_usd, quantity FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_product_full(code: str, name: str, price_bs: float, price_usd: float, quantity: int) -> int:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (code, name, price_bs, price_usd, quantity) VALUES (?, ?, ?, ?, ?)",
        (code, name, float(price_bs), float(price_usd), int(quantity)),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def delete_product(product_id: int) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed


def update_product(product_id: int, code: str = None, name: str = None, price_bs: float = None, price_usd: float = None, quantity: int = None) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        fields = []
        params = []
        if code is not None:
            fields.append('code = ?')
            params.append(code)
        if name is not None:
            fields.append('name = ?')
            params.append(name)
        if price_bs is not None:
            fields.append('price_bs = ?')
            params.append(float(price_bs))
        if price_usd is not None:
            fields.append('price_usd = ?')
            params.append(float(price_usd))
        if quantity is not None:
            fields.append('quantity = ?')
            params.append(int(quantity))
        if not fields:
            return False
        params.append(int(product_id))
        sql = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def decrease_product_quantity(product_id: int, amount: int) -> bool:
    """Decrease product quantity by amount if enough stock exists. Returns True if decreased."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # Only decrease if current quantity >= amount
        cur.execute("UPDATE products SET quantity = quantity - ? WHERE id = ? AND quantity >= ?", (int(amount), int(product_id), int(amount)))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def increase_product_quantity(product_id: int, amount: int) -> bool:
    """Increase product quantity by amount. Returns True if updated."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (int(amount), int(product_id)))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# Settings helpers
def get_setting(key: str, default=None):
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
    return default


def set_setting(key: str, value: str) -> bool:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
        conn.commit()
        conn.close()
        return True
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return False


def update_prices_by_rate(rate: float) -> bool:
    """Update price_bs for all products using price_usd * rate. Returns True on success."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE products SET price_bs = price_usd * ?", (float(rate),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        return False


# Funciones para clientes
def add_client(nombre: str, apellido: str, cedula: str, telefono: str = "") -> int:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO clients (nombre, apellido, cedula, telefono) VALUES (?, ?, ?, ?)",
            (nombre, apellido, cedula, telefono),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return -1
    finally:
        conn.close()


def get_clients():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, apellido, cedula, telefono FROM clients ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_client(client_id: int) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed


def update_client(client_id: int, nombre: str, apellido: str, cedula: str, telefono: str) -> bool:
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE clients SET nombre = ?, apellido = ?, cedula = ?, telefono = ? WHERE id = ?",
            (nombre, apellido, cedula, telefono, client_id),
        )
        conn.commit()
        changed = cur.rowcount > 0
        return changed
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_client(client_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, apellido, cedula, telefono FROM clients WHERE id = ?", (client_id,))
    row = cur.fetchone()
    conn.close()
    return row
