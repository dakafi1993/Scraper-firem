"""
Aleo.com Category Scraper - Prohledává více kategorií
Vytvořeno: 2026-01-16
"""

import time
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import argparse
import os

# Konfigurace
OUTPUT_DIR = "output"
REQUEST_DELAY = 3
CLOUDFLARE_WAIT = 120

def setup_driver():
    """Nastavení Chrome driveru"""
    print("🚀 Spouštím Chrome...")
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def wait_for_cloudflare(driver):
    """Počká na vyřešení Cloudflare výzvy"""
    print("\n⚠️  CLOUDFLARE DETEKOVÁNA!")
    print("=" * 60)
    print("MANUÁLNÍ KROK:")
    print("1. Klikněte na checkbox 'Verify you are human'")
    print("2. Vyřešte případnou captcha")
    print("3. Počkejte, až se stránka načte")
    print(f"\nČekám max. {CLOUDFLARE_WAIT} sekund...")
    print("=" * 60)
    
    start_time = time.time()
    while time.time() - start_time < CLOUDFLARE_WAIT:
        try:
            # Zkontrolovat, zda Cloudflare pryč (původní FUNGUJÍCÍ logika)
            page_source = driver.page_source
            if "cloudflare" not in page_source.lower() or "challenge" not in page_source.lower():
                print("✅ Cloudflare vyřešena!")
                time.sleep(2)
                return True
        except:
            pass
        time.sleep(1)
    
    print("❌ Timeout při čekání na Cloudflare")
    return False

def extract_website_from_profile(driver, profile_url):
    """Extrahuje web firmy z jejího profilu"""
    try:
        driver.get(profile_url)
        time.sleep(REQUEST_DELAY)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Hledat odkaz na web
        patterns = [
            r'https?://(?:www\.)?[\w\-\.]+\.[a-z]{2,}',
        ]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not any(x in href.lower() for x in ['aleo.com', 'facebook', 'linkedin', 'twitter', 'instagram']):
                for pattern in patterns:
                    match = re.search(pattern, href)
                    if match:
                        return match.group(0)
        
        return None
    except Exception as e:
        print(f"  ⚠️  Chyba při extrakci webu: {e}")
        return None

def search_email_on_website(driver, website_url):
    """Hledá email přímo na webu firmy"""
    try:
        # Zkusit hlavní stránku
        driver.get(website_url)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text = soup.get_text()
        
        # Regex pro email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if emails:
            # Vrátit první validní email (ne obrázky apod.)
            for email in emails:
                if not any(x in email.lower() for x in ['.png', '.jpg', '.gif', 'example.com', 'sentry']):
                    return email, "Web firmy"
        
        # Zkusit kontaktní stránku
        contact_urls = [
            f"{website_url}/contact",
            f"{website_url}/kontakt",
            f"{website_url}/en/contact",
            f"{website_url}/about",
        ]
        
        for contact_url in contact_urls:
            try:
                driver.get(contact_url)
                time.sleep(1)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                text = soup.get_text()
                emails = re.findall(email_pattern, text)
                
                if emails:
                    for email in emails:
                        if not any(x in email.lower() for x in ['.png', '.jpg', '.gif', 'example.com', 'sentry']):
                            return email, "Kontaktní stránka"
            except:
                continue
        
        return None, None
        
    except Exception as e:
        return None, None

def scrape_category(driver, category_url, max_companies=None):
    """Prohledá jednu kategorii a vrátí seznam firem"""
    print(f"\n📂 Kategorie: {category_url}")
    
    companies = []
    
    try:
        driver.get(category_url)
        time.sleep(REQUEST_DELAY)
        
        # Zkontrolovat Cloudflare
        if "cloudflare" in driver.page_source.lower() or "challenge" in driver.page_source.lower():
            if not wait_for_cloudflare(driver):
                return companies
        
        # KRITICKÉ: Počkat na načtení JavaScript obsahu
        print("  ⏳ Čekám na načtení firem (JavaScript)...")
        time.sleep(5)  # Základní čekání
        
        # Scrollovat pro načtení lazy-load obsahu
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Zkusit počkat na konkrétní elementy
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.TAG_NAME, "a")) > 5
            )
            print("  ✅ JavaScript obsah načten")
        except:
            print("  ⚠️  Timeout čekání na obsah")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Debug - uložit HTML
        with open('debug_category.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("  💾 Debug HTML uloženo: debug_category.html")
        
        # Najít odkazy na profily firem
        company_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Opravený pattern - "firma/" může být i bez úvodního lomítka!
            if re.search(r'(^|/)firma/', href) and '/firmy/' not in href:
                # Přeskočit sociální sítě
                if any(x in href.lower() for x in ['linkedin', 'facebook', 'twitter']):
                    continue
                    
                # Sestavit plnou URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = f"https://aleo.com{href}"
                else:
                    full_url = f"https://aleo.com/pl/{href}"
                    
                if full_url not in company_links:
                    company_links.append(full_url)
        
        print(f"  ✅ Nalezeno {len(company_links)} firem")
        
        if max_companies:
            company_links = company_links[:max_companies]
        
        # Zpracovat každou firmu
        for idx, company_url in enumerate(company_links, 1):
            print(f"\n  [{idx}/{len(company_links)}] Zpracovávám: {company_url}")
            
            try:
                driver.get(company_url)
                time.sleep(REQUEST_DELAY)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Získat název firmy
                company_name = None
                for tag in ['h1', 'h2']:
                    title = soup.find(tag)
                    if title:
                        company_name = title.get_text(strip=True)
                        break
                
                if not company_name:
                    company_name = "Neznámá firma"
                
                print(f"    🏢 {company_name}")
                
                # Získat web firmy
                website = extract_website_from_profile(driver, company_url)
                
                email = None
                email_source = None
                
                if website:
                    print(f"    🌐 Web: {website}")
                    email, email_source = search_email_on_website(driver, website)
                    
                    if email:
                        print(f"    ✉️  Email: {email} ({email_source})")
                    else:
                        print(f"    ⚠️  Email nenalezen")
                else:
                    print(f"    ⚠️  Web nenalezen")
                
                companies.append({
                    'název_společnosti': company_name,
                    'email': email if email else '',
                    'web': website if website else '',
                    'zdroj': email_source if email_source else '',
                    'url_profilu': company_url,
                    'kategorie': category_url
                })
                
            except Exception as e:
                print(f"    ❌ Chyba: {e}")
                continue
        
    except Exception as e:
        print(f"  ❌ Chyba při zpracování kategorie: {e}")
    
    return companies

def main():
    parser = argparse.ArgumentParser(description='Aleo.com Category Scraper')
    parser.add_argument('--categories', nargs='+', help='URL kategorií k prohledání', required=False)
    parser.add_argument('--max', type=int, help='Max počet firem z každé kategorie', default=None)
    parser.add_argument('--file', help='Soubor s kategoriemi (1 URL na řádek)', default=None)
    
    args = parser.parse_args()
    
    # Získat kategorie
    categories = []
    
    if args.file and os.path.exists(args.file):
        print(f"📄 Načítám kategorie ze souboru: {args.file}")
        with open(args.file, 'r', encoding='utf-8') as f:
            categories = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif args.categories:
        categories = args.categories
    else:
        print("\n🔗 ZADEJTE KATEGORIE K PROHLEDÁNÍ")
        print("=" * 60)
        print("Zadejte URL kategorií (jedna na řádek).")
        print("Prázdný řádek = konec zadávání")
        print("\nPříklad:")
        print("  https://aleo.com/pl/firmy/it-i-telekomunikacja")
        print("  https://aleo.com/pl/firmy/marketing-reklama-i-pr")
        print("=" * 60)
        
        while True:
            url = input(">>> ").strip()
            if not url:
                break
            categories.append(url)
    
    if not categories:
        print("❌ Žádné kategorie k prohledání!")
        return
    
    print(f"\n✅ Budu prohledávat {len(categories)} kategorií:")
    for cat in categories:
        print(f"  • {cat}")
    
    if args.max:
        print(f"\n⚙️  Limit: {args.max} firem z každé kategorie")
    
    # Vytvořit output složku
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Spustit scraping
    driver = setup_driver()
    all_companies = []
    
    try:
        for cat_idx, category_url in enumerate(categories, 1):
            print(f"\n{'='*60}")
            print(f"KATEGORIE {cat_idx}/{len(categories)}")
            print(f"{'='*60}")
            
            companies = scrape_category(driver, category_url, args.max)
            all_companies.extend(companies)
            
            print(f"\n✅ Z kategorie získáno: {len(companies)} firem")
            
            # Pauza mezi kategoriemi
            if cat_idx < len(categories):
                print(f"\n⏳ Pauza {REQUEST_DELAY}s před další kategorií...")
                time.sleep(REQUEST_DELAY)
        
        # Uložit výsledky
        if all_companies:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # CSV
            csv_filename = os.path.join(OUTPUT_DIR, f'aleo_categories_{timestamp}.csv')
            df = pd.DataFrame(all_companies)
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            
            # Excel
            excel_filename = os.path.join(OUTPUT_DIR, f'aleo_categories_{timestamp}.xlsx')
            df.to_excel(excel_filename, index=False, engine='openpyxl')
            
            print(f"\n{'='*60}")
            print("✅ HOTOVO!")
            print(f"{'='*60}")
            print(f"Celkem nalezeno firem: {len(all_companies)}")
            print(f"Firem s emailem: {sum(1 for c in all_companies if c['email'])}")
            print(f"\n📁 Soubory:")
            print(f"  • {csv_filename}")
            print(f"  • {excel_filename}")
        else:
            print("\n❌ Žádné firmy nenalezeny!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
