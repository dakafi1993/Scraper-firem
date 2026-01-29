from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Speciální sekce které nemají standardní /branze.html strukturu
special_sections = [
    ('biuro,z', 'Biuro'),
    ('kancelaria,o', 'Kancelaria'),
]

# Chrome options
options = Options()
# Viditelný prohlížeč pro debug
# options.add_argument('--headless=new')

driver = webdriver.Chrome(options=options)

all_categories = {}

for section_code, section_name in special_sections:
    print(f'\n{"="*80}')
    print(f'📂 {section_name}')
    
    # Zkusím různé URL varianty
    urls_to_try = [
        f'https://panoramafirm.pl/{section_code}/branze.html',
        f'https://panoramafirm.pl/{section_code}',
        f'https://panoramafirm.pl/{section_code}/',
    ]
    
    for url in urls_to_try:
        print(f'\n   📄 Zkouším: {url}')
        driver.get(url)
        time.sleep(3)
        
        try:
            # Hledám kategorie - různé selektory
            categories_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="' + section_code + '"]')
            
            print(f'      Nalezeno {len(categories_links)} odkazů')
            
            found_count = 0
            for link in categories_links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    
                    # Filtrovat jen kategorie (ne branze, ne stejná URL)
                    if text and href and 'branze' not in href and href != url:
                        # Kontrola že to není duplicita nebo navigace
                        if len(text) > 2 and len(text) < 100:
                            key = f'panorama_{href}'
                            value = f'PANORAMA [{section_name}]: {text}'
                            
                            if key not in all_categories:
                                all_categories[key] = value
                                found_count += 1
                                if found_count <= 5:  # První 5 pro ukázku
                                    print(f'         ✅ {text}')
                except:
                    pass
            
            print(f'      📊 Celkem nových: {found_count}')
            
            if found_count > 0:
                break  # Našli jsme kategorie, nemusíme zkoušet další URL
                
        except Exception as e:
            print(f'      ❌ Chyba: {e}')

driver.quit()

print(f'\n{"="*80}')
print(f'📊 CELKEM nalezeno kategorií: {len(all_categories)}')
print(f'{"="*80}')

if all_categories:
    # Uložit do souboru
    output_file = 'd:/skript/biuro_kancelaria_categories.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for key, value in sorted(all_categories.items()):
            f.write(f"    '{key}': '{value}',\n")
    
    print(f'\n💾 Uloženo do: {output_file}')
    print('\n📋 Ukázka:')
    for i, (key, value) in enumerate(list(all_categories.items())[:5]):
        print(f'  {value}')
else:
    print('\n⚠️  Žádné kategorie nenalezeny - Biuro a Kancelaria pravděpodobně nemají podkategorie')
    print('   Jsou to přímo seznamy firem, použij URLs:')
    print('   - https://panoramafirm.pl/biuro,z')
    print('   - https://panoramafirm.pl/kancelaria,o')
