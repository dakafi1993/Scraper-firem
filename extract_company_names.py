"""
Jednoduchý extraktor názvů firem z aleo.com
Výstup: CSV se jmény firem pro další zpracování
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime
import os
import argparse

OUTPUT_DIR = "output"
MAX_CLOUDFLARE_WAIT = 120

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
    print("\n⚠️  CLOUDFLARE!")
    print("Klikněte na checkbox...")
    print(f"Čekám {MAX_CLOUDFLARE_WAIT}s...")
    
    start_time = time.time()
    while time.time() - start_time < MAX_CLOUDFLARE_WAIT:
        if "cloudflare" not in driver.page_source.lower() and "challenge" not in driver.page_source.lower():
            print("✅ OK!")
            return True
        time.sleep(1)
    
    return False

def extract_companies(driver, url, max_companies):
    """Extrahuje názvy firem"""
    print(f"\n📂 {url}")
    
    driver.get(url)
    
    if "cloudflare" in driver.page_source.lower():
        if not wait_for_cloudflare(driver):
            return []
    
    time.sleep(5)
    
    # Scrollování
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    
    companies = []
    
    try:
        elements = driver.find_elements(By.CLASS_NAME, "catalog-row-first-line__company-name")
        print(f"✅ Nalezeno {len(elements)} firem")
        
        for elem in elements[:max_companies]:
            try:
                name = elem.text.strip()
                if name and len(name) > 2:
                    companies.append(name)
            except:
                continue
    except Exception as e:
        print(f"❌ Chyba: {str(e)}")
    
    # Odstranění duplikátů
    return list(dict.fromkeys(companies))

def main(categories, max_per_category):
    print("="*60)
    print("🚀 ALEO.COM - EXTRAKTOR NÁZVŮ FIREM")
    print("="*60)
    
    all_companies = []
    driver = setup_driver()
    
    try:
        for idx, url in enumerate(categories, 1):
            print(f"\n[{idx}/{len(categories)}]")
            companies = extract_companies(driver, url, max_per_category)
            all_companies.extend(companies)
            
            if idx < len(categories):
                time.sleep(3)
        
    finally:
        driver.quit()
    
    if all_companies:
        create_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV s jedním sloupcem "company_name"
        csv_file = os.path.join(OUTPUT_DIR, f"company_names_{timestamp}.csv")
        
        df = pd.DataFrame({'company_name': all_companies})
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*60)
        print("✅ HOTOVO!")
        print("="*60)
        print(f"Celkem firem: {len(all_companies)}")
        print(f"\n📁 Soubor: {csv_file}")
        print(f"\n💡 Použijte: python email_finder.py --input {csv_file}")
    else:
        print("\n❌ Žádné firmy!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--categories', nargs='+')
    parser.add_argument('--category-file', default='kategorie.txt')
    parser.add_argument('--max', type=int, default=50, help='Max firem z kategorie')
    
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
