"""
Scraper s undetected-chromedriver - lepší bypass Cloudflare
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

def main():
    url = "https://aleo.com/pl/firmy/artykuly-dla-biur-i-wyposazenie-biurowe"
    
    print("🚀 Spouštím undetected Chrome...")
    
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    
    # Automatická detekce Chrome verze
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        print(f"\n📂 Načítám: {url}")
        driver.get(url)
        
        # Čekání na možnou Cloudflare
        print("\n⏳ Čekám 15 sekund na automatické vyřešení Cloudflare...")
        time.sleep(15)
        
        # Pokud je stále Cloudflare, čekáme na manuální řešení
        if "cloudflare" in driver.page_source.lower() or "challenge" in driver.page_source.lower():
            print("\n⚠️  CLOUDFLARE stále aktivní - vyřešte manuálně")
            print("Čekám 60 sekund...")
            time.sleep(60)
        
        print("\n⏳ Čekám dalších 10 sekund na načtení dat...")
        time.sleep(10)
        
        # Scrollování
        print("📜 Scrolluji stránku...")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Hledání odkazů pomocí Selenium
        print("\n🔍 Hledám odkazy na firmy...")
        
        # Metoda 1: Pomocí CSS selektoru
        try:
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/pl/firma/']")
            print(f"  ✅ CSS selector našel: {len(links)} odkazů")
            
            firma_links = []
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and '/pl/firma/' in href and '/pl/firmy/' not in href:
                        if href not in firma_links:
                            firma_links.append(href)
                            print(f"    • {text[:50] if text else 'N/A'}: {href}")
                except:
                    continue
            
            print(f"\n✅ Celkem unikátních firem: {len(firma_links)}")
            
        except Exception as e:
            print(f"❌ Chyba: {e}")
        
        # Metoda 2: XPath
        try:
            print("\n🔍 Zkouším XPath...")
            xpath_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/pl/firma/')]")
            print(f"  ✅ XPath našel: {len(xpath_links)} odkazů")
        except Exception as e:
            print(f"  ⚠️  XPath chyba: {e}")
        
        # Uložení HTML
        html = driver.page_source
        with open('undetected_html.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\n💾 HTML uloženo: undetected_html.html")
        
        # Regex v HTML
        firma_regex = re.findall(r'href=["\']([^"\']*?/pl/firma/[^"\']*?)["\']', html)
        print(f"\n🔍 Regex v HTML našel: {len(set(firma_regex))} odkazů")
        
        # Screenshot
        driver.save_screenshot('screenshot.png')
        print("📸 Screenshot uložen: screenshot.png")
        
    finally:
        print("\n⏸️  Browser zůstane otevřený - zkontrolujte, co vidíte")
        print("Stiskněte Enter pro zavření...")
        input()
        driver.quit()

if __name__ == "__main__":
    main()
