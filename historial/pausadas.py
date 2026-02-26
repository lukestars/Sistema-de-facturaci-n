"""Facturas en pausa: listado y acciones para carpeta venta."""
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

from . import dialogs as _dialogs

_UI_SCALE = 1.15


def show_paused_invoices(app):
    data_dir = getattr(app, '_data_dir', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))
    products_path = os.path.join(data_dir, getattr(app, 'FILE_PRODUCTS', 'products.json'))

    win = tk.Toplevel(app.root)
    win.title('Facturas en pausa')
    try:
        win.resizable(True, True)
    except Exception:
        pass
    colors = getattr(app, 'colors', None) or getattr(app, 'theme_colors', {})
    panel_p = colors.get('frame', '#1b1b1f')
    fg_p = colors.get('text', '#e6eef8')
    border_gray = colors.get('muted', '#4a4a4f')
    head_bg = colors.get('table_header', '#2b2b2b')
    try:
        st = ttk.Style()
        st.configure('SmallPaused.Treeview', rowheight=int(22 * _UI_SCALE), font=('Helvetica', int(9 * _UI_SCALE)),
                    background=panel_p, fieldbackground=panel_p, foreground=fg_p)
        st.configure('SmallPaused.Treeview.Heading', font=('Helvetica', int(10 * _UI_SCALE), 'bold'),
                    background=head_bg, foreground=fg_p)
        st.map('SmallPaused.Treeview.Heading', background=[('active', border_gray)], foreground=[('active', fg_p)])
    except Exception:
        pass
    try:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        w = min(int(1200 * _UI_SCALE), max(int(800 * _UI_SCALE), sw - 200))
        h = min(int(700 * _UI_SCALE), max(int(480 * _UI_SCALE), sh - 200))
        win.geometry(f"{w}x{h}")
        win.minsize(int(700 * _UI_SCALE), int(420 * _UI_SCALE))
        _dialogs.center_window(app, win, w, h)
    except Exception:
        try:
            win.geometry('1000x640')
            _dialogs.center_window(app, win, 1000, 640)
        except Exception:
            pass
    content = _dialogs.style_window(app, win)
    pad = int(10 * _UI_SCALE)
    hdr = ttk.Frame(content)
    hdr.pack(fill=tk.X, pady=(pad, 4))
    ttk.Label(hdr, text='Facturas en pausa', font=('Helvetica', int(14 * _UI_SCALE), 'bold')).pack(side=tk.LEFT, padx=pad)

    main_pane = ttk.PanedWindow(content, orient=tk.HORIZONTAL)
    main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    left = ttk.Frame(main_pane)
    right = ttk.Frame(main_pane)
    main_pane.add(left, weight=3)
    main_pane.add(right, weight=2)

    list_frame = ttk.Frame(left)
    list_frame.pack(fill=tk.BOTH, expand=True)
    tree_wrap = tk.Frame(list_frame, bg=border_gray, highlightbackground=border_gray, highlightcolor=border_gray, highlightthickness=1)
    tree_wrap.pack(fill=tk.BOTH, expand=True)
    tree = ttk.Treeview(tree_wrap, columns=('ID', 'Fecha', 'Hora', 'Cliente', 'Productos', 'TotalBS', 'TotalUSD'),
                        show='tree headings', height=18, style='SmallPaused.Treeview')
    tree.heading('#0', text='Fecha')
    tree.heading('ID', text='ID')
    tree.heading('Fecha', text='Fecha/Hora')
    tree.heading('Hora', text='Hora')
    tree.heading('Cliente', text='Cliente')
    tree.heading('Productos', text='Productos')
    tree.heading('TotalBS', text='Total (BS)')
    tree.heading('TotalUSD', text='Total ($)')
    tree.column('#0', width=120)
    tree.column('ID', width=80)
    tree.column('Fecha', width=160)
    tree.column('Hora', width=70, anchor=tk.CENTER)
    tree.column('Cliente', width=180)
    tree.column('Productos', width=320)
    tree.column('TotalBS', width=110, anchor=tk.E)
    tree.column('TotalUSD', width=90, anchor=tk.E)
    vsb = ttk.Scrollbar(tree_wrap, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)

    invoices_map = {}
    date_nodes = {}
    try:
        from datetime import datetime, date, timedelta
        today = date.today()
        yesterday = today - timedelta(days=1)
    except Exception:
        today = None
        yesterday = None
    for inv in getattr(app, 'paused_invoices', []):
        cid = inv.get('id', '')
        ts = inv.get('timestamp') or inv.get('id') or ''
        fecha_human = ''
        hora = ''
        date_label = str(ts)
        try:
            if isinstance(ts, str) and '_' in ts:
                dpart = ts.split('_')[0]
                tpart = ts.split('_')[1]
                fecha_human = f"{dpart[0:4]}-{dpart[4:6]}-{dpart[6:8]} {tpart[0:2]}:{tpart[2:4]}:{tpart[4:6]}"
                hora = f"{tpart[0:2]}:{tpart[2:4]}"
                try:
                    dd = datetime.strptime(dpart, '%Y%m%d').date()
                    if today and dd == today:
                        date_label = 'Hoy'
                    elif yesterday and dd == yesterday:
                        date_label = 'Ayer'
                    else:
                        date_label = dd.strftime('%Y-%m-%d')
                except Exception:
                    date_label = dpart
            else:
                fecha_human = str(ts)
        except Exception:
            fecha_human = str(ts)
        client_name = inv.get('client', {}).get('name', '') if inv.get('client') else ''
        productos_str = ', '.join(f"{p.get('name', '')}({p.get('qty', 1)})" for p in inv.get('productos', []))
        total_bs = float(inv.get('total_bs', 0) or 0)
        total_usd = float(inv.get('total_usd', 0) or 0)
        node = date_nodes.get(date_label)
        if not node:
            node = tree.insert('', tk.END, text=date_label, open=False)
            date_nodes[date_label] = node
        child = tree.insert(node, tk.END, text=ts, iid=cid,
                            values=(cid, fecha_human, hora, client_name, productos_str, f"{total_bs:.2f}", f"{total_usd:.2f}"))
        invoices_map[child] = inv

    detail_hdr = ttk.Label(right, text='Detalle', font=('Helvetica', 12, 'bold'))
    detail_hdr.pack(anchor=tk.W, pady=(6, 4), padx=8)
    detail_box = ttk.Frame(right)
    detail_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    info_vars = {'id': tk.StringVar(), 'client': tk.StringVar(), 'items': tk.StringVar(), 'total': tk.StringVar(),
                 'timestamp': tk.StringVar(), 'total_usd': tk.StringVar(), 'selected_method': tk.StringVar(value='')}
    placeholder = None
    try:
        fg_ph = getattr(app, 'theme_colors', {}).get('table_row_fg', '#8b8b8b')
        icon_ph = app._get_lucide_icon('file-text', 48, fg_ph) if hasattr(app, '_get_lucide_icon') else None
        if icon_ph:
            placeholder = ttk.Label(detail_box, image=icon_ph, text='')
            placeholder.image = icon_ph
        else:
            placeholder = ttk.Label(detail_box, text='📄', font=('Helvetica', 48), foreground=fg_ph)
        if placeholder:
            placeholder.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=12)
    except Exception:
        placeholder = None
    ttk.Label(detail_box, text='ID:').grid(row=1, column=0, sticky=tk.W)
    ttk.Label(detail_box, textvariable=info_vars['id']).grid(row=1, column=1, sticky=tk.W)
    ttk.Label(detail_box, text='Cliente:').grid(row=2, column=0, sticky=tk.W)
    ttk.Label(detail_box, textvariable=info_vars['client']).grid(row=2, column=1, sticky=tk.W)
    ttk.Label(detail_box, text='Items:').grid(row=3, column=0, sticky=tk.NW)
    box_outer = tk.Frame(detail_box, bg=border_gray, highlightbackground=border_gray, highlightcolor=border_gray, highlightthickness=1)
    box_outer.grid(row=3, column=1, sticky='nsew', padx=2, pady=2)
    box_inner = tk.Frame(box_outer, bg=panel_p)
    box_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    try:
        detail_box.grid_rowconfigure(3, weight=1)
        detail_box.grid_columnconfigure(1, weight=1)
    except Exception:
        pass
    try:
        ttk.Style().configure('SmallPausedDetail.Treeview', background=panel_p, fieldbackground=panel_p, foreground=fg_p)
        ttk.Style().configure('SmallPausedDetail.Treeview.Heading', background=head_bg, foreground=fg_p)
    except Exception:
        pass
    p_cols = ('Cant', 'Producto', 'Precio')
    p_tree = ttk.Treeview(box_inner, columns=p_cols, show='headings', selectmode='none', style='SmallPausedDetail.Treeview')
    p_tree.heading('Cant', text='Cant.')
    p_tree.heading('Producto', text='Producto')
    p_tree.heading('Precio', text='Precio')
    p_tree.column('Cant', width=60, anchor=tk.CENTER)
    p_tree.column('Producto', width=260)
    p_tree.column('Precio', width=100, anchor=tk.E)
    p_tree.pack(fill=tk.BOTH, expand=True)
    try:
        p_tree.tag_configure('odd', background=head_bg)
        p_tree.tag_configure('even', background=panel_p)
    except Exception:
        pass
    ttk.Label(detail_box, text='Total (BS):').grid(row=4, column=0, sticky=tk.W, pady=(8, 0))
    ttk.Label(detail_box, textvariable=info_vars['total'], font=('Helvetica', 11, 'bold'),
              foreground=colors.get('accent', '#22c55e')).grid(row=4, column=1, sticky=tk.W, pady=(8, 0))
    ttk.Label(detail_box, text='Total ($):').grid(row=5, column=0, sticky=tk.W)
    ttk.Label(detail_box, textvariable=info_vars['total_usd'], font=('Helvetica', 12, 'bold')).grid(row=5, column=1, sticky=tk.W)

    btns = ttk.Frame(right)
    btns.pack(fill=tk.X, pady=8, padx=8)

    def resume_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Retomar', 'No hay factura seleccionada')
            return
        iid = sel[0]
        inv = invoices_map.get(iid)
        if not inv:
            messagebox.showwarning('Retomar', 'Por favor seleccione una factura (no una carpeta de fecha)')
            return
        inv_id = inv.get('id')
        try:
            if inv.get('client'):
                app.set_active_client(inv.get('client'))
        except Exception:
            pass
        try:
            app.clear_selected_items()
            for p in inv.get('productos', []):
                try:
                    app.add_to_cart_no_reserve(p.get('name', ''), p.get('price', 0.0), p.get('qty', 1))
                except Exception:
                    pass
        except Exception:
            pass
        try:
            app.paused_invoices = [i for i in app.paused_invoices if i.get('id') != inv_id]
            if hasattr(app, 'save_paused_to_disk'):
                app.save_paused_to_disk()
        except Exception:
            pass
        messagebox.showinfo('Retomada', 'Factura cargada en el carrito. Revísela y finalice la compra cuando esté lista.')
        win.destroy()

    def restart_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Reiniciar', 'No hay factura seleccionada')
            return
        iid = sel[0]
        inv = invoices_map.get(iid)
        if not inv:
            messagebox.showwarning('Reiniciar', 'Por favor seleccione una factura (no una carpeta de fecha)')
            return
        inv_id = inv.get('id')
        try:
            for p in inv.get('productos', []):
                try:
                    prod = next((x for x in app.products if x.get('producto') == p.get('name') or x.get('codigo') == p.get('name')), None)
                    if prod and prod.get('cantidad_disponible') is not None:
                        old_q = int(prod.get('cantidad_disponible'))
                        new_q = old_q + int(p.get('qty', 0))
                        app._log_stock_change(prod.get('codigo'), prod.get('producto'), old_q, new_q, 'devolucion_venta')
                        prod['cantidad_disponible'] = new_q
                except Exception:
                    pass
            with open(products_path, 'w', encoding='utf-8') as f:
                json.dump(app.products, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        try:
            app.paused_invoices = [i for i in app.paused_invoices if i.get('id') != inv_id]
            if hasattr(app, 'save_paused_to_disk'):
                app.save_paused_to_disk()
        except Exception:
            pass
        try:
            if hasattr(app, 'load_products'):
                app.load_products()
        except Exception:
            pass
        messagebox.showinfo('Reiniciada', 'Factura reiniciada y stock restaurado')
        win.destroy()

    def delete_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Eliminar', 'No hay factura seleccionada')
            return
        iid = sel[0]
        inv = invoices_map.get(iid)
        if not inv:
            messagebox.showwarning('Eliminar', 'Por favor seleccione una factura (no una carpeta de fecha)')
            return
        inv_id = inv.get('id')
        if not messagebox.askyesno('Eliminar', '¿Eliminar la factura pausada? Esto restaurará el stock y no se podrá recuperar.'):
            return
        try:
            for p in inv.get('productos', []):
                try:
                    prod = next((x for x in app.products if x.get('producto') == p.get('name') or x.get('codigo') == p.get('name')), None)
                    if prod and prod.get('cantidad_disponible') is not None:
                        old_q = int(prod.get('cantidad_disponible'))
                        new_q = old_q + int(p.get('qty', 0))
                        app._log_stock_change(prod.get('codigo'), prod.get('producto'), old_q, new_q, 'devolucion_venta')
                        prod['cantidad_disponible'] = new_q
                except Exception:
                    pass
            with open(products_path, 'w', encoding='utf-8') as f:
                json.dump(app.products, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        try:
            app.paused_invoices = [i for i in app.paused_invoices if i.get('id') != inv_id]
            if hasattr(app, 'save_paused_to_disk'):
                app.save_paused_to_disk()
        except Exception:
            pass
        messagebox.showinfo('Eliminada', 'Factura pausada eliminada y stock restaurado')
        win.destroy()

    ttk.Button(btns, text='Retomar', command=resume_selected, style='Accent.TButton').pack(side=tk.LEFT, padx=6)
    ttk.Button(btns, text='Reiniciar', command=restart_selected, style='TButton').pack(side=tk.LEFT, padx=6)
    ttk.Button(btns, text='Eliminar', command=delete_selected, style='TButton').pack(side=tk.LEFT, padx=6)
    ttk.Button(btns, text='Cerrar', command=win.destroy, style='TButton').pack(side=tk.RIGHT, padx=6)

    def on_select(event=None):
        sel = tree.selection()
        if not sel:
            return
        sid = sel[0]
        inv = invoices_map.get(sid)
        if not inv:
            try:
                children = tree.get_children(sid)
                if children:
                    tree.item(sid, open=not tree.item(sid, 'open'))
                    return
            except Exception:
                return
        if not inv:
            return
        info_vars['id'].set(inv.get('id', ''))
        info_vars['client'].set(inv.get('client', {}).get('name', '') if inv.get('client') else '')
        try:
            def _abbrev(n, l=30):
                s = str(n or '')
                return s if len(s) <= l else s[:l - 3] + '...'
            for r in p_tree.get_children():
                p_tree.delete(r)
            for i, p in enumerate(inv.get('productos', [])):
                try:
                    qty = p.get('qty', 1)
                    name = _abbrev(p.get('name', ''))
                    price = float(p.get('price', 0) or 0)
                    tag = 'even' if i % 2 == 0 else 'odd'
                    p_tree.insert('', tk.END, values=(qty, name, f"{price:.2f}"), tags=(tag,))
                except Exception:
                    pass
        except Exception:
            pass
        info_vars['total'].set(f"{inv.get('total_bs', 0):.2f} BS")
        try:
            usd = float(inv.get('total_usd', 0) or 0)
            if not usd:
                usd = round(float(inv.get('total_bs', 0)) / float(getattr(app, 'exchange_rate', 1.0)), 2)
        except Exception:
            usd = 0.0
        info_vars['total_usd'].set(f"{usd:.2f} $")
        try:
            pm = inv.get('payment_methods') if isinstance(inv.get('payment_methods'), (list, tuple)) and inv.get('payment_methods') else None
            if pm:
                info_vars['selected_method'].set(pm[0])
        except Exception:
            pass

    tree.bind('<<TreeviewSelect>>', on_select)
    try:
        tree.bind('<Double-1>', lambda e: resume_selected())
    except Exception:
        pass
