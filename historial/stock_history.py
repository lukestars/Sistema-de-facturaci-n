"""Historial de movimientos de stock para carpeta venta."""
import tkinter as tk
from tkinter import ttk
import os, json


def show_stock_history_window(app):
    win = tk.Toplevel(app.root)
    win.title('Historial de stock')
    win.transient(app.root)
    win.resizable(True, True)
    _UI_SCALE = getattr(app, '_ui_scale', 1.15)
    w, h = int(960 * _UI_SCALE), int(520 * _UI_SCALE)
    win.minsize(int(700 * _UI_SCALE), int(400 * _UI_SCALE))
    try:
        win.geometry(f'{w}x{h}')
    except Exception:
        pass
    try:
        from . import dialogs
        dialogs.center_window(app, win, w, h)
        content = dialogs.style_window(app, win)
    except Exception:
        content = tk.Frame(win)
        content.pack(fill=tk.BOTH, expand=True)
    panel_bg = getattr(app, 'theme_colors', {}).get('panel', '#0e1014')
    fg_text = getattr(app, 'theme_colors', {}).get('fg_text', '#E8ECF4')
    pad = int(12 * _UI_SCALE)
    frm = tk.Frame(content, bg=panel_bg, padx=pad, pady=pad)
    frm.pack(fill=tk.BOTH, expand=True)
    frm.columnconfigure(0, weight=1)
    hdr = tk.Frame(frm, bg=panel_bg)
    hdr.grid(row=0, column=0, sticky='ew', pady=(0, pad))
    tk.Label = getattr(__import__('tkinter'), 'Label')
    try:
        tk.Label(hdr, text='Historial de stock', font=('Helvetica', int(14 * _UI_SCALE), 'bold'), bg=panel_bg, fg=fg_text).pack(side=tk.LEFT)
    except Exception:
        pass
    try:
        tk.Label(hdr, text='Movimientos de entrada y salida de productos.', font=('Helvetica', int(10 * _UI_SCALE)), bg=panel_bg, fg=fg_text).pack(side=tk.LEFT, padx=(12, 0))
    except Exception:
        pass
    cols = ('fecha_hora', 'codigo', 'producto', 'cant_ant', 'cant_nueva', 'delta', 'motivo')
    row_h = int(24 * _UI_SCALE)
    try:
        s = ttk.Style()
        s.configure('StockHist.Treeview', background=panel_bg, fieldbackground=panel_bg, foreground=fg_text, rowheight=row_h)
        s.configure('StockHist.Treeview.Heading', background=panel_bg, foreground=fg_text, font=('Helvetica', int(10 * _UI_SCALE), 'bold'))
        s.map('StockHist.Treeview.Heading', background=[('active', panel_bg)], foreground=[('active', fg_text)])
        tree = ttk.Treeview(frm, columns=cols, show='headings', height=18, style='StockHist.Treeview')
    except Exception:
        tree = ttk.Treeview(frm, columns=cols, show='headings', height=18)
    tree.heading('fecha_hora', text='Fecha y hora')
    tree.heading('codigo', text='Código')
    tree.heading('producto', text='Producto')
    tree.heading('cant_ant', text='Cant. ant.')
    tree.heading('cant_nueva', text='Cant. nueva')
    tree.heading('delta', text='Delta')
    tree.heading('motivo', text='Motivo')
    cw = lambda x: int(x * _UI_SCALE)
    tree.column('fecha_hora', width=cw(150))
    tree.column('codigo', width=cw(100))
    tree.column('producto', width=cw(260))
    tree.column('cant_ant', width=cw(72))
    tree.column('cant_nueva', width=cw(72))
    tree.column('delta', width=cw(72))
    tree.column('motivo', width=cw(130))
    tree_frame = tk.Frame(frm, bg=panel_bg)
    tree_frame.grid(row=1, column=0, sticky='nsew', pady=(0, pad))
    frm.rowconfigure(1, weight=1)
    vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    # use grid inside tree_frame to avoid mixing pack/grid in same container
    tree.grid(row=0, column=0, sticky='nsew')
    vsb.grid(row=0, column=1, sticky='ns')
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)
    data_dir = getattr(app, '_data_dir', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))
    stock_path = os.path.join(data_dir, 'stock_history.json')
    history = []
    if os.path.exists(stock_path):
        try:
            with open(stock_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError):
            history = []
    if not isinstance(history, list):
        history = []
    for r in reversed(history):
        tree.insert('', tk.END, values=(
            r.get('fecha_hora', ''),
            r.get('codigo', ''),
            (r.get('producto', '') or '')[:48] + ('...' if len(r.get('producto', '') or '') > 48 else ''),
            r.get('cantidad_anterior', ''),
            r.get('cantidad_nueva', ''),
            r.get('delta', ''),
            r.get('motivo', ''),
        ))
    if not history:
        try:
            tk.Label(frm, text='Aún no hay movimientos registrados.', font=('Helvetica', int(11 * _UI_SCALE)), bg=panel_bg, fg=fg_text).grid(row=2, column=0, pady=pad)
        except Exception:
            pass
    ttk.Button(frm, text='Cerrar', command=win.destroy, style='TButton').grid(row=3, column=0, pady=pad)
