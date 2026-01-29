"""
Stažení pouze sekce Kancelaria s delšími timeouty
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    """Nastavení Chrome driveru"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # Přidáme více stability
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def download_kancelaria():
    """Stáhne sekci Kancelaria"""
    
    url = 'https://panoramafirm.pl/kancelaria,d/branze.html'
    filename = 'kancelaria_branze.html'
    
    print("="*70)
    print("📥 STAHOVÁNÍ SEKCE: Kancelaria")
    print("="*70)
    print(f"🔗 URL: {url}")
    print(f"💾 Soubor: {filename}")
    print()
    
    driver = setup_driver()
    
    try:
        print("🌐 Načítám stránku...")
        driver.get(url)
        
        # DELŠÍ timeout - 30 sekund
        print("⏳ Čekám na načtení kategorií (timeout 30s)...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[id^="letter-"]'))
        )
        
        # Spočítáme písmena
        letter_divs = driver.find_elements(By.CSS_SELECTOR, 'div[id^="letter-"]')
        print(f"✅ Nalezeno {len(letter_divs)} písmen s kategoriemi")
        
        # Počkáme ještě 5 sekund pro jistotu
        print("⏳ Čekám dalších 5 sekund pro kompletní načtení...")
        time.sleep(5)
        
        # Uložíme HTML
        html_content = driver.page_source
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print()
        print("="*70)
        print("✅ ÚSPĚŠNĚ STAŽENO!")
        print("="*70)
        print(f"💾 Soubor: {filename}")
        print(f"📊 Velikost: {len(html_content):,} bytů")
        print(f"📝 Počet písmen: {len(letter_divs)}")
        print()
        print("🔜 DALŠÍ KROK:")
        print("   python process_manual_html.py")
        print("="*70)
        
        return True
        
    except Exception as e:
        print()
        print("="*70)
        print("❌ CHYBA PŘI STAHOVÁNÍ")
        print("="*70)
        print(f"Chyba: {str(e)}")
        print()
        print("💡 ŘEŠENÍ:")
        print("   1. Zkuste to znovu")
        print("   2. Nebo stáhněte ručně:")
        print(f"      Otevřete: {url}")
        print(f"      Ctrl+S → Uložte jako: {filename}")
        print("="*70)
        return False
        
    finally:
        driver.quit()
        print("\n🔒 Prohlížeč uzavřen")

if __name__ == '__main__':
    download_kancelaria()
