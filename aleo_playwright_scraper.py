"""
Aleo.com Scraper s Playwright podporou pro Angular SPA
Playwright má lepší podporu pro Single Page Applications než Selenium
"""

import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import pandas as pd
from datetime import datetime
import os
import argparse
import time

# === KONFIGURACE ===
OUTPUT_DIR = "output"
MAX_CLOUDFLARE_WAIT = 120  # sekund na vyřešení Cloudflare
PAGE_LOAD_TIMEOUT = 30000  # 30s timeout pro načtení stránky
NETWORK_IDLE_TIMEOUT = 10000  # 10s pro network idle

# === HELPER FUNKCE ===
def create_output_dir():
    """Vytvoří výstupní adresář, pokud neexistuje"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 Vytvořen adresář: {OUTPUT_DIR}")

async def wait_for_cloudflare(page):
    """
    Čeká na vyřešení Cloudflare challenge
    """
    print("\n⚠️  CLOUDFLARE DETEKOVÁNA!")
    print("="*60)
    print("MANUÁLNÍ KROK:")
    print("1. Klikněte na checkbox 'Verify you are human'")
    print("2. Vyřešte případnou captcha")
    print("3. Počkejte, až se stránka načte")
    print(f"\nČekám max. {MAX_CLOUDFLARE_WAIT} sekund...")
    print("="*60)
    
    start_time = time.time()
    
    while time.time() - start_time < MAX_CLOUDFLARE_WAIT:
        content = await page.content()
        
        # Kontrola, zda Cloudflare zmizela
        if "cloudflare" not in content.lower() or "challenge" not in content.lower():
            print("✅ Cloudflare vyřešena!")
            return True
        
        await asyncio.sleep(1)
    
    print("❌ Timeout - Cloudflare nebyla vyřešena včas")
    return False

async def scrape_category(page, category_url, max_companies=10):
    """
    Scrapuje jednu kategorii pomocí Playwright
    """
    companies = []
    
    print(f"\n📂 Kategorie: {category_url}")
    
    try:
        # Načtení stránky
        await page.goto(category_url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
        
        # Kontrola Cloudflare
        content = await page.content()
        if "cloudflare" in content.lower() or "challenge" in content.lower():
            if not await wait_for_cloudflare(page):
                return companies
        
        # Čekání na načtení Angular obsahu - KLÍČOVÉ PRO SPA!
        print("  ⏳ Čekám na načtení Angular obsahu...")
        
        try:
            # Čekáme na network idle - signalizuje, že API requesty skončily
            await page.wait_for_load_state('networkidle', timeout=NETWORK_IDLE_TIMEOUT)
            print("  ✅ Network idle - API požadavky dokončeny")
        except PlaywrightTimeout:
            print("  ⚠️  Network idle timeout - pokračuji...")
        
        # Čekáme na specifický Angular element s firmami
        try:
            await page.wait_for_selector('.catalog-row-container', timeout=10000)
            print("  ✅ Angular komponenta načtena")
        except PlaywrightTimeout:
            print("  ⚠️  Angular komponenta nenalezena - možná žádné firmy")
        
        # Scrollování pro načtení lazy-loaded obsahu
        print("  📜 Scrolluji stránku...")
        for i in range(3):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)
        
        # Získání aktuálního HTML po načtení Angularu
        content = await page.content()
        
        # Debug: uložení HTML
        debug_file = "debug_playwright.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  💾 Debug HTML uloženo: {debug_file}")
        
        # Hledání odkazů na firmy pomocí Playwright lokátorů
        # Zkusíme najít linky s pattern /pl/firma/
        links = await page.locator('a[href*="/pl/firma/"]').all()
        
        print(f"  ✅ Nalezeno {len(links)} odkazů na firmy")
        
        # Zpracování firem
        processed = 0
        seen_urls = set()
        
        for link in links:
            if processed >= max_companies:
                break
            
            try:
                href = await link.get_attribute('href')
                if not href or href in seen_urls:
                    continue
                
                # Přeskočit nežádoucí linky
                if any(skip in href.lower() for skip in ['linkedin', 'facebook', 'cookie', 'privacy', '/pl/firmy/']):
                    continue
                
                seen_urls.add(href)
                
                # Kompletní URL
                if href.startswith('/'):
                    full_url = f"https://aleo.com{href}"
                else:
                    full_url = href
                
                processed += 1
                print(f"\n  [{processed}/{max_companies}] Zpracovávám: {full_url}")
                
                # Získání názvu firmy z textu linku nebo z URL
                try:
                    company_name = await link.text_content()
                    if not company_name or len(company_name.strip()) == 0:
                        # Extrahuj název z URL
                        company_name = href.split('/')[-1].replace('-', ' ').title()
                except:
                    company_name = href.split('/')[-1].replace('-', ' ').title()
                
                print(f"    🏢 {company_name}")
                
                companies.append({
                    'name': company_name.strip(),
                    'profile_url': full_url,
                    'website': '',
                    'email': '',
                    'category': category_url
                })
                
            except Exception as e:
                print(f"    ⚠️  Chyba při zpracování linku: {str(e)}")
                continue
        
        print(f"\n✅ Z kategorie získáno: {len(companies)} firem")
        
    except Exception as e:
        print(f"❌ Chyba při scrapování kategorie: {str(e)}")
    
    return companies

async def main(categories, max_companies_per_category):
    """
    Hlavní funkce scraperu
    """
    print("\n" + "="*60)
    print("🚀 ALEO.COM SCRAPER S PLAYWRIGHT")
    print("="*60)
    
    all_companies = []
    
    async with async_playwright() as p:
        # Spuštění browseru (headless=False pro Cloudflare)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print(f"\n✅ Budu prohledávat {len(categories)} kategorií:")
        for cat in categories:
            print(f"  • {cat}")
        
        print(f"\n⚙️  Limit: {max_companies_per_category} firem z každé kategorie")
        
        # Procházení kategorií
        for idx, category_url in enumerate(categories, 1):
            print(f"\n{'='*60}")
            print(f"KATEGORIE {idx}/{len(categories)}")
            print("="*60)
            
            companies = await scrape_category(page, category_url, max_companies_per_category)
            all_companies.extend(companies)
            
            # Pauza mezi kategoriemi
            if idx < len(categories):
                print(f"\n⏸️  Pauza 3s před další kategorií...")
                await asyncio.sleep(3)
        
        await browser.close()
    
    # Export dat
    if all_companies:
        create_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_file = os.path.join(OUTPUT_DIR, f"aleo_playwright_{timestamp}.csv")
        df = pd.DataFrame(all_companies)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        # Excel
        xlsx_file = os.path.join(OUTPUT_DIR, f"aleo_playwright_{timestamp}.xlsx")
        df.to_excel(xlsx_file, index=False, engine='openpyxl')
        
        print("\n" + "="*60)
        print("✅ HOTOVO!")
        print("="*60)
        print(f"Celkem nalezeno firem: {len(all_companies)}")
        print(f"Firem s emailem: {sum(1 for c in all_companies if c['email'])}")
        print(f"\n📁 Soubory:")
        print(f"  • {csv_file}")
        print(f"  • {xlsx_file}")
    else:
        print("\n❌ Nebyly nalezeny žádné firmy!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Aleo.com scraper s Playwright')
    parser.add_argument('--categories', nargs='+', help='Seznam URL kategorií k prohledání')
    parser.add_argument('--category-file', default='kategorie.txt', help='Soubor s kategoriemi (1 URL na řádek)')
    parser.add_argument('--max', type=int, default=10, help='Maximální počet firem z každé kategorie')
    
    args = parser.parse_args()
    
    # Načtení kategorií
    categories = []
    
    if args.categories:
        categories = args.categories
    elif os.path.exists(args.category_file):
        with open(args.category_file, 'r', encoding='utf-8') as f:
            categories = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not categories:
        print("❌ Chyba: Nebyly zadány žádné kategorie!")
        print("Použijte: --categories URL1 URL2 ... nebo vytvořte soubor kategorie.txt")
        exit(1)
    
    # Spuštění async funkce
    asyncio.run(main(categories, args.max))
