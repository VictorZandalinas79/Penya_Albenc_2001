import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def scrapear_diadia():
    url = "https://diadia.cat/"
    
    # Palabras clave
    keywords = [
        "festa", "fiesta", "festes", "tardeo", "toros", "bous",
        "orquesta", "discomobil", "discomovil", "fira", "feria", "patron",
        "sant antoni", "sopar", "dinar", "actes", "entrades", 
        "vacances", "agenda", "cultural", "nadal", "navidad", "tardeo", "kintos", "quintos", "sant", "tributo", "fiestas",
    ]
    
    # Construimos una ÚNICA expresión regular optimizada.
    # \b: Límite de palabra (asegura que 'festa' no salte con 'manifesta')
    # | : O (esto O lo otro)
    # map(re.escape, keywords): Escapa caracteres especiales si los hubiera
    patron_regex = re.compile(r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b', re.IGNORECASE)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    noticias = []
    
    try:
        print(f"🕷️ [SCRAPER] Iniciando escaneo de {url}...")
        response = requests.get(url, headers=headers, timeout=15)
        
        # Usamos lxml si está disponible, sino html.parser
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except:
            soup = BeautifulSoup(response.content, 'html.parser')
        
        articulos = soup.find_all('div', class_=re.compile(r'td_module_|td-block-span'))
        
        # Usamos dos conjuntos para evitar duplicados estrictamente
        seen_links = set()
        seen_titles = set()

        for art in articulos:
            try:
                # 1. Título y Link
                titulo_tag = art.find('h3', class_='entry-title')
                if not titulo_tag: continue
                
                link_tag = titulo_tag.find('a')
                if not link_tag: continue

                titulo = link_tag.get('title', '').strip()
                if not titulo: titulo = link_tag.get_text(strip=True)
                
                raw_link = link_tag.get('href', '')
                
                # LIMPIEZA DE URL: Quitamos parámetros extra (?utm_source...) para comparar mejor
                link_limpio = raw_link.split('?')[0]
                
                # COMPROBACIÓN DE DUPLICADOS (Link O Título)
                if link_limpio in seen_links or titulo in seen_titles:
                    continue
                
                # 2. Resumen
                excerpt_tag = art.find('div', class_='td-excerpt')
                resumen = excerpt_tag.get_text(strip=True) if excerpt_tag else ""
                
                # 3. Filtrado por PALABRA EXACTA (Usando el Regex compilado arriba)
                texto_completo = f"{titulo} {resumen}"
                
                # .search busca en cualquier parte del texto respetando los límites \b
                if not patron_regex.search(texto_completo):
                    continue
                
                # Si pasa el filtro, añadimos a "vistos" para no repetir
                seen_links.add(link_limpio)
                seen_titles.add(titulo)

                # 4. Imagen
                imagen = ""
                thumb_tag = art.find('span', class_='entry-thumb')
                
                if thumb_tag and thumb_tag.has_attr('data-img-url'):
                    imagen = thumb_tag['data-img-url']
                elif thumb_tag and thumb_tag.has_attr('style'):
                    match = re.search(r'url\("?\'?([^"\')]+)"?\'?\)', thumb_tag['style'])
                    if match: imagen = match.group(1)
                
                if not imagen:
                    img_tag_normal = art.find('img')
                    if img_tag_normal:
                        if img_tag_normal.has_attr('src'): imagen = img_tag_normal['src']
                        elif img_tag_normal.has_attr('data-src'): imagen = img_tag_normal['data-src']

                if not imagen: imagen = "/assets/logo.png"
                # Limpiar tamaño de imagen de WordPress para obtener la original
                if '-696x' in imagen: imagen = re.sub(r'-\d+x\d+(?=\.\w+$)', '', imagen)

                noticias.append({
                    'fecha_scraping': datetime.now(),
                    'titulo': titulo,
                    'link': link_limpio, # Guardamos el link limpio
                    'imagen': imagen,
                    'resumen': resumen,
                    'origen': 'DiaDia'
                })
                
            except Exception:
                continue

        print(f"✅ [SCRAPER] Finalizado. {len(noticias)} noticias encontradas.")
        return pd.DataFrame(noticias) if noticias else pd.DataFrame()

    except Exception as e:
        print(f"❌ [SCRAPER] Error crítico: {e}")
        return pd.DataFrame()