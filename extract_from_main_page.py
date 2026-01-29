"""
Extraktor kategorií přímo z hlavní stránky Panorama Firm
Projde navigační menu a získá všechny kategorie a podkategorie
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import json

def setup_driver():
    options = Options()
    # Bez headless - musíme vidět menu
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    return webdriver.Chrome(options=options)

print("="*80)
print("🔍 PANORAMA FIRM - Extraktor z hlavního menu")
print("="*80)

driver = setup_driver()
all_categories = {}

try:
    # Seznam všech sekcí ke zpracování  
    sections = {
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
    
    # Projít každou sekci
    for section_url, section_name in sections.items():
        print(f"\n{'='*80}")
        print(f"📂 {section_name}")
        
        # URL sekce
        url = f'https://panoramafirm.pl/{section_url}'
        
        try:
            print(f"   🔗 {url}")
            driver.get(url)
            time.sleep(3)
            
            # Najít všechny odkazy na kategorii
            links = driver.find_elements(By.TAG_NAME, 'a')
            section_cats = 0
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    
                    # Kategorie jsou odkazy začínající /název_kategorie
                    if (href and text and
                        'panoramafirm.pl/' in href and
                        len(text) > 2 and len(text) < 100):
                        
                        url_part = href.replace('https://panoramafirm.pl/', '').replace('http://panoramafirm.pl/', '')
                        
                        # Filtrovat platné kategorie
                        if (url_part and
                            not any(skip in url_part.lower() for skip in [
                                '.html', 'dodaj', 'kontakt', 'regulamin',
                                'polityka', 'reklama', 'artykul', 'inf/',
                                'panorama_', 'lista', 'firmy', 'wizytowki',
                                'zapytania', 'cookies', 'obowiazek', 'popularne'
                            ]) and
                            ',' not in url_part and
                            url_part.count('/') <= 1 and
                            len(url_part) > 2):
                            
                            category_key = f"panorama_{href}"
                            category_label = f"PANORAMA [{section_name}]: {text}"
                            
                            if category_key not in all_categories:
                                all_categories[category_key] = category_label
                                section_cats += 1
                                
                                if section_cats <= 5:  # Zobrazit prvních 5
                                    print(f"      ✓ {text}")
                                    
                except Exception as e:
                    continue
            
            if section_cats > 0:
                if section_cats > 5:
                    print(f"      ... a {section_cats - 5} dalších")
                print(f"   📊 Celkem: {section_cats} kategorií")
            else:
                print(f"   ⚠️  Žádné kategorie")
                
        except Exception as e:
            print(f"   ❌ Chyba: {e}")
        
        time.sleep(1)
    
    print(f"\n{'='*80}")
    print(f"📊 CELKEM: {len(all_categories)} kategorií ze {len(sections)} sekcí")
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
    
    # Uložit výsledky
    output_file = 'd:/skript/panorama_from_main.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for key, label in sorted(all_categories.items(), key=lambda x: x[1]):
            safe_key = key.replace("'", "\\'")
            safe_label = label.replace("'", "\\'")
            f.write(f"    '{safe_key}': '{safe_label}',\n")
    
    print(f"\n💾 Uloženo do: {output_file}")
    print(f"📊 Celkem: {len(all_categories)} kategorií")
    
finally:
    driver.quit()
    print("\n✅ HOTOVO!")
