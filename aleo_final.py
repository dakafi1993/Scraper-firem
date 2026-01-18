"""
KOMPLETNÍ ALEO.COM SCRAPER
1. Získá názvy firem z aleo.com kategorií
2. Najde jejich weby přes Google search
3. Najde emaily na webech nebo přes Google
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import argparse

# === KONFIGURACE ===
OUTPUT_DIR = "output"
MAX_CLOUDFLARE_WAIT = 120
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

def create_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

def wait_for_cloudflare(driver):
    print("\n⚠️  CLOUDFLARE DETEKOVÁNA!")
    print("="*60)
    print("KLIKNĚTE NA CHECKBOX 'Verify you are human'")
    print(f"Čekám max. {MAX_CLOUDFLARE_WAIT} sekund...")
    print("="*60)
    
    start_time = time.time()
    while time.time() - start_time < MAX_CLOUDFLARE_WAIT:
        if "cloudflare" not in driver.page_source.lower() and "challenge" not in driver.page_source.lower():
            print("✅ Cloudflare vyřešena!")
            return True
        time.sleep(1)
    
    return False

def extract_company_names(driver, category_url, max_companies):
    """Krok 1: Extrakce názvů firem z aleo.com"""
    print(f"\n📂 Kategorie: {category_url}")
    
    driver.get(category_url)
    
    if "cloudflare" in driver.page_source.lower():
        if not wait_for_cloudflare(driver):
            return []
    
    print("  ⏳ Načítám firmy...")
    time.sleep(5)
    
    # Scrollování pro načtení všech firem
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    companies = []
    
    try:
        elements = driver.find_elements(By.CLASS_NAME, "catalog-row-first-line__company-name")
        print(f"  ✅ Nalezeno {len(elements)} firem")
        
        for elem in elements[:max_companies]:
            try:
                name = elem.text.strip()
                if name and len(name) > 2:
                    companies.append(name)
            except:
                continue
    except Exception as e:
        print(f"  ❌ Chyba: {str(e)}")
    
    return list(dict.fromkeys(companies))  # Odstranění duplikátů

def search_google_maps(driver, company_name):
    """Hledá firmu na Google Maps a získá kontakty"""
    try:
        short_name = company_name.split('SPÓŁKA')[0].strip()
        short_name = short_name.split(' SP.')[0].strip()
        
        print(f"    🗺️  Google Maps: {short_name}")
        
        # Otevřít Google Maps
        maps_url = f"https://www.google.com/maps/search/{requests.utils.quote(short_name + ' Poland')}"
        driver.get(maps_url)
        time.sleep(6)  # Delší čekání pro Maps
        
        result = {'website': None, 'email': None, 'phone': None}
        
        try:
            # Prostě kliknout na první výsledek - zjednodušeně
            try:
                # Různé možné selektory pro první výsledek
                selectors = [
                    "a[href*='maps/place']",
                    "div[role='article'] a",
                    ".Nv2PK a"
                ]
                
                clicked = False
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            elements[0].click()
                            clicked = True
                            time.sleep(4)
                            break
                    except:
                        continue
                
                if not clicked:
                    print(f"    ⚠️  Nenalezen výsledek v Maps")
                    return result
                
            except Exception as e:
                print(f"    ⚠️  Klik chyba: {str(e)[:50]}")
                return result
            
            # Získat HTML po kliknutí
            page_source = driver.page_source
            
            # Hledat web - jednodušší regex
            urls = re.findall(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s"<>]*)?', page_source)
            
            for url in urls:
                # Filtrovat Google domény
                if not any(skip in url.lower() for skip in 
                    ['google.', 'gstatic.', 'googleapis.', 'facebook.', 'instagram.', 'twitter.', 'youtube.']):
                    result['website'] = url
                    print(f"    🌐 Web z Maps: {url}")
                    break
            
            # Hledat email
            emails = EMAIL_PATTERN.findall(page_source)
            for email in emails:
                if not any(skip in email.lower() for skip in 
                    ['google.', 'example.', 'test@', 'noreply', '@gstatic', '.png', '.jpg']):
                    result['email'] = email
                    print(f"    ✅ Email z Maps: {email}")
                    break
            
        except Exception as e:
            print(f"    ⚠️  Maps parse chyba: {str(e)[:50]}")
        
        return result
        
    except Exception as e:
        print(f"    ⚠️  Maps chyba: {str(e)[:50]}")
        return {'website': None, 'email': None, 'phone': None}

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
    """Najde email firmy přes Google (Selenium)"""
    try:
        short_name = company_name.split('SPÓŁKA')[0].strip()
        short_name = short_name.split(' SP.')[0].strip()
        
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
            skip = ['google.', 'youtube.', 'example.', 'noreply', 'privacy', '.png', '.jpg', '@gstatic']
            if not any(skip in email.lower() for skip in skip):
                print(f"    ✅ Email: {email}")
                return email
        
        return None
        
    except Exception as e:
        print(f"    ⚠️  Chyba: {str(e)[:50]}")
        return None

def find_email_on_website(url):
    """Krok 3b: Hledá email přímo na webu firmy"""
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

def scrape_category(driver, category_url, max_companies):
    """Zpracuje jednu kategorii - kompletní workflow"""
    
    # KROK 1: Získat názvy firem z aleo.com
    company_names = extract_company_names(driver, category_url, max_companies)
    
    if not company_names:
        print("  ❌ Žádné firmy nenalezeny")
        return []
    
    print(f"\n✅ Nalezeno {len(company_names)} firem, zpracovávám...")
    
    results = []
    
    # KROK 2 & 3: Pro každou firmu najít web a email
    for idx, company_name in enumerate(company_names, 1):
        print(f"\n  [{idx}/{len(company_names)}] {company_name}")
        
        website = None
        email = None
        phone = None
        
        # PRIORITA 1: Google search pro web
        website = google_search_website(driver, company_name)
        
        # PRIORITA 2: Email z webu nebo z Google
        if website:
            print(f"    📧 Hledám email na webu...")
            email = find_email_on_website(website)
            if email:
                print(f"    ✅ Email z webu: {email}")
        
        # PRIORITA 3: Pokud není email, zkus Google
        if not email:
            email = google_search_email(driver, company_name)
        
        if email:
            print(f"    ✅ Kompletní!")
        else:
            print(f"    ⚠️  Email nenalezen")
        
        results.append({
            'name': company_name,
            'website': website or '',
            'email': email or '',
            'phone': phone or '',
            'category': category_url
        })
        
        # Pauza mezi firmami
        time.sleep(2)
    
    return results

def main(categories, max_companies_per_category):
    print("\n" + "="*60)
    print("🚀 KOMPLETNÍ ALEO.COM SCRAPER")
    print("="*60)
    
    all_results = []
    driver = setup_driver()
    
    try:
        print(f"\n✅ Kategorie: {len(categories)}")
        for cat in categories:
            print(f"  • {cat}")
        
        print(f"\n⚙️  Limit: {max_companies_per_category} firem/kategorii")
        print("🚀 Spouštím Chrome...")
        
        for idx, category_url in enumerate(categories, 1):
            print(f"\n{'='*60}")
            print(f"KATEGORIE {idx}/{len(categories)}")
            print("="*60)
            
            results = scrape_category(driver, category_url, max_companies_per_category)
            all_results.extend(results)
            
            if idx < len(categories):
                print(f"\n⏸️  Pauza 5s před další kategorií...")
                time.sleep(5)
        
    finally:
        driver.quit()
    
    # Export
    if all_results:
        create_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = os.path.join(OUTPUT_DIR, f"aleo_complete_{timestamp}.csv")
        xlsx_file = os.path.join(OUTPUT_DIR, f"aleo_complete_{timestamp}.xlsx")
        
        df = pd.DataFrame(all_results)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        df.to_excel(xlsx_file, index=False, engine='openpyxl')
        
        print("\n" + "="*60)
        print("✅ HOTOVO!")
        print("="*60)
        print(f"Celkem firem: {len(all_results)}")
        print(f"Firem s emailem: {sum(1 for r in all_results if r['email'])}")
        print(f"Firem s webem: {sum(1 for r in all_results if r['website'])}")
        print(f"Firem s telefonem: {sum(1 for r in all_results if r.get('phone'))}")
        print(f"\n📁 Soubory:")
        print(f"  • {csv_file}")
        print(f"  • {xlsx_file}")
    else:
        print("\n❌ Žádné výsledky!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kompletní Aleo.com scraper')
    parser.add_argument('--categories', nargs='+', help='URL kategorií')
    parser.add_argument('--category-file', default='kategorie.txt', help='Soubor s kategoriemi')
    parser.add_argument('--max', type=int, default=10, help='Max firem z kategorie')
    
    args = parser.parse_args()
    
    categories = []
    if args.categories:
        categories = args.categories
    elif os.path.exists(args.category_file):
        with open(args.category_file, 'r', encoding='utf-8') as f:
            categories = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not categories:
        print("❌ Chyba: Žádné kategorie!")
        print("Použijte: --categories URL nebo vytvořte kategorie.txt")
        exit(1)
    
    main(categories, args.max)
