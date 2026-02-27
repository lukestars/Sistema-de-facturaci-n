"""Cierre de caja: reporte analítico por método de pago y guardado automático en PDF."""
import datetime
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

from . import dialogs

# Nombres de mes en español para carpetas
_MESES = ('Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
          'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')

# Métodos considerados "Divisa" para el módulo exclusivo
_METODOS_DIVISA = ('dólar', 'dólares', 'divisa', 'usd', 'dolar', 'dolares')


def _is_divisa_primary(inv: dict) -> bool:
    """True si el método de pago principal de la factura es Dólar/Divisa."""
    pm = inv.get('payment_methods')
    if isinstance(pm, (list, tuple)) and pm:
        first = str(pm[0]).strip().lower()
        return any(m in first for m in _METODOS_DIVISA)
    pays = inv.get('payments') or {}
    usd = float(pays.get('usd') or 0)
    if usd > 0:
        efectivo = float(pays.get('efectivo_bs') or 0)
        pv = float(pays.get('punto_bs') or 0)
        pm_bs = float(pays.get('pago_movil_bs') or 0)
        if usd >= efectivo and usd >= pv and usd >= pm_bs:
            return True
    return False


def compute_cierre_totals(facturas_dia: list, exchange_rate: float = 1.0) -> dict:
    """Totales básicos (compatibilidad). Preferir compute_cierre_analytics."""
    a = compute_cierre_analytics(facturas_dia, exchange_rate)
    return {
        'total_efectivo': a['total_efectivo'],
        'total_pv': a['total_pv'],
        'total_pm': a['total_pm'],
        'total_usd_bs': a['total_usd_bs'],
        'total_gral': a['total_gral_bs'],
        'total_gral_usd': a['total_gral_usd'],
    }


def compute_cierre_analytics(facturas_dia: list, exchange_rate: float = 1.0) -> dict:
    """
    Reporte analítico de cierre:
    - Conteo de transacciones por método (cuántas facturas usaron cada método).
    - Totales segregados por método (BS).
    - Módulo Divisas: solo facturas con método Dólar/Divisa → total $ y equiv. BS.
    - Gran total BS y USD.
    """
    count_efectivo = count_pv = count_pm = count_dolar = 0
    total_efectivo = total_pv = total_pm = total_usd_bs = 0.0
    total_gral_usd = 0.0
    divisa_total_usd = divisa_total_bs_equiv = 0.0
    divisa_count = 0

    for inv in facturas_dia:
        pays = inv.get('payments') or {}
        ef = float(pays.get('efectivo_bs') or 0)
        pv = float(pays.get('punto_bs') or 0)
        pm = float(pays.get('pago_movil_bs') or 0)
        usd = float(pays.get('usd') or 0)
        usd_bs = usd * exchange_rate

        if ef > 0:
            count_efectivo += 1
        if pv > 0:
            count_pv += 1
        if pm > 0:
            count_pm += 1
        if usd > 0:
            count_dolar += 1

        total_efectivo += ef
        total_pv += pv
        total_pm += pm
        total_usd_bs += usd_bs
        total_gral_usd += float(inv.get('total_usd') or 0)

        if _is_divisa_primary(inv):
            divisa_count += 1
            divisa_total_usd += float(inv.get('total_usd') or 0)
            divisa_total_bs_equiv += float(inv.get('total_bs') or 0)  # o (total_usd * exchange_rate)

    total_gral_bs = total_efectivo + total_pv + total_pm + total_usd_bs

    return {
        'num_facturas': len(facturas_dia),
        'count_efectivo': count_efectivo,
        'count_pv': count_pv,
        'count_pm': count_pm,
        'count_dolar': count_dolar,
        'total_efectivo': total_efectivo,
        'total_pv': total_pv,
        'total_pm': total_pm,
        'total_usd_bs': total_usd_bs,
        'total_gral_bs': total_gral_bs,
        'total_gral_usd': total_gral_usd,
        'divisa_count': divisa_count,
        'divisa_total_usd': divisa_total_usd,
        'divisa_total_bs_equiv': divisa_total_bs_equiv,
        'exchange_rate': exchange_rate,
    }


def get_cierre_base_path(app: Any) -> str:
    """Ruta base Cierres_Caja (junto a data o en _data_dir)."""
    data_dir = getattr(app, '_data_dir', None)
    if data_dir and os.path.isdir(data_dir):
        parent = os.path.dirname(data_dir.rstrip(os.sep))
    else:
        parent = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    return os.path.join(parent, 'Cierres_Caja')


def get_cierre_folder_for_date(app: Any, date_str: str) -> str:
    """Carpeta Cierres_Caja/YYYY/MM_MesNombre/ para la fecha dada (YYYY-MM-DD)."""
    base = get_cierre_base_path(app)
    try:
        parts = date_str.strip()[:10].split('-')
        year = parts[0]
        month_num = int(parts[1])
        month_name = _MESES[month_num - 1] if 1 <= month_num <= 12 else str(month_num)
        folder = os.path.join(base, year, f"{parts[1]}_{month_name}")
        return folder
    except (IndexError, ValueError):
        return os.path.join(base, date_str[:4] or '2024', '01_Enero')


def get_cierre_pdf_filename(date_str: str, time_str: str = None) -> str:
    """Nombre de archivo: Cierre_DD-MM-YYYY_HHmm.pdf (o HHMMSS si time_str tiene 6 dígitos)."""
    try:
        parts = date_str.strip()[:10].split('-')
        d, m, y = parts[2], parts[1], parts[0]
        if time_str:
            t = time_str.replace(':', '')[:6].ljust(4, '0')
            if len(t) > 4:
                t = t[:6]
            else:
                t = t[:4]
        else:
            now = datetime.datetime.now()
            t = now.strftime('%H%m')
        return f"Cierre_{d}-{m}-{y}_{t}.pdf"
    except (IndexError, ValueError):
        return f"Cierre_{date_str[:10]}_0000.pdf"


def save_cierre_pdf(app: Any, analytics: dict, date_str: str, user: str = '') -> str:
    """
    Guarda el reporte de cierre en PDF en Cierres_Caja/YYYY/MM_Mes/Cierre_DD-MM-YYYY_HHmm.pdf.
    Crea carpetas si no existen. Retorna la ruta del archivo guardado o '' si falla.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except ImportError:
        return ''

    folder = get_cierre_folder_for_date(app, date_str)
    os.makedirs(folder, exist_ok=True)
    now = datetime.datetime.now()
    time_part = now.strftime('%H%m')
    filename = get_cierre_pdf_filename(date_str, time_part)
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        time_part = now.strftime('%H%M%S')
        filename = get_cierre_pdf_filename(date_str, time_part)
        path = os.path.join(folder, filename)

    try:
        doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
                                topMargin=15 * mm, bottomMargin=15 * mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CierreTitle', parent=styles['Heading1'], fontSize=16)
        story = []
        story.append(Paragraph('Cierre de Caja', title_style))
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f'Fecha: {date_str}', styles['Normal']))
        story.append(Paragraph(f'Generado: {now.strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
        if user:
            story.append(Paragraph(f'Usuario: {user}', styles['Normal']))
        story.append(Spacer(1, 8 * mm))

        # Conteo por método
        story.append(Paragraph('<b>Conteo de transacciones por método</b>', styles['Heading2']))
        data_count = [
            ['Método', 'Cantidad'],
            ['Efectivo', str(analytics.get('count_efectivo', 0))],
            ['Punto de venta (TDD/TDC)', str(analytics.get('count_pv', 0))],
            ['Pago móvil', str(analytics.get('count_pm', 0))],
            ['Dólar / Divisa', str(analytics.get('count_dolar', 0))],
        ]
        t1 = Table(data_count, colWidths=[120 * mm, 40 * mm])
        t1.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b2b2b')),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                               ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(t1)
        story.append(Spacer(1, 6 * mm))

        # Totales segregados
        story.append(Paragraph('<b>Totales por método de pago (BS)</b>', styles['Heading2']))
        data_totals = [
            ['Método', 'Total (BS)'],
            ['Efectivo', f"{analytics.get('total_efectivo', 0):.2f}"],
            ['Punto de venta', f"{analytics.get('total_pv', 0):.2f}"],
            ['Pago móvil', f"{analytics.get('total_pm', 0):.2f}"],
            ['Dólar (equiv. BS)', f"{analytics.get('total_usd_bs', 0):.2f}"],
        ]
        t2 = Table(data_totals, colWidths=[120 * mm, 40 * mm])
        t2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b2b2b')),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                               ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(t2)
        story.append(Spacer(1, 6 * mm))

        # Módulo Divisas (solo si hay facturas en dólares/divisa)
        if analytics.get('divisa_count', 0) > 0:
            story.append(Paragraph('<b>Módulo Divisas</b> (facturas con método Dólar/Divisa)', styles['Heading2']))
            story.append(Paragraph(f"Cantidad de transacciones: {analytics.get('divisa_count', 0)}", styles['Normal']))
            story.append(Paragraph(f"Total en USD ($): {analytics.get('divisa_total_usd', 0):.2f}", styles['Normal']))
            story.append(Paragraph(f"Equivalente en BS: {analytics.get('divisa_total_bs_equiv', 0):.2f}", styles['Normal']))
            story.append(Spacer(1, 6 * mm))

        # Gran total
        story.append(Paragraph('<b>Gran Total</b>', styles['Heading2']))
        story.append(Paragraph(f"Total ventas (BS): {analytics.get('total_gral_bs', 0):.2f}", styles['Normal']))
        story.append(Paragraph(f"Total ventas (USD): {analytics.get('total_gral_usd', 0):.2f}", styles['Normal']))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(f"Facturas del día: {analytics.get('num_facturas', 0)}", styles['Normal']))

        doc.build(story)
        return path
    except Exception:
        return ''


def show_cierre_caja(app, date_str: str = None, analytics: dict = None):
    """
    Ventana de Cierre de caja (analítica).
    Si se pasa date_str y analytics (p. ej. tras un cierre reciente), se muestran esos datos.
    Si no, se puede elegir fecha y cargar.
    """
    facturas_dir = getattr(app, '_facturas_dir', os.path.join(getattr(app, '_data_dir', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')), 'facturas'))
    colors = getattr(app, 'colors', None) or getattr(app, 'theme_colors', {})
    border_gray = colors.get('muted', '#4a4a4f')

    win = tk.Toplevel(app.root)
    win.title('Historial de Cierre de Caja')
    win.resizable(True, True)
    try:
        win.geometry('520x580')
    except Exception:
        pass
    content = dialogs.style_window(app, win)
    pad = 12
    ttk.Label(content, text='Historial de Cierre de Caja', font=('Helvetica', 14, 'bold')).pack(pady=(0, pad))

    date_var = tk.StringVar(value=date_str or datetime.datetime.now().strftime('%Y-%m-%d'))
    f = ttk.Frame(content)
    f.pack(fill=tk.X, pady=4)
    ttk.Label(f, text='Fecha:').pack(side=tk.LEFT, padx=(0, 6))
    date_entry = ttk.Entry(f, textvariable=date_var, width=12)
    date_entry.pack(side=tk.LEFT, padx=6)

    report_outer = tk.Frame(content, bg=border_gray, highlightbackground=border_gray, highlightcolor=border_gray, highlightthickness=1)
    report_outer.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)
    report_inner = ttk.Frame(report_outer)
    report_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    canvas = tk.Canvas(report_inner, bg=colors.get('frame', '#1b1b1f'), highlightthickness=0)
    vsb = ttk.Scrollbar(report_inner, orient=tk.VERTICAL, command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)
    scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _render_analytics(a: dict):
        for w in scroll_frame.winfo_children():
            w.destroy()
        if not a:
            ttk.Label(scroll_frame, text='Sin datos para la fecha seleccionada.').pack(anchor=tk.W)
            return
        num = a.get('num_facturas', 0)
        ttk.Label(scroll_frame, text=f'Facturas del día: {num}', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
        ttk.Separator(scroll_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Label(scroll_frame, text='Conteo de transacciones por método', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Efectivo: {a.get("count_efectivo", 0)}').pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Punto de venta (TDD/TDC): {a.get("count_pv", 0)}').pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Pago móvil: {a.get("count_pm", 0)}').pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Dólar / Divisa: {a.get("count_dolar", 0)}').pack(anchor=tk.W)
        ttk.Separator(scroll_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Label(scroll_frame, text='Totales segregados por método (BS)', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Efectivo (BS): {a.get("total_efectivo", 0):.2f}').pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Punto de venta (BS): {a.get("total_pv", 0):.2f}').pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Pago móvil (BS): {a.get("total_pm", 0):.2f}').pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Dólar equiv. (BS): {a.get("total_usd_bs", 0):.2f}').pack(anchor=tk.W)
        ttk.Separator(scroll_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        if a.get('divisa_count', 0) > 0:
            ttk.Label(scroll_frame, text='Módulo Divisas (método Dólar/Divisa)', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
            ttk.Label(scroll_frame, text=f'  Transacciones: {a.get("divisa_count", 0)}').pack(anchor=tk.W)
            ttk.Label(scroll_frame, text=f'  Total en USD ($): {a.get("divisa_total_usd", 0):.2f}').pack(anchor=tk.W)
            ttk.Label(scroll_frame, text=f'  Equivalente en BS: {a.get("divisa_total_bs_equiv", 0):.2f}').pack(anchor=tk.W)
            ttk.Separator(scroll_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Label(scroll_frame, text='Gran Total', font=('Helvetica', 11, 'bold')).pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Total ventas (BS): {a.get("total_gral_bs", 0):.2f}', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(scroll_frame, text=f'  Total ventas ($): {a.get("total_gral_usd", 0):.2f}', font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)

    def _cargar():
        ds = date_var.get().strip()
        if not ds or len(ds) < 10:
            messagebox.showwarning('Fecha', 'Indique una fecha (YYYY-MM-DD)')
            return
        facturas_dia = []
        day_dir = os.path.join(facturas_dir, ds[:10])
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
                r = app.request_get(f"{app.server_url}/invoices?from_date={ds[:10]}&to_date={ds[:10]}", timeout=5)
                if r and r.status_code == 200:
                    for inv in (r.json() or []):
                        if (inv.get('state') or '').upper() == 'ANULADA':
                            continue
                        if not any(f.get('id') == inv.get('id') for f in facturas_dia):
                            facturas_dia.append(inv)
            except (AttributeError, TypeError, ValueError):
                pass
        tc = float(getattr(app, 'exchange_rate', 1.0))
        a = compute_cierre_analytics(facturas_dia, tc)
        _render_analytics(a)

    ttk.Button(f, text='Cargar', command=_cargar).pack(side=tk.LEFT, padx=6)
    if analytics and date_str:
        _render_analytics(analytics)
    else:
        _cargar()
    ttk.Button(content, text='Cerrar', command=win.destroy).pack(pady=pad)
