"""
Debug - uloží HTML po Cloudflare pro analýzu
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def setup_driver():
    options = Options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

print("🔍 DEBUG - Analyzuji HTML PO Cloudflare")
print("=" * 60)

driver = setup_driver()

try:
    url = "https://aleo.com/pl/firmy/artykuly-dla-biur-i-wyposazenie-biurowe"
    print(f"📂 URL: {url}")
    
    driver.get(url)
    
    print("\n⚠️  VYŘEŠTE CLOUDFLARE CHECKBOX!")
    print("Čekám 30 sekund...")
    time.sleep(30)
    
    # Scroll
    print("\n📜 Scrolluji...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    print("\n💾 Ukládám HTML...")
    html = driver.page_source
    
    with open('after_cloudflare.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Uloženo: after_cloudflare.html")
    
    # Analýza
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\n" + "=" * 60)
    print("ANALÝZA ODKAZŮ:")
    print("=" * 60)
    
    all_links = soup.find_all('a', href=True)
    print(f"\nCelkem odkazů: {len(all_links)}")
    
    # Hledat různé patterny
    patterns = {
        '/pl/firma/': [],
        '/firma/': [],
        'company': [],
        'firmy': []
    }
    
    for link in all_links:
        href = link['href']
        text = link.get_text(strip=True)[:50]
        
        for pattern in patterns:
            if pattern in href.lower():
                patterns[pattern].append((href, text))
    
    for pattern, links in patterns.items():
        print(f"\n📌 Pattern '{pattern}': {len(links)} odkazů")
        for href, text in links[:5]:
            print(f"  • {href}")
            if text:
                print(f"    Text: {text}")
    
    print("\n" + "=" * 60)
    print("PRVNÍCH 20 ODKAZŮ:")
    print("=" * 60)
    for i, link in enumerate(all_links[:20], 1):
        print(f"{i}. {link['href']}")
        text = link.get_text(strip=True)
        if text:
            print(f"   Text: {text[:60]}")
    
    print("\n✅ Zkontrolujte soubor: after_cloudflare.html")
    print("Hledejte v něm odkaz na JAKOUKOLIV firmu a napište mi pattern!")
    
finally:
    input("\nStiskněte Enter pro zavření...")
    driver.quit()
