import traceback
import time

try:
    import sys
    sys.path.insert(0, r'd:/venta')
    import tkinter as tk
    from ventanas.ventana_principal import VentanaPrincipal
    root = tk.Tk()
    root.withdraw()
    win = VentanaPrincipal(master=root, user='test')
    # ensure attributes expected by historial modules
    win.root = root
    try:
        win._open_history()
        print('Called _open_history() successfully')
    except Exception:
        print('Error calling _open_history:')
        traceback.print_exc()
    # keep open briefly to allow any errors to surface
    time.sleep(1)
    try:
        win.destroy()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass
except Exception:
    print('Fatal error:')
    traceback.print_exc()
