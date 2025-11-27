import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def scrapear_diadia():
    url = "https://diadia.cat/"
    # Palabras clave (normalizadas a minúsculas para búsqueda)
    keywords = [
        "festa", "fiesta", "festes", "tardeo", "toros", 
        "orquesta", "discomobil", "discomovil", "fira", "feria"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    noticias = []
    
    try:
        print(f"🕷️ Scrapeando {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Error cargando la web: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'lxml')
        
        # En temas Newspaper/WordPress, las noticias suelen estar en bloques 'td_module_wrap'
        # Buscamos elementos que contengan la estructura que mencionaste
        articulos = soup.find_all('div', class_=re.compile(r'td_module_'))

        for art in articulos:
            try:
                # 1. Extraer Título y Link
                titulo_tag = art.find('h3', class_='entry-title')
                if not titulo_tag:
                    continue
                
                link_tag = titulo_tag.find('a')
                titulo = link_tag.get('title', '').strip()
                link = link_tag.get('href', '')
                
                # 2. Extraer Resumen (excerpt)
                excerpt_tag = art.find('div', class_='td-excerpt')
                resumen = excerpt_tag.get_text(strip=True) if excerpt_tag else ""
                
                # 3. Filtrado por palabras clave
                texto_completo = (titulo + " " + resumen).lower()
                if not any(kw in texto_completo for kw in keywords):
                    continue # Si no contiene ninguna palabra clave, saltamos
                
                # 4. Extraer Imagen (del atributo data-img-url o style)
                # Tu ejemplo: <span class="entry-thumb..." data-img-url="...">
                img_tag = art.find('span', class_='entry-thumb')
                imagen = ""
                if img_tag:
                    imagen = img_tag.get('data-img-url')
                    if not imagen and 'style' in img_tag.attrs:
                        # Fallback si está en style="background-image: url(...)"
                        match = re.search(r'url\("?(.+?)"?\)', img_tag['style'])
                        if match:
                            imagen = match.group(1)
                
                # Si no hay imagen, poner una por defecto o dejar vacía
                if not imagen:
                    imagen = "/assets/logo.png" # Usar logo de la peña por defecto

                noticias.append({
                    'fecha_scraping': datetime.now(),
                    'titulo': titulo,
                    'link': link,
                    'imagen': imagen,
                    'resumen': resumen,
                    'origen': 'DiaDia'
                })
                
            except Exception as e:
                continue # Si falla una noticia, seguir con la siguiente

        # Convertir a DataFrame
        if noticias:
            return pd.DataFrame(noticias)
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"❌ Error general en scraping: {e}")
        return pd.DataFrame()