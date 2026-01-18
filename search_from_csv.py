#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hledá weby a emaily pro firmy z CSV (bez scraping aleo.com)
"""

import argparse
import pandas as pd
import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# Email regex
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

def setup_driver():
    """Nastavení Chrome driveru"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def google_search_website(driver, company_name):
    """Najde web firmy přes Google search (Selenium)"""
    try:
        short_name = company_name.split('SPÓŁKA')[0].strip()
        short_name = short_name.split(' SP.')[0].strip()
        short_name = short_name.split(' S.A.')[0].strip()
        
        query = f"{short_name} Poland"
        
        print(f"    🔍 Google: {query}")
        
        # Otevřít Google
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=pl"
        driver.get(url)
        time.sleep(3)
        
        # Získat HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Hledat linky
        links = soup.find_all('a')
        
        for link in links:
            href = link.get('href', '')
            
            # Google redirect pattern
            if '/url?q=' in href:
                match = re.search(r'/url\?q=([^&]+)', href)
                if match:
                    found_url = requests.utils.unquote(match.group(1))
                    
                    # Filtrovat nesmysly
                    skip_domains = ['google.', 'facebook.', 'linkedin.', 'wikipedia.', 'aleo.com', 'youtube.']
                    if not any(skip in found_url.lower() for skip in skip_domains):
                        if found_url.startswith('http'):
                            print(f"    🌐 Web: {found_url}")
                            return found_url
            
            # Přímý link
            elif href.startswith('http'):
                skip_domains = ['google.', 'facebook.', 'linkedin.', 'wikipedia.', 'aleo.com', 'youtube.']
                if not any(skip in href.lower() for skip in skip_domains):
                    print(f"    🌐 Web: {href}")
                    return href
        
        return None
        
    except Exception as e:
        print(f"    ⚠️  Chyba: {str(e)[:50]}")
        return None

def google_search_email(driver, company_name):
    """Hledá email přes Google (Selenium)"""
    try:
        short_name = company_name.split('SPÓŁKA')[0].strip()
        short_name = short_name.split(' SP.')[0].strip()
        short_name = short_name.split(' S.A.')[0].strip()
        
        query = f"{short_name} email kontakt Poland"
        
        print(f"    📧 Google email: {query}")
        
        # Otevřít Google
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=pl"
        driver.get(url)
        time.sleep(3)
        
        # Hledat emaily v HTML
        emails = EMAIL_PATTERN.findall(driver.page_source)
        
        for email in emails:
            # Filtrovat nesmysly
            skip = ['google.com', 'example.com', 'noreply', 'test@', '@gstatic']
            if not any(s in email.lower() for s in skip):
                print(f"    ✅ Email: {email}")
                return email
        
        return None
        
    except Exception as e:
        print(f"    ⚠️  Chyba: {str(e)[:50]}")
        return None

def find_email_on_website(url):
    """Hledá email na webu firmy"""
    if not url:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        pages = [
            url,
            f"{url}/kontakt",
            f"{url}/contact",
            f"{url}/kontakty",
            f"{url}/o-nas"
        ]
        
        for page_url in pages:
            try:
                response = requests.get(page_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()
                    
                    emails = EMAIL_PATTERN.findall(text)
                    
                    for email in emails:
                        if not any(skip in email.lower() for skip in 
                            ['example.', 'test@', 'noreply', 'wix.com', 'domain.']):
                            return email
            except:
                continue
        
        return None
    except:
        return None

def main():
    parser = argparse.ArgumentParser(description='Hledá weby a emaily z CSV')
    parser.add_argument('--input', type=str, required=True, help='Vstupní CSV s názvy firem')
    parser.add_argument('--column', type=str, default='company_name', help='Název sloupce s názvy firem')
    parser.add_argument('--max', type=int, default=None, help='Max počet firem ke zpracování')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔍 GOOGLE SEARCH PRO FIRMY Z CSV")
    print("="*60)
    print(f"\n📂 CSV: {args.input}")
    print(f"📋 Sloupec: {args.column}")
    if args.max:
        print(f"⚙️  Max firem: {args.max}")
    
    # Načíst CSV
    try:
        df = pd.read_csv(args.input)
        print(f"✅ Načteno: {len(df)} řádků")
    except Exception as e:
        print(f"❌ Chyba načítání CSV: {e}")
        return
    
    if args.column not in df.columns:
        print(f"❌ Sloupec '{args.column}' nenalezen v CSV!")
        print(f"Dostupné sloupce: {', '.join(df.columns)}")
        return
    
    # Filtrovat
    companies = df[args.column].dropna().tolist()
    
    if args.max:
        companies = companies[:args.max]
    
    print(f"\n🚀 Zpracovávám {len(companies)} firem...\n")
    
    # Setup driver
    driver = setup_driver()
    
    results = []
    
    try:
        for idx, company_name in enumerate(companies, 1):
            print(f"[{idx}/{len(companies)}] {company_name}")
            
            website = None
            email = None
            
            # PRIORITA 1: Google search pro web
            website = google_search_website(driver, company_name)
            
            # PRIORITA 2: Email z webu
            if website:
                print(f"    📧 Hledám email na webu...")
                email = find_email_on_website(website)
                if email:
                    print(f"    ✅ Email z webu: {email}")
            
            # PRIORITA 3: Email z Google
            if not email:
                email = google_search_email(driver, company_name)
            
            if email:
                print(f"    ✅ Kompletní!")
            else:
                print(f"    ⚠️  Email nenalezen")
            
            results.append({
                'name': company_name,
                'website': website or '',
                'email': email or ''
            })
            
            print()
            time.sleep(2)
        
    finally:
        driver.quit()
    
    # Uložit výsledky
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_csv = f'output/search_results_{timestamp}.csv'
    output_xlsx = f'output/search_results_{timestamp}.xlsx'
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_csv, index=False, encoding='utf-8-sig')
    df_results.to_excel(output_xlsx, index=False)
    
    print("\n" + "="*60)
    print("📊 STATISTIKY")
    print("="*60)
    print(f"Celkem firem: {len(results)}")
    print(f"S webem: {sum(1 for r in results if r['website'])}")
    print(f"S emailem: {sum(1 for r in results if r['email'])}")
    print(f"\n💾 Uloženo:")
    print(f"  • {output_csv}")
    print(f"  • {output_xlsx}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
