#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test skript pro zjištění struktury aleo.com"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Inicializace prohlížeče
chrome_options = Options()
# chrome_options.add_argument('--headless')  # Zakomentováno pro debugging
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    print("Načítám https://www.aleo.com/firmy ...")
    driver.get("https://www.aleo.com/firmy")
    
    # Čekání na načtení obsahu (více času pro JS)
    print("Čekám na načtení JavaScriptu...")
    time.sleep(8)
    
    # Scroll dolů pro načtení lazy-loaded obsahu
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    # Uložení HTML pro analýzu
    with open('aleo_page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("✓ HTML uloženo do aleo_page_source.html")
    
    soup = BeautifulSoup(driver.page_source, 'lxml')
    
    # Hledání všech odkazů
    all_links = soup.find_all('a', href=True)
    print(f"\nCelkem odkazů: {len(all_links)}")
    
    # Analýza odkazů
    company_like_links = []
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Hledání odkazů, které vypadají jako profily firem
        if text and len(text) > 3 and href:
            if any(keyword in href.lower() for keyword in ['firma', 'company', 'detail', 'profil']):
                company_like_links.append({
                    'text': text[:50],
                    'href': href[:80],
                    'class': link.get('class', [])
                })
    
    print(f"\nPotenciální odkazy na firmy: {len(company_like_links)}")
    for i, link in enumerate(company_like_links[:10], 1):
        print(f"\n{i}. {link['text']}")
        print(f"   URL: {link['href']}")
        print(f"   Class: {link['class']}")
    
    # Hledání seznamů/divů s firmami
    print("\n" + "="*60)
    print("Hledání kontejnerů s firmami...")
    
    possible_containers = soup.find_all(['div', 'ul', 'section'], class_=True)
    for container in possible_containers[:20]:
        classes = ' '.join(container.get('class', []))
        if any(word in classes.lower() for word in ['company', 'firma', 'list', 'item', 'result']):
            print(f"\nKontejner: {container.name}")
            print(f"Class: {classes}")
            links_inside = container.find_all('a', href=True)
            print(f"Počet odkazů uvnitř: {len(links_inside)}")
            if links_inside:
                print(f"První odkaz: {links_inside[0].get_text(strip=True)[:40]}")

finally:
    driver.quit()
    print("\n✓ Test dokončen")
