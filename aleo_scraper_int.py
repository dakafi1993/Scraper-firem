#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aleo.com International Scraper s Google vyhledáváním
Automatické stahování dat firem a vyhledávání emailů
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime
from pathlib import Path
import json
import logging

# Konfigurace loggingu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_int.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AleoInternationalScraper:
    """Scraper pro aleo.com/int s vyhledáváním emailů"""
    
    def __init__(self):
        self.results = []
        self.driver = None
        self.companies = []
        self._init_driver()
    
    def _init_driver(self):
        """Inicializace Chrome prohlížeče"""
        logger.info("🚀 Inicializuji prohlížeč...")
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Headless mode pro rychlejší běh
        # chrome_options.add_argument('--headless')  # Odkomentovat pro běh na pozadí
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        logger.info("✓ Prohlížeč připraven\n")
    
    def _extract_email(self, text: str) -> str:
        """Extrahuje e-mailovou adresu z textu"""
        if not text:
            return None
        
        # Regex pattern pro e-mailové adresy
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if emails:
            # Filtrování běžných placeholder e-mailů
            filtered = [e for e in emails if not any(
                placeholder in e.lower() 
                for placeholder in ['example.com', 'domain.com', 'email.cz', 
                                   'test.com', 'sample.com', 'xxx.com']
            )]
            return filtered[0] if filtered else None
        return None
    
    def wait_for_cloudflare(self):
        """Počká na vyřešení Cloudflare challenge"""
        logger.info("⏳ Čekám na Cloudflare challenge...")
        logger.info("   ⚠️  NYNÍ: Pokud vidíte CAPTCHA, vyřešte ji RUČNĚ v prohlížeči!")
        logger.info("   Po vyřešení stránka automaticky pokračuje...")
        
        max_wait = 120  # 2 minuty
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                page_source = self.driver.page_source.lower()
                current_url = self.driver.current_url.lower()
                
                # Kontrola, zda je stránka načtena
                if ("ověřujeme" not in page_source and 
                    "challenge" not in page_source and
                    "cloudflare" not in page_source and
                    "__cf_chl" not in current_url):
                    logger.info("✓ Cloudflare vyřešen!")
                    time.sleep(3)  # Extra čas na plné načtení
                    return True
            except:
                pass
            time.sleep(2)
        
        logger.warning("⚠️  Timeout při čekání na Cloudflare")
        logger.info("   Zkuste: Ručně proklikat CAPTCHA v prohlížeči")
        input("\n   >>> Stiskněte ENTER po vyřešení CAPTCHA <<<\n")
        time.sleep(3)
        return True
    
    def scrape_company_list(self, url: str, max_companies: int = None):
        """Získá seznam společností z aleo.com/int"""
        logger.info(f"📋 Načítám seznam společností z: {url}")
        
        try:
            self.driver.get(url)
            self.wait_for_cloudflare()
            
            # Scroll pro načtení lazy-loaded obsahu
            logger.info("📜 Scrolluji stránku pro načtení všech dat...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            for i in range(5):  # Max 5 scrollů
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Scroll zpět nahoru
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Extrakce dat
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Uložit HTML pro analýzu
            with open('aleo_int_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info("💾 HTML stránky uloženo do aleo_int_page.html pro analýzu")
            
            # Hledání různých vzorů odkazů na firmy
            all_links = soup.find_all('a', href=True)
            
            logger.info(f"🔍 Analyzuji {len(all_links)} odkazů...")
            
            seen_urls = set()
            
            # METODA 1: Hledání specifických CSS tříd pro firmy
            # Zkuste najít karty/položky firem
            company_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'company|firma|card|item|listing|result', re.I))
            
            logger.info(f"📦 Nalezeno {len(company_containers)} potenciálních kontejnerů")
            
            for container in company_containers:
                # Hledat odkazy uvnitř kontejneru
                link = container.find('a', href=True)
                if link:
                    href = link.get('href', '')
                    text = link.get_text(strip=True) or container.get_text(strip=True)
                    
                    # Musí obsahovat /int/ a být dostatečně dlouhá cesta
                    if '/int/' in href and href.count('/') >= 4:
                        full_url = href if href.startswith('http') else f"https://aleo.com{href}"
                        
                        # Filtrovat systémové stránky
                        if not any(skip in href.lower() for skip in 
                                 ['cookie', 'privacy', 'about', 'terms', 'login', 'register']):
                            if full_url not in seen_urls and len(text) > 3:
                                self.companies.append({
                                    'name': text[:100],  # Omezit délku
                                    'url': full_url
                                })
                                seen_urls.add(full_url)
            
            # METODA 2: Pokud první metoda nenašla nic, použít obecnější přístup
            if len(self.companies) == 0:
                logger.warning("⚠️  Metoda 1 nenašla firmy, zkouším obecnější přístup...")
                
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Hledat odkazy, které vypadají jako profily firem
                    # Musí obsahovat /int/ a mít více než 3 úrovně
                    if '/int/' in href and href.count('/') >= 4:
                        # Vyloučit navigaci a systémové stránky
                        if not any(skip in href.lower() for skip in 
                                 ['about', 'cookie', 'privacy', 'terms', 'faq', 
                                  'help', 'login', 'register', 'contact']):
                            
                            full_url = href if href.startswith('http') else f"https://aleo.com{href}"
                            
                            if full_url not in seen_urls and text and len(text) > 3 and len(text) < 150:
                                self.companies.append({
                                    'name': text,
                                    'url': full_url
                                })
                                seen_urls.add(full_url)
            
            # METODA 3: Pokud stále nic, analyzovat všechny odkazy
            if len(self.companies) == 0:
                logger.warning("⚠️  Standardní metody nenašly firmy")
                logger.info("📊 Zobrazuji všechny nalezené odkazy pro manuální kontrolu:")
                
                unique_links = []
                for link in all_links[:30]:  # První 30 odkazů
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if href and text:
                        logger.info(f"   • {text[:60]} → {href[:60]}")
                        unique_links.append({'text': text, 'href': href})
            
            logger.info(f"✓ Nalezeno {len(self.companies)} potenciálních společností")
            
            if max_companies:
                self.companies = self.companies[:max_companies]
                logger.info(f"📊 Omezeno na {max_companies} společností")
            
            # Zobrazení vzorku
            if self.companies:
                logger.info("\n📋 Příklady nalezených společností:")
                for i, comp in enumerate(self.companies[:5], 1):
                    logger.info(f"   {i}. {comp['name'][:60]}")
            
        except Exception as e:
            logger.error(f"❌ Chyba při načítání seznamu: {e}")
    
    def extract_website_from_profile(self, soup: BeautifulSoup) -> str:
        """Extrahuje webovou stránku firmy z profilu"""
        # Hledání různých vzorů odkazů na web
        patterns = [
            {'text': re.compile(r'web|website|www|homepage|stránk', re.I)},
            {'class': re.compile(r'web|url|link|external', re.I)},
            {'itemprop': 'url'}
        ]
        
        for pattern in patterns:
            links = soup.find_all('a', pattern, href=True)
            for link in links:
                href = link.get('href', '')
                # Musí být externí odkaz
                if href.startswith('http') and 'aleo.com' not in href:
                    return href
        
        # Hledání v textu (www.firma.cz apod.)
        text = soup.get_text()
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
        urls = re.findall(url_pattern, text)
        for url in urls:
            if 'aleo.com' not in url and any(tld in url for tld in ['.com', '.cz', '.sk', '.eu', '.net', '.org']):
                return url
        
        return None
    
    def search_email_on_website(self, company_name: str, website_url: str = None) -> tuple:
        """Vyhledá email na webu společnosti"""
        logger.info(f"   🔎 Hledám web společnosti: {company_name[:40]}...")
        
        try:
            # Pokud není URL, zkusit odhadnout
            if not website_url:
                # Pokus o vytvoření URL z názvu
                clean_name = re.sub(r'[^a-zA-Z0-9]', '', company_name.lower())
                possible_urls = [
                    f"https://www.{clean_name}.com",
                    f"https://www.{clean_name}.cz",
                    f"https://{clean_name}.com"
                ]
                
                for test_url in possible_urls[:1]:  # Zkusit jen první
                    try:
                        logger.info(f"   🌐 Zkouším: {test_url}")
                        self.driver.get(test_url)
                        time.sleep(3)
                        
                        # Kontrola, zda stránka existuje (ne 404)
                        if "404" not in self.driver.title.lower() and len(self.driver.page_source) > 1000:
                            website_url = test_url
                            break
                    except:
                        continue
            
            if website_url:
                logger.info(f"   📄 Načítám web: {website_url[:50]}...")
                
                # Otevření webu
                self.driver.get(website_url)
                time.sleep(3)
                
                soup = BeautifulSoup(self.driver.page_source, 'lxml')
                
                # Hledání kontaktní stránky
                contact_links = soup.find_all('a', href=True, text=re.compile(r'contact|kontakt', re.I))
                
                if contact_links:
                    contact_url = contact_links[0].get('href', '')
                    if not contact_url.startswith('http'):
                        from urllib.parse import urljoin
                        contact_url = urljoin(website_url, contact_url)
                    
                    logger.info(f"   📞 Našel jsem kontaktní stránku: {contact_url[:50]}...")
                    self.driver.get(contact_url)
                    time.sleep(2)
                    soup = BeautifulSoup(self.driver.page_source, 'lxml')
                
                # Hledání emailu
                page_text = soup.get_text()
                email = self._extract_email(page_text)
                
                if email:
                    logger.info(f"   ✓ Email nalezen na webu: {email}")
                    return email, f"Web společnosti ({website_url})"
                else:
                    logger.info(f"   ✗ Email na webu nenalezen")
                    return None, "Email nenalezen na webu"
            
            logger.info(f"   ⚠️  Web společnosti nebyl nalezen")
            return None, "Web nenalezen"
            
        except Exception as e:
            logger.warning(f"   ⚠️  Chyba při hledání na webu: {e}")
            return None, f"Chyba: {str(e)[:30]}"
    
    def process_company(self, company: dict, search_website: bool = True) -> dict:
        """Zpracuje jednu společnost"""
        result = {
            'název_společnosti': company['name'],
            'email': None,
            'zdroj': None,
            'url_profilu': company['url'],
            'web_společnosti': None
        }
        
        try:
            # 1. Pokus - profil na aleo.com
            logger.info(f"\n[Firma] {company['name'][:60]}")
            logger.info(f"   📄 Otevírám profil: {company['url'][:60]}...")
            
            self.driver.get(company['url'])
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            page_text = soup.get_text()
            
            # Hledání emailu na profilu
            email = self._extract_email(page_text)
            
            if email:
                result['email'] = email
                result['zdroj'] = 'Profil na aleo.com'
                logger.info(f"   ✓ Email z profilu: {email}")
                return result
            
            logger.info(f"   ⚠️  Email na profilu nenalezen")
            
            # 2. Pokus - extrakce webu společnosti z profilu
            website_url = self.extract_website_from_profile(soup)
            
            if website_url:
                result['web_společnosti'] = website_url
                logger.info(f"   🌐 Nalezen web v profilu: {website_url[:50]}")
            
            # 3. Pokus - vyhledání na webu společnosti
            if search_website:
                email, source = self.search_email_on_website(company['name'], website_url)
                if email:
                    result['email'] = email
                    result['zdroj'] = source
                    return result
            
            result['zdroj'] = 'Email nenalezen'
            
        except Exception as e:
            logger.error(f"   ❌ Chyba: {e}")
            result['zdroj'] = f'Chyba: {str(e)[:50]}'
        
        return result
    
    def run(self, url: str = "https://aleo.com/int/", 
            max_companies: int = None, 
            search_website: bool = True):
        """Hlavní metoda scraperu"""
        
        logger.info("=" * 70)
        logger.info("ALEO.COM INTERNATIONAL SCRAPER - START")
        logger.info("=" * 70)
        
        # 1. Získání seznamu společností
        self.scrape_company_list(url, max_companies)
        
        if not self.companies:
            logger.error("❌ Žádné společnosti nebyly nalezeny!")
            logger.info("\n💡 TIP: Zkuste:")
            logger.info("   1. Zkontrolovat URL")
            logger.info("   2. Ručně otevřít stránku a podívat se na HTML strukturu")
            logger.info("   3. Použít semi-manuální režim")
            return
        
        # 2. Zpracování společností
        logger.info("\n" + "=" * 70)
        logger.info(f"ZPRACOVÁVÁM {len(self.companies)} SPOLEČNOSTÍ")
        logger.info("=" * 70)
        
        for i, company in enumerate(self.companies, 1):
            logger.info(f"\n[{i}/{len(self.companies)}]")
            result = self.process_company(company, search_website)
            self.results.append(result)
            time.sleep(2)  # Prodleva mezi požadavky
        
        # 3. Uložení výsledků
        self.save_results()
        
        # 4. Statistiky
        logger.info("\n" + "=" * 70)
        logger.info("✅ SCRAPING DOKONČEN")
        logger.info("=" * 70)
        logger.info(f"📊 Celkem zpracováno: {len(self.results)}")
        logger.info(f"✓ Nalezeno emailů: {sum(1 for r in self.results if r['email'])}")
        logger.info(f"✗ Nenalezeno: {sum(1 for r in self.results if not r['email'])}")
        logger.info(f"📈 Úspěšnost: {sum(1 for r in self.results if r['email']) / len(self.results) * 100:.1f}%")
        logger.info("=" * 70)
    
    def save_results(self):
        """Uložení výsledků"""
        if not self.results:
            logger.warning("⚠️  Žádné výsledky k uložení")
            return
        
        df = pd.DataFrame(self.results)
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV
        csv_path = output_dir / f'aleo_int_{timestamp}.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"\n💾 CSV uloženo: {csv_path}")
        
        # Excel
        excel_path = output_dir / f'aleo_int_{timestamp}.xlsx'
        df.to_excel(excel_path, index=False, engine='openpyxl')
        logger.info(f"💾 Excel uloženo: {excel_path}")
        
        # Statistiky
        stats = {
            'celkem_zpracováno': len(self.results),
            'nalezeno_emailů': int(df['email'].notna().sum()),
            'nenalezeno_emailů': int(df['email'].isna().sum()),
            'úspěšnost': f"{(df['email'].notna().sum() / len(self.results) * 100):.1f}%",
            'zdroje': {k: int(v) for k, v in df['zdroj'].value_counts().to_dict().items()}
        }
        
        stats_path = output_dir / f'stats_int_{timestamp}.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Statistiky: {stats_path}")
    
    def close(self):
        """Uzavře prohlížeč"""
        if self.driver:
            self.driver.quit()
            logger.info("\n✓ Prohlížeč uzavřen")


def main():
    import argparse
    
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║     ALEO.COM INTERNATIONAL SCRAPER                                ║
║     Automatické stahování dat + vyhledávání emailů               ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    parser = argparse.ArgumentParser(description='Aleo.com International Scraper')
    parser.add_argument('--url', type=str, default='https://aleo.com/int/',
                       help='URL pro scraping (výchozí: https://aleo.com/int/)')
    parser.add_argument('--max', type=int, default=None,
                       help='Maximální počet společností')
    parser.add_argument('--no-website', action='store_true',
                       help='Nehledat na webech společností (rychlejší)')
    
    args = parser.parse_args()
    
    scraper = AleoInternationalScraper()
    
    try:
        scraper.run(
            url=args.url,
            max_companies=args.max,
            search_website=not args.no_website
        )
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Scraping přerušen uživatelem")
    except Exception as e:
        logger.error(f"\n❌ Kritická chyba: {e}", exc_info=True)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
