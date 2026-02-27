import customtkinter as ctk
try:
    from database import get_setting, add_product_full, get_products
    import database
except Exception:
    get_setting = lambda k, d=None: d
    add_product_full = None
    get_products = lambda: []


def open_add_product_dialog(parent):
    try:
        # replicate behavior from VentanaPrincipal._open_add_product_dialog
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Agregar producto")
        try:
            from utils.window_utils import enforce_custom_titlebar
            content = enforce_custom_titlebar(dialog, title="Agregar producto", colors=getattr(parent, 'colors', {}), fonts=getattr(parent, 'fonts', {}))
        except Exception:
            content = dialog

        content.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(content, text="Código:").grid(row=0, column=0, sticky='e', padx=6, pady=6)
        # auto-generate numeric code up to 5 digits
        try:
            existing = get_products()
            nums = []
            for r in existing:
                c = r[1]
                if c and str(c).isdigit() and len(str(c)) <= 5:
                    try:
                        nums.append(int(c))
                    except Exception:
                        pass
            maxnum = max(nums) if nums else 0
            nextnum = maxnum + 1
            if nextnum > 99999:
                parent.show_status('Límite de códigos alcanzado')
                return
            gen_code = str(nextnum)
        except Exception:
            gen_code = '1'
        code_entry = ctk.CTkEntry(content)
        code_entry.grid(row=0, column=1, sticky='ew', padx=6, pady=6)
        try:
            code_entry.insert(0, gen_code)
            code_entry.configure(state='disabled')
        except Exception:
            pass

        ctk.CTkLabel(content, text="Nombre:").grid(row=1, column=0, sticky='e', padx=6, pady=6)
        name_entry = ctk.CTkEntry(content)
        name_entry.grid(row=1, column=1, sticky='ew', padx=6, pady=6)

        ctk.CTkLabel(content, text="Precio Bs:").grid(row=2, column=0, sticky='e', padx=6, pady=6)
        price_bs_entry = ctk.CTkEntry(content)
        price_bs_entry.grid(row=2, column=1, sticky='ew', padx=6, pady=6)

        # foreign currency label will use selected symbol
        try:
            cur_sym = get_setting('currency', 'USD')
            symbol = '$' if str(cur_sym) == 'USD' else '€'
        except Exception:
            symbol = '$'
        price_label = ctk.CTkLabel(content, text=f"Precio {symbol}:")
        price_label.grid(row=3, column=0, sticky='e', padx=6, pady=6)
        try:
            dialog.price_label = price_label
        except Exception:
            pass
        price_usd_entry = ctk.CTkEntry(content)
        price_usd_entry.grid(row=3, column=1, sticky='ew', padx=6, pady=6)

        updating = {'flag': False}

        def _get_rate():
            try:
                return float(get_setting('exchange_rate', '1.0'))
            except Exception:
                return 1.0

        def bs_to_usd_event(evt=None):
            if updating['flag']:
                return
            try:
                updating['flag'] = True
                txt = price_bs_entry.get().strip()
                if not txt:
                    price_usd_entry.delete(0, 'end')
                    return
                val_bs = float(txt)
                rate = _get_rate()
                usd = val_bs / rate if rate != 0 else 0.0
                price_usd_entry.delete(0, 'end')
                price_usd_entry.insert(0, f"{usd:.2f}")
            except Exception:
                pass
            finally:
                updating['flag'] = False

        def usd_to_bs_event(evt=None):
            if updating['flag']:
                return
            try:
                updating['flag'] = True
                txt = price_usd_entry.get().strip()
                if not txt:
                    price_bs_entry.delete(0, 'end')
                    return
                val_usd = float(txt)
                rate = _get_rate()
                bs = val_usd * rate
                price_bs_entry.delete(0, 'end')
                price_bs_entry.insert(0, f"{bs:.2f}")
            except Exception:
                pass
            finally:
                updating['flag'] = False

        try:
            price_bs_entry.bind('<KeyRelease>', bs_to_usd_event)
            price_usd_entry.bind('<KeyRelease>', usd_to_bs_event)
        except Exception:
            pass

        # center dialog over parent
        try:
            from utils.window_utils import center_window
            center_window(parent, dialog, w=520, h=360)
        except Exception:
            pass

        def on_add():
            try:
                code = code_entry.get().strip()
            except Exception:
                code = gen_code
            name = name_entry.get().strip()
            try:
                price_bs = float(price_bs_entry.get()) if price_bs_entry.get().strip() else 0.0
            except Exception:
                price_bs = 0.0
            try:
                price_usd = float(price_usd_entry.get()) if price_usd_entry.get().strip() else 0.0
            except Exception:
                price_usd = 0.0
            qty = 1
            if not name:
                parent.show_status('Nombre requerido')
                return
            try:
                if add_product_full is None:
                    parent.show_status('Función de base de datos no disponible')
                    return
                add_product_full(code=code, name=name, price_bs=price_bs, price_usd=price_usd, quantity=qty)
                try:
                    parent._reload()
                except Exception:
                    pass
                parent.show_status('Producto agregado')
                parent._close_dialog(dialog)
            except Exception:
                import traceback
                traceback.print_exc()
                parent.show_status('Error al agregar')

        btn_frame = ctk.CTkFrame(content)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(10,6))
        add_btn = ctk.CTkButton(btn_frame, text='Agregar', command=on_add)
        add_btn.pack(side='left', padx=6)

        def _on_cancel():
            try:
                parent._close_dialog(dialog)
            except Exception:
                pass

        cancel_btn = ctk.CTkButton(btn_frame, text='Cancelar', command=_on_cancel)
        cancel_btn.pack(side='left', padx=6)

        dialog.transient(parent)
        try:
            try:
                parent._open_product_dialogs.append(dialog)
            except Exception:
                pass
        except Exception:
            pass
        try:
            def _on_close_wrapper():
                try:
                    parent._open_product_dialogs.remove(dialog)
                except Exception:
                    pass
                _on_cancel()
            dialog.protocol('WM_DELETE_WINDOW', _on_close_wrapper)
        except Exception:
            pass
        try:
            dialog.grab_set()
            try:
                dialog.lift()
                dialog.focus_force()
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        # fallback simple dialogs
        try:
            import tkinter.simpledialog as sd
            try:
                existing = get_products()
                nums = []
                for r in existing:
                    c = r[1]
                    if c and str(c).isdigit() and len(str(c)) <= 5:
                        try:
                            nums.append(int(c))
                        except Exception:
                            pass
                maxnum = max(nums) if nums else 0
                nextnum = maxnum + 1
                if nextnum > 99999:
                    parent.show_status('Límite de códigos alcanzado')
                    return
                gen_code = str(nextnum)
            except Exception:
                gen_code = '1'
            code = sd.askstring('Agregar producto', 'Código:', initialvalue=gen_code, parent=parent)
            if code is None:
                return
            name = sd.askstring('Agregar producto', 'Nombre:', parent=parent)
            if not name:
                parent.show_status('Nombre requerido')
                return
            try:
                price_bs = sd.askfloat('Agregar producto', 'Precio Bs:', parent=parent)
            except Exception:
                price_bs = 0.0
            try:
                price_usd = sd.askfloat('Agregar producto', 'Precio $:', parent=parent)
            except Exception:
                price_usd = 0.0
            try:
                if add_product_full is None:
                    parent.show_status('Función de base de datos no disponible')
                    return
                add_product_full(code=code, name=name, price_bs=price_bs or 0.0, price_usd=price_usd or 0.0, quantity=1)
                try:
                    parent._reload()
                except Exception:
                    pass
                parent.show_status('Producto agregado')
            except Exception:
                import traceback
                traceback.print_exc()
                parent.show_status('Error al agregar (fallback)')
        except Exception:
            pass
