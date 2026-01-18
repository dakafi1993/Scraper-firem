#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test skript pro analýzu struktury aleo.com/int/
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

chrome_options = Options()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    print("📋 Načítám https://aleo.com/int/ ...")
    driver.get("https://aleo.com/int/")
    
    # Čekání na Cloudflare
    print("⏳ Čekám na načtení (10s)...")
    time.sleep(10)
    
    # Scroll
    print("📜 Scrolluji...")
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    # Uložení HTML
    with open('aleo_int_debug.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("✓ HTML uloženo do aleo_int_debug.html")
    
    soup = BeautifulSoup(driver.page_source, 'lxml')
    
    # Analýza
    print("\n" + "="*60)
    print("ANALÝZA STRÁNKY")
    print("="*60)
    
    all_links = soup.find_all('a', href=True)
    print(f"\nCelkem odkazů: {len(all_links)}")
    
    # Skupina podle vzoru
    int_links = []
    other_links = []
    
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        if '/int/' in href and href.count('/') >= 3:
            int_links.append({
                'text': text[:60],
                'href': href[:80],
                'levels': href.count('/')
            })
        else:
            other_links.append({
                'text': text[:60],
                'href': href[:80]
            })
    
    print(f"\nOdkazy s /int/: {len(int_links)}")
    print("\nPrvních 20 /int/ odkazů:")
    for i, link in enumerate(int_links[:20], 1):
        print(f"{i:2}. [{link['levels']} úrovní] {link['text']}")
        print(f"    → {link['href']}")
    
    # Hledání kontejnerů
    print("\n" + "="*60)
    print("HLEDÁNÍ KONTEJNERŮ S FIRMAMI")
    print("="*60)
    
    # Různé možné CSS třídy
    for class_pattern in ['company', 'firma', 'card', 'item', 'list', 'result', 'business']:
        containers = soup.find_all(class_=lambda x: x and class_pattern in x.lower() if x else False)
        if containers:
            print(f"\n✓ Nalezeno {len(containers)} kontejnerů s třídou obsahující '{class_pattern}'")
            for i, cont in enumerate(containers[:3], 1):
                classes = ' '.join(cont.get('class', []))
                print(f"  {i}. Class: {classes[:60]}")
                text = cont.get_text(strip=True)[:100]
                print(f"     Text: {text}")
    
    # Hledání podle tagů
    print("\n" + "="*60)
    print("ANALÝZA STRUKTURY")
    print("="*60)
    
    for tag in ['article', 'section', 'div']:
        elements = soup.find_all(tag, class_=True)
        if elements:
            print(f"\n{tag.upper()} s CSS třídami: {len(elements)}")
            # Ukázka prvních
            for elem in elements[:5]:
                classes = ' '.join(elem.get('class', []))
                if len(classes) > 10:
                    print(f"  • {classes[:70]}")

finally:
    print("\n✓ Zavírám prohlížeč...")
    driver.quit()
    print("\n💡 TIP: Prohlédněte si aleo_int_debug.html a najděte opakující se vzor pro firmy")
