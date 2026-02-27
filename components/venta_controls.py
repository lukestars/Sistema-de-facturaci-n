import tkinter as tk
import customtkinter as ctk
import os
import json
import datetime
from typing import Optional


class VentaControls(ctk.CTkFrame):
    """Controls related to opening/closing a venta session.

    Buttons:
    - Abrir Venta: marks the app as venta_open and enables client selection.
    - Cierre: computes totals for the day, appends a cierre record to data/closures.json
      and opens the cierre dialog.
    """

    def __init__(self, master, app=None, header_ref=None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app or (header_ref.winfo_toplevel() if header_ref is not None else None)
        self.header_ref = header_ref
        # colors
        self._color_green = kwargs.get('open_color', '#2ecc71')
        self._color_red = kwargs.get('close_color', '#e74c3c')
        self._color_gray = kwargs.get('disabled_color', '#7f8c8d')

        self.abrir_btn = ctk.CTkButton(self, text='Abrir Venta', width=120, height=28, command=self.open_venta,
                                       fg_color=self._color_green)
        self.abrir_btn.grid(row=0, column=0, padx=(0, 6))

        self.cierre_btn = ctk.CTkButton(self, text='Cierre', width=80, height=28, command=self.do_cierre,
                                        fg_color=self._color_gray)
        self.cierre_btn.grid(row=0, column=1)

        # reflect initial app state
        try:
            self.update_buttons_state()
        except Exception:
            pass

    def _show_notification(self, text: str, duration_ms: int = 1400):
        """Show a small transient notification window near the app center."""
        try:
            app = self.app or (self.header_ref.winfo_toplevel() if self.header_ref is not None else None)
            if app is None:
                return
            try:
                win = ctk.CTkToplevel(app)
            except Exception:
                import tkinter as tk
                win = tk.Toplevel(app)
            win.overrideredirect(True)
            try:
                win.attributes('-topmost', True)
            except Exception:
                pass
            frm = ctk.CTkFrame(win, fg_color='#111111') if hasattr(ctk, 'CTkFrame') else None
            try:
                if frm is not None:
                    frm.pack(fill='both', expand=True)
                    lbl = ctk.CTkLabel(frm, text=text, text_color='#ffffff')
                    lbl.pack(padx=12, pady=8)
                else:
                    import tkinter as tk
                    lbl = tk.Label(win, text=text, bg='#111111', fg='#ffffff')
                    lbl.pack(padx=12, pady=8)
            except Exception:
                pass
            # center near parent
            try:
                win.update_idletasks()
                pwx = app.winfo_rootx()
                pwy = app.winfo_rooty()
                pww = app.winfo_width()
                pwh = app.winfo_height()
                ww = win.winfo_width()
                wh = win.winfo_height()
                dx = pwx + max(0, int((pww - ww) / 2))
                dy = pwy + max(0, int((pwh - wh) / 2))
                win.geometry(f"{ww}x{wh}+{dx}+{dy}")
            except Exception:
                try:
                    win.geometry('+100+100')
                except Exception:
                    pass

            def _close():
                try:
                    win.destroy()
                except Exception:
                    pass

            try:
                win.after(duration_ms, _close)
            except Exception:
                pass
        except Exception:
            pass

    def _set_opened_ui(self):
        try:
            self.abrir_btn.configure(state='disabled', text='Venta abierta', fg_color=self._color_gray)
        except Exception:
            pass
        try:
            self.cierre_btn.configure(state='normal', fg_color=self._color_red)
        except Exception:
            pass
        try:
            if self.header_ref and hasattr(self.header_ref, 'update_venta_state'):
                self.header_ref.update_venta_state()
        except Exception:
            pass

    def update_buttons_state(self):
        """Update buttons appearance according to `app.venta_open` boolean."""
        try:
            app = self.app or (self.header_ref.winfo_toplevel() if self.header_ref is not None else None)
            venta_open = bool(getattr(app, 'venta_open', False))
        except Exception:
            venta_open = False
        try:
            if venta_open:
                # venta is open: Abrir disabled (gray), Cierre active (red)
                self.abrir_btn.configure(state='disabled', text='Venta abierta', fg_color=self._color_gray)
                self.cierre_btn.configure(state='normal', fg_color=self._color_red)
            else:
                # venta closed: Abrir active (green), Cierre disabled (gray)
                self.abrir_btn.configure(state='normal', text='Abrir Venta', fg_color=self._color_green)
                self.cierre_btn.configure(state='disabled', fg_color=self._color_gray)
        except Exception:
            pass
        try:
            if self.header_ref and hasattr(self.header_ref, 'update_venta_state'):
                self.header_ref.update_venta_state()
        except Exception:
            pass

    def open_venta(self):
        try:
            app = self.app or (self.header_ref.winfo_toplevel() if self.header_ref is not None else None)
            if app is None:
                return
            app.venta_open = True
            try:
                app.show_status('Venta abierta')
            except Exception:
                pass
            # show notification window
            try:
                self._show_notification('Venta abierta')
            except Exception:
                pass
            self.update_buttons_state()
        except Exception:
            pass

    def do_cierre(self):
        """Compute cierre totals for today, save a closure record, and show the cierre dialog."""
        try:
            app = self.app or (self.header_ref.winfo_toplevel() if self.header_ref is not None else None)
            if app is None:
                return
            # collect invoices for today (same logic used in cierre_caja)
            facturas_dir = getattr(app, '_facturas_dir', os.path.join(getattr(app, '_data_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')), 'facturas'))
            today = datetime.date.today().strftime('%Y-%m-%d')
            facturas_dia = []
            day_dir = os.path.join(facturas_dir, today)
            if os.path.isdir(day_dir):
                for fname in os.listdir(day_dir):
                    if not (fname.lower().endswith('.json') or 'invoice' in fname.lower()):
                        continue
                    fpath = os.path.join(day_dir, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as fp:
                            inv = json.load(fp)
                    except Exception:
                        continue
                    if (inv.get('state') or '').upper() == 'ANULADA':
                        continue
                    facturas_dia.append(inv)
            # attempt to include server invoices if available
            try:
                if getattr(app, 'server_url', None) and getattr(app, 'auth_token', None):
                    r = app.request_get(f"{app.server_url}/invoices?from_date={today}&to_date={today}", timeout=5)
                    if r and getattr(r, 'status_code', None) == 200:
                        for inv in (r.json() or []):
                            if (inv.get('state') or '').upper() == 'ANULADA':
                                continue
                            if not any(f.get('id') == inv.get('id') for f in facturas_dia):
                                facturas_dia.append(inv)
            except Exception:
                pass

            # compute full analytics (conteo por método, totales, módulo divisas, gran total)
            analytics = None
            try:
                from historial.cierre_caja import compute_cierre_analytics, save_cierre_pdf
                tc = float(getattr(app, 'exchange_rate', 1.0) or 1.0)
                analytics = compute_cierre_analytics(facturas_dia, tc)
            except Exception:
                try:
                    from venta.historial.cierre_caja import compute_cierre_analytics, save_cierre_pdf
                    tc = float(getattr(app, 'exchange_rate', 1.0) or 1.0)
                    analytics = compute_cierre_analytics(facturas_dia, tc)
                except Exception:
                    analytics = {'total_efectivo': 0.0, 'total_pv': 0.0, 'total_pm': 0.0, 'total_usd_bs': 0.0,
                                'total_gral_bs': 0.0, 'total_gral_usd': 0.0, 'num_facturas': 0,
                                'count_efectivo': 0, 'count_pv': 0, 'count_pm': 0, 'count_dolar': 0,
                                'divisa_count': 0, 'divisa_total_usd': 0.0, 'divisa_total_bs_equiv': 0.0}
                    try:
                        for inv in facturas_dia:
                            pays = inv.get('payments') or {}
                            analytics['total_efectivo'] += float(pays.get('efectivo_bs') or 0)
                            analytics['total_pv'] += float(pays.get('punto_bs') or 0)
                            analytics['total_pm'] += float(pays.get('pago_movil_bs') or 0)
                            analytics['total_usd_bs'] += float(pays.get('usd') or 0) * tc
                            analytics['total_gral_usd'] += float(inv.get('total_usd') or 0)
                            if float(pays.get('efectivo_bs') or 0) > 0:
                                analytics['count_efectivo'] += 1
                            if float(pays.get('punto_bs') or 0) > 0:
                                analytics['count_pv'] += 1
                            if float(pays.get('pago_movil_bs') or 0) > 0:
                                analytics['count_pm'] += 1
                            if float(pays.get('usd') or 0) > 0:
                                analytics['count_dolar'] += 1
                        analytics['total_gral_bs'] = analytics['total_efectivo'] + analytics['total_pv'] + analytics['total_pm'] + analytics['total_usd_bs']
                        analytics['num_facturas'] = len(facturas_dia)
                    except Exception:
                        pass

            # persist closure record (with full analytics)
            try:
                d = getattr(app, '_data_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
                os.makedirs(d, exist_ok=True)
                path = os.path.join(d, 'closures.json')
                try:
                    if os.path.exists(path):
                        with open(path, 'r', encoding='utf-8') as f:
                            arr = json.load(f) or []
                    else:
                        arr = []
                except Exception:
                    arr = []
                rec = {
                    'date': today,
                    'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'analytics': analytics,
                    'user': getattr(app, 'user', '')
                }
                arr.append(rec)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(arr, f, ensure_ascii=False, indent=2)
            except Exception:
                try:
                    app.show_status('No se pudo guardar el cierre')
                except Exception:
                    pass

            # save PDF to Cierres_Caja/YYYY/MM_Mes/Cierre_DD-MM-YYYY_HHmm.pdf
            try:
                from historial.cierre_caja import save_cierre_pdf
            except Exception:
                from venta.historial.cierre_caja import save_cierre_pdf
            try:
                pdf_path = save_cierre_pdf(app, analytics or {}, today, getattr(app, 'user', ''))
                if pdf_path and hasattr(app, 'show_status'):
                    app.show_status(f'Cierre guardado en {pdf_path}')
            except Exception:
                pass

            # mark venta closed
            try:
                app.venta_open = False
            except Exception:
                pass
            try:
                if hasattr(self.header_ref, 'update_venta_state'):
                    self.header_ref.update_venta_state()
            except Exception:
                pass

            # visual feedback: set cierre button to gray and abrir to green
            try:
                self.cierre_btn.configure(state='disabled', fg_color=self._color_gray)
                self.abrir_btn.configure(state='normal', fg_color=self._color_green, text='Abrir Venta')
            except Exception:
                pass

            # show notification
            try:
                self._show_notification('Cierre realizado')
            except Exception:
                pass

            # open cierre dialog with current analytics
            try:
                from historial.cierre_caja import show_cierre_caja
                show_cierre_caja(app, date_str=today, analytics=analytics)
            except Exception:
                try:
                    from venta.historial.cierre_caja import show_cierre_caja
                    show_cierre_caja(app, date_str=today, analytics=analytics)
                except Exception:
                    pass

        except Exception:
            pass
