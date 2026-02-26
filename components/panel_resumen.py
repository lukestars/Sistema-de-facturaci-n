import customtkinter as ctk


class PanelResumen(ctk.CTkFrame):
    """Panel a la derecha que muestra resumen rápido del inventario."""

    def __init__(self, master, colors=None, fonts=None, **kwargs):
        # use themed frame color if provided
        fg = None
        if colors:
            fg = colors.get('frame')
        if fg is not None:
            super().__init__(master, fg_color=fg, **kwargs)
        else:
            super().__init__(master, **kwargs)
        self.colors = colors or {}
        self.fonts = fonts or {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(self, text="Resumen", font=self.fonts.get("heading"))
        self.lbl_title.grid(row=0, column=0, pady=(10, 8))

        self.total_items = ctk.CTkLabel(self, text="Items: 0", font=self.fonts.get("normal"))
        self.total_items.grid(row=1, column=0, pady=6, padx=10, sticky='w')

        self.total_value = ctk.CTkLabel(self, text="Valor total: 0.00", font=self.fonts.get("normal"))
        self.total_value.grid(row=2, column=0, pady=6, padx=10, sticky='w')

        self.last_action = ctk.CTkLabel(self, text="Última acción: -", font=self.fonts.get("small"))
        self.last_action.grid(row=3, column=0, pady=(10, 6), padx=10, sticky='w')

    def update_summary(self, products):
        # products puede ser de distintas versiones:
        # - versión nueva: (id, code, name, price_bs, price_usd, quantity)
        # - versión antigua: (id, name, price, quantity)
        # validar que recibimos una lista de tuplas
        if not isinstance(products, list) or not all(isinstance(x, tuple) for x in products):
            try:
                # intentar convertir iterables razonables a lista de tuplas
                products = [tuple(x) for x in list(products)]
            except Exception:
                # no es convertible -> mostrar ceros
                self.total_items.configure(text="Items: 0")
                self.total_value.configure(text="Valor total: 0.00")
                self.last_action.configure(text="Última acción: datos inválidos")
                return

        total_items = 0
        total_value = 0.0
        for p in products:
            if not isinstance(p, tuple):
                # ignorar entradas no tupla
                continue

            price_raw = None
            qty_raw = None

            # extraer campos según estructura conocida
            try:
                if len(p) >= 6:
                    # nueva estructura: (id, code, name, price_bs, price_usd, quantity)
                    price_raw = p[3]
                    qty_raw = p[5]
                elif len(p) >= 4:
                    # estructura antigua: (id, name, price, quantity)
                    price_raw = p[2]
                    qty_raw = p[3]
                else:
                    # intento genérico: último campo -> qty, buscar price en campos anteriores
                    qty_raw = p[-1]
                    for x in p[:-1][::-1]:
                        if x is None or x == "":
                            continue
                        try:
                            # tomar el primero convertible a float
                            _ = float(x)
                            price_raw = x
                            break
                        except Exception:
                            continue

                # intentar convertir a números seguros
                try:
                    if price_raw is None or price_raw == "":
                        raise ValueError("precio inválido")
                    price = float(price_raw)
                except Exception:
                    # no se puede interpretar el precio -> ignorar fila
                    continue

                try:
                    if qty_raw is None or qty_raw == "":
                        raise ValueError("cantidad inválida")
                    qty = float(qty_raw)
                except Exception:
                    # no se puede interpretar la cantidad -> ignorar fila
                    continue

                # acumular: items como entero cuando corresponde
                try:
                    # si qty es entero en valor, cuenta como int
                    if qty.is_integer():
                        total_items += int(qty)
                    else:
                        total_items += qty
                except Exception:
                    total_items += qty

                total_value += price * qty
            except Exception:
                # cualquier fila mal formada se ignora
                continue
        self.total_items.configure(text=f"Items: {total_items}")
        self.total_value.configure(text=f"Valor total: {total_value:.2f}")
        self.last_action.configure(text=f"Última acción: actualizado")
