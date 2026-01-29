from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 20 hlavních sekcí
sections = [
    ('budownictwo,b', 'Budownictwo'),
    ('dom_i_ogród,c', 'Dom i ogród'),
    ('dzieci,u', 'Dzieci'),
    ('finanse_i_ubezpieczenia,r', 'Finanse i ubezpieczenia'),
    ('instytucje_urzędy,f', 'Instytucje, urzędy'),
    ('motoryzacja_i_transport,h', 'Motoryzacja i transport'),
    ('nauka,i', 'Nauka'),
    ('odzież_i_tekstylia,g', 'Odzież i tekstylia'),
    ('porady,w', 'Porady'),
    ('przemysł_i_energetyka,k', 'Przemysł i energetyka'),
    ('rolnictwo_i_leśnictwo,j', 'Rolnictwo i leśnictwo'),
    ('rozrywka_i_rekreacja,l', 'Rozrywka i rekreacja'),
    ('telekomunikacja_internet_technologie,t', 'Telekomunikacja, internet, technologie'),
    ('turystyka,m', 'Turystyka'),
    ('usługi_dla_firm,n', 'Usługi dla firm'),
    ('usługi_dla_każdego,p', 'Usługi dla każdego'),
    ('zdrowie_i_uroda,s', 'Zdrowie i uroda'),
    ('żywność_i_używki,a', 'Żywność i używki'),
]

# Chrome options
options = Options()
# options.add_argument('--headless=new')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

all_categories = {}
total_count = 0

print(f'{"="*80}')
print(f'🔍 PANORAMA FIRM - Správná extrakce podle písmen')
print(f'{"="*80}\n')

for section_code, section_name in sections:
    url = f'https://panoramafirm.pl/{section_code}/branze.html'
    print(f'\n📂 {section_name}')
    print(f'   URL: {url}')
    
    driver.get(url)
    time.sleep(3)
    
    section_total = 0
    
    try:
        # Najdi všechny LINKY ke kategoriím (ne samotné kategorie)
        # Hledám odkazy které nejsou navigace
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        
        found_categories = {}
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                if not href or not text:
                    continue
                    
                # Musí být Panorama Firm URL
                if 'panoramafirm.pl' not in href:
                    continue
                    
                # NESMÍ obsahovat: branze, firmy, strona, regulamin, polityka, kontakt, dodaj
                skip_words = ['branze', 'firmy,', 'strona', 'regulamin', 'polityka', 'kontakt', 'dodaj', 'premium']
                if any(word in href.lower() for word in skip_words):
                    continue
                
                # Musí být rozumná délka názvu
                if len(text) < 3 or len(text) > 80:
                    continue
                    
                # Validní kategorie mají formát: /category_name
                # nebo /category_name,location
                parts = href.replace('https://panoramafirm.pl/', '').split('/')
                if len(parts) > 0 and len(parts[0]) > 0:
                    category_slug = parts[0].split(',')[0]
                    
                    # Zkontrolovat že není to navigace
                    if category_slug and category_slug not in ['', 'biuro', 'kancelaria']:
                        key = f'panorama_{href}'
                        value = f'PANORAMA [{section_name}]: {text}'
                        
                        if key not in found_categories:
                            found_categories[key] = value
                            section_total += 1
                            
            except Exception as e:
                pass
        
        # Přidat do globálního seznamu
        all_categories.update(found_categories)
        
        print(f'   ✅ Nalezeno: {section_total} kategorií')
        total_count += section_total
        
    except Exception as e:
        print(f'   ❌ Chyba: {e}')

driver.quit()

print(f'\n{"="*80}')
print(f'📊 CELKEM: {total_count} kategorií z {len(sections)} sekcí')
print(f'{"="*80}')

# Uložit
if all_categories:
    output_file = 'd:/skript/panorama_correct_all.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for key, value in sorted(all_categories.items()):
            f.write(f"    '{key}': '{value}',\n")
    
    print(f'\n💾 Uloženo do: {output_file}')
    
    # Statistika podle sekcí
    print(f'\n📋 Statistika:')
    section_counts = {}
    for value in all_categories.values():
        section = value.split('[')[1].split(']')[0]
        section_counts[section] = section_counts.get(section, 0) + 1
    
    for section, count in sorted(section_counts.items()):
        print(f'   {section}: {count}')
