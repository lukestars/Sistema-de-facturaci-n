import os
import tempfile
import datetime
import database

text = []
text.append('Comercio de prueba')
text.append('Fecha: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
text.append('')
text.append('Prueba de impresión — texto de ejemplo')
text.append('Gracias por su compra!')
text = '\n'.join(text)

# write file
fd, path = tempfile.mkstemp(prefix='factura_test_', suffix='.txt')
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    f.write(text)

print('Archivo creado en:', path)

try:
    target_printer = database.get_setting('default_printer', '') or ''
except Exception:
    target_printer = ''

print('Configuración de impresora:', target_printer)

# helper
def _startfile_print(p):
    try:
        os.startfile(p, 'print')
        return True
    except Exception as e:
        print('startfile error:', e)
        return False

if target_printer:
    try:
        import win32print
        try:
            hPrinter = win32print.OpenPrinter(target_printer)
        except Exception as e:
            print('OpenPrinter failed:', e)
            hPrinter = None
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
                print('Error envío a impresora:', e)
                print('Fallback a startfile...')
                _startfile_print(path)
            finally:
                try:
                    win32print.ClosePrinter(hPrinter)
                except Exception:
                    pass
        else:
            print('No se abrió impresora, fallback startfile')
            _startfile_print(path)
    except Exception as e:
        print('win32print no disponible o error:', e)
        _startfile_print(path)
else:
    print('No printer configured, using default system print')
    _startfile_print(path)

print('Done')
