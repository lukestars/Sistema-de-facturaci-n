"""Cierre de caja: ventas del día por forma de pago (para carpeta venta)."""
import datetime
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

from . import dialogs


def compute_cierre_totals(facturas_dia: list, exchange_rate: float = 1.0) -> dict:
    total_efectivo = total_pv = total_pm = total_usd = 0.0
    for inv in facturas_dia:
        pays = inv.get('payments') or {}
        total_efectivo += float(pays.get('efectivo_bs') or 0)
        total_pv += float(pays.get('punto_bs') or 0)
        total_pm += float(pays.get('pago_movil_bs') or 0)
        total_usd += float(pays.get('usd') or 0) * exchange_rate
    total_gral = total_efectivo + total_pv + total_pm + total_usd
    return {
        'total_efectivo': total_efectivo,
        'total_pv': total_pv,
        'total_pm': total_pm,
        'total_usd_bs': total_usd,
        'total_gral': total_gral,
    }


def show_cierre_caja(app):
    facturas_dir = getattr(app, '_facturas_dir', os.path.join(getattr(app, '_data_dir', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')), 'facturas'))
    colors = getattr(app, 'colors', None) or getattr(app, 'theme_colors', {})
    border_gray = colors.get('muted', '#4a4a4f')
    win = tk.Toplevel(app.root)
    win.title('Cierre de caja')
    win.resizable(True, True)
    content = dialogs.style_window(app, win)
    pad = 12
    ttk.Label(content, text='Cierre de caja', font=('Helvetica', 14, 'bold')).pack(pady=(0, pad))
    date_var = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m-%d'))
    f = ttk.Frame(content)
    f.pack(fill=tk.X, pady=4)
    ttk.Label(f, text='Fecha:').pack(side=tk.LEFT, padx=(0, 6))
    date_entry = ttk.Entry(f, textvariable=date_var, width=12)
    date_entry.pack(side=tk.LEFT, padx=6)

    report_outer = tk.Frame(content, bg=border_gray, highlightbackground=border_gray, highlightcolor=border_gray, highlightthickness=1)
    report_outer.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)
    report_frame = ttk.Frame(report_outer)
    report_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    def _cargar():
        date_str = date_var.get().strip()
        if not date_str or len(date_str) < 10:
            messagebox.showwarning('Fecha', 'Indique una fecha (YYYY-MM-DD)')
            return
        facturas_dia = []
        base = facturas_dir
        day_dir = os.path.join(base, date_str[:10])
        if os.path.isdir(day_dir):
            for fname in os.listdir(day_dir):
                if not (fname.lower().endswith('.json') or 'invoice' in fname.lower()):
                    continue
                fpath = os.path.join(day_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as fp:
                        inv = json.load(fp)
                except (OSError, json.JSONDecodeError):
                    continue
                if (inv.get('state') or '').upper() == 'ANULADA':
                    continue
                facturas_dia.append(inv)
        if getattr(app, 'server_url', None) and getattr(app, 'auth_token', None):
            try:
                r = app.request_get(f"{app.server_url}/invoices?from_date={date_str[:10]}&to_date={date_str[:10]}", timeout=5)
                if r and r.status_code == 200:
                    for inv in (r.json() or []):
                        if (inv.get('state') or '').upper() == 'ANULADA':
                            continue
                        if not any(f.get('id') == inv.get('id') for f in facturas_dia):
                            facturas_dia.append(inv)
            except (AttributeError, TypeError, ValueError):
                pass
        tc = float(getattr(app, 'exchange_rate', 1.0))
        totals = compute_cierre_totals(facturas_dia, tc)
        total_efectivo = totals['total_efectivo']
        total_pv = totals['total_pv']
        total_pm = totals['total_pm']
        total_usd = totals['total_usd_bs']
        total_gral = totals['total_gral']
        for w in report_frame.winfo_children():
            w.destroy()
        ttk.Label(report_frame, text=f'Facturas del día: {len(facturas_dia)}', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(report_frame, text=f'Efectivo (BS): {total_efectivo:.2f}').pack(anchor=tk.W)
        ttk.Label(report_frame, text=f'Punto de venta (BS): {total_pv:.2f}').pack(anchor=tk.W)
        ttk.Label(report_frame, text=f'Pago móvil (BS): {total_pm:.2f}').pack(anchor=tk.W)
        ttk.Label(report_frame, text=f'Dólar (BS equiv.): {total_usd:.2f}').pack(anchor=tk.W)
        ttk.Separator(report_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Label(report_frame, text=f'Total (BS): {total_gral:.2f}', font=('Helvetica', 11, 'bold')).pack(anchor=tk.W)

    ttk.Button(f, text='Cargar', command=_cargar).pack(side=tk.LEFT, padx=6)
    _cargar()
    ttk.Button(content, text='Cerrar', command=win.destroy).pack(pady=pad)
