"""
Panorama Firm - Extraktor kategorií pomocí Selenium
Extrauje VŠECHNY podkategorie ze všech 19 sekcí
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json

# 19 hlavních kategorií z menu
MAIN_CATEGORIES = {
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
    'kancelaria,o': 'Kancelaria',
}

def setup_driver():
    """Nastaví Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    return webdriver.Chrome(options=chrome_options)

def extract_subcategories_selenium(driver, main_cat_url, main_cat_name):
    """Extrahuje podkategorie z dané sekce pomocí Selenium"""
    url = f'https://panoramafirm.pl/{main_cat_url}/branze.html'
    
    print(f"\n📂 {main_cat_name}")
    print(f"   URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)  # Počkat na načtení
        
        # Najít všechny odkazy na branže
        # Panorama používá různé struktury, zkusíme více selektorů
        categories = {}
        
        # Strategie 1: Odkazy v seznamu branží
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/"]')
        
        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                if (text and 
                    len(text) > 2 and
                    href and
                    'panoramafirm.pl' in href and
                    not any(skip in href.lower() for skip in [
                        '/branze', '/kategorie', '/lista', '/firmy',
                        '/regiony', '/miasta', '/wizytowki', 
                        '/regulamin', '/kontakt', '/polityka',
                        '/dodaj', '/popularne', '/najnowsze'
                    ]) and
                    href.count('/') <= 4):  # Basic URL structure
                    
                    # Klíč
                    category_key = f'panorama_{href}'
                    
                    # Label
                    category_label = f'PANORAMA [{main_cat_name}]: {text}'
                    
                    if category_key not in categories:
                        categories[category_key] = category_label
                        
            except Exception as e:
                continue
        
        print(f"   ✅ Nalezeno {len(categories)} podkategorií")
        return categories
        
    except Exception as e:
        print(f"   ❌ Chyba: {e}")
        return {}

def main():
    print("=" * 80)
    print("🔍 PANORAMA FIRM - SELENIUM EXTRAKTOR")
    print("=" * 80)
    
    driver = setup_driver()
    all_categories = {}
    
    try:
        for url_part, name in MAIN_CATEGORIES.items():
            subcats = extract_subcategories_selenium(driver, url_part, name)
            all_categories.update(subcats)
            time.sleep(2)  # Rate limiting
        
        print("\n" + "=" * 80)
        print(f"📊 CELKEM: {len(all_categories)} kategorií z {len(MAIN_CATEGORIES)} sekcí")
        print("=" * 80)
        
        # Uložit
        with open('panorama_selenium_categories.txt', 'w', encoding='utf-8') as f:
            for key, value in sorted(all_categories.items(), key=lambda x: x[1]):
                f.write(f"    '{key}': '{value}',\n")
        
        print(f"\n💾 Uloženo do: panorama_selenium_categories.txt")
        print("\n✅ HOTOVO!")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
