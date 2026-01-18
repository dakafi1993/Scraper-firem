#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aleo.com Semi-Manual Scraper
Řešení pro weby chráněné Cloudflare - manuální procházení s automatickým extrakcí
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime
from pathlib import Path
import json

class SemiManualScraper:
    """Semi-manuální scraper pro weby s Cloudflare ochranou"""
    
    def __init__(self):
        self.results = []
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """Inicializace Chrome prohlížeče"""
        print("🚀 Inicializuji prohlížeč...")
        chrome_options = Options()
        # NEPOUŽÍVAT headless mode - musí být viditelný pro Cloudflare
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        print("✓ Prohlížeč připraven\n")
    
    def _extract_email(self, text: str) -> str:
        """Extrahuje e-mailovou adresu z textu"""
        if not text:
            return None
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            filtered = [e for e in emails if not any(
                placeholder in e.lower() 
                for placeholder in ['example.com', 'domain.com', 'email.cz']
            )]
            return filtered[0] if filtered else None
        return None
    
    def wait_for_user(self, message: str):
        """Počká na potvrzení uživatele"""
        input(f"\n{'='*60}\n{message}\nStiskněte ENTER pro pokračování...\n{'='*60}\n")
    
    def scrape_current_page(self) -> list:
        """Extrahuje data z aktuálně načtené stránky"""
        print("📊 Analyzuji aktuální stránku...")
        time.sleep(2)
        
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        companies = []
        
        # Hledání všech odkazů
        all_links = soup.find_all('a', href=True)
        
        print(f"   Nalezeno {len(all_links)} odkazů na stránce")
        print("   Hledám odkazy na společnosti...")
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Filtrování odkazů, které vypadají jako profily firem
            if text and len(text) > 3:
                # Různé možné vzory URL
                if any(pattern in href.lower() for pattern in 
                       ['firma', 'company', 'detail', 'profil', 'subjekt']):
                    
                    full_url = href if href.startswith('http') else f"https://www.aleo.com{href}"
                    
                    companies.append({
                        'name': text,
                        'url': full_url
                    })
        
        # Odstranění duplikátů
        seen = set()
        unique_companies = []
        for comp in companies:
            if comp['url'] not in seen:
                seen.add(comp['url'])
                unique_companies.append(comp)
        
        print(f"   ✓ Nalezeno {len(unique_companies)} unikátních společností\n")
        return unique_companies
    
    def scrape_company_detail(self, company: dict) -> dict:
        """Získá detaily o jedné společnosti"""
        result = {
            'název_společnosti': company['name'],
            'email': None,
            'zdroj': None,
            'url_profilu': company['url']
        }
        
        try:
            print(f"   Načítám: {company['name'][:50]}...")
            self.driver.get(company['url'])
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            page_text = soup.get_text()
            
            # Hledání e-mailu
            email = self._extract_email(page_text)
            
            if email:
                result['email'] = email
                result['zdroj'] = 'Profil společnosti'
                print(f"   ✓ Email: {email}")
            else:
                print(f"   ✗ Email nenalezen")
                result['zdroj'] = 'Email nenalezen'
                
        except Exception as e:
            print(f"   ✗ Chyba: {e}")
            result['zdroj'] = f'Chyba: {str(e)[:50]}'
        
        return result
    
    def run_manual_mode(self):
        """Hlavní režim - manuální procházení s automatickou extrakcí"""
        print("\n" + "="*60)
        print("SEMI-MANUÁLNÍ REŽIM SCRAPERU")
        print("="*60)
        print("\nTento režim funguje takto:")
        print("1. Ručně otevřete stránku katalogu v prohlížeči")
        print("2. Vyřešte Cloudflare challenge (pokud se zobrazí)")
        print("3. Skript automaticky extrahuje data z aktuální stránky")
        print("4. Procházejte jednotlivé profily společností\n")
        
        self.wait_for_user(
            "⚠️  NYNÍ:\n"
            "1. Otevře se Chrome prohlížeč\n"
            "2. Ručně přejděte na https://www.aleo.com/firmy\n"
            "3. Vyřešte Cloudflare kontrolu (klikněte na checkbox)\n"
            "4. Počkejte, až se stránka plně načte"
        )
        
        # Otevření stránky (uživatel vyřeší Cloudflare)
        self.driver.get("https://www.aleo.com/firmy")
        
        self.wait_for_user(
            "✅ Ujistěte se, že:\n"
            "   - Cloudflare challenge je vyřešen\n"
            "   - Stránka s firmami je plně načtena\n"
            "   - Vidíte seznam firem"
        )
        
        # Extrakce společností z aktuální stránky
        companies = self.scrape_current_page()
        
        if not companies:
            print("❌ Nebyly nalezeny žádné společnosti!")
            print("   Možná je potřeba upravit CSS selektory v kódu.")
            self.wait_for_user("Zkontrolujte stránku a stiskněte ENTER")
            return
        
        print(f"\n📋 Celkem nalezeno: {len(companies)} společností")
        print("\nPříklady:")
        for i, comp in enumerate(companies[:5], 1):
            print(f"   {i}. {comp['name'][:50]}")
        
        # Dotaz na zpracování
        process = input(f"\n❓ Zpracovat těchto {len(companies)} společností? (y/n/číslo): ").strip().lower()
        
        if process == 'n':
            print("Ukončuji...")
            return
        elif process.isdigit():
            companies = companies[:int(process)]
            print(f"✓ Zpracovávám prvních {process} společností")
        
        # Zpracování jednotlivých společností
        print(f"\n{'='*60}")
        print("ZPRACOVÁVÁM DETAILY SPOLEČNOSTÍ")
        print("="*60 + "\n")
        
        for i, company in enumerate(companies, 1):
            print(f"[{i}/{len(companies)}]")
            result = self.scrape_company_detail(company)
            self.results.append(result)
            time.sleep(2)  # Slušná prodleva
        
        # Uložení výsledků
        self.save_results()
        
        print("\n" + "="*60)
        print("✅ SCRAPING DOKONČEN!")
        print(f"   Zpracováno: {len(self.results)} společností")
        print(f"   S e-mailem: {sum(1 for r in self.results if r['email'])}")
        print("="*60 + "\n")
    
    def run_current_page_only(self):
        """Režim pro extrakci pouze z aktuální stránky"""
        print("\n" + "="*60)
        print("REŽIM: ANALÝZA AKTUÁLNÍ STRÁNKY")
        print("="*60 + "\n")
        
        self.wait_for_user(
            "Otevře se prohlížeč.\n"
            "Ručně přejděte na stránku, kterou chcete analyzovat."
        )
        
        self.driver.get("https://www.aleo.com")
        
        self.wait_for_user("Přejděte na stránku k analýze a stiskněte ENTER")
        
        companies = self.scrape_current_page()
        
        if companies:
            # Export do CSV
            df = pd.DataFrame(companies)
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = output_dir / f'found_companies_{timestamp}.csv'
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\n✓ Seznam společností uložen: {csv_path}")
        
        self.close()
    
    def save_results(self):
        """Uložení výsledků"""
        if not self.results:
            return
        
        df = pd.DataFrame(self.results)
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV
        csv_path = output_dir / f'aleo_manual_{timestamp}.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"   ✓ CSV: {csv_path}")
        
        # Excel
        excel_path = output_dir / f'aleo_manual_{timestamp}.xlsx'
        df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"   ✓ Excel: {excel_path}")
        
        # Statistiky
        stats = {
            'celkem': len(self.results),
            'nalezeno_emailů': df['email'].notna().sum(),
            'nenalezeno': df['email'].isna().sum(),
            'úspěšnost': f"{(df['email'].notna().sum() / len(self.results) * 100):.1f}%"
        }
        
        stats_path = output_dir / f'stats_manual_{timestamp}.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def close(self):
        """Uzavře prohlížeč"""
        if self.driver:
            self.driver.quit()
            print("\n✓ Prohlížeč uzavřen")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║        ALEO.COM SEMI-MANUÁLNÍ SCRAPER                     ║
║     Řešení pro weby chráněné Cloudflare                   ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print("\nVyberte režim:")
    print("1. Plný scraping (s procházením profilů)")
    print("2. Pouze analýza aktuální stránky")
    
    choice = input("\nVolba (1/2): ").strip()
    
    scraper = SemiManualScraper()
    
    try:
        if choice == "1":
            scraper.run_manual_mode()
        elif choice == "2":
            scraper.run_current_page_only()
        else:
            print("Neplatná volba!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Přerušeno uživatelem")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
