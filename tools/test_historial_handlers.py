import sys
import traceback
import time

sys.path.insert(0, r'd:/venta')
try:
    import tkinter as tk
    from ventanas.ventana_principal import VentanaPrincipal
    import historial.listado as listado
    import historial.pausadas as pausadas
    import historial.stock_history as stock_history
    import historial.cierre_caja as cierre
    import historial.export as export
except Exception:
    print('Import failure:')
    traceback.print_exc()
    raise

root = tk.Tk()
root.withdraw()
app = VentanaPrincipal(master=root, user='test')
app.root = root

handlers = [
    ('listado', getattr(listado, 'show_facturas', None)),
    ('pausadas', getattr(pausadas, 'show_paused_invoices', None)),
    ('stock', getattr(stock_history, 'show_stock_history_window', None)),
    ('cierre', getattr(cierre, 'show_cierre_caja', None)),
    ('export', getattr(export, 'show_export_menu', None)),
]

for name, fn in handlers:
    print('\n--- Testing', name, 'handler ---')
    if not fn:
        print(name, 'handler not found')
        continue
    try:
        fn(app)
        print(name, 'opened OK')
    except Exception:
        print('Error invoking', name)
        traceback.print_exc()
    time.sleep(0.5)

# cleanup
try:
    app.destroy()
except Exception:
    pass
try:
    root.destroy()
except Exception:
    pass
print('\nDone')
