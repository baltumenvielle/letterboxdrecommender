from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.http import TextResponse
import time

# Configuración del navegador
options = Options()
# Comentá esta línea para ver el navegador funcionando visualmente
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get('https://www.imdb.com/search/title/?groups=top_1000')

wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

# Simula scroll tipo humano y clic en botón si aparece
while True:
    try:
        # Intentamos encontrar el botón "Ver más"
        button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.ipc-see-more__button')))
        if button.is_displayed():
            print("🔘 Botón visible. Scrolleando hacia él y haciendo clic...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            button.click()
            time.sleep(2)
            continue
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
        pass

    # Scroll hacia abajo "como humano"
    actions.send_keys(Keys.PAGE_DOWN).perform()
    time.sleep(0.4)
    actions.send_keys(Keys.PAGE_DOWN).perform()
    time.sleep(0.4)

    # Check opcional: si no hay botón visible después de muchos intentos, cortar
    page_end = driver.execute_script("return window.innerHeight + window.scrollY >= document.body.scrollHeight")
    if page_end:
        print("✔ No hay más botón o llegamos al final de la página.")
        break

# Extraer HTML final antes de cerrar el navegador
html = driver.page_source
driver.quit()

# Scrapy para parsear la respuesta (sin usar driver.current_url)
response = TextResponse(url='https://www.imdb.com/search/title/?groups=top_1000', body=html, encoding='utf-8')

# Guardar URLs
with open('urls_peliculas.txt', 'w') as f:
    for relative_url in response.css('.ipc-title a::attr(href)').getall():
        full_url = f'https://www.imdb.com{relative_url}'
        f.write(full_url + '\n')

print("✔ URLs guardadas en urls_peliculas.txt")
