#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jednoduchý Email Finder - Hledá emaily firem na jejich webech
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
from pathlib import Path

def extract_email(text):
    """Najde email v textu"""
    if not text:
        return None
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    if emails:
        return emails[0]
    return None

def find_company_website(company_name, driver):
    """Pokusí se najít web společnosti"""
    print(f"   🔎 Hledám web pro: {company_name}")
    
    # Vyčistit název
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', company_name).strip().lower()
    words = clean.split()[:3]  # První 3 slova
    base_name = ''.join(words)
    
    # Možné URLs
    urls_to_try = [
        f"https://www.{base_name}.com",
        f"https://{base_name}.com",
        f"https://www.{base_name}.cz",
        f"https://www.{base_name}.eu"
    ]
    
    for url in urls_to_try:
        try:
            driver.set_page_load_timeout(10)
            driver.get(url)
            time.sleep(2)
            
            # Zkontrolovat, že stránka existuje
            if "404" not in driver.title.lower() and len(driver.page_source) > 1000:
                print(f"   ✓ Nalezen web: {url}")
                return url
        except:
            continue
    
    print(f"   ✗ Web nenalezen")
    return None

def find_email_on_website(url, driver):
    """Hledá email na webu"""
    try:
        print(f"   📄 Procházím: {url}")
        driver.get(url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Zkusit najít kontaktní stránku
        contact_links = soup.find_all('a', href=True, text=re.compile(r'contact|kontakt|о нас', re.I))
        
        if contact_links:
            contact_href = contact_links[0]['href']
            if not contact_href.startswith('http'):
                from urllib.parse import urljoin
                contact_href = urljoin(url, contact_href)
            
            print(f"   📞 Našel jsem kontakty: {contact_href}")
            driver.get(contact_href)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Hledat email
        text = soup.get_text()
        email = extract_email(text)
        
        if email:
            print(f"   ✓ Email nalezen: {email}")
            return email
        else:
            print(f"   ✗ Email nenalezen")
            return None
            
    except Exception as e:
        print(f"   ⚠️ Chyba: {e}")
        return None

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║           EMAIL FINDER - Hledač emailů firem              ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Načtení seznamu firem
    print("\n📋 Zadejte seznam firem:")
    print("   Formát: Jeden název na řádek, prázdný řádek = konec")
    print("   Nebo napište 'csv' pro načtení z CSV souboru\n")
    
    first_line = input(">>> ").strip()
    
    companies = []
    
    if first_line.lower() == 'csv':
        csv_file = input("Cesta k CSV souboru: ").strip()
        try:
            df = pd.read_csv(csv_file)
            # Hledat sloupec s názvy
            name_col = None
            for col in df.columns:
                if 'name' in col.lower() or 'název' in col.lower() or 'firma' in col.lower():
                    name_col = col
                    break
            
            if name_col:
                companies = df[name_col].dropna().tolist()
                print(f"✓ Načteno {len(companies)} firem z CSV")
            else:
                print("❌ Nenalezen sloupec s názvy firem!")
                return
        except Exception as e:
            print(f"❌ Chyba při načítání CSV: {e}")
            return
    else:
        companies.append(first_line)
        while True:
            line = input(">>> ").strip()
            if not line:
                break
            companies.append(line)
    
    if not companies:
        print("❌ Žádné firmy k zpracování!")
        return
    
    print(f"\n✓ Celkem {len(companies)} firem k zpracování")
    
    # Inicializace prohlížeče
    print("\n🚀 Spouštím prohlížeč...")
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Odkomentovat pro běh na pozadí
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    results = []
    
    try:
        print("\n" + "="*60)
        print("ZAČÍNÁM HLEDÁNÍ EMAILŮ")
        print("="*60 + "\n")
        
        for i, company in enumerate(companies, 1):
            print(f"[{i}/{len(companies)}] {company}")
            
            result = {
                'název_firmy': company,
                'web': None,
                'email': None,
                'zdroj': 'Nenalezeno'
            }
            
            # Pokus 1: Najít web
            website = find_company_website(company, driver)
            
            if website:
                result['web'] = website
                
                # Pokus 2: Najít email na webu
                email = find_email_on_website(website, driver)
                
                if email:
                    result['email'] = email
                    result['zdroj'] = 'Web společnosti'
            
            results.append(result)
            time.sleep(2)  # Prodleva
            print()
        
        # Uložení výsledků
        print("\n" + "="*60)
        print("💾 UKLÁDÁM VÝSLEDKY")
        print("="*60)
        
        df = pd.DataFrame(results)
        
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_path = output_dir / f'email_finder_{timestamp}.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✓ CSV: {csv_path}")
        
        excel_path = output_dir / f'email_finder_{timestamp}.xlsx'
        df.to_excel(excel_path, index=False)
        print(f"✓ Excel: {excel_path}")
        
        # Statistiky
        total = len(results)
        found = sum(1 for r in results if r['email'])
        
        print(f"\n📊 STATISTIKY:")
        print(f"   Celkem: {total}")
        print(f"   Nalezeno: {found}")
        print(f"   Nenalezeno: {total - found}")
        print(f"   Úspěšnost: {found/total*100:.1f}%")
        
    finally:
        driver.quit()
        print("\n✓ Hotovo!")

if __name__ == "__main__":
    main()
