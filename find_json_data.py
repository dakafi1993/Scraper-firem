"""
Hledání JSON dat přímo v HTML stránky
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import json

def setup_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def wait_for_cloudflare(driver):
    print("\n⚠️  CLOUDFLARE - Klikněte na checkbox")
    start_time = time.time()
    while time.time() - start_time < 120:
        if "cloudflare" not in driver.page_source.lower():
            print("✅ Cloudflare vyřešena!")
            return True
        time.sleep(1)
    return False

def main():
    url = "https://aleo.com/pl/firmy/artykuly-dla-biur-i-wyposazenie-biurowe"
    
    driver = setup_driver()
    
    try:
        print(f"📂 Načítám: {url}")
        driver.get(url)
        
        if "cloudflare" in driver.page_source.lower():
            if not wait_for_cloudflare(driver):
                return
        
        print("\n⏳ Čekám 10 sekund...")
        time.sleep(10)
        
        # Scrollování
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        html = driver.page_source
        
        # Hledání JSON dat v HTML
        print("\n🔍 Hledám JSON data v HTML...")
        
        # Pattern 1: <script type="application/json">
        json_scripts = re.findall(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"  📦 Nalezeno {len(json_scripts)} JSON scriptů")
        
        # Pattern 2: window.__DATA__ = {...}
        window_data = re.findall(r'window\.__\w+__\s*=\s*(\{.*?\});', html, re.DOTALL)
        print(f"  📦 Nalezeno {len(window_data)} window.__DATA__ objektů")
        
        # Pattern 3: Hledání odkazů /pl/firma/
        firma_links = re.findall(r'href=["\']([^"\']*?/pl/firma/[^"\']*?)["\']', html)
        print(f"  🔗 Nalezeno {len(firma_links)} odkazů /pl/firma/")
        
        # Výpis prvních 10 odkazů
        if firma_links:
            print("\n✅ Nalezené odkazy na firmy:")
            unique_links = list(set(firma_links))[:10]
            for link in unique_links:
                print(f"  • {link}")
        
        # Uložení HTML pro analýzu
        with open('full_html_after_wait.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\n💾 HTML uloženo: full_html_after_wait.html")
        
        # Hledání všech <a> tagů pomocí Selenium
        print("\n🔍 Hledám <a> tagy pomocí Selenium...")
        links = driver.find_elements("tag name", "a")
        firma_selenium_links = []
        
        for link in links:
            try:
                href = link.get_attribute('href')
                if href and '/pl/firma/' in href and '/pl/firmy/' not in href:
                    firma_selenium_links.append(href)
            except:
                continue
        
        print(f"  ✅ Selenium našel {len(firma_selenium_links)} odkazů na firmy")
        
        if firma_selenium_links:
            print("\nPrvních 10 odkazů (Selenium):")
            for link in list(set(firma_selenium_links))[:10]:
                print(f"  • {link}")
        
    finally:
        print("\n🔒 Zavírám browser za 5 sekund...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()
