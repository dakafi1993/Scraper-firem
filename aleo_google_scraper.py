"""
Aleo.com scraper s Google vyhledáváním firem
1. Získá názvy firem z aleo.com
2. Najde jejich weby přes Google
3. Extrahuje emaily z webů
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
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
    """Vytvoří výstupní adresář"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def setup_driver():
    """Nastavení Chrome driveru"""
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
    """Čeká na vyřešení Cloudflare"""
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
    
    print("❌ Timeout - Cloudflare nebyla vyřešena")
    return False

def extract_company_names_from_page(driver):
    """
    Extrahuje názvy firem A jejich profile URLs ze stránky
    """
    print("  🔍 Hledám názvy firem na stránce...")
    
    # Čekání na načtení
    time.sleep(5)
    
    # Scrollování
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    companies = []
    
    try:
        # Hledání odkazů na profily firem
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/pl/firma/']")
        
        if elements:
            print(f"  ✅ Nalezeno {len(elements)} odkazů na profily firem")
            
            seen_urls = set()
            for elem in elements:
                try:
                    href = elem.get_attribute('href')
                    text = elem.text.strip()
                    
                    # Přeskočit duplikáty a nežádoucí odkazy
                    if href and href not in seen_urls:
                        if '/pl/firma/' in href and '/pl/firmy/' not in href:
                            if text and len(text) > 2:
                                seen_urls.add(href)
                                companies.append({
                                    'name': text,
                                    'profile_url': href
                                })
                except:
                    continue
    
    except Exception as e:
        print(f"  ⚠️  Chyba při extrakci: {str(e)}")
    
    return companies

def get_website_from_profile(driver, profile_url):
    """
    Získá web firmy z jejího profilu na aleo.com
    """
    try:
        print(f"    📄 Otevírám profil...")
        driver.get(profile_url)
        time.sleep(3)
        
        # Hledání webu v profilu - různé možné selektory
        web_selectors = [
            (By.CSS_SELECTOR, "a[href^='http']:not([href*='aleo.com']):not([href*='facebook']):not([href*='linkedin'])"),
            (By.XPATH, "//a[starts-with(@href, 'http') and not(contains(@href, 'aleo.com'))]"),
        ]
        
        for by, selector in web_selectors:
            try:
                elements = driver.find_elements(by, selector)
                for elem in elements:
                    href = elem.get_attribute('href')
                    if href and href.startswith('http'):
                        # Přeskočit sociální sítě
                        if not any(skip in href.lower() for skip in ['facebook', 'linkedin', 'youtube', 'twitter', 'instagram']):
                            print(f"    🌐 Web z profilu: {href}")
                            return href
            except:
                continue
        
        # Pokud nenajdeme v elementech, zkusíme regex v HTML
        html = driver.page_source
        urls = re.findall(r'href=["\']?(https?://[^"\'>\s]+)', html)
        
        for url in urls:
            if 'aleo.com' not in url and not any(skip in url.lower() for skip in 
                ['facebook', 'linkedin', 'youtube', 'twitter', 'instagram', 'google']):
                print(f"    🌐 Web z HTML: {url}")
                return url
        
        return None
        
    except Exception as e:
        print(f"    ⚠️  Chyba při získávání webu: {str(e)}")
        return None

def find_email_on_website(url):
    """
    Najde email na webu firmy
    """
    if not url:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Zkusíme hlavní stránku a kontaktní stránky
        pages_to_check = [
            url,
            f"{url}/contact",
            f"{url}/kontakt",
            f"{url}/kontakty",
            f"{url}/about",
            f"{url}/o-nas"
        ]
        
        for page_url in pages_to_check:
            try:
                response = requests.get(page_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()
                    
                    # Hledání emailů
                    emails = EMAIL_PATTERN.findall(text)
                    
                    # Filtrování nežádoucích emailů
                    valid_emails = [
                        email for email in emails
                        if not any(skip in email.lower() for skip in 
                                  ['example.', 'test@', 'admin@', 'noreply', 'wix.com', 'domain.'])
                    ]
                    
                    if valid_emails:
                        return valid_emails[0]
            except:
                continue
        
        return None
        
    except Exception as e:
        return None

def scrape_category(driver, category_url, max_companies=10):
    """
    Scrapuje jednu kategorii
    """
    companies = []
    
    print(f"\n📂 Kategorie: {category_url}")
    
    try:
        driver.get(category_url)
        
        # Cloudflare check
        if "cloudflare" in driver.page_source.lower() or "challenge" in driver.page_source.lower():
            if not wait_for_cloudflare(driver):
                return companies
        
        # Extrakce názvů firem
        company_names = extract_company_names_from_page(driver)
        
        if not company_names:
            print("  ❌ Nebyly nalezeny žádné firmy na stránce")
            return companies
        
        print(f"  ✅ Nalezeno {len(company_names)} názvů firem")
        
        # Omezení počtu
        company_names = company_names[:max_companies]
        
        # Zpracování každé firmy
        for idx, company_name in enumerate(company_names, 1):
            print(f"\n  [{idx}/{len(company_names)}] {company_name}")
            
            # Google search pro web
            website = google_search_company(company_name, driver)
            
            # Hledání emailu
            email = None
            if website:
                print(f"    📧 Hledám email...")
                email = find_email_on_website(website)
                if email:
                    print(f"    ✅ Email: {email}")
                else:
                    print(f"    ⚠️  Email nenalezen")
            else:
                print(f"    ⚠️  Web nenalezen")
            
            companies.append({
                'name': company_name,
                'website': website or '',
                'email': email or '',
                'category': category_url
            })
            
            # Pauza mezi firmami
            time.sleep(2)
        
        print(f"\n✅ Z kategorie zpracováno: {len(companies)} firem")
        
    except Exception as e:
        print(f"❌ Chyba: {str(e)}")
    
    return companies

def main(categories, max_companies_per_category):
    """Hlavní funkce"""
    print("\n" + "="*60)
    print("🚀 ALEO.COM SCRAPER S GOOGLE VYHLEDÁVÁNÍM")
    print("="*60)
    
    all_companies = []
    driver = setup_driver()
    
    try:
        print(f"\n✅ Budu prohledávat {len(categories)} kategorií:")
        for cat in categories:
            print(f"  • {cat}")
        
        print(f"\n⚙️  Limit: {max_companies_per_category} firem z každé kategorie")
        print("🚀 Spouštím Chrome...")
        
        for idx, category_url in enumerate(categories, 1):
            print(f"\n{'='*60}")
            print(f"KATEGORIE {idx}/{len(categories)}")
            print("="*60)
            
            companies = scrape_category(driver, category_url, max_companies_per_category)
            all_companies.extend(companies)
            
            if idx < len(categories):
                print(f"\n⏸️  Pauza 5s před další kategorií...")
                time.sleep(5)
        
    finally:
        driver.quit()
    
    # Export
    if all_companies:
        create_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = os.path.join(OUTPUT_DIR, f"aleo_google_{timestamp}.csv")
        xlsx_file = os.path.join(OUTPUT_DIR, f"aleo_google_{timestamp}.xlsx")
        
        df = pd.DataFrame(all_companies)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        df.to_excel(xlsx_file, index=False, engine='openpyxl')
        
        print("\n" + "="*60)
        print("✅ HOTOVO!")
        print("="*60)
        print(f"Celkem firem: {len(all_companies)}")
        print(f"Firem s emailem: {sum(1 for c in all_companies if c['email'])}")
        print(f"\n📁 Soubory:")
        print(f"  • {csv_file}")
        print(f"  • {xlsx_file}")
    else:
        print("\n❌ Nebyly nalezeny žádné firmy!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aleo.com scraper s Google vyhledáváním')
    parser.add_argument('--categories', nargs='+', help='Seznam URL kategorií')
    parser.add_argument('--category-file', default='kategorie.txt', help='Soubor s kategoriemi')
    parser.add_argument('--max', type=int, default=10, help='Max firem z každé kategorie')
    
    args = parser.parse_args()
    
    categories = []
    if args.categories:
        categories = args.categories
    elif os.path.exists(args.category_file):
        with open(args.category_file, 'r', encoding='utf-8') as f:
            categories = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not categories:
        print("❌ Chyba: Nebyly zadány kategorie!")
        exit(1)
    
    main(categories, args.max)
