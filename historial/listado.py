"""Listado de facturas finalizadas (historial) para la carpeta venta.

Función principal: show_facturas(app)
"""
import json
import logging
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from . import dialogs

logger = logging.getLogger('VentaHist')


def show_facturas(app):
    """Abre la ventana de historial de facturas finalizadas."""
    facturas_base = getattr(app, '_facturas_dir', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'facturas'))
    ui_scale = getattr(app, '_ui_scale', 1.15)
    colors = getattr(app, 'colors', None) or getattr(app, 'theme_colors', {})
    panel_bg = colors.get('frame', '#1b1b1f')
    fg_text = colors.get('text', '#e6eef8')
    bg_main = colors.get('bg', '#121212')
    border_gray = colors.get('muted', '#4a4a4f')
    detail_bg = colors.get('frame', '#1b1b1f')
    detail_border = '#3a3a3f'
    accent = colors.get('accent', '#22c55e')

    os.makedirs(facturas_base, exist_ok=True)
    win = tk.Toplevel(app.root)
    win.title('Historial de Facturas Finalizadas')
    default_w = int(1000 * ui_scale)
    default_h = int(700 * ui_scale)
    try:
        win.geometry(f"{default_w}x{default_h}")
        win.minsize(int(640 * ui_scale), int(420 * ui_scale))
        dialogs.center_window(app, win, default_w, default_h)
        win.resizable(True, True)
    except Exception:
        try:
            win.geometry('1000x700')
        except Exception:
            pass
    content = dialogs.style_window(app, win)
    pad = int(10 * ui_scale)
    hdr = ttk.Frame(content)
    hdr.pack(fill=tk.X, pady=(pad, 4))
    ttk.Label(hdr, text='Facturas finalizadas', font=('Helvetica', int(14 * ui_scale), 'bold')).pack(side=tk.LEFT, padx=pad)

    # Use a plain frame instead of PanedWindow to avoid any sash/separator
    main_pane = ttk.Frame(content)
    main_pane.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)
    try:
        st = ttk.Style()
        st.configure('Small.Treeview', rowheight=int(22 * ui_scale), font=('Helvetica', int(9 * ui_scale)), background=panel_bg, fieldbackground=panel_bg, foreground=fg_text)
        st.configure('Small.Treeview.Heading', font=('Helvetica', int(10 * ui_scale), 'bold'), background=detail_border, foreground=fg_text)
        st.map('Small.Treeview.Heading', background=[('active', border_gray)], foreground=[('active', fg_text)])
    except Exception:
        pass

    # sizing will be applied after calculating column widths

    left = ttk.Frame(main_pane)
    right = ttk.Frame(main_pane)
    # pack left and right side-by-side; sizes will be fixed after measuring columns
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
    right.pack(side=tk.LEFT, fill=tk.Y, expand=False)

    list_frame = ttk.Frame(left)
    list_frame.pack(fill=tk.BOTH, expand=True)
    tree_wrap = tk.Frame(list_frame, bg=border_gray, highlightbackground=border_gray, highlightcolor=border_gray, highlightthickness=1)
    tree_wrap.pack(fill=tk.BOTH, expand=True)
    tree = ttk.Treeview(tree_wrap, columns=('Nro', 'FechaHora', 'Productos', 'Total', 'Pago'), show='tree headings', height=20, style='Small.Treeview')
    tree.heading('#0', text='Fecha', anchor=tk.W)
    tree.heading('Nro', text='Nro', anchor=tk.W)
    tree.heading('FechaHora', text='Fecha/Hora', anchor=tk.W)
    tree.heading('Productos', text='Productos', anchor=tk.W)
    tree.heading('Total', text='Total (BS/$)', anchor=tk.E)
    tree.heading('Pago', text='Método', anchor=tk.W)
    tree.column('#0', width=72, minwidth=56, stretch=False, anchor=tk.W)
    tree.column('Nro', width=64, minwidth=52, stretch=False, anchor=tk.W)
    tree.column('FechaHora', width=100, minwidth=80, stretch=False, anchor=tk.W)
    tree.column('Productos', width=140, minwidth=80, stretch=False, anchor=tk.W)
    tree.column('Total', width=88, minwidth=72, stretch=False, anchor=tk.E)
    tree.column('Pago', width=80, minwidth=64, stretch=False, anchor=tk.W)
    vsb = ttk.Scrollbar(tree_wrap, orient=tk.VERTICAL, command=tree.yview)
    # show vertical scrollbar only when needed
    def _on_yscroll(first, last):
        try:
            vsb.set(first, last)
            if float(first) <= 0.0 and float(last) >= 0.9999:
                try:
                    vsb.pack_forget()
                except Exception:
                    pass
            else:
                try:
                    vsb.pack(side=tk.RIGHT, fill=tk.Y)
                except Exception:
                    pass
        except Exception:
            pass
    tree.configure(yscrollcommand=_on_yscroll)
    tree.pack(fill=tk.BOTH, expand=True)
    # initialize scrollbar visibility
    try:
        tree.after_idle(lambda: _on_yscroll(*(tree.yview())))
    except Exception:
        pass
    tree.pack(fill=tk.BOTH, expand=True)

    invoices_map = {}
    date_children = {}
    try:
        for entry in sorted(os.listdir(facturas_base)):
            day_path = os.path.join(facturas_base, entry)
            if not os.path.isdir(day_path):
                continue
            date_node = tree.insert('', tk.END, text=entry, open=False)
            date_children[date_node] = []
            files = sorted([f for f in os.listdir(day_path) if f.lower().endswith('.json') or f.lower().startswith('invoice_') or f.lower().startswith('factura_')])
            for idx, fname in enumerate(files, 1):
                fpath = os.path.join(day_path, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        inv = json.load(f)
                except (OSError, json.JSONDecodeError, TypeError):
                    continue
                def _prod_preview(p):
                                name = (p.get('name') or '').strip()
                                if name:
                                    name = name[0].upper() + name[1:] if len(name) > 1 else name.upper()
                                qty = p.get('qty') if p.get('qty') is not None else p.get('quantity', '')
                                return f"{name}({qty})"
                productos_str = ', '.join(_prod_preview(p) for p in inv.get('productos', []))
                preview = productos_str if len(productos_str) <= 80 else productos_str[:77] + '...'
                fecha_h = inv.get('datetime') or inv.get('timestamp', '')
                total_str = f"{inv.get('total_bs', 0):.2f} BS / {inv.get('total_usd', 0):.2f} $"
                pays = inv.get('payments', {}) or {}
                try:
                    tc = float(getattr(app, 'exchange_rate', 1.0))
                except Exception:
                    tc = 1.0
                amounts = {
                    'Dólar': float(pays.get('usd', 0)) * tc,
                    'Punto de Venta': float(pays.get('punto_bs', 0)),
                    'Pago Móvil': float(pays.get('pago_movil_bs', 0)),
                    'Efectivo': float(pays.get('efectivo_bs', 0))
                }
                method = 'Desconocido'
                try:
                    if any(v and float(v) for v in amounts.values()):
                        method = max(amounts, key=lambda k: amounts[k])
                except Exception:
                    pass
                pm = inv.get('payment_methods') if isinstance(inv.get('payment_methods'), (list, tuple)) else None
                method_display = ', '.join(pm) if pm else method
                nro_display = inv.get('numero_factura') or str(idx)
                if (inv.get('state') or '').upper() == 'ANULADA':
                    nro_display = f"{nro_display} [Anulada]"
                child = tree.insert(date_node, tk.END, text=inv.get('timestamp', ''), values=(nro_display, fecha_h, preview, total_str, method_display))
                invoices_map[child] = inv
                date_children[date_node].append(child)
    except Exception:
        pass

    # Auto-size columns to content and prevent user from resizing columns
    try:
        import tkinter.font as tkfont
        cols = ('#0', 'Nro', 'FechaHora', 'Productos', 'Total', 'Pago')
        # use the same base font size as the tree style if possible
        try:
            base_font = tkfont.Font(family='Helvetica', size=int(9 * ui_scale))
        except Exception:
            base_font = tkfont.nametofont('TkDefaultFont')
        padding = int(12 * ui_scale)
        # measure header and values
        max_widths = {c: base_font.measure(tree.heading(c)['text']) + padding for c in cols}
        for parent in tree.get_children(''):
            # include date rows for #0
            try:
                txt = tree.item(parent, 'text')
                w = base_font.measure(str(txt) or '') + padding
                if w > max_widths['#0']:
                    max_widths['#0'] = w
            except Exception:
                pass
            # children (actual invoices)
            for child in tree.get_children(parent):
                vals = tree.item(child, 'values') or ()
                # '#0' column uses item text
                try:
                    t0 = tree.item(child, 'text')
                    w0 = base_font.measure(str(t0) or '') + padding
                    if w0 > max_widths['#0']:
                        max_widths['#0'] = w0
                except Exception:
                    pass
                # other columns map to vals indices
                try:
                    for idx, cid in enumerate(cols[1:], start=0):
                        v = vals[idx] if idx < len(vals) else ''
                        w = base_font.measure(str(v) or '') + padding
                        if w > max_widths[cid]:
                            max_widths[cid] = w
                except Exception:
                    pass
        # apply widths and prevent stretching
        total_w = 0
        for c in cols:
            try:
                minw = tree.column(c, option='minwidth') or 20
            except Exception:
                minw = 20
            w = int(max(max_widths.get(c, 40), int(minw)))
            tree.column(c, width=w, stretch=False)
            total_w += w
        # set left/right frame widths to match content and detail panel
        try:
            right_w = int(360 * ui_scale)
            extra = int(80 * ui_scale)
            # ensure left frame uses total_w
            try:
                left.config(width=total_w)
                left.pack_propagate(False)
            except Exception:
                pass
            try:
                right.config(width=right_w)
                right.pack_propagate(False)
            except Exception:
                pass
        except Exception:
            right_w = int(360 * ui_scale)
        # now compute final window size, cap to screen and center
        try:
            try:
                win.update_idletasks()
            except Exception:
                pass
            extra = int(80 * ui_scale)
            win_w = int(total_w + right_w + extra)
            win_h = int(default_h)
            # cap to screen size with margins
            try:
                screen_w = win.winfo_screenwidth()
                screen_h = win.winfo_screenheight()
                max_w = max(int(screen_w * 0.9), 200)
                max_h = max(int(screen_h * 0.9), 200)
                if win_w > max_w:
                    win_w = max_w
                if win_h > max_h:
                    win_h = max_h
            except Exception:
                pass
            try:
                win.geometry(f"{win_w}x{win_h}")
                win.minsize(win_w, win_h)
                win.maxsize(win_w, win_h)
                win.resizable(False, False)
            except Exception:
                pass
            try:
                dialogs.center_window(app, win, win_w, win_h)
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        pass

    detail_hdr = ttk.Label(right, text='Detalle', font=('Helvetica', 12, 'bold'))
    detail_hdr.pack(anchor=tk.W, pady=(6, 4), padx=8)
    empty_hint = ttk.Label(right, text='No hay facturas finalizadas.' if not invoices_map else 'Seleccione una factura de la lista.', font=('Helvetica', 10))
    empty_hint.pack(anchor=tk.W, padx=8, pady=(0, 4))
    outer_box = tk.Frame(right, bg=border_gray)
    outer_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
    panel = tk.Frame(outer_box, bg=panel_bg)
    panel.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    panel.columnconfigure(0, weight=1)
    panel.rowconfigure(2, weight=1)

    _detail_bg = detail_bg
    _detail_border = detail_border
    _detail_fg = fg_text

    def _detail_value_lbl(parent, textvariable, **kw):
        f = tk.Frame(parent, bg=_detail_border, padx=1, pady=1)
        lbl = tk.Label(f, textvariable=textvariable, bg=_detail_bg, fg=_detail_fg, anchor=tk.W, padx=6, pady=2, font=('Helvetica', 9), **kw)
        lbl.pack(fill=tk.BOTH, expand=True)
        return f

    info_frame = tk.Frame(panel, bg=panel_bg)
    info_frame.grid(row=0, column=0, sticky='ew', padx=8, pady=4)
    info_frame.columnconfigure(1, weight=1)
    info_vars = {
        'id': tk.StringVar(value=''),
        'timestamp': tk.StringVar(value=''),
        'subtotal': tk.StringVar(value='0.00 BS'),
        'iva': tk.StringVar(value='0.00 BS'),
        'total': tk.StringVar(value='0.00 BS'),
        'pago_ref': tk.StringVar(value=''),
        'pago_movil_amt': tk.StringVar(value='0.00 BS'),
        'dolar_amt': tk.StringVar(value='0.00 $'),
        'efectivo_amt': tk.StringVar(value='0.00 BS'),
        'punto_amt': tk.StringVar(value='0.00 BS')
    }
    payment_method_var = tk.StringVar(value='')
    tk.Label(info_frame, text='ID:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=0, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['id']).grid(row=0, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Fecha:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=1, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['timestamp']).grid(row=1, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Método de Pago:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=2, column=0, sticky=tk.W, pady=1)
    f_pm = tk.Frame(info_frame, bg=_detail_border, padx=1, pady=1)
    payment_method_value_lbl = tk.Label(f_pm, textvariable=payment_method_var, font=('Helvetica', 9, 'bold'), bg=_detail_bg, fg=_detail_fg, anchor=tk.W, padx=6, pady=2)
    payment_method_value_lbl.pack(fill=tk.BOTH, expand=True)
    f_pm.grid(row=2, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Subtotal:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=3, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['subtotal']).grid(row=3, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='IVA:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=4, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['iva']).grid(row=4, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Total:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=1)
    f_total = tk.Frame(info_frame, bg=_detail_border, padx=1, pady=1)
    tk.Label(f_total, textvariable=info_vars['total'], font=('Helvetica', 10, 'bold'), bg=_detail_bg, fg=accent, anchor=tk.W, padx=6, pady=2).pack(fill=tk.BOTH, expand=True)
    f_total.grid(row=5, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Ref. Pago Móvil:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=6, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['pago_ref']).grid(row=6, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Pago móvil:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=7, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['pago_movil_amt']).grid(row=7, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Dólar:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=8, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['dolar_amt']).grid(row=8, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Efectivo:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=9, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['efectivo_amt']).grid(row=9, column=1, sticky='ew', pady=1)
    tk.Label(info_frame, text='Punto de Venta:', bg=panel_bg, fg=fg_text, font=('Helvetica', 9)).grid(row=10, column=0, sticky=tk.W, pady=1)
    _detail_value_lbl(info_frame, info_vars['punto_amt']).grid(row=10, column=1, sticky='ew', pady=1)
    methods_box = tk.Frame(panel, bg=panel_bg)
    methods_box.grid(row=1, column=0, sticky='w', padx=8, pady=(6, 0))

    text_container = tk.Frame(panel, bg=panel_bg)
    text_container.grid(row=2, column=0, sticky='nsew', padx=8, pady=4)
    text_container.columnconfigure(0, weight=1)
    text_container.rowconfigure(0, weight=1)
    products_text = tk.Text(text_container, wrap=tk.WORD, height=12, state='disabled', background=panel_bg, foreground=fg_text, insertbackground=fg_text, bd=0, highlightthickness=0, font=('Helvetica', 10))
    products_text.grid(row=0, column=0, sticky='nsew')
    det_scroll = tk.Scrollbar(text_container, orient=tk.VERTICAL, command=products_text.yview, bg=panel_bg, troughcolor=panel_bg, activebackground=panel_bg)
    products_text.configure(yscrollcommand=det_scroll.set)
    det_scroll.grid(row=0, column=1, sticky='ns')

    btns = ttk.Frame(right)
    btns.pack(fill=tk.X, pady=8, padx=8)

    def open_detail():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Seleccionar', 'Seleccione una factura')
            return
        item = sel[0]
        if item in date_children and date_children.get(item):
            messagebox.showinfo('Seleccione', 'Seleccione una factura dentro de la fecha seleccionada')
            return
        inv = invoices_map.get(item)
        if not inv:
            messagebox.showwarning('Seleccionar', 'Factura no encontrada')
            return
        # delegate to app if it has show_factura_detail
        try:
            if hasattr(app, 'show_factura_detail'):
                app.show_factura_detail(inv)
        except Exception:
            pass

    def reprint_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Seleccionar', 'Seleccione una factura')
            return
        item = sel[0]
        if item in date_children:
            messagebox.showinfo('Reimprimir', 'Seleccione una factura (no una carpeta de fecha)')
            return
        inv = invoices_map.get(item)
        if not inv:
            messagebox.showwarning('Reimprimir', 'Factura no encontrada')
            return
        file_path = inv.get('file', '')
        if not file_path or not os.path.isfile(file_path):
            messagebox.showwarning('Reimprimir', 'Archivo de factura no disponible para reimprimir')
            return
        try:
            os.startfile(file_path, 'print')
            messagebox.showinfo('Impresión', 'Enviado a la impresora')
        except (OSError, AttributeError) as e:
            messagebox.showerror('Error', f'No se pudo reimprimir: {e}')

    def anular_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning('Seleccionar', 'Seleccione una factura')
            return
        item = sel[0]
        if item in date_children:
            messagebox.showinfo('Anular', 'Seleccione una factura (no una carpeta de fecha)')
            return
        inv = invoices_map.get(item)
        if not inv:
            return
        if (inv.get('state') or '').upper() == 'ANULADA':
            messagebox.showinfo('Anular', 'Esta factura ya está anulada.')
            return
        motivo = simpledialog.askstring('Motivo de anulación', 'Indique el motivo de anulación (opcional):', parent=win)
        if motivo is None:
            return
        motivo = (motivo or '').strip() or 'Sin motivo'
        inv_id = inv.get('id')
        if inv_id is not None and getattr(app, 'server_url', None) and getattr(app, 'auth_token', None):
            r = app.request_post(f"{app.server_url}/invoices/{inv_id}/anular", json={'motivo': motivo}, timeout=5)
            if not r or r.status_code != 200 or not (r.json() or {}).get('ok'):
                err = (r.json() or {}).get('error', r.text if r else 'Sin respuesta')
                messagebox.showerror('Anular', f'No se pudo anular en el servidor: {err}')
                return
        inv['state'] = 'ANULADA'
        inv['anulada_motivo'] = motivo
        fpath = inv.get('file')
        if fpath and os.path.isfile(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['state'] = 'ANULADA'
                data['anulada_motivo'] = motivo
                with open(fpath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except (OSError, json.JSONDecodeError, TypeError) as e:
                logger.warning('No se pudo guardar anulación en archivo: %s', e)
        vals_old = tree.item(item, 'values')
        nro_old = str(vals_old[0]) if vals_old else inv.get('numero_factura') or ''
        if not nro_old.endswith(' [Anulada]'):
            tree.item(item, values=(nro_old + ' [Anulada]',) + (vals_old[1:] if len(vals_old) > 1 else ()))
        messagebox.showinfo('Anular', 'Factura marcada como anulada.')

    ttk.Button(btns, text='Ver Detalle', command=open_detail, style="Accent.TButton").pack(side=tk.LEFT, padx=6)
    ttk.Button(btns, text='Reimprimir', command=reprint_selected, style="TButton").pack(side=tk.LEFT, padx=6)
    ttk.Button(btns, text='Anular', command=anular_selected, style="TButton").pack(side=tk.LEFT, padx=6)
    ttk.Button(btns, text='Cerrar', command=win.destroy, style="TButton").pack(side=tk.RIGHT, padx=6)

    def on_select(event=None):
        sel = tree.selection()
        if not sel:
            info_vars['id'].set('')
            info_vars['timestamp'].set('')
            payment_method_var.set('')
            info_vars['subtotal'].set('0.00 BS')
            info_vars['iva'].set('0.00 BS')
            info_vars['total'].set('')
            try:
                products_text.configure(state='normal')
                products_text.delete('1.0', tk.END)
                products_text.configure(state='disabled')
            except Exception:
                pass
            return
        item = sel[0]
        if item in date_children:
            try:
                products_text.configure(state='normal')
                products_text.delete('1.0', tk.END)
                products_text.insert(tk.END, f"Facturas del día {tree.item(item, 'text')}:\n\n")
                for child in date_children.get(item, []):
                    inv = invoices_map.get(child)
                    if not inv:
                        continue
                    pm = inv.get('payment_methods') if isinstance(inv.get('payment_methods'), (list, tuple)) else None
                    if pm:
                        method = ', '.join(pm)
                    else:
                        pays = inv.get('payments', {}) or {}
                        method = 'Desconocido'
                        try:
                            tc = float(getattr(app, 'exchange_rate', 1.0))
                        except Exception:
                            tc = 1.0
                        amounts = {'Dólar': float(pays.get('usd', 0)) * tc, 'Punto de Venta': float(pays.get('punto_bs', 0)), 'Pago Móvil': float(pays.get('pago_movil_bs', 0)), 'Efectivo': float(pays.get('efectivo_bs', 0))}
                        try:
                            if any(v and float(v) for v in amounts.values()):
                                method = max(amounts, key=lambda k: amounts[k])
                        except Exception:
                            pass
                    total_bs = inv.get('total_bs', 0)
                    products_text.insert(tk.END, f"ID: {inv.get('timestamp', '')} — Total: {total_bs:.2f} BS — Método: {method}\n")
                products_text.configure(state='disabled')
            except Exception:
                pass
            info_vars['id'].set('')
            info_vars['timestamp'].set('')
            payment_method_var.set('')
            info_vars['subtotal'].set('0.00 BS')
            info_vars['iva'].set('0.00 BS')
            info_vars['total'].set('')
            return
        inv = invoices_map.get(item)
        if not inv:
            return
        info_vars['id'].set(inv.get('numero_factura') or str(inv.get('id', '')) or inv.get('timestamp', ''))
        info_vars['timestamp'].set(inv.get('datetime', inv.get('timestamp', '')))
        info_vars['subtotal'].set(f"{inv.get('subtotal_bs', 0):.2f} BS")
        info_vars['iva'].set(f"{inv.get('iva_amount_bs', 0):.2f} BS")
        info_vars['total'].set(f"{inv.get('total_bs', 0):.2f} BS")
        pays = inv.get('payments', {}) or {}
        try:
            tc = float(getattr(app, 'exchange_rate', 1.0))
        except Exception:
            tc = 1.0
        amounts = {'Dólar': float(pays.get('usd', 0)) * tc, 'Punto de Venta': float(pays.get('punto_bs', 0)), 'Pago Móvil': float(pays.get('pago_movil_bs', 0)), 'Efectivo': float(pays.get('efectivo_bs', 0))}
        pm = inv.get('payment_methods') if isinstance(inv.get('payment_methods'), (list, tuple)) else None
        if pm:
            method_display = ', '.join(pm)
        else:
            method_display = 'Desconocido'
            try:
                if any(v and float(v) for v in amounts.values()):
                    method_display = max(amounts, key=lambda k: amounts[k])
            except Exception:
                pass
        payment_method_var.set(method_display)
        color_map = {'Dólar': '#0062ff', 'Punto de Venta': '#1E90FF', 'Pago Móvil': '#00a2ff', 'Efectivo': '#AAAAAA', 'Desconocido': '#E0E0E0'}
        try:
            primary = method_display.split(',')[0].strip()
            payment_method_value_lbl.config(foreground=color_map.get(primary, '#E0E0E0'))
        except Exception:
            pass
        try:
            pays = inv.get('payments', {}) or {}
            pago_movil_amt = float(pays.get('pago_movil_bs', 0) or 0)
            usd_amt = float(pays.get('usd', 0) or 0)
            efectivo_amt = float(pays.get('efectivo_bs', 0) or 0)
            punto_amt = float(pays.get('punto_bs', 0) or 0)
            mvref = inv.get('pago_movil_ref') or pays.get('pago_movil_ref', '')
        except Exception:
            pago_movil_amt = usd_amt = efectivo_amt = punto_amt = 0.0
            mvref = ''
        try:
            info_vars['pago_ref'].set(str(mvref))
            info_vars['pago_movil_amt'].set(f"{pago_movil_amt:.2f} BS")
            info_vars['dolar_amt'].set(f"{usd_amt:.2f} $")
            info_vars['efectivo_amt'].set(f"{efectivo_amt:.2f} BS")
            info_vars['punto_amt'].set(f"{punto_amt:.2f} BS")
        except Exception:
            pass
        try:
            for w in methods_box.winfo_children():
                try:
                    w.destroy()
                except Exception:
                    pass
            color_map = {'Pago Móvil': '#00a2ff', 'Punto de Venta': '#1E90FF', 'Efectivo': '#FFFFFF', 'Dólar': '#0062ff'}
            fg_map = {'Pago Móvil': '#000000', 'Punto de Venta': '#FFFFFF', 'Efectivo': '#000000', 'Dólar': '#FFFFFF'}
            used = []
            try:
                pm_list = inv.get('payment_methods') if isinstance(inv.get('payment_methods'), (list, tuple)) else []
            except Exception:
                pm_list = []
            if pago_movil_amt and 'Pago Móvil' not in used:
                used.append('Pago Móvil')
            if punto_amt and 'Punto de Venta' not in used:
                used.append('Punto de Venta')
            if efectivo_amt and 'Efectivo' not in used:
                used.append('Efectivo')
            if usd_amt and 'Dólar' not in used:
                used.append('Dólar')
            for m in (pm_list or []):
                if m and m not in used:
                    used.append(m)
            for m in used:
                try:
                    bgc = color_map.get(m, '#333333')
                    fgc = fg_map.get(m, '#FFFFFF')
                    lbl = tk.Label(methods_box, text=m, bg=bgc, fg=fgc, padx=8, pady=4, font=('Helvetica', 9, 'bold'), relief='raised', bd=1)
                    lbl.pack(side=tk.LEFT, padx=6)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            products_text.configure(state='normal')
            products_text.delete('1.0', tk.END)
            for p in inv.get('productos', []):
                name = (p.get('name') or '').strip()
                if name:
                    name = name[0].upper() + name[1:] if len(name) > 1 else name.upper()
                qty = p.get('qty') if p.get('qty') is not None else p.get('quantity', '')
                price = p.get('price', 0.0)
                products_text.insert(tk.END, f"{name} — Cant.: {qty} — Precio: {float(price):.2f} $\n")
            products_text.insert(tk.END, '\n')
            products_text.insert(tk.END, f"Total: {inv.get('total_bs', 0):.2f} BS / {inv.get('total_usd', 0):.2f} $\n")
            products_text.configure(state='disabled')
        except Exception:
            pass

    tree.bind('<<TreeviewSelect>>', on_select)
