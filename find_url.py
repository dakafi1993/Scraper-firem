#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aleo.com URL Finder - Pomůže najít správnou URL se seznamem firem
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

print("""
╔═══════════════════════════════════════════════════════════╗
║     ALEO.COM URL FINDER - Hledání správné URL             ║
╚═══════════════════════════════════════════════════════════╝

NÁVOD:
1. Otevře se Chrome prohlížeč
2. RUČNĚ přejděte na aleo.com a najděte seznam firem
3. Vyřešte Cloudflare CAPTCHA
4. Zkopírujte URL adresu ze stránky se seznamem firem
5. Použijte tuto URL ve scraperu

""")

input("Stiskněte ENTER pro spuštění prohlížeče...")

# Inicializace prohlížeče
chrome_options = Options()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    print("\n✓ Prohlížeč spuštěn")
    print("\n📋 ÚKOLY:")
    print("1. Přejděte na https://aleo.com nebo https://aleo.com/int/")
    print("2. Najděte kategorii nebo seznam firem")
    print("3. Klikněte na nějakou kategorii (např. 'Companies', 'Directory', 'Seznam firem')")
    print("4. Vyřešte Cloudflare CAPTCHA pokud se zobrazí")
    print("5. Zkopírujte URL ze stránky se seznamem firem")
    
    driver.get("https://aleo.com/int/")
    
    print("\n⏳ Prohlížeč je otevřený...")
    print("   Najděte stránku se SEZNAMEM FIREM a zkopírujte URL")
    
    url = input("\n📎 Vložte URL adresu: ").strip()
    
    if url:
        print(f"\n✓ URL zkopírována: {url}")
        print("\nNyní zkouším načíst stránku a analyzovat...")
        
        driver.get(url)
        time.sleep(10)
        
        # Scroll
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        all_links = soup.find_all('a', href=True)
        
        print(f"\n📊 ANALÝZA STRÁNKY:")
        print(f"   Celkem odkazů: {len(all_links)}")
        
        # Hledání vzorů
        unique_hrefs = set()
        company_patterns = []
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if href and text and len(text) > 3:
                if href not in unique_hrefs:
                    unique_hrefs.add(href)
                    
                    # Hledat vzory, které by mohly být firmy
                    if any(kw in href.lower() for kw in ['/company/', '/firma/', '/detail/', '/profile/']):
                        company_patterns.append({
                            'text': text[:60],
                            'href': href[:80]
                        })
        
        if company_patterns:
            print(f"\n✓ Našel jsem {len(company_patterns)} potenciálních firem!")
            print("\nPrvních 10:")
            for i, comp in enumerate(company_patterns[:10], 1):
                print(f"{i:2}. {comp['text']}")
                print(f"    → {comp['href']}")
            
            print(f"\n💡 DOPORUČENÍ:")
            print(f"   Použijte tento příkaz:")
            print(f'   python aleo_scraper_int.py --url "{url}" --max 20')
        else:
            print("\n⚠️  Nenašel jsem jednoznačný vzor firem")
            print("\n   Zobrazuji prvních 20 odkazů:")
            
            shown = []
            for link in all_links[:50]:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if text and len(text) > 5 and href not in shown:
                    print(f"   • {text[:50]} → {href[:50]}")
                    shown.append(href)
                    if len(shown) >= 20:
                        break
            
            print("\n💡 TIPY:")
            print("   1. Zkuste jinou stránku/kategorii")
            print("   2. Hledejte stránku s názvem 'Companies', 'Directory', 'Seznam'")
            print("   3. Možná aleo.com/int/ nemá veřejný seznam firem")
            print("   4. Zkuste použít email_finder.py s vlastním seznamem")
        
        # Uložit HTML
        with open('aleo_page_analysis.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"\n💾 HTML uloženo do: aleo_page_analysis.html")
    
finally:
    input("\nStiskněte ENTER pro zavření prohlížeče...")
    driver.quit()
    print("\n✓ Hotovo!")
