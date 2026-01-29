"""
Automatické stahování HTML pomocí Selenium s viditelným prohlížečem
Stáhne všechny sekce postupně a uloží je jako HTML soubory
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# 20 sekcí Panorama Firm
SECTIONS = [
    ("biuro", "z", "Biuro", "biuro_branze.html"),
    ("budownictwo", "b", "Budownictwo", "budownictwo_branze.html"),
    ("dom_i_ogród", "c", "Dom i ogród", "dom_i_ogrod_branze.html"),
    ("dzieci", "u", "Dzieci", "dzieci_branze.html"),
    ("finanse_i_ubezpieczenia", "r", "Finanse i ubezpieczenia", "finanse_branze.html"),
    ("instytucje_urzędy", "f", "Instytucje, urzędy", "instytucje_branze.html"),
    ("kancelaria", "y", "Kancelaria", "kancelaria_branze.html"),
    ("motoryzacja_i_transport", "h", "Motoryzacja i transport", "motoryzacja_branze.html"),
    ("nauka", "i", "Nauka", "nauka_branze.html"),
    ("odzież_i_tekstylia", "g", "Odzież i tekstylia", "odziez_branze.html"),
    ("porady", "w", "Porady", "porady_branze.html"),
    ("przemysł_i_energetyka", "k", "Przemysł i energetyka", "przemysl_branze.html"),
    ("rolnictwo_i_leśnictwo", "j", "Rolnictwo i leśnictwo", "rolnictwo_branze.html"),
    ("rozrywka_i_rekreacja", "l", "Rozrywka i rekreacja", "rozrywka_branze.html"),
    ("telekomunikacja_internet_technologie", "t", "Telekomunikacja, Internet, technologie", "telekomunikacja_branze.html"),
    ("turystyka", "m", "Turystyka", "turystyka_branze.html"),
    ("usługi_dla_firm", "n", "Usługi dla firm", "uslugi_dla_firm_branze.html"),
    ("usługi_dla_każdego", "p", "Usługi dla każdego", "uslugi_dla_kazdego_branze.html"),
    ("zdrowie_i_uroda", "s", "Zdrowie i uroda", "zdrowie_branze.html"),
    ("żywność_i_używki", "a", "Żywność i używki", "zywnosc_branze.html"),
]

def setup_driver():
    """Nastavení Chrome driveru - VIDITELNÝ prohlížeč"""
    chrome_options = Options()
    # NEPOUŽÍVÁM headless - prohlížeč bude viditelný!
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Skrij že je to Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def download_section(driver, section_code, section_letter, section_name, filename):
    """Stáhne HTML pro jednu sekci"""
    url = f"https://panoramafirm.pl/{section_code},{section_letter}/branze.html"
    
    print(f"\n📂 {section_name}")
    print(f"   URL: {url}")
    
    try:
        # Načíst stránku
        driver.get(url)
        
        # Počkat na načtení - čekat na div s id začínajícím na "letter-"
        print("   ⏳ Čekám na načtení stránky...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='letter-']")))
        
        # Extra pauza pro jistotu
        time.sleep(3)
        
        # Získat HTML
        html_content = driver.page_source
        
        # Uložit do souboru
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Rychlé spočítání kategorií
        letter_count = html_content.count('<div id="letter-')
        
        print(f"   ✅ Uloženo: {filename}")
        print(f"   📊 Písmen: {letter_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Chyba: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🌐 AUTOMATICKÉ STAHOVÁNÍ POMOCÍ SELENIUM (viditelný prohlížeč)")
    print("=" * 80)
    print("\n💡 Prohlížeč se otevře automaticky - neklikej do něj!")
    print("⏱️  Odhadovaný čas: 2-3 minuty")
    print()
    
    driver = setup_driver()
    
    try:
        downloaded = 0
        failed = []
        
        for i, (section_code, section_letter, section_name, filename) in enumerate(SECTIONS, 1):
            print(f"\n[{i}/{len(SECTIONS)}]", end=" ")
            
            success = download_section(driver, section_code, section_letter, section_name, filename)
            
            if success:
                downloaded += 1
            else:
                failed.append(section_name)
            
            # Pauza mezi požadavky (kromě poslední)
            if i < len(SECTIONS):
                wait_time = 3
                print(f"   💤 Pauza {wait_time}s...")
                time.sleep(wait_time)
        
        print("\n" + "=" * 80)
        print(f"📊 HOTOVO!")
        print(f"✅ Staženo: {downloaded}/{len(SECTIONS)} sekcí")
        if failed:
            print(f"❌ Selhalo: {len(failed)} sekcí: {', '.join(failed)}")
        print("=" * 80)
        
        print("\n🎯 DALŠÍ KROK:")
        print("   python process_manual_html.py")
        print()
        
    finally:
        print("\n🔒 Zavírám prohlížeč...")
        driver.quit()
        print("✅ Dokončeno!")

if __name__ == "__main__":
    main()
