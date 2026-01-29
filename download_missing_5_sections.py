"""
Skript pro stažení 5 chybějících sekcí Panorama Firm
Pouze sekce, které selhaly při předchozím stahování
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# 5 CHYBĚJÍCÍCH SEKCÍ
MISSING_SECTIONS = [
    {
        'name': 'Kancelaria',
        'code': 'd',
        'filename': 'kancelaria_branze.html'
    },
    {
        'name': 'Usługi dla firm',
        'code': 'n',
        'filename': 'uslugi_dla_firm_branze.html'
    },
    {
        'name': 'Usługi dla każdego',
        'code': 'p',
        'filename': 'uslugi_dla_kazdego_branze.html'
    },
    {
        'name': 'Zdrowie i uroda',
        'code': 's',
        'filename': 'zdrowie_i_uroda_branze.html'
    },
    {
        'name': 'Żywność i używki',
        'code': 'a',
        'filename': 'zywnosc_i_uzywki_branze.html'
    }
]

def setup_driver():
    """Nastavení Chrome driveru s viditelnými okny"""
    chrome_options = Options()
    # VIDITELNÝ prohlížeč - NE headless!
    # chrome_options.add_argument('--headless')  # VYPNUTO!
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def download_section(driver, section_info):
    """Stáhne jednu sekci"""
    name = section_info['name']
    code = section_info['code']
    filename = section_info['filename']
    
    # Formátování URL pro polské znaky
    url_name = name.lower()
    url_name = url_name.replace(' ', '_')
    url_name = url_name.replace('ł', '%C5%82')
    url_name = url_name.replace('ą', '%C4%85')
    url_name = url_name.replace('ę', '%C4%99')
    url_name = url_name.replace('ć', '%C4%87')
    url_name = url_name.replace('ń', '%C5%84')
    url_name = url_name.replace('ó', '%C3%B3')
    url_name = url_name.replace('ś', '%C5%9B')
    url_name = url_name.replace('ź', '%C5%BA')
    url_name = url_name.replace('ż', '%C5%BC')
    
    url = f'https://panoramafirm.pl/{url_name},{code}/branze.html'
    
    print(f"\n{'='*60}")
    print(f"📥 STAHUJI: {name}")
    print(f"🔗 URL: {url}")
    print(f"💾 Soubor: {filename}")
    print(f"{'='*60}")
    
    try:
        driver.get(url)
        
        # Počkáme na načtení stránky - čekáme na div s id začínajícím "letter-"
        print("⏳ Čekám na načtení kategoriií...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id^="letter-"]'))
        )
        
        # Spočítáme kolik divů s písmenky jsme našli
        letter_divs = driver.find_elements(By.CSS_SELECTOR, 'div[id^="letter-"]')
        print(f"✅ Nalezeno {len(letter_divs)} písmen s kategoriemi")
        
        # Krátká pauza pro jistotu
        time.sleep(2)
        
        # Uložíme HTML
        html_content = driver.page_source
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"💾 ✅ ULOŽENO: {filename}")
        print(f"📊 Velikost: {len(html_content):,} bytů")
        
        return True
        
    except Exception as e:
        print(f"❌ CHYBA při stahování {name}:")
        print(f"   {str(e)}")
        return False

def main():
    print("="*70)
    print("🔥 STAHOVÁNÍ 5 CHYBĚJÍCÍCH SEKCÍ PANORAMA FIRM")
    print("="*70)
    print()
    print("⚠️  DŮLEŽITÉ:")
    print("   • Chrome se otevře VIDITELNĚ (ne headless)")
    print("   • Počkejte na dokončení všech 5 sekcí")
    print("   • Pokud Chrome spadne, zkuste to znovu")
    print()
    
    driver = setup_driver()
    
    results = {
        'success': [],
        'failed': []
    }
    
    try:
        for i, section in enumerate(MISSING_SECTIONS, 1):
            print(f"\n{'#'*70}")
            print(f"# SEKCE {i}/5")
            print(f"{'#'*70}")
            
            success = download_section(driver, section)
            
            if success:
                results['success'].append(section['name'])
            else:
                results['failed'].append(section['name'])
            
            # Pauza mezi sekcemi (kromě poslední)
            if i < len(MISSING_SECTIONS):
                print("\n⏸️  Pauza 3 sekundy před další sekcí...")
                time.sleep(3)
        
    finally:
        driver.quit()
        print("\n🔒 Prohlížeč uzavřen")
    
    # VÝSLEDKY
    print("\n" + "="*70)
    print("📊 VÝSLEDKY STAHOVÁNÍ")
    print("="*70)
    
    print(f"\n✅ ÚSPĚŠNĚ STAŽENO ({len(results['success'])}/5):")
    for name in results['success']:
        print(f"   ✓ {name}")
    
    if results['failed']:
        print(f"\n❌ SELHALO ({len(results['failed'])}/5):")
        for name in results['failed']:
            print(f"   ✗ {name}")
    else:
        print("\n🎉 VŠECH 5 SEKCÍ STAŽENO ÚSPĚŠNĚ!")
    
    print("\n" + "="*70)
    print("🔜 DALŠÍ KROK:")
    print("   Spusťte: python process_manual_html.py")
    print("   Pro zpracování všech HTML souborů")
    print("="*70)

if __name__ == '__main__':
    main()
