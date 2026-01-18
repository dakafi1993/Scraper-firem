"""
Aleo.com scraper s CEIDG API pro polské firmy
1. Získá názvy firem z aleo.com
2. Vyhledá je v CEIDG (veřejná databáze polských firem)
3. Získá weby a kontakty
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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
    print("MANUÁLNÍ KROK:")
    print("1. Klikněte na checkbox 'Verify you are human'")
    print("2. Vyřešte případnou captcha")
    print(f"\nČekám max. {MAX_CLOUDFLARE_WAIT} sekund...")
    print("="*60)
    
    start_time = time.time()
    while time.time() - start_time < MAX_CLOUDFLARE_WAIT:
        if "cloudflare" not in driver.page_source.lower() and "challenge" not in driver.page_source.lower():
            print("✅ Cloudflare vyřešena!")
            return True
        time.sleep(1)
    
    print("❌ Timeout")
    return False

def extract_company_names_from_page(driver):
    """Extrahuje názvy firem z aleo.com"""
    print("  🔍 Hledám názvy firem...")
    
    time.sleep(5)
    
    # Scrollování
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    companies = []
    
    try:
        # Zkusíme najít elementy s názvy přímo
        try:
            elements = driver.find_elements(By.CLASS_NAME, "catalog-row-first-line__company-name")
            if elements:
                print(f"  ✅ Nalezeno {len(elements)} názvů firem")
                
                for elem in elements:
                    try:
                        name = elem.text.strip()
                        if name and len(name) > 2:
                            companies.append({
                                'name': name,
                                'profile_url': ''  # Nemáme přímý link, ale název stačí pro CEIDG
                            })
                    except:
                        continue
        except:
            pass
        
        # Pokud nenajdeme, zkusíme linky
        if not companies:
            elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/pl/firma/']")
            
            if elements:
                print(f"  ✅ Nalezeno {len(elements)} odkazů")
                
                seen = set()
                for elem in elements:
                    try:
                        href = elem.get_attribute('href')
                        text = elem.text.strip()
                        
                        if href and text and len(text) > 2:
                            if '/pl/firma/' in href and '/pl/firmy/' not in href:
                                if href not in seen:
                                    seen.add(href)
                                    companies.append({
                                        'name': text,
                                        'profile_url': href
                                    })
                    except:
                        continue
    except Exception as e:
        print(f"  ⚠️  Chyba: {str(e)}")
    
    # Odstranění duplikátů podle názvu
    seen_names = set()
    unique_companies = []
    for comp in companies:
        if comp['name'] not in seen_names:
            seen_names.add(comp['name'])
            unique_companies.append(comp)
    
    return unique_companies

def search_krs(company_name):
    """
    Vyhledá firmu v KRS API (pro s.r.o., S.A. apod.)
    """
    try:
        clean_name = company_name.split('SPÓŁKA')[0].strip()
        clean_name = clean_name.split(' SP.')[0].strip()
        clean_name = clean_name.split(' S.A.')[0].strip()
        
        print(f"    🔍 KRS API: {clean_name}")
        
        # API MS Justice - veřejné KRS API
        api_url = f"https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{requests.utils.quote(clean_name)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extrakce kontaktů z KRS
            website = ''
            email = ''
            
            # KRS má složitější strukturu - zkusíme najít základní info
            if isinstance(data, dict):
                # Přepsat podle skutečné struktury KRS API
                print(f"    ✅ Firma nalezena v KRS")
                return {'website': website, 'email': email}
        
        return None
        
    except Exception as e:
        print(f"    ⚠️  KRS chyba: {str(e)}")
        return None

def search_ceidg(company_name):
    """
    Vyhledá firmu v CEIDG databázi (veřejné API polských firem)
    """
    try:
        # Očistit název firmy od "SPÓŁKA..." apod.
        clean_name = company_name.split('SPÓŁKA')[0].strip()
        clean_name = clean_name.split(' SP.')[0].strip()
        clean_name = clean_name.split(' S.A.')[0].strip()
        
        print(f"    🔍 CEIDG: {clean_name}")
        
        # CEIDG API endpoint
        api_url = "https://dane.biznes.gov.pl/api/ceidg/v1/firmy"
        
        params = {
            'nazwa': clean_name,
            'format': 'json'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # CEIDG vrací pole firem
            if isinstance(data, dict) and 'firmy' in data:
                firmy = data['firmy']
                if firmy and len(firmy) > 0:
                    firma = firmy[0]  # První výsledek
                    
                    # Extrakce dat
                    website = firma.get('adresStronyInternetowej', '').strip()
                    email = firma.get('adresEmail', '').strip()
                    telefon = firma.get('numerTelefonu', '').strip()
                    nip = firma.get('nip', '').strip()
                    
                    result = {
                        'website': website if website else '',
                        'email': email if email else '',
                        'telefon': telefon if telefon else '',
                        'nip': nip if nip else ''
                    }
                    
                    if website:
                        print(f"    🌐 Web: {website}")
                    if email:
                        print(f"    ✅ Email: {email}")
                    if telefon:
                        print(f"    📞 Tel: {telefon}")
                    
                    return result
        
        return None
        
    except Exception as e:
        print(f"    ⚠️  CEIDG chyba: {str(e)}")
        return None

def find_email_on_website(url):
    """Hledá email na webu firmy"""
    if not url:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        pages = [url, f"{url}/kontakt", f"{url}/contact"]
        
        for page_url in pages:
            try:
                response = requests.get(page_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()
                    
                    emails = EMAIL_PATTERN.findall(text)
                    valid_emails = [
                        email for email in emails
                        if not any(skip in email.lower() for skip in 
                                  ['example.', 'test@', 'noreply', 'wix.com'])
                    ]
                    
                    if valid_emails:
                        return valid_emails[0]
            except:
                continue
        
        return None
    except:
        return None

def scrape_category(driver, category_url, max_companies=10):
    """Scrapuje jednu kategorii"""
    companies = []
    
    print(f"\n📂 Kategorie: {category_url}")
    
    try:
        driver.get(category_url)
        
        if "cloudflare" in driver.page_source.lower() or "challenge" in driver.page_source.lower():
            if not wait_for_cloudflare(driver):
                return companies
        
        # Extrakce názvů firem z aleo.com
        company_list = extract_company_names_from_page(driver)
        
        if not company_list:
            print("  ❌ Žádné firmy nenalezeny")
            return companies
        
        print(f"  ✅ Nalezeno {len(company_list)} firem")
        
        # Omezení
        company_list = company_list[:max_companies]
        
        # Zpracování každé firmy
        for idx, company in enumerate(company_list, 1):
            company_name = company['name']
            profile_url = company['profile_url']
            
            print(f"\n  [{idx}/{len(company_list)}] {company_name}")
            
            # Vyhledání v CEIDG
            ceidg_data = search_ceidg(company_name)
            
            website = ''
            email = ''
            telefon = ''
            nip = ''
            
            if ceidg_data:
                website = ceidg_data.get('website', '')
                email = ceidg_data.get('email', '')
                telefon = ceidg_data.get('telefon', '')
                nip = ceidg_data.get('nip', '')
                
                # Pokud CEIDG nemá email, zkusíme ho najít na webu
                if website and not email:
                    print(f"    📧 Hledám email na webu...")
                    found_email = find_email_on_website(website)
                    if found_email:
                        email = found_email
                        print(f"    ✅ Email nalezen: {email}")
            else:
                print(f"    ⚠️  Firma nenalezena v CEIDG")
            
            companies.append({
                'name': company_name,
                'website': website,
                'email': email,
                'telefon': telefon,
                'nip': nip,
                'aleo_profile': profile_url,
                'category': category_url
            })
            
            time.sleep(1)  # Rate limiting
        
        print(f"\n✅ Zpracováno: {len(companies)} firem")
        
    except Exception as e:
        print(f"❌ Chyba: {str(e)}")
    
    return companies

def main(categories, max_companies_per_category):
    print("\n" + "="*60)
    print("🚀 ALEO.COM + CEIDG SCRAPER")
    print("="*60)
    
    all_companies = []
    driver = setup_driver()
    
    try:
        print(f"\n✅ Kategorie ({len(categories)}):")
        for cat in categories:
            print(f"  • {cat}")
        
        print(f"\n⚙️  Limit: {max_companies_per_category} firem/kategorii")
        print("🚀 Spouštím Chrome...")
        
        for idx, category_url in enumerate(categories, 1):
            print(f"\n{'='*60}")
            print(f"KATEGORIE {idx}/{len(categories)}")
            print("="*60)
            
            companies = scrape_category(driver, category_url, max_companies_per_category)
            all_companies.extend(companies)
            
            if idx < len(categories):
                print(f"\n⏸️  Pauza 3s...")
                time.sleep(3)
        
    finally:
        driver.quit()
    
    # Export
    if all_companies:
        create_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = os.path.join(OUTPUT_DIR, f"aleo_ceidg_{timestamp}.csv")
        xlsx_file = os.path.join(OUTPUT_DIR, f"aleo_ceidg_{timestamp}.xlsx")
        
        df = pd.DataFrame(all_companies)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        df.to_excel(xlsx_file, index=False, engine='openpyxl')
        
        print("\n" + "="*60)
        print("✅ HOTOVO!")
        print("="*60)
        print(f"Celkem firem: {len(all_companies)}")
        print(f"Firem s emailem: {sum(1 for c in all_companies if c['email'])}")
        print(f"Firem s webem: {sum(1 for c in all_companies if c['website'])}")
        print(f"\n📁 Soubory:")
        print(f"  • {csv_file}")
        print(f"  • {xlsx_file}")
    else:
        print("\n❌ Žádné firmy!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aleo.com + CEIDG scraper')
    parser.add_argument('--categories', nargs='+', help='URL kategorií')
    parser.add_argument('--category-file', default='kategorie.txt', help='Soubor s kategoriemi')
    parser.add_argument('--max', type=int, default=10, help='Max firem/kategorii')
    
    args = parser.parse_args()
    
    categories = []
    if args.categories:
        categories = args.categories
    elif os.path.exists(args.category_file):
        with open(args.category_file, 'r', encoding='utf-8') as f:
            categories = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not categories:
        print("❌ Žádné kategorie!")
        exit(1)
    
    main(categories, args.max)
