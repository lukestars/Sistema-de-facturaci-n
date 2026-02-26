import tkinter as tk
import os
import datetime
import database
import re
try:
    from utils.window_utils import set_native_titlebar_black, fit_window
except Exception:
    try:
        from ..utils.window_utils import set_native_titlebar_black, fit_window
    except Exception:
        set_native_titlebar_black = lambda w: None
        fit_window = lambda w, padding=40, enlarge_factor=1.08: None
try:
    import customtkinter as ctk
except Exception:
    ctk = None
from tkinter import ttk, messagebox


def open_print_window(parent):
    """Open a print dialog using customtkinter when available to match the app styles."""
    try:
        items_panel = getattr(parent, 'factura_panel', None)
        if items_panel is None:
            messagebox.showinfo('Imprimir', 'No hay una factura abierta.')
            return
        selected = items_panel.get_items()
    except Exception:
        selected = []
    if not selected:
        messagebox.showinfo('Imprimir', 'No hay productos seleccionados para imprimir.')
        return

    try:
        rate = float(database.get_setting('exchange_rate', '1.0') or 1.0)
    except Exception:
        rate = 1.0
    try:
        paper_size = str(database.get_setting('receipt_paper_size', '58mm') or '58mm')
    except Exception:
        paper_size = '58mm'

    total_bs = sum((it.get('subtotal', 0.0) or 0.0) for it in selected)
    try:
        total_usd = total_bs / rate if rate else 0.0
    except Exception:
        total_usd = 0.0

    # create CTkToplevel if available to keep visual consistency
    if ctk is not None:
        try:
            win = ctk.CTkToplevel(parent)
        except Exception:
            win = tk.Toplevel(parent)
    else:
        win = tk.Toplevel(parent)

    win.title('Impresión de factura')
    try:
        # sensible default size for print dialog
        win.geometry('640x760')
    except Exception:
        pass
    try:
        win.transient(parent)
        win.grab_set()
    except Exception:
        pass

    # try to enforce a black native titlebar for consistency
    try:
        set_native_titlebar_black(win)
    except Exception:
        pass

    # center relative to parent when possible, otherwise fit to content and center on screen
    try:
        if hasattr(parent, '_center_window'):
            # estimate dialog size and center relative to parent
            parent._center_window(win, dw=640, dh=760)
        else:
            fit_window(win)
    except Exception:
        try:
            fit_window(win)
        except Exception:
            pass

    # choose frames/labels/buttons according to ctk availability
    if ctk is not None:
        Frame = ctk.CTkFrame
        Label = ctk.CTkLabel
        Button = ctk.CTkButton
        Entry = ctk.CTkEntry
    else:
        Frame = ttk.Frame
        Label = ttk.Label
        Button = ttk.Button
        Entry = ttk.Entry

    content = Frame(win)
    try:
        # apply parent palette to main content when possible
        pcolors = getattr(parent, 'colors', {}) or {}
        if ctk is not None:
            try:
                content.configure(fg_color=pcolors.get('bg', None) or pcolors.get('frame', '#1b1b1f'))
            except Exception:
                pass
        else:
            try:
                content.configure(bg=pcolors.get('bg', win.cget('bg')))
            except Exception:
                pass
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    except Exception:
        content.pack(fill=tk.BOTH, expand=True)

    # Shop title
    try:
        shop_title_var = getattr(parent, 'shop_title_var', None)
        if shop_title_var is not None:
            try:
                Label(content, textvariable=shop_title_var, font=('Helvetica', 14, 'bold')).pack(pady=10)
            except Exception:
                Label(content, text=str(shop_title_var)).pack(pady=10)
        else:
            Label(content, text='Comercio', font=('Helvetica', 14, 'bold')).pack(pady=10)
    except Exception:
        Label(content, text='Comercio', font=('Helvetica', 14, 'bold')).pack(pady=10)

    # product list (use ttk.Treeview for tabular display)
    tree_frame = ttk.Frame(content)
    tree_frame.pack(fill=tk.BOTH, padx=6, expand=True)
    # adjust UI column widths according to paper size
    name_col_chars = 16 if '58' in paper_size else 24
    tree = ttk.Treeview(tree_frame, columns=('Producto', 'Cant.', 'Precio Bs'), show='headings', height=min(len(selected), 20))
    tree.heading('Producto', text='Producto')
    tree.heading('Cant.', text='Cant.')
    tree.heading('Precio Bs', text='Precio Bs')
    # approximate pixel widths for columns (simple heuristic)
    tree.column('Producto', width=20 * name_col_chars)
    tree.column('Cant.', width=80, anchor='e')
    tree.column('Precio Bs', width=120, anchor='e')
    vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

    for it in selected:
        name = it.get('name', '')
        qty = int(it.get('quantity', 1) or 1)
        price = float(it.get('price', 0.0) or 0.0)
        tree.insert('', tk.END, values=(name, qty, f"{price:.2f}"))

    try:
        Label(content, text=f'Total: {total_bs:.2f} BS / {total_usd:.2f} $', font=('Helvetica', 11, 'bold')).pack(pady=8)
    except Exception:
        Label(content, text=f'Total: {total_bs:.2f} BS / {total_usd:.2f} $').pack(pady=8)

    # Payments area: style using parent's palette when available and larger entry fields
    pcolors = getattr(parent, 'colors', {}) or {}
    # user selected dark payment background
    payment_bg = pcolors.get('payment_bg', pcolors.get('frame', '#2B2B2B'))
    muted_color = pcolors.get('muted_text', '#7a7a7a')
    entry_bg = pcolors.get('bg', payment_bg)
    try:
        base_font = getattr(parent, 'fonts', {}).get('normal', ('Helvetica', 12))
        # increase font size slightly (+2)
        try:
            if isinstance(base_font, (tuple, list)) and len(base_font) >= 2 and isinstance(base_font[1], (int, float)):
                entry_font = (base_font[0], int(base_font[1]) + 2)
            else:
                entry_font = ('Helvetica', 14)
        except Exception:
            entry_font = ('Helvetica', 14)
    except Exception:
        entry_font = ('Helvetica', 14)

    if ctk is not None:
        try:
            payments_frame = ctk.CTkFrame(content, fg_color=payment_bg, corner_radius=6)
            payments_frame.pack(fill=tk.X, padx=6, pady=(4, 6))
        except Exception:
            payments_frame = ttk.LabelFrame(content, text='Pagos', padding=8)
            payments_frame.pack(fill=tk.X, padx=6, pady=(4, 6))
    else:
        style = ttk.Style()
        try:
            style.configure('Payments.TLabelframe', background=payment_bg)
            style.configure('Payments.TLabelframe.Label', background=payment_bg)
            payments_frame = ttk.LabelFrame(content, text='Pagos', padding=8, style='Payments.TLabelframe')
        except Exception:
            payments_frame = ttk.LabelFrame(content, text='Pagos', padding=8)
        payments_frame.pack(fill=tk.X, padx=6, pady=(4, 6))

    # Ensure grid alignment inside payments frame
    try:
        payments_frame.grid_columnconfigure(0, weight=0)
        payments_frame.grid_columnconfigure(1, weight=1)
    except Exception:
        pass

    # Numeric entry configuration
    entry_digits = 9  # max digits allowed before decimal
    entry_width = entry_digits  # width in characters equals allowed digits

    def format_amount_display(value):
        try:
            v = float(value)
        except Exception:
            try:
                v = float(str(value).replace(',', ''))
            except Exception:
                return ''
        s = f"{v:.2f}"
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s

    # input validation: up to 9 digits before decimal, optional 2 decimals
    def validate_amount(new_value):
        if new_value is None:
            return True
        if new_value == '':
            return True
        # allow commas while typing - remove for validation
        nv = str(new_value).replace(',', '')
        pattern = r'^\d{0,' + str(entry_digits) + r'}(?:\.\d{0,2})?$'
        return bool(re.match(pattern, nv))

    try:
        vcmd = win.register(validate_amount)
    except Exception:
        vcmd = None

    # Labels use muted color
    try:
        lab_maker = Label
    except Exception:
        lab_maker = ttk.Label
    try:
        # CTkLabel supports text_color
        lbl = lab_maker(payments_frame, text='Pago punto de venta (BS):')
        try:
            if ctk is not None:
                lbl.configure(text_color=muted_color)
            else:
                s = ttk.Style()
                s.configure('Impr.Muted.TLabel', foreground=muted_color, background=payment_bg)
                lbl.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl.grid(row=0, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(payments_frame, text='Pago punto de venta (BS):').grid(row=0, column=0, sticky=tk.W)
        except Exception:
            pass
    pago_pv_var = tk.StringVar(value='')
    try:
        pago_pv_entry = Entry(payments_frame, textvariable=pago_pv_var, width=entry_width, justify='right')
        try:
            if vcmd:
                pago_pv_entry.configure(validate='key', validatecommand=(vcmd, '%P'))
        except Exception:
            pass
        pago_pv_entry.grid(row=0, column=1, sticky=tk.EW, padx=6, pady=4)
        try:
            pago_pv_entry.configure(font=entry_font)
        except Exception:
            pass
        try:
            # make background blend with frame
            if ctk is not None:
                pago_pv_entry.configure(fg_color=entry_bg)
            else:
                pago_pv_entry.configure(background=entry_bg)
        except Exception:
            pass
    except Exception:
        pago_pv_entry = ttk.Entry(payments_frame, textvariable=pago_pv_var, width=entry_width, justify='right')
        try:
            if vcmd:
                pago_pv_entry.configure(validate='key', validatecommand=(vcmd, '%P'))
        except Exception:
            pass
        pago_pv_entry.grid(row=0, column=1, sticky=tk.EW, padx=6, pady=4)
        try:
            pago_pv_entry.configure(background=entry_bg)
        except Exception:
            pass

    try:
        lbl = lab_maker(payments_frame, text='Pago efectivo (BS):')
        try:
            if ctk is not None:
                lbl.configure(text_color=muted_color)
            else:
                lbl.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl.grid(row=1, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(payments_frame, text='Pago efectivo (BS):').grid(row=1, column=0, sticky=tk.W)
        except Exception:
            pass
    pago_ef_var = tk.StringVar(value='')
    try:
        pago_ef_entry = Entry(payments_frame, textvariable=pago_ef_var, width=entry_width, justify='right')
        try:
            if vcmd:
                pago_ef_entry.configure(validate='key', validatecommand=(vcmd, '%P'))
        except Exception:
            pass
        pago_ef_entry.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=4)
        try:
            pago_ef_entry.configure(font=entry_font)
        except Exception:
            pass
        try:
            if ctk is not None:
                pago_ef_entry.configure(fg_color=entry_bg)
            else:
                pago_ef_entry.configure(background=entry_bg)
        except Exception:
            pass
    except Exception:
        pago_ef_entry = ttk.Entry(payments_frame, textvariable=pago_ef_var, width=entry_width)
        pago_ef_entry.grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

    try:
        lbl = lab_maker(payments_frame, text='Pago en $ (USD):')
        try:
            if ctk is not None:
                lbl.configure(text_color=muted_color)
            else:
                lbl.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl.grid(row=2, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(payments_frame, text='Pago en $ (USD):').grid(row=2, column=0, sticky=tk.W)
        except Exception:
            pass
    pago_usd_var = tk.StringVar(value='')
    try:
        pago_usd_entry = Entry(payments_frame, textvariable=pago_usd_var, width=entry_width, justify='right')
        try:
            if vcmd:
                pago_usd_entry.configure(validate='key', validatecommand=(vcmd, '%P'))
        except Exception:
            pass
        pago_usd_entry.grid(row=2, column=1, sticky=tk.EW, padx=6, pady=4)
        try:
            pago_usd_entry.configure(font=entry_font)
        except Exception:
            pass
        try:
            if ctk is not None:
                pago_usd_entry.configure(fg_color=entry_bg)
            else:
                pago_usd_entry.configure(background=entry_bg)
        except Exception:
            pass
    except Exception:
        pago_usd_entry = ttk.Entry(payments_frame, textvariable=pago_usd_var, width=entry_width)
        pago_usd_entry.grid(row=2, column=1, sticky=tk.W, padx=6, pady=4)

    try:
        lbl = lab_maker(payments_frame, text='Pago móvil (BS):')
        try:
            if ctk is not None:
                lbl.configure(text_color=muted_color)
            else:
                lbl.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl.grid(row=3, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(payments_frame, text='Pago móvil (BS):').grid(row=3, column=0, sticky=tk.W)
        except Exception:
            pass
    pago_movil_var = tk.StringVar(value='')
    try:
        pago_movil_entry = Entry(payments_frame, textvariable=pago_movil_var, width=entry_width, justify='right')
        try:
            if vcmd:
                pago_movil_entry.configure(validate='key', validatecommand=(vcmd, '%P'))
        except Exception:
            pass
        pago_movil_entry.grid(row=3, column=1, sticky=tk.EW, padx=6, pady=4)
        try:
            pago_movil_entry.configure(font=entry_font)
        except Exception:
            pass
        try:
            if ctk is not None:
                pago_movil_entry.configure(fg_color=entry_bg)
            else:
                pago_movil_entry.configure(background=entry_bg)
        except Exception:
            pass
    except Exception:
        pago_movil_entry = ttk.Entry(payments_frame, textvariable=pago_movil_var, width=entry_width)
        pago_movil_entry.grid(row=3, column=1, sticky=tk.W, padx=6, pady=4)

    try:
        lbl = lab_maker(payments_frame, text='Ref. Pago móvil (6 dígitos):')
        try:
            if ctk is not None:
                lbl.configure(text_color=muted_color)
            else:
                lbl.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl.grid(row=4, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(payments_frame, text='Ref. Pago móvil (6 dígitos):').grid(row=4, column=0, sticky=tk.W)
        except Exception:
            pass
    pago_ref_var = tk.StringVar(value='')
    # Helper to keep entry display tidy while typing: remove trailing .00 and unnecessary commas
    def _format_var_display(var):
        try:
            v = var.get()
        except Exception:
            return
        if v is None:
            return
        s = str(v).strip()
        if s == '':
            return
        # remove commas
        s2 = s.replace(',', '')
        # if looks like a number, remove trailing .00 or trailing zeros
        try:
            if re.match(r'^\d+(?:\.\d+)?$', s2):
                # format removing unnecessary trailing zeros
                if '.' in s2:
                    s_fmt = s2.rstrip('0').rstrip('.')
                else:
                    s_fmt = s2
            else:
                s_fmt = s2
        except Exception:
            s_fmt = s2
        if s_fmt != s:
            try:
                var.set(s_fmt)
            except Exception:
                pass

    # attach formatting trace to numeric payment vars so display updates as user types
    try:
        for _v in (pago_pv_var, pago_ef_var, pago_usd_var, pago_movil_var):
            try:
                _v.trace_add('write', lambda *a, v=_v: _format_var_display(v))
            except Exception:
                try:
                    _v.trace('w', lambda *a, v=_v: _format_var_display(v))
                except Exception:
                    pass
    except Exception:
        pass
    try:
        pago_ref_entry = Entry(payments_frame, textvariable=pago_ref_var, width=entry_width, justify='center')
        try:
            # reference limit: max 6 digits
            def validate_ref(nv):
                if nv == '':
                    return True
                return bool(re.match(r'^\d{0,12}$', nv))
            vref = win.register(validate_ref)
            try:
                pago_ref_entry.configure(validate='key', validatecommand=(vref, '%P'))
            except Exception:
                pass
        except Exception:
            pass
        pago_ref_entry.grid(row=4, column=1, sticky=tk.EW, padx=6, pady=4)
        try:
            pago_ref_entry.configure(font=entry_font)
        except Exception:
            pass
        try:
            if ctk is not None:
                pago_ref_entry.configure(fg_color=entry_bg)
            else:
                pago_ref_entry.configure(background=entry_bg)
        except Exception:
            pass
    except Exception:
        pago_ref_entry = ttk.Entry(payments_frame, textvariable=pago_ref_var, width=entry_width)
        pago_ref_entry.grid(row=4, column=1, sticky=tk.W, padx=6, pady=4)

    status_var = tk.StringVar(value='Pendiente por cobrar')
    # status label styling
    status_bg = pcolors.get('status_bg', pcolors.get('frame', '#2B2B2B'))
    status_fg_default = 'red'
    if ctk is not None:
        status_lbl = Label(content, textvariable=status_var, text_color=status_fg_default)
        try:
            status_lbl.pack(pady=(4, 6))
        except Exception:
            status_lbl.grid(pady=(4, 6))
    else:
        # create a ttk style for the status label so we can update foreground dynamically
        style = ttk.Style()
        try:
            style.configure('Impr.Status.TLabel', background=status_bg, foreground=status_fg_default)
        except Exception:
            pass
        status_lbl = ttk.Label(content, textvariable=status_var, style='Impr.Status.TLabel')
        try:
            status_lbl.pack(pady=(4, 6))
        except Exception:
            status_lbl.grid(pady=(4, 6))

    # Summary box: use a frame that matches the app palette so it blends with the UI
    try:
        if ctk is not None:
            summary_frame = ctk.CTkFrame(content, fg_color=pcolors.get('frame'))
            summary_frame.pack(fill=tk.X, padx=6, pady=(0, 6), ipadx=6, ipady=6)
        else:
            summary_frame = tk.Frame(content, bg=pcolors.get('frame', '#1b1b1f'))
            summary_frame.pack(fill=tk.X, padx=6, pady=(0, 6))
    except Exception:
        summary_frame = ttk.Frame(content)
        try:
            summary_frame.pack(fill=tk.X, padx=6, pady=(0, 6))
        except Exception:
            summary_frame.grid(sticky='ew')
    # grid labels
    try:
        lbl = lab_maker(summary_frame, text='Total requerido:')
        try:
            if ctk is not None:
                lbl.configure(text_color=muted_color)
            else:
                lbl.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl.grid(row=0, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(summary_frame, text='Total requerido:').grid(row=0, column=0, sticky=tk.W)
        except Exception:
            pass
    total_req_var = tk.StringVar(value=f"{total_bs:.2f} BS")
    try:
        tr_lbl = lab_maker(summary_frame, textvariable=total_req_var)
        try:
            if ctk is None:
                tr_lbl.configure(background=pcolors.get('frame', '#1b1b1f'))
        except Exception:
            pass
        tr_lbl.grid(row=0, column=1, sticky=tk.W, padx=6)
    except Exception:
        try:
            ttk.Label(summary_frame, textvariable=total_req_var).grid(row=0, column=1, sticky=tk.W, padx=6)
        except Exception:
            pass
    try:
        lbl2 = lab_maker(summary_frame, text='Pagado (BS):')
        try:
            if ctk is not None:
                lbl2.configure(text_color=muted_color)
            else:
                lbl2.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl2.grid(row=1, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(summary_frame, text='Pagado (BS):').grid(row=1, column=0, sticky=tk.W)
        except Exception:
            pass
    paid_var = tk.StringVar(value='0.00 BS')
    try:
        pv_lbl = lab_maker(summary_frame, textvariable=paid_var)
        try:
            if ctk is None:
                pv_lbl.configure(background=pcolors.get('frame', '#1b1b1f'))
        except Exception:
            pass
        pv_lbl.grid(row=1, column=1, sticky=tk.W, padx=6)
    except Exception:
        try:
            ttk.Label(summary_frame, textvariable=paid_var).grid(row=1, column=1, sticky=tk.W, padx=6)
        except Exception:
            pass
    try:
        lbl3 = lab_maker(summary_frame, text='Falta / Exceso:')
        try:
            if ctk is not None:
                lbl3.configure(text_color=muted_color)
            else:
                lbl3.configure(style='Impr.Muted.TLabel')
        except Exception:
            pass
        lbl3.grid(row=2, column=0, sticky=tk.W)
    except Exception:
        try:
            ttk.Label(summary_frame, text='Falta / Exceso:').grid(row=2, column=0, sticky=tk.W)
        except Exception:
            pass
    diff_var = tk.StringVar(value=f"{total_bs:.2f} BS")
    try:
        dv_lbl = lab_maker(summary_frame, textvariable=diff_var)
        try:
            if ctk is None:
                dv_lbl.configure(background=pcolors.get('frame', '#1b1b1f'))
        except Exception:
            pass
        dv_lbl.grid(row=2, column=1, sticky=tk.W, padx=6)
    except Exception:
        try:
            ttk.Label(summary_frame, textvariable=diff_var).grid(row=2, column=1, sticky=tk.W, padx=6)
        except Exception:
            pass

    payment_summary_var = tk.StringVar(value='')
    ps_lbl = Label(content, textvariable=payment_summary_var)
    ps_lbl.pack(pady=(0, 6))

    def parse_amount(s):
        try:
            return float(str(s).replace(',', ''))
        except Exception:
            return 0.0

    printed = [False]

    def update_payment_status(*a):
        paid_bs = parse_amount(pago_pv_var.get()) + parse_amount(pago_ef_var.get()) + parse_amount(pago_usd_var.get()) * rate + parse_amount(pago_movil_var.get())
        try:
            paid_var.set(f"{format_amount_display(paid_bs)} BS")
        except Exception:
            pass
        diff = round(total_bs - paid_bs, 2)
        try:
            if diff > 0:
                diff_usd = round(diff / rate, 2) if rate else 0.0
                diff_var.set(f"Falta: {format_amount_display(diff)} BS (≈ {format_amount_display(diff_usd)} $)")
                status_var.set('Pendiente por cobrar')
                try:
                    status_lbl.configure(text_color='red')
                except Exception:
                    pass
                try:
                    if ctk is None:
                        s = ttk.Style()
                        s.configure('Impr.Status.TLabel', foreground='red')
                except Exception:
                    pass
                try:
                    btn_print.configure(state='disabled')
                except Exception:
                    pass
            elif abs(diff) <= 0.01:
                diff_var.set('Exacto (0.00 $)')
                status_var.set('Monto Cubierto')
                try:
                    status_lbl.configure(text_color='green')
                except Exception:
                    pass
                try:
                    if ctk is None:
                        s = ttk.Style()
                        s.configure('Impr.Status.TLabel', foreground='green')
                except Exception:
                    pass
                try:
                    btn_print.configure(state='normal')
                except Exception:
                    pass
            else:
                ex = abs(diff)
                if ex <= 50.0:
                    status_var.set(f'Monto Cubierto (Exceso aceptable: {format_amount_display(ex)} BS)')
                    try:
                        status_lbl.configure(text_color='green')
                    except Exception:
                        pass
                    try:
                        if ctk is None:
                            s = ttk.Style()
                            s.configure('Impr.Status.TLabel', foreground='green')
                    except Exception:
                        pass
                    try:
                        btn_print.configure(state='normal')
                    except Exception:
                        pass
                else:
                    status_var.set('Pago excede el total — corrija')
                    try:
                        status_lbl.configure(text_color='red')
                    except Exception:
                        pass
                    try:
                        if ctk is None:
                            s = ttk.Style()
                            s.configure('Impr.Status.TLabel', foreground='red')
                    except Exception:
                        pass
                    try:
                        btn_print.configure(state='disabled')
                    except Exception:
                        pass
        except Exception:
            try:
                btn_print.configure(state='disabled')
            except Exception:
                pass

        try:
            parts = []
            pv = parse_amount(pago_pv_var.get())
            ef = parse_amount(pago_ef_var.get())
            usd = parse_amount(pago_usd_var.get())
            mov = parse_amount(pago_movil_var.get())
            if pv > 0:
                parts.append(f"Punto de Venta: {format_amount_display(pv)} BS")
            if ef > 0:
                parts.append(f"Efectivo: {format_amount_display(ef)} BS")
            if usd > 0:
                parts.append(f"USD: {format_amount_display(usd)} $")
            if mov > 0:
                ref = pago_ref_var.get().strip()
                s = f"Pago Móvil: {format_amount_display(mov)} BS"
                if ref:
                    s += f" (Ref: {ref})"
                parts.append(s)
            payment_summary_var.set(' | '.join(parts) if parts else 'Sin pagos')
        except Exception:
            pass

    for v in (pago_pv_var, pago_ef_var, pago_usd_var, pago_movil_var, pago_ref_var):
        try:
            v.trace_add('write', update_payment_status)
        except Exception:
            try:
                v.trace('w', update_payment_status)
            except Exception:
                pass

    def do_print():
        if printed[0]:
            messagebox.showinfo('Impresión', 'Ya se imprimió esta factura.')
            return
        # Build receipt text adapting to the selected paper size.
        try:
            st = getattr(parent, 'shop_title_var', None)
            shop_title = st.get() if hasattr(st, 'get') else (str(st) if st is not None else 'MI COMERCIO C.A.')
        except Exception:
            shop_title = 'MI COMERCIO C.A.'

        try:
            rif = str(database.get_setting('shop_rif', 'J-12345678-9') or 'J-12345678-9')
        except Exception:
            rif = 'J-12345678-9'

        try:
            iva_enabled = True if str(database.get_setting('vat_enabled', '0')) == '1' else False
            vat_pct = float(database.get_setting('vat_percent', '16') or 16.0)
        except Exception:
            iva_enabled = True
            vat_pct = 16.0

        fecha_print = datetime.datetime.now().strftime("%d/%m/%y %H:%M")

        # 58mm paper: narrow layout (approx 32 chars)
        if '58' in (paper_size or '').lower():
            W = 32
            lines = []
            lines.append(f"{shop_title:^{W}}")
            lines.append(f"{'RIF: ' + rif:^{W}}")
            lines.append('-' * W)
            try:
                client = getattr(parent, 'current_client', None)
                cname = ''
                if client:
                    cname = client.get('name') or client.get('nombre') or str(client)
                lines.append(f"CLI: {cname[:25]}")
            except Exception:
                lines.append(f"CLI: ")
            lines.append(f"FECHA: {fecha_print}")
            lines.append('-' * W)
            # CN(3) + PRODUCTO(9) + $ (7) + Bs (13) = 32
            lines.append(f"{ 'CN':<3}{'PRODUCTO':<9}{'$':>7}{'Bs':>13}")
            lines.append('-' * W)

            sub_usd = 0.0
            for it in selected:
                qty = int(it.get('quantity') or it.get('cantidad') or 1)
                name = (it.get('name') or it.get('nombre') or '')[:8]
                # determine unit price in USD
                unit = None
                if 'price_usd' in it:
                    try:
                        unit = float(it.get('price_usd') or 0.0)
                    except Exception:
                        unit = None
                if unit is None:
                    p = it.get('price') or it.get('precio') or it.get('unit_price') or 0.0
                    try:
                        p = float(p)
                        # if p looks like BS, convert to USD
                        if rate and p > rate * 0.1:
                            unit = p / rate
                        else:
                            unit = p
                    except Exception:
                        unit = 0.0
                total_item_usd = round(unit * qty, 2)
                total_item_bs = round(total_item_usd * rate, 2)
                sub_usd += total_item_usd
                lines.append(f"{qty:<3}{name:<9}{total_item_usd:>7.2f}{total_item_bs:>13.2f}")

            imp_usd = round(sub_usd * (vat_pct / 100.0), 2) if iva_enabled else 0.0
            total_usd = round(sub_usd + imp_usd, 2)

            lines.append('-' * W)
            lines.append(f"SUBTOTAL: {sub_usd:>8.2f}$ | {sub_usd*rate:>9.2f}B")
            lines.append(f"IVA {int(vat_pct)}%:  {imp_usd:>8.2f}$ | {imp_usd*rate:>9.2f}B")
            lines.append('-' * W)
            lines.append(f"{'TOTAL USD:':<15} {total_usd:>15.2f} $")
            lines.append(f"{'TOTAL BS:':<15} {total_usd*rate:>15.2f} Bs")
            lines.append('-' * W)
            lines.append(f"{'¡GRACIAS POR SU COMPRA!':^{W}}")

            text = '\n'.join(lines)
        else:
            # Wider receipt (default, ~45 chars) — previous bimonetary layout
            lines = []
            lines.append('\n' + '=' * 45)
            lines.append(f"{shop_title:^45}")
            lines.append(f"{'RIF: ' + rif:^45}")
            lines.append('-' * 45)
            lines.append(f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
            try:
                client = getattr(parent, 'current_client', None)
                if client:
                    cname = client.get('name') or client.get('nombre') or str(client)
                    lines.append(f"Cliente: {cname}")
            except Exception:
                pass
            lines.append(f"Tasa del día: {rate:,.2f} BS/USD")
            lines.append('-' * 45)
            lines.append(f"{'Cant':<5}{'Descripción':<18}{'USD':>10}{'BS':>12}")
            lines.append('-' * 45)

            subtotal_usd = 0.0
            products_lines = []
            for it in selected:
                name = (it.get('name') or it.get('nombre') or '')
                qty = int(it.get('quantity') or it.get('cantidad') or 1)
                unit_usd = None
                if 'price_usd' in it:
                    try:
                        unit_usd = float(it.get('price_usd') or 0.0)
                    except Exception:
                        unit_usd = None
                if unit_usd is None:
                    p = it.get('price') or it.get('precio') or it.get('unit_price') or 0.0
                    try:
                        p = float(p)
                        if rate and p > rate * 0.1:
                            unit_usd = p / rate
                        else:
                            unit_usd = p
                    except Exception:
                        unit_usd = 0.0
                p_usd = round(unit_usd * qty, 2)
                p_bs = round(p_usd * rate, 2)
                subtotal_usd += p_usd
                products_lines.append((qty, name, p_usd, p_bs))

            for qty, name, p_usd, p_bs in products_lines:
                lines.append(f"{qty:<5}{name[:18]:<18}{p_usd:>10,.2f}{p_bs:>12,.2f}")

            lines.append('-' * 45)
            impuesto_usd = round(subtotal_usd * (vat_pct / 100.0), 2) if iva_enabled else 0.0
            total_usd_calc = round(subtotal_usd + impuesto_usd, 2)
            subtotal_bs = round(subtotal_usd * rate, 2)
            impuesto_bs = round(impuesto_usd * rate, 2)
            total_bs_calc = round(total_usd_calc * rate, 2)

            lines.append(f"{'SUBTOTAL:':>23} {subtotal_usd:>10,.2f} USD | {subtotal_bs:>10,.2f} BS")
            lines.append(f"{'IVA ('+str(int(vat_pct))+'%):':>23} {impuesto_usd:>10,.2f} USD | {impuesto_bs:>10,.2f} BS")
            lines.append(f"{'TOTAL A PAGAR:':>23} {total_usd_calc:>10,.2f} USD | {total_bs_calc:>10,.2f} BS")
            lines.append('-' * 45)
            lines.append(f"{'GRACIAS POR SU COMPRA':^45}")
            lines.append('=' * 45 + '\n')

            text = '\n'.join(lines)

        facturas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'facturas')
        if not os.path.exists(facturas_dir):
            try:
                os.makedirs(facturas_dir)
            except Exception:
                facturas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
                if not os.path.exists(facturas_dir):
                    try:
                        os.makedirs(facturas_dir)
                    except Exception:
                        facturas_dir = os.path.dirname(os.path.dirname(__file__))
        fecha = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fecha_human = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = f'factura_{fecha}.txt'
        file_path = os.path.join(facturas_dir, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception:
            try:
                tf = os.path.join(os.path.expanduser('~'), filename)
                with open(tf, 'w', encoding='utf-8') as f:
                    f.write(text)
                file_path = tf
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo guardar la factura: {e}')
                return

        try:
            # Attempt to print to the configured Windows printer if set.
            printed[0] = False
            try:
                from database import get_setting
                target_printer = get_setting('default_printer', '') or ''
            except Exception:
                target_printer = ''

            def _startfile_print(path):
                try:
                    os.startfile(path, 'print')
                    return True
                except Exception:
                    return False

            if target_printer:
                try:
                    # If pywin32 is available, send the file directly to the named printer
                    import win32print
                    import win32api
                    try:
                        # open the printer
                        hPrinter = win32print.OpenPrinter(target_printer)
                    except Exception:
                        hPrinter = None
                    if hPrinter:
                        try:
                            # read file bytes
                            with open(file_path, 'rb') as f:
                                data = f.read()
                            # Start a raw document
                            doc_info = ("Factura", None, "RAW")
                            job = win32print.StartDocPrinter(hPrinter, 1, doc_info)
                            try:
                                win32print.StartPagePrinter(hPrinter)
                                win32print.WritePrinter(hPrinter, data)
                                win32print.EndPagePrinter(hPrinter)
                            finally:
                                try:
                                    win32print.EndDocPrinter(hPrinter)
                                except Exception:
                                    pass
                        except Exception:
                            # fallback to using os.startfile
                            _startfile_print(file_path)
                        finally:
                            try:
                                win32print.ClosePrinter(hPrinter)
                            except Exception:
                                pass
                    else:
                        # could not open named printer, fallback
                        _startfile_print(file_path)
                except Exception:
                    # win32print not available or failed — fallback to default printing
                    _startfile_print(file_path)
            else:
                _startfile_print(file_path)
            printed[0] = True
            try:
                items_panel.finalize()
            except Exception:
                try:
                    items_panel.clear()
                except Exception:
                    pass
            try:
                parent.update_totals()
            except Exception:
                pass
            invoice = {
                'productos': selected,
                'subtotal_usd': round(subtotal_usd, 2),
                'iva_amount_usd': round(impuesto_usd, 2),
                'total_usd': round(total_usd_calc, 2),
                'subtotal_bs': subtotal_bs,
                'iva_amount_bs': impuesto_bs,
                'total_bs': total_bs_calc,
                'file': file_path,
                'timestamp': fecha,
                'datetime': fecha_human,
                'state': 'FINALIZADA',
                'global_iva_pct': vat_pct,
                'iva_enabled': iva_enabled,
                'paper_size': paper_size,
                'payments': {
                    'punto_bs': parse_amount(pago_pv_var.get()),
                    'efectivo_bs': parse_amount(pago_ef_var.get()),
                    'usd': parse_amount(pago_usd_var.get()),
                    'pago_movil_bs': parse_amount(pago_movil_var.get()),
                    'pago_movil_ref': pago_ref_var.get().strip()
                }
            }
            try:
                if hasattr(parent, 'facturas') and isinstance(parent.facturas, list):
                    parent.facturas.append(invoice)
                else:
                    parent.facturas = [invoice]
            except Exception:
                pass
            try:
                win.destroy()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo imprimir: {e}')

    btn_print = Button(content, text='Imprimir Factura', command=do_print)
    try:
        btn_print.pack(pady=8)
    except Exception:
        btn_print.grid()
    try:
        btn_print.configure(state='disabled')
    except Exception:
        pass

    Button(content, text='Cerrar', command=win.destroy).pack(pady=8)

    # initial status update
    update_payment_status()
