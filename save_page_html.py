from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
driver = webdriver.Chrome(options=options)

# Načti jednu stránku
url = 'https://panoramafirm.pl/dom_i_ogród,c/branze.html'
print(f'Načítám: {url}')
driver.get(url)
time.sleep(5)

# Ulož HTML
html = driver.page_source
with open('d:/skript/branze_page_structure.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'✅ HTML uloženo do: branze_page_structure.html')
print(f'📊 Velikost: {len(html)} znaků')

driver.quit()
