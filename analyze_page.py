"""
Analyzuje HTML strukturu stránky s firmami
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

print("🔍 ANALYZUJI STRUKTURU ALEO.COM")
print("=" * 60)

driver = setup_driver()

try:
    url = "https://aleo.com/pl/firmy/artykuly-dla-biur-i-wyposazenie-biurowe"
    print(f"\n📂 URL: {url}")
    
    driver.get(url)
    print("\n⚠️  Vyřešte Cloudflare checkbox...")
    time.sleep(15)  # Čas na vyřešení Cloudflare
    
    print("\n📄 Analyzuji HTML...")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Uložit HTML pro inspekci
    with open('page_structure.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("✅ HTML uloženo do: page_structure.html")
    
    # Hledat všechny odkazy
    print("\n🔗 VŠECHNY ODKAZY (prvních 50):")
    print("-" * 60)
    links = soup.find_all('a', href=True)[:50]
    for i, link in enumerate(links, 1):
        href = link['href']
        text = link.get_text(strip=True)[:50]
        print(f"{i}. {href}")
        if text:
            print(f"   Text: {text}")
    
    # Hledat odkazy s /pl/firma/
    print(f"\n🎯 ODKAZY s '/pl/firma/':")
    print("-" * 60)
    company_links = [a for a in soup.find_all('a', href=True) if '/pl/firma/' in a['href']]
    print(f"Nalezeno: {len(company_links)}")
    for link in company_links[:10]:
        print(f"  • {link['href']}")
        print(f"    Text: {link.get_text(strip=True)}")
    
    # Hledat různé CSS třídy
    print(f"\n📋 ELEMENTY s class obsahující 'company' nebo 'firma':")
    print("-" * 60)
    elements = soup.find_all(class_=lambda x: x and ('company' in x.lower() or 'firma' in x.lower()))
    print(f"Nalezeno: {len(elements)}")
    for elem in elements[:10]:
        print(f"  • Tag: {elem.name}, Class: {elem.get('class')}")
        print(f"    Text: {elem.get_text(strip=True)[:80]}")
    
    # Hledat seznamy
    print(f"\n📝 UL/OL SEZNAMY:")
    print("-" * 60)
    lists = soup.find_all(['ul', 'ol'])
    for i, lst in enumerate(lists[:5], 1):
        items = lst.find_all('li')
        print(f"{i}. {lst.name} - {len(items)} položek, class: {lst.get('class')}")
        if items:
            print(f"   První položka: {items[0].get_text(strip=True)[:60]}")
    
    print("\n✅ Analýza dokončena!")
    print("Podívejte se do page_structure.html pro detaily")
    
finally:
    driver.quit()
