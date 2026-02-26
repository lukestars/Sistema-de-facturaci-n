from ventanas.login_window import LoginWindow
import database
try:
    from utils.bcv_fetch import obtener_bcv
except Exception:
    obtener_bcv = None


def main():
    database.init_db()
    # On app start: if exchange mode is 'Automático', fetch BCV and set exchange_rate for selected currency
    try:
        mode = database.get_setting('exchange_mode', 'Manual')
        if mode == 'Automático' and obtener_bcv is not None:
            try:
                res = obtener_bcv()
                if res and 'error' not in res:
                    cur = database.get_setting('currency', 'USD')
                    key = 'dolar' if cur == 'USD' else 'euro'
                    val = res.get(key)
                    if val:
                        database.set_setting('exchange_rate', str(val))
                        try:
                            database.update_prices_by_rate(float(val))
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass
    app = LoginWindow()
    app.mainloop()


if __name__ == '__main__':
    main()
