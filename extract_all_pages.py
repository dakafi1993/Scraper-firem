"""
Kompletní extraktor - prochází všechny podstránky každé kategorie
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_driver():
    options = Options()
    # BEZ headless - chci vidět co se děje
    # options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    return webdriver.Chrome(options=options)

SECTIONS = {
    'budownictwo,b': 'Budownictwo',
    'dom_i_ogród,c': 'Dom i ogród',
    'dzieci,u': 'Dzieci',
    'finanse_i_ubezpieczenia,r': 'Finanse i ubezpieczenia',
    'instytucje_urzędy,f': 'Instytucje, urzędy',
    'motoryzacja_i_transport,h': 'Motoryzacja i transport',
    'nauka,i': 'Nauka',
    'odzież_i_tekstylia,g': 'Odzież i tekstylia',
    'porady,w': 'Porady',
    'przemysł_i_energetyka,k': 'Przemysł i energetyka',
    'rolnictwo_i_leśnictwo,j': 'Rolnictwo i leśnictwo',
    'rozrywka_i_rekreacja,l': 'Rozrywka i rekreacja',
    'telekomunikacja_internet_technologie,t': 'Telekomunikacja, internet, technologie',
    'turystyka,m': 'Turystyka',
    'usługi_dla_firm,n': 'Usługi dla firm',
    'usługi_dla_każdego,p': 'Usługi dla każdego',
    'zdrowie_i_uroda,s': 'Zdrowie i uroda',
    'żywność_i_używki,a': 'Żywność i używki',
    'biuro,z': 'Biuro',
    'kancelaria,o': 'Kancelaria',
}

print("="*80)
print("🔍 PANORAMA FIRM - Kompletní extraktor s pagination")
print("="*80)

driver = setup_driver()
all_categories = {}

try:
    for section_url, section_name in SECTIONS.items():
        print(f"\n{'='*80}")
        print(f"📂 {section_name}")
        
        page = 1
        section_total = 0
        
        while True:
            # URL s pagination
            if page == 1:
                url = f'https://panoramafirm.pl/{section_url}/branze.html'
            else:
                url = f'https://panoramafirm.pl/{section_url}/branze,{page}.html'
            
            print(f"   📄 Stránka {page}: {url}")
            
            try:
                driver.get(url)
                time.sleep(2)
                
                # Najít všechny odkazy na branže
                links = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                page_cats = 0
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        
                        if (href and text and
                            'panoramafirm.pl/' in href and
                            len(text) > 2 and len(text) < 100):
                            
                            url_part = href.replace('https://panoramafirm.pl/', '').replace('http://panoramafirm.pl/', '')
                            
                            # Filtr pro podkategorie
                            if (url_part and
                                not any(skip in url_part.lower() for skip in [
                                    '.html', 'branze', 'dodaj', 'kontakt', 'regulamin',
                                    'polityka', 'reklama', 'artykul', 'inf/',
                                    'panorama_', 'lista', 'wizytowki', 'firma/',
                                    'zapytania', 'cookies', 'obowiazek', 'popularne',
                                    'miasta', 'region'
                                ]) and
                                ',' not in url_part and
                                url_part.count('/') == 0 and
                                len(url_part) > 2):
                                
                                category_key = f"panorama_{href}"
                                category_label = f"PANORAMA [{section_name}]: {text}"
                                
                                if category_key not in all_categories:
                                    all_categories[category_key] = category_label
                                    page_cats += 1
                                    
                    except Exception as e:
                        continue
                
                if page_cats > 0:
                    print(f"      ✅ Nalezeno {page_cats} nových kategorií")
                    section_total += page_cats
                    page += 1
                else:
                    print(f"      ⛔ Žádné nové kategorie - konec sekce")
                    break
                    
                # Limit stránek pro bezpečnost
                if page > 50:
                    print(f"      ⚠️  Dosažen limit 50 stránek")
                    break
                    
            except Exception as e:
                print(f"      ❌ Chyba: {e}")
                break
        
        print(f"   📊 Sekce celkem: {section_total} kategorií")
        time.sleep(1)
    
    print(f"\n{'='*80}")
    print(f"📊 CELKEM: {len(all_categories)} kategorií ze {len(SECTIONS)} sekcí")
    print(f"{'='*80}")
    
    # Seskupit podle sekcí
    by_section = {}
    for key, label in all_categories.items():
        if '[' in label and ']:' in label:
            section = label.split('[')[1].split(']')[0]
            if section not in by_section:
                by_section[section] = 0
            by_section[section] += 1
    
    print("\n📋 Kategorie podle sekcí:")
    for section in sorted(by_section.keys()):
        print(f"   {section}: {by_section[section]} kategorií")
    
    # Uložit
    output_file = 'd:/skript/panorama_complete_all.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for key, label in sorted(all_categories.items(), key=lambda x: x[1]):
            safe_key = key.replace("'", "\\'")
            safe_label = label.replace("'", "\\'")
            f.write(f"    '{safe_key}': '{safe_label}',\n")
    
    print(f"\n💾 Uloženo do: {output_file}")
    print("✅ HOTOVO!")
    
finally:
    driver.quit()
