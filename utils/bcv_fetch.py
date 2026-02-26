import requests
from bs4 import BeautifulSoup
import urllib3

# Desactivar advertencias de certificados inseguros
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def obtener_bcv():
    url = "https://www.bcv.org.ve/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        ids = {'dolar': 'dolar', 'euro': 'euro'}
        resultados = {}
        for moneda, id_html in ids.items():
            contenedor = soup.find('div', id=id_html)
            if contenedor:
                strong = contenedor.find('strong')
                if strong and strong.text:
                    valor_texto = strong.text.strip()
                    try:
                        valor_float = float(valor_texto.replace(',', '.'))
                        resultados[moneda] = valor_float
                    except Exception:
                        resultados[moneda] = None
                else:
                    resultados[moneda] = None
            else:
                resultados[moneda] = None
        fecha_box = soup.find('span', class_='date-display-single')
        resultados['fecha'] = fecha_box.text.strip() if fecha_box else None
        return resultados
    except Exception as e:
        return {"error": f"Error de conexión: {str(e)}"}
