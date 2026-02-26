"""Gestión del ID de factura: formato YYYYMMDD-N."""
import os
import json
import datetime


def _counter_path(data_dir=None):
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'invoice_counter.json')


def get_next_invoice_id(data_dir=None):
    """Devuelve el próximo ID de factura para hoy (formato 20260226-1). No incrementa."""
    path = _counter_path(data_dir)
    today = datetime.datetime.now().strftime('%Y%m%d')
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('date') == today:
                n = int(data.get('next', 1))
                return f"{today}-{n}"
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return f"{today}-1"


def increment_invoice_counter(data_dir=None):
    """Incrementa el contador del día para la siguiente factura."""
    path = _counter_path(data_dir)
    today = datetime.datetime.now().strftime('%Y%m%d')
    n = 1
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('date') == today:
                n = int(data.get('next', 1)) + 1
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'date': today, 'next': n}, f, indent=2)
    except OSError:
        pass
