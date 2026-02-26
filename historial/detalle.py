"""Detalle de factura (reimprimir) para la carpeta venta."""
import os
import tkinter as tk
from tkinter import ttk, messagebox

from . import dialogs


def show_factura_detail(app, factura):
    win = tk.Toplevel(app.root)
    win.title('Detalle de Factura')
    try:
        win.state('normal')
        win.state('zoomed')
    except Exception:
        try:
            win.geometry('900x680')
            dialogs.center_window(app, win, 900, 680)
        except Exception:
            pass
    content = dialogs.style_window(app, win)

    outer = tk.Frame(content, bg='#d3d3d3')
    outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
    panel = tk.Frame(outer, bg='#1e1e1e')
    panel.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    header = tk.Frame(panel, bg='#1e1e1e')
    header.pack(fill=tk.X, padx=16, pady=(12, 8))
    lucide = getattr(app, '_lucide_photo', None)
    try:
        icon_ft = lucide('file-text', 28, '#FFFFFF') if lucide else None
        if icon_ft:
            win._icons = getattr(win, '_icons', {})
            win._icons['file-text'] = icon_ft
            tk.Label(header, image=icon_ft, bg='#1e1e1e').pack(side=tk.LEFT)
        else:
            tk.Label(header, text='📄', font=('Helvetica', 26), bg='#1e1e1e', fg='#FFFFFF').pack(side=tk.LEFT)
    except Exception:
        tk.Label(header, text='[DOC]', font=('Helvetica', 18), bg='#1e1e1e', fg='#FFFFFF').pack(side=tk.LEFT)
    num = factura.get('numero_factura') or factura.get('id') or ''
    ttk.Label(header, text=f"Factura: {num}", font=('Helvetica', 16, 'bold')).pack(side=tk.LEFT, padx=10)

    right_top = tk.Frame(header, bg='#1e1e1e')
    right_top.pack(side=tk.RIGHT)

    pm = None
    try:
        if isinstance(factura.get('payment_methods'), (list, tuple)) and factura.get('payment_methods'):
            pm = factura.get('payment_methods')[0]
        else:
            pays = factura.get('payments', {}) or {}
            for k in ('pago_movil_bs', 'punto_bs', 'efectivo_bs', 'usd'):
                if pays.get(k):
                    if k == 'pago_movil_bs':
                        pm = 'Pago Móvil'
                        break
                    if k == 'punto_bs':
                        pm = 'Punto de Venta'
                        break
                    if k == 'efectivo_bs':
                        pm = 'Efectivo'
                        break
                    if k == 'usd':
                        pm = 'Dólar'
                        break
    except Exception:
        pm = None

    color_map = {'Pago Móvil': '#00a2ff', 'Punto de Venta': '#1E90FF', 'Efectivo': '#FFFFFF', 'Dólar': '#0062ff'}
    badge_bg = color_map.get(pm, '#333333')
    badge_fg = '#000000' if pm == 'Efectivo' else '#FFFFFF'
    badge = tk.Label(right_top, text=pm or 'Método: N/D', bg=badge_bg, fg=badge_fg, font=('Helvetica', 10, 'bold'), padx=8, pady=6)
    badge.pack(anchor=tk.E, pady=6)

    totals = tk.Frame(panel, bg='#1e1e1e')
    totals.pack(fill=tk.X, padx=16, pady=(0, 8))
    total_bs = float(factura.get('total_bs', 0) or 0)
    total_usd = 0.0
    try:
        total_usd = float(factura.get('total_usd', 0) or 0)
        if not total_usd and getattr(app, 'exchange_rate', None):
            total_usd = round(total_bs / float(getattr(app, 'exchange_rate', 1.0)), 2)
    except Exception:
        total_usd = 0.0
    ttk.Label(totals, text="Total (BS):", background='#1e1e1e', foreground='#FFFFFF').pack(side=tk.LEFT)
    ttk.Label(totals, text=f"{total_bs:.2f} BS", font=('Helvetica', 14, 'bold'), background='#1e1e1e', foreground='#FFFFFF').pack(side=tk.LEFT, padx=(6, 16))
    ttk.Label(totals, text=f"{total_usd:.2f} $", font=('Helvetica', 14, 'bold'), background='#1e1e1e', foreground=app.theme_colors.get('accent', '#0062ff')).pack(side=tk.LEFT)

    prods = factura.get('productos', []) or []
    table_frame = tk.Frame(panel, bg='#1e1e1e')
    table_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
    cols = ('Cant', 'Producto', 'PrecioUnit', 'Subtotal')
    p_tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=min(12, max(4, len(prods))))
    p_tree.heading('Cant', text='Cant.')
    p_tree.heading('Producto', text='Producto')
    p_tree.heading('PrecioUnit', text='Precio Unit. ($)')
    p_tree.heading('Subtotal', text='Subtotal ($)')
    p_tree.column('Cant', width=80, anchor=tk.CENTER)
    p_tree.column('Producto', width=360)
    p_tree.column('PrecioUnit', width=120, anchor=tk.E)
    p_tree.column('Subtotal', width=120, anchor=tk.E)
    p_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    try:
        p_tree.tag_configure('odd', background='#222222')
        p_tree.tag_configure('even', background='#1f1f1f')
    except Exception:
        pass
    for i, prod in enumerate(prods):
        qty = prod.get('qty', 1)
        name = prod.get('name', '')
        price = float(prod.get('price', 0) or 0)
        subtotal = qty * price
        tag = 'even' if i % 2 == 0 else 'odd'
        p_tree.insert('', tk.END, values=(qty, name, f"{price:.2f}", f"{subtotal:.2f}"), tags=(tag,))

    summary = tk.Frame(panel, bg='#1e1e1e')
    summary.pack(fill=tk.X, padx=16, pady=(8, 16))
    ttk.Label(summary, text='Resumen de Pago:', background='#1e1e1e', foreground='#FFFFFF', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
    pays = factura.get('payments', {}) or {}
    efectivo_amt = float(pays.get('efectivo_bs', 0) or 0)
    usd_amt = float(pays.get('usd', 0) or 0)
    punto_amt = float(pays.get('punto_bs', 0) or 0)
    movil_amt = float(pays.get('pago_movil_bs', 0) or 0)
    pm_ref = factura.get('pago_movil_ref') or pays.get('pago_movil_ref', '')

    line = tk.Frame(summary, bg='#1e1e1e')
    line.pack(fill=tk.X, pady=6)

    def make_item(parent, label_text, amount, fg='#FFFFFF'):
        f = tk.Frame(parent, bg='#1e1e1e')
        f.pack(side=tk.LEFT, padx=8)
        tk.Label(f, text=label_text, bg='#1e1e1e', fg='#AAAAAA').pack(anchor=tk.W)
        tk.Label(f, text=f"{amount:.2f}", bg='#1e1e1e', fg=fg, font=('Helvetica', 11, 'bold')).pack(anchor=tk.W)

    make_item(line, 'Efectivo (BS)', efectivo_amt, fg='#FFFFFF')
    make_item(line, 'Dólar ($)', usd_amt, fg=app.theme_colors.get('accent', '#0062ff'))
    make_item(line, 'Punto', punto_amt, fg='#1E90FF')
    make_item(line, 'Pago Móvil', movil_amt, fg='#00a2ff')
    if pm_ref:
        ttk.Label(summary, text=f'Ref. Pago Móvil: {pm_ref}', background='#1e1e1e', foreground='#CCCCCC').pack(anchor=tk.W, pady=(4, 0))

    btns = tk.Frame(panel, bg='#1e1e1e')
    btns.pack(fill=tk.X, padx=16, pady=(6, 12))

    def reimprimir():
        try:
            os.startfile(factura.get('file', ''), 'print')
            messagebox.showinfo('Impresión', 'Factura enviada a la impresora.')
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo imprimir: {e}')

    ttk.Button(btns, text='Reimprimir', command=reimprimir, style="Accent.TButton").pack(side=tk.LEFT)
    ttk.Button(btns, text='Cerrar', command=win.destroy, style="TButton").pack(side=tk.RIGHT)
