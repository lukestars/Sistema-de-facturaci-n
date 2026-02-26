import customtkinter as ctk
try:
    from database import get_setting, update_product
    import database
except Exception:
    get_setting = lambda k, d=None: d
    update_product = None


def open_edit_product_dialog(parent):
    try:
        selection = parent.tabla.tree.selection()
        if not selection:
            parent.show_status('Seleccione un producto para editar')
            return
        item_id = selection[0]
        pid = int(item_id)
        vals = parent.tabla.tree.item(item_id, 'values') or []
        code = vals[0] if len(vals) > 0 else ''
        name = vals[1] if len(vals) > 1 else ''
        try:
            price_bs = float(vals[2]) if len(vals) > 2 else 0.0
        except Exception:
            price_bs = 0.0
        try:
            price_usd = float(vals[3]) if len(vals) > 3 else 0.0
        except Exception:
            price_usd = 0.0

        dialog = ctk.CTkToplevel(parent)
        dialog.title('Editar producto')
        try:
            from utils.window_utils import enforce_custom_titlebar
            content = enforce_custom_titlebar(dialog, title='Editar producto', colors=getattr(parent, 'colors', {}), fonts=getattr(parent, 'fonts', {}))
        except Exception:
            content = dialog

        content.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(content, text='Código:').grid(row=0, column=0, sticky='e', padx=6, pady=6)
        code_entry = ctk.CTkEntry(content)
        code_entry.grid(row=0, column=1, sticky='ew', padx=6, pady=6)
        try:
            code_entry.insert(0, str(code))
            code_entry.configure(state='disabled')
        except Exception:
            pass

        ctk.CTkLabel(content, text='Nombre:').grid(row=1, column=0, sticky='e', padx=6, pady=6)
        name_entry = ctk.CTkEntry(content)
        name_entry.grid(row=1, column=1, sticky='ew', padx=6, pady=6)
        name_entry.insert(0, str(name))

        ctk.CTkLabel(content, text='Precio Bs:').grid(row=2, column=0, sticky='e', padx=6, pady=6)
        price_bs_entry = ctk.CTkEntry(content)
        price_bs_entry.grid(row=2, column=1, sticky='ew', padx=6, pady=6)
        price_bs_entry.insert(0, str(price_bs))

        try:
            cur_sym = get_setting('currency', 'USD')
            symbol = '$' if str(cur_sym) == 'USD' else '€'
        except Exception:
            symbol = '$'
        price_label = ctk.CTkLabel(content, text=f'Precio {symbol}:')
        price_label.grid(row=3, column=0, sticky='e', padx=6, pady=6)
        try:
            dialog.price_label = price_label
        except Exception:
            pass
        price_usd_entry = ctk.CTkEntry(content)
        price_usd_entry.grid(row=3, column=1, sticky='ew', padx=6, pady=6)
        price_usd_entry.insert(0, str(price_usd))

        updating = {'flag': False}

        def _get_rate():
            try:
                return float(get_setting('exchange_rate', '1.0'))
            except Exception:
                return 1.0

        def _bs_to_usd(evt=None):
            if updating['flag']:
                return
            try:
                updating['flag'] = True
                t = price_bs_entry.get().strip()
                if not t:
                    price_usd_entry.delete(0, 'end')
                    return
                v = float(t)
                r = _get_rate()
                price_usd_entry.delete(0, 'end')
                price_usd_entry.insert(0, f"{(v / r) if r!=0 else 0.0:.2f}")
            except Exception:
                pass
            finally:
                updating['flag'] = False

        def _usd_to_bs(evt=None):
            if updating['flag']:
                return
            try:
                updating['flag'] = True
                t = price_usd_entry.get().strip()
                if not t:
                    price_bs_entry.delete(0, 'end')
                    return
                v = float(t)
                r = _get_rate()
                price_bs_entry.delete(0, 'end')
                price_bs_entry.insert(0, f"{(v * r):.2f}")
            except Exception:
                pass
            finally:
                updating['flag'] = False

        try:
            price_bs_entry.bind('<KeyRelease>', _bs_to_usd)
            price_usd_entry.bind('<KeyRelease>', _usd_to_bs)
        except Exception:
            pass

        try:
            parent._center_window(dialog, dw=520, dh=360)
        except Exception:
            pass

        def on_save():
            new_code = code_entry.get().strip()
            new_name = name_entry.get().strip()
            try:
                new_price_bs = float(price_bs_entry.get()) if price_bs_entry.get().strip() else 0.0
            except Exception:
                new_price_bs = 0.0
            try:
                new_price_usd = float(price_usd_entry.get()) if price_usd_entry.get().strip() else 0.0
            except Exception:
                new_price_usd = 0.0
            try:
                if update_product is None:
                    parent.show_status('Función de base de datos no disponible')
                    return
                update_product(pid, code=new_code, name=new_name, price_bs=new_price_bs, price_usd=new_price_usd)
                try:
                    parent._reload()
                except Exception:
                    pass
                parent.show_status('Producto actualizado')
                parent._close_dialog(dialog)
            except Exception:
                import traceback
                traceback.print_exc()
                parent.show_status('Error al actualizar')

        btn_frame = ctk.CTkFrame(content)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(10,6))
        save_btn = ctk.CTkButton(btn_frame, text='Guardar', command=on_save)
        save_btn.pack(side='left', padx=6)

        def _on_cancel():
            try:
                parent._close_dialog(dialog)
            except Exception:
                pass

        cancel_btn = ctk.CTkButton(btn_frame, text='Cancelar', command=_on_cancel)
        cancel_btn.pack(side='left', padx=6)

        dialog.transient(parent)
        try:
            parent._open_product_dialogs.append(dialog)
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
        # fallback simpledialog behavior
        try:
            import tkinter.simpledialog as sd
            selection = parent.tabla.tree.selection()
            if not selection:
                return
            item_id = selection[0]
            pid = int(item_id)
            vals = parent.tabla.tree.item(item_id, 'values') or []
            code = vals[0] if len(vals) > 0 else ''
            name = vals[1] if len(vals) > 1 else ''
            try:
                price_bs = float(vals[2]) if len(vals) > 2 else 0.0
            except Exception:
                price_bs = 0.0
            try:
                price_usd = float(vals[3]) if len(vals) > 3 else 0.0
            except Exception:
                price_usd = 0.0

            new_code = sd.askstring('Editar producto', 'Código:', initialvalue=code, parent=parent)
            if new_code is None:
                return
            new_name = sd.askstring('Editar producto', 'Nombre:', initialvalue=name, parent=parent)
            if new_name is None:
                return
            try:
                new_price_bs = sd.askfloat('Editar producto', 'Precio Bs:', initialvalue=price_bs, parent=parent)
            except Exception:
                new_price_bs = price_bs
            try:
                new_price_usd = sd.askfloat('Editar producto', 'Precio $:', initialvalue=price_usd, parent=parent)
            except Exception:
                new_price_usd = price_usd

            try:
                if update_product is None:
                    parent.show_status('Función de base de datos no disponible')
                    return
                update_product(pid, code=new_code, name=new_name, price_bs=new_price_bs, price_usd=new_price_usd)
                try:
                    parent._reload()
                except Exception:
                    pass
                parent.show_status('Producto actualizado')
            except Exception:
                import traceback
                traceback.print_exc()
                parent.show_status('Error al actualizar (fallback)')
        except Exception:
            pass
