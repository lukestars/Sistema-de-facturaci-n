import customtkinter as ctk
try:
    from database import increase_product_quantity
except Exception:
    increase_product_quantity = None


def open_stock_dialog(parent):
    try:
        selection = parent.tabla.tree.selection()
        if not selection:
            parent.show_status('Seleccione un producto para ajustar stock')
            return
        item_id = selection[0]
        pid = int(item_id)
        vals = parent.tabla.tree.item(item_id, 'values') or []
        name = vals[1] if len(vals) > 1 else (vals[0] if len(vals) > 0 else '')
        try:
            current_stock = int(vals[4]) if len(vals) > 4 else int(vals[-1]) if vals else 0
        except Exception:
            try:
                current_stock = int(vals[-1])
            except Exception:
                current_stock = 0

        dialog = ctk.CTkToplevel(parent)
        dialog.title('Ajustar stock')
        try:
            from utils.window_utils import enforce_custom_titlebar
            content = enforce_custom_titlebar(dialog, title='Ajustar stock', colors=getattr(parent, 'colors', {}), fonts=getattr(parent, 'fonts', {}))
        except Exception:
            content = dialog

        content.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(content, text=f'Producto: {name}').grid(row=0, column=0, columnspan=2, padx=6, pady=6)
        ctk.CTkLabel(content, text='Stock actual:').grid(row=1, column=0, sticky='e', padx=6, pady=6)
        ctk.CTkLabel(content, text=str(current_stock)).grid(row=1, column=1, sticky='w', padx=6, pady=6)

        ctk.CTkLabel(content, text='Agregar cantidad:').grid(row=2, column=0, sticky='e', padx=6, pady=6)
        add_entry = ctk.CTkEntry(content)
        add_entry.grid(row=2, column=1, sticky='ew', padx=6, pady=6)

        def on_add_stock():
            try:
                amt = int(add_entry.get()) if add_entry.get().strip() else 0
            except Exception:
                amt = 0
            if amt <= 0:
                parent.show_status('Ingrese cantidad positiva')
                return
            try:
                if increase_product_quantity is None:
                    parent.show_status('Función de base de datos no disponible')
                    return
                ok = increase_product_quantity(pid, amt)
            except Exception:
                ok = False
            if ok:
                try:
                    parent._reload()
                    try:
                        parent.update_totals()
                    except Exception:
                        pass
                except Exception:
                    pass
                # log stock change (cantidad anterior -> nueva) in history
                try:
                    code = vals[0] if len(vals) > 0 else str(pid)
                except Exception:
                    code = str(pid)
                try:
                    parent._log_stock_change(code, name, current_stock, current_stock + amt, 'agregado')
                except Exception:
                    pass
                parent.show_status('Stock actualizado')
                parent._close_dialog(dialog)
            else:
                parent.show_status('No se pudo actualizar stock')

        btn_frame = ctk.CTkFrame(content)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(10,6))
        add_btn = ctk.CTkButton(btn_frame, text='Agregar', command=on_add_stock)
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
            dialog.protocol('WM_DELETE_WINDOW', _on_cancel)
        except Exception:
            pass
        try:
            from utils.window_utils import center_window
            center_window(parent, dialog, w=420, h=220)
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
        import traceback
        traceback.print_exc()
        parent.show_status('Error abriendo diálogo de stock')
