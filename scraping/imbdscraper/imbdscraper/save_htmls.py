import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import os
import time
from tqdm import tqdm

# Carpeta donde se guardarán los HTMLs
output_dir = 'html_movies'
os.makedirs(output_dir, exist_ok=True)

# Leer URLs del archivo (sin modificar nada)
with open('urls_peliculas.txt', 'r') as f:
    urls = [url.strip() for url in f.readlines()]

# Configuración del navegador con idioma en inglés
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
# options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--start-maximized')
options.add_argument('--lang=en-US')  # Idioma del navegador

# Preferencias del perfil para que envíe 'Accept-Language: en-US'
prefs = {
    "intl.accept_languages": "en-US,en"
}
options.add_experimental_option("prefs", prefs)

# Iniciar navegador
driver = uc.Chrome(options=options)

# Descargar las páginas
for i, url in enumerate(tqdm(urls, desc="Descargando páginas")):
    try:
        driver.get(url)
        time.sleep(3)  # Esperar a que cargue la página

        final_url = driver.current_url
        # Corregir si fue redirigido a /es/
        if '/es/' in final_url:
            final_url = final_url.replace('/es/', '/')

        imdb_id = final_url.split('/')[4]
        html = driver.page_source
        with open(f'{output_dir}/{imdb_id}.html', 'w', encoding='utf-8') as f:
            f.write(html)
    except WebDriverException as e:
        print(f"❌ Error en {url}: {e}")
        continue

driver.quit()
print("✔ Todos los archivos guardados en 'html_movies/'")