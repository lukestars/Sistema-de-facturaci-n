"""Exportar facturas/productos/clientes desde la carpeta venta (CSV y backup)."""
import csv
import tkinter as tk
import datetime
import json
import logging
import os
import shutil
from tkinter import ttk, messagebox, filedialog

from . import dialogs

logger = logging.getLogger('VentaExport')


def show_export_menu(app):
    data_dir = getattr(app, '_data_dir', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))
    facturas_dir = getattr(app, '_facturas_dir', os.path.join(data_dir, 'facturas'))
    backups_dir = getattr(app, '_backups_dir', os.path.join(data_dir, 'backups'))

    win = tk.Toplevel(app.root)
    win.title('Exportar')
    win.resizable(True, True)
    try:
        from utils.window_utils import center_window
        center_window(app, win)
    except Exception:
        pass
    content = dialogs.style_window(app, win)
    pad = 14
    ttk.Label(content, text='Exportar a CSV', font=('Helvetica', 12, 'bold')).pack(pady=(0, pad))

    def _export_facturas():
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')], title='Guardar facturas')
        if not path:
            return
        try:
            rows = []
            base = facturas_dir
            for entry in sorted(os.listdir(base)) if os.path.isdir(base) and os.path.exists(base) else []:
                day_path = os.path.join(base, entry)
                if not os.path.isdir(day_path):
                    continue
                for fname in os.listdir(day_path):
                    if not fname.lower().endswith('.json'):
                        continue
                    with open(os.path.join(day_path, fname), 'r', encoding='utf-8') as f:
                        inv = json.load(f)
                    nro = inv.get('numero_factura') or inv.get('id') or ''
                    fecha = inv.get('datetime') or inv.get('timestamp') or ''
                    total_bs = inv.get('total_bs', 0)
                    total_usd = inv.get('total_usd', 0)
                    state = inv.get('state', '')
                    rows.append((nro, fecha, total_bs, total_usd, state))
            with open(path, 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f)
                w.writerow(['numero', 'fecha', 'total_bs', 'total_usd', 'estado'])
                w.writerows(rows)
            messagebox.showinfo('Exportar', f'Exportadas {len(rows)} facturas a {path}')
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.exception('Export facturas CSV')
            messagebox.showerror('Error', str(e))
        win.destroy()

    def _export_productos():
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')], title='Guardar productos')
        if not path:
            return
        try:
            prods = getattr(app, 'products', [])
            with open(path, 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f)
                w.writerow(['codigo', 'producto', 'precio', 'cantidad_disponible', 'stock_alerta'])
                for p in prods:
                    w.writerow([p.get('codigo'), p.get('producto'), p.get('precio', 0), p.get('cantidad_disponible'), p.get('stock_alerta')])
            messagebox.showinfo('Exportar', f'Exportados {len(prods)} productos a {path}')
        except (OSError, TypeError) as e:
            logger.warning('Export productos: %s', e)
            messagebox.showerror('Error', str(e))
        win.destroy()

    def _export_clientes():
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')], title='Guardar clientes')
        if not path:
            return
        try:
            clients = getattr(app, 'clients', [])
            if not clients and os.path.isfile(os.path.join(data_dir, 'clients.json')):
                with open(os.path.join(data_dir, 'clients.json'), 'r', encoding='utf-8') as f:
                    clients = json.load(f)
            with open(path, 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f)
                w.writerow(['nombre', 'ci'])
                for c in clients:
                    w.writerow([c.get('name'), c.get('ci')])
            messagebox.showinfo('Exportar', f'Exportados {len(clients)} clientes a {path}')
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.warning('Export clientes: %s', e)
            messagebox.showerror('Error', str(e))
        win.destroy()

    def _backup_local():
        os.makedirs(backups_dir, exist_ok=True)
        dest = os.path.join(backups_dir, f"client_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(dest, exist_ok=True)
        for name in ('products.json', 'clients.json', 'app_state.json'):
            src = os.path.join(data_dir, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(dest, name))
        facturas_src = facturas_dir
        if os.path.isdir(facturas_src):
            shutil.copytree(facturas_src, os.path.join(dest, 'facturas'), dirs_exist_ok=True)
        messagebox.showinfo('Respaldo', f'Copia de respaldo creada en:\n{dest}')
        win.destroy()

    ttk.Button(content, text='  Exportar facturas', command=_export_facturas, width=24).pack(fill=tk.X, pady=4)
    ttk.Button(content, text='  Exportar productos', command=_export_productos, width=24).pack(fill=tk.X, pady=4)
    ttk.Button(content, text='  Exportar clientes', command=_export_clientes, width=24).pack(fill=tk.X, pady=4)
    ttk.Button(content, text='  Crear respaldo local', command=_backup_local, width=24).pack(fill=tk.X, pady=4)
    ttk.Button(content, text='Cerrar', command=win.destroy).pack(pady=pad)
