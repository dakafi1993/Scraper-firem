"""
Scraper s undetected-chromedriver pro obejití Cloudflare
"""

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
import os
from datetime import datetime

OUTPUT_DIR = "output"
REQUEST_DELAY = 3

def setup_driver():
    """Nastavení undetected Chrome driveru"""
    print("🚀 Spouštím Chrome (undetected mode)...")
    options = uc.ChromeOptions()
    # options.add_argument('--headless')  # Nechte viditelné pro Cloudflare
    driver = uc.Chrome(options=options, version_main=131)  # Zkuste různé verze
    return driver

def scrape_category(driver, category_url, max_companies=10):
    """Prohledá kategorii"""
    print(f"\n📂 Kategorie: {category_url}")
    companies = []
    
    try:
        driver.get(category_url)
        
        print("\n⚠️  Pokud vidíte Cloudflare, klikněte checkbox...")
        print("Čekám 20 sekund na načtení...")
        time.sleep(20)
        
        # Scroll
        print("📜 Scrolluji...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Debug - uložit HTML
        with open('debug_undetected.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("💾 HTML uloženo: debug_undetected.html")
        
        # Najít odkazy
        company_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/pl/firma/' in href and '/firmy/' not in href:
                full_url = href if href.startswith('http') else f"https://aleo.com{href}"
                if full_url not in company_links and 'aleo.com' in full_url:
                    company_links.append(full_url)
        
        print(f"  ✅ Nalezeno: {len(company_links)} firem")
        
        if max_companies:
            company_links = company_links[:max_companies]
        
        # Zpracovat firmy
        for idx, url in enumerate(company_links, 1):
            print(f"\n  [{idx}/{len(company_links)}] {url}")
            
            try:
                driver.get(url)
                time.sleep(REQUEST_DELAY)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Název
                name = None
                for tag in ['h1', 'h2']:
                    h = soup.find(tag)
                    if h:
                        name = h.get_text(strip=True)
                        break
                
                if not name:
                    name = "Neznámá firma"
                
                print(f"    🏢 {name}")
                
                companies.append({
                    'název': name,
                    'url': url,
                    'kategorie': category_url
                })
                
            except Exception as e:
                print(f"    ❌ Chyba: {e}")
        
    except Exception as e:
        print(f"❌ Chyba: {e}")
    
    return companies

def main():
    url = "https://aleo.com/pl/firmy/artykuly-dla-biur-i-wyposazenie-biurowe"
    
    driver = setup_driver()
    
    try:
        companies = scrape_category(driver, url, max_companies=10)
        
        if companies:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            csv_file = os.path.join(OUTPUT_DIR, f'test_undetected_{timestamp}.csv')
            df = pd.DataFrame(companies)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            print(f"\n✅ Uloženo: {csv_file}")
            print(f"Nalezeno firem: {len(companies)}")
        else:
            print("\n❌ Žádné firmy")
            print("Zkontrolujte: debug_undetected.html")
    
    finally:
        input("\nStiskněte Enter pro zavření Chrome...")
        driver.quit()

if __name__ == "__main__":
    main()
