"""
KOMPLETNÍ EXTRAKTOR - Všech kategorií ze všech 19 sekcí Panorama Firm
Použije Selenium pro správné načtení dynamického obsahu
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys

# 20 hlavních sekcí (všechny sekce z Panorama Firm)
SECTIONS = {
    'biuro,z': 'Biuro',
    'kancelaria,o': 'Kancelaria',
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
}

def setup_driver():
    """Nastaví Chrome driver s headless režimem"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    return driver

def extract_categories_from_section(driver, section_url, section_name):
    """
    Extrahuje všechny podkategorie z dané sekce
    Zkouší více strategií pro různé struktury stránek
    """
    # URL pro seznam branží v sekci
    url = f'https://panoramafirm.pl/{section_url}/branze.html'
    
    print(f"\n{'='*80}")
    print(f"📂 {section_name}")
    print(f"   {url}")
    print(f"{'='*80}")
    
    categories = {}
    
    try:
        driver.get(url)
        
        # Počkat na načtení
        time.sleep(3)
        
        # Zkusit kliknout na "Pokaż wszystkie" pokud existuje
        try:
            show_all_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Pokaż wszystkie') or contains(text(), 'wszystkie')]")
            show_all_button.click()
            time.sleep(2)
            print("   ✅ Kliknuto na 'Pokaż wszystkie'")
        except:
            print("   ℹ️  Tlačítko 'Pokaż wszystkie' nenalezeno (možná nejsou potřeba)")
        
        # Strategie 1: Najít všechny odkazy v hlavním obsahu
        links = driver.find_elements(By.TAG_NAME, 'a')
        
        seen_texts = set()  # Prevence duplicit
        
        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                # Filtrovat platné kategorie
                if (text and 
                    len(text) > 2 and
                    text not in seen_texts and
                    href and 
                    'panoramafirm.pl/' in href and
                    not any(skip in href.lower() for skip in [
                        '/branze', '/kategorie', '/lista', '/firmy',
                        '/miasto', '/region', '/wizytowki',
                        '/regulamin', '/kontakt', '/polityka', '/cookies',
                        '/dodaj', '/popularne', '/najnowsze', '/artykuly',
                        '/poradniki', '/reklama', '/inf/', '/panorama_',
                        '.html', '.php'
                    ]) and
                    # Musí mít jednoduchou strukturu URL
                    href.count('/') >= 3 and href.count('/') <= 5 and
                    # Nesmí končit číslem (to jsou jednotlivé firmy)
                    not href.rstrip('/').split('/')[-1].isdigit()):
                    
                    # Přidat kategorii
                    category_key = f"panorama_{href}"
                    category_label = f"PANORAMA [{section_name}]: {text}"
                    
                    if category_key not in categories and len(text) < 100:
                        categories[category_key] = category_label
                        seen_texts.add(text)
                        print(f"   ✓ {text}")
                        
            except Exception as e:
                continue
        
        print(f"\n   📊 Celkem nalezeno: {len(categories)} podkategorií")
        return categories
        
    except Exception as e:
        print(f"   ❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    print("="*80)
    print("🔍 PANORAMA FIRM - KOMPLETNÍ EXTRAKTOR KATEGORIÍ")
    print("="*80)
    print(f"📋 Sekcí k procházení: {len(SECTIONS)}")
    print("="*80)
    
    driver = None
    all_categories = {}
    
    try:
        driver = setup_driver()
        print("✅ Chrome driver spuštěn\n")
        
        # Projít všechny sekce
        for i, (url_part, section_name) in enumerate(SECTIONS.items(), 1):
            print(f"\n[{i}/{len(SECTIONS)}] Zpracovávám sekci...")
            
            section_cats = extract_categories_from_section(driver, url_part, section_name)
            all_categories.update(section_cats)
            
            time.sleep(2)  # Rate limiting
        
        # Výsledky
        print("\n" + "="*80)
        print(f"✅ DOKONČENO!")
        print("="*80)
        print(f"📊 Celkem nalezeno: {len(all_categories)} kategorií")
        print(f"📂 Z počtu sekcí: {len(SECTIONS)}")
        print("="*80)
        
        # Seskupit podle sekcí
        by_section = {}
        for key, label in all_categories.items():
            section = label.split('[')[1].split(']')[0]
            if section not in by_section:
                by_section[section] = []
            by_section[section].append(label)
        
        print("\n📋 Kategorie podle sekcí:")
        for section in sorted(by_section.keys()):
            print(f"   {section}: {len(by_section[section])} kategorií")
        
        # Uložit do souboru
        output_file = 'd:/skript/panorama_complete_categories.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            for key, label in sorted(all_categories.items(), key=lambda x: x[1]):
                # Escapovat apostrofy v textu
                safe_key = key.replace("'", "\\'")
                safe_label = label.replace("'", "\\'")
                f.write(f"    '{safe_key}': '{safe_label}',\n")
        
        print(f"\n💾 Uloženo {len(all_categories)} kategorií do: {output_file}")
        
        print(f"\n💾 Uloženo do: {output_file}")
        print("\n✅ HOTOVO!")
        
    except Exception as e:
        print(f"\n❌ Kritická chyba: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
            print("\n🔒 Chrome driver uzavřen")

if __name__ == '__main__':
    main()
