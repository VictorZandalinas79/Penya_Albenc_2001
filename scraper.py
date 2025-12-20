import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

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

def scrapear_eventos_externos():
    session = requests.Session()
    # Configuración de reintentos
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9'
    }
    
    eventos = []
    # Palabras clave para ViveCastellón (Filtro de música)
    keywords_musica = ["concierto", "musica", "música", "jazz", "band", "festival", "recital", "sonora", "tributo", "big band", "orquesta"]

    # --- FUENTE 1: VIVE CASTELLÓN (Páginas 1 y 2) ---
    paginas_vc = ["", "2/"] # "" es la primera página, "2/" la segunda
    for p in paginas_vc:
        try:
            url_vc = f"https://www.vivecastellon.com/eventos-castellon-agenda/{p}"
            print(f"🎸 [SCRAPER] Escaneando ViveCastellón: {url_vc}")
            res = session.get(url_vc, headers=headers, timeout=15)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.content, 'html.parser')
            bloques = soup.find_all('div', class_='agenda1')

            for art in bloques:
                try:
                    # 1. Categoría y Título (para filtrar)
                    cat_tag = art.find('span', class_='url_cate')
                    categoria = cat_tag.get_text(strip=True).lower() if cat_tag else ""
                    
                    titulo_tag = art.find('h2')
                    if not titulo_tag: continue
                    titulo = titulo_tag.get_text(strip=True)
                    
                    # FILTRO DE SEGURIDAD: Solo eventos relacionados con música
                    texto_completo = f"{categoria} {titulo}".lower()
                    if not any(k in texto_completo for k in keywords_musica):
                        continue

                    # 2. Fecha (Limpia rangos: "20/12/25 — 30/12/25" -> "20/12/25")
                    fecha_raw = art.find('h1').get_text(strip=True)
                    fecha_limpia = fecha_raw.split('—')[0].strip()
                    # Normalizamos el separador de hora si lo hubiera a " - "
                    fecha_limpia = fecha_limpia.replace(' - ', '-').replace('-', ' - ')

                    # 3. Lugar
                    lugar_tag = art.find('p')
                    lugar = lugar_tag.get_text(strip=True).split('−')[-1].strip() if lugar_tag else "Castelló"

                    # 4. Link
                    a_link = titulo_tag.find('a')
                    link = a_link['href'] if a_link and a_link.has_attr('href') else url_vc
                    if link.startswith('/'): link = "https://www.vivecastellon.com" + link

                    eventos.append({
                        'fecha_scraping': datetime.now(),
                        'fecha_evento': fecha_limpia,
                        'titulo': titulo,
                        'lugar': lugar,
                        'precio': "Ver Web",
                        'link': link,
                        'imagen': "/assets/logo.png",
                        'tipo': 'concierto',
                        'origen': 'ViveCastellón'
                    })
                except: continue
        except Exception as e:
            print(f"❌ Error en ViveCastellón: {e}")

    # --- FUENTE 2: NOMEPIERDONIUNA (Agenda Cultural) ---
    try:
        url_nm = "https://www.nomepierdoniuna.net/agenda/"
        print(f"📅 [SCRAPER] Escaneando NMPNU: {url_nm}")
        res = session.get(url_nm, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            filas = soup.find_all('tr')
            for row in filas:
                tds = row.find_all('td')
                if len(tds) >= 5:
                    try:
                        link_tag = tds[4].find('a')
                        if not link_tag: continue
                        
                        # Normalizamos fecha para que use " - " entre fecha y hora
                        f_nmpnu = tds[0].get_text(strip=True).replace(' - ', '-').replace('-', ' - ')

                        eventos.append({
                            'fecha_scraping': datetime.now(),
                            'fecha_evento': f_nmpnu,
                            'titulo': link_tag.get_text(strip=True),
                            'lugar': f"{tds[1].get_text(strip=True)}, {tds[2].get_text(strip=True)}",
                            'precio': tds[5].get_text(strip=True),
                            'link': link_tag['href'] if link_tag.has_attr('href') else "",
                            'imagen': "/assets/logo.png",
                            'tipo': 'agenda',
                            'origen': 'NMPNU'
                        })
                    except: continue
    except Exception as e:
        print(f"❌ Error en NMPNU: {e}")

    print(f"✅ [SCRAPER] Total eventos capturados: {len(eventos)}")
    return pd.DataFrame(eventos)