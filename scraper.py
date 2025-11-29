import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

def scrapear_diadia():
    url = "https://diadia.cat/"
    
    # Palabras clave (usaremos regex para buscar palabra exacta)
    # Ejemplo: que "festa" no salte con "manifesta"
    keywords = [
        "festa", "fiesta", "festes", "tardeo", "toros", "bous",
        "orquesta", "discomobil", "discomovil", "fira", "feria", 
        "sant antoni", "sopar", "dinar", "actes", "entrades", "vacances", "agenda", "cultural", "nadal", "navidad", "festes"
    ]
    
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
        
        seen_links = set()

        for art in articulos:
            try:
                # 1. Título y Link
                titulo_tag = art.find('h3', class_='entry-title')
                if not titulo_tag: continue
                
                link_tag = titulo_tag.find('a')
                if not link_tag: continue

                titulo = link_tag.get('title', '').strip()
                if not titulo: titulo = link_tag.get_text(strip=True)
                
                link = link_tag.get('href', '')
                if link in seen_links: continue
                seen_links.add(link)

                # 2. Resumen
                excerpt_tag = art.find('div', class_='td-excerpt')
                resumen = excerpt_tag.get_text(strip=True) if excerpt_tag else ""
                
                # 3. Filtrado por PALABRA EXACTA (Regex)
                texto_completo = (titulo + " " + resumen).lower()
                
                match_found = False
                for kw in keywords:
                    # \b significa "borde de palabra". 
                    # Busca 'festa' pero no 'manifesta', busca 'bous' pero no 'lobous'
                    if re.search(r'\b' + re.escape(kw) + r'\b', texto_completo):
                        match_found = True
                        break
                
                if not match_found:
                    continue

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
                if '-696x' in imagen: imagen = re.sub(r'-\d+x\d+(?=\.\w+$)', '', imagen)

                noticias.append({
                    'fecha_scraping': datetime.now(),
                    'titulo': titulo,
                    'link': link,
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