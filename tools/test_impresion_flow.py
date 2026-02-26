import os
import datetime
import tempfile
import database

# sample selected items similar to TablaFactura.get_items()
selected = [
    {'id': 1, 'name': 'Producto A Largo Nombre', 'price': 10.0, 'quantity': 2, 'subtotal': 20.0},
    {'id': 2, 'name': 'Producto B', 'price': 5.5, 'quantity': 3, 'subtotal': 16.5},
]

try:
    rate = float(database.get_setting('exchange_rate', '1.0') or 1.0)
except Exception:
    rate = 1.0

try:
    paper_size = str(database.get_setting('receipt_paper_size', '58mm') or '58mm')
except Exception:
    paper_size = '58mm'

name_col_chars = 16 if '58' in paper_size else 24

lines = []
try:
    shop_title = database.get_setting('shop_title', 'Comercio')
except Exception:
    shop_title = 'Comercio'
lines.append(shop_title)
lines.append('Fecha: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
lines.append('')
lines.append('Factura - Detalle')
lines.append('')
header_fmt = '{:<4} {:<' + str(name_col_chars) + '} {:>6} {:>10} {:>12}'
lines.append(header_fmt.format('','Producto','Cant','Precio(BS)','Total(BS)'))
for it in selected:
    name = it.get('name','')[:name_col_chars]
    qty = int(it.get('quantity',1) or 1)
    price = float(it.get('price',0.0) or 0.0)
    total = float(it.get('subtotal',0.0) or 0.0)
    lines.append(header_fmt.format('', name, qty, f"{price:.2f}", f"{total:.2f}"))

subtotal = round(sum(it['subtotal'] for it in selected),2)
try:
    vat_enabled = True if str(database.get_setting('vat_enabled','0'))=='1' else False
    vat_pct = float(database.get_setting('vat_percent','0') or 0.0)
except Exception:
    vat_enabled=False; vat_pct=0.0
iva_amount = round(subtotal * (vat_pct/100.0),2) if vat_enabled else 0.0
total_with_iva = round(subtotal + iva_amount,2)
lines.append('')
lines.append(f'Subtotal: {subtotal:.2f} BS')
lines.append(f'IVA ({vat_pct:.2f}%): {iva_amount:.2f} BS')
lines.append(f'Total: {total_with_iva:.2f} BS / {total_with_iva/rate if rate else 0.0:.2f} $')
text = '\n'.join(lines)

# write file
fd, path = tempfile.mkstemp(prefix='factura_impresion_', suffix='.txt')
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    f.write(text)

print('Factura generada en:', path)
print('Paper size:', paper_size)

# send to printer
try:
    target_printer = database.get_setting('default_printer','') or ''
except Exception:
    target_printer = ''

print('Target printer:', target_printer)

def startfile_print(p):
    try:
        os.startfile(p, 'print')
        return True
    except Exception as e:
        print('startfile error', e)
        return False

if target_printer:
    try:
        import win32print
        hPrinter = None
        try:
            hPrinter = win32print.OpenPrinter(target_printer)
        except Exception as e:
            print('OpenPrinter failed:', e)
        if hPrinter:
            try:
                with open(path, 'rb') as f:
                    data = f.read()
                doc_info = ('FacturaTest', None, 'RAW')
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
                print('Impresa vía win32print en:', target_printer)
            except Exception as e:
                print('Error impresión via win32print:', e)
                print('Fallback a startfile')
                startfile_print(path)
            finally:
                try:
                    win32print.ClosePrinter(hPrinter)
                except Exception:
                    pass
        else:
            startfile_print(path)
    except Exception as e:
        print('win32print no disponible o error:', e)
        startfile_print(path)
else:
    print('No hay impresora configurada, uso startfile')
    startfile_print(path)

print('Prueba completa')
