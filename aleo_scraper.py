#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aleo.com Web Scraper
Automatické získávání veřejně dostupných informací o firmách z katalogu aleo.com
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
import json
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Konfigurace loggingu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AleoScraper:
    """Scraper pro získávání veřejně dostupných dat z katalogu aleo.com"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Inicializace scraperu
        
        Args:
            config_file: Cesta ke konfiguračnímu souboru
        """
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.ua = UserAgent()
        self.results = []
        self.failed_companies = []
        self.driver = None
        
        # Nastavení session
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'cs,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Inicializace Selenium WebDriver
        if self.config.get('use_selenium', True):
            self._init_selenium()
        
    def _load_config(self, config_file: str) -> dict:
        """Načte konfiguraci ze souboru"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Konfigurační soubor {config_file} nebyl nalezen!")
            raise
    
    def _init_selenium(self):
        """Inicializuje Selenium WebDriver"""
        try:
            logger.info("Inicializuji Selenium WebDriver...")
            chrome_options = Options()
            
            if self.config.get('headless', False):
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument(f'user-agent={self.ua.random}')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✓ Selenium WebDriver inicializován")
        except Exception as e:
            logger.warning(f"Nepodařilo se inicializovat Selenium: {e}")
            logger.warning("Pokračuji s použitím requests...")
            self.driver = None
    
    def _make_request(self, url: str, retries: int = 3) -> Optional[str]:
        """
        Provede HTTP požadavek s ošetřením chyb a rate limiting
        Používá Selenium pokud je dostupný, jinak requests
        
        Args:
            url: URL adresa k načtení
            retries: Počet opakování při chybě
            
        Returns:
            HTML obsah stránky nebo None při chybě
        """
        for attempt in range(retries):
            try:
                # Respektování rate limiting
                time.sleep(self.config['request_delay'])
                
                # Použití Selenium pokud je dostupný
                if self.driver:
                    try:
                        self.driver.get(url)
                        # Čekání na načtení stránky
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        time.sleep(2)  # Dodatečná prodleva pro JS
                        return self.driver.page_source
                    except Exception as e:
                        logger.warning(f"Selenium chyba: {e}")
                        if attempt < retries - 1:
                            continue
                        return None
                
                # Fallback na requests
                response = self.session.get(
                    url, 
                    timeout=self.config['timeout'],
                    allow_redirects=True
                )
                
                # Kontrola HTTP status kódu
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    logger.warning(f"Rate limit - čekám {self.config['rate_limit_wait']}s")
                    time.sleep(self.config['rate_limit_wait'])
                    continue
                elif response.status_code == 403:
                    logger.warning(f"Přístup zakázán (403) pro {url}")
                    return None
                elif response.status_code == 404:
                    logger.warning(f"Stránka nenalezena (404): {url}")
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code} pro {url}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout při načítání {url} (pokus {attempt + 1}/{retries})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Chyba připojení k {url} (pokus {attempt + 1}/{retries})")
            except Exception as e:
                logger.error(f"Neočekávaná chyba: {e}")
                
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                logger.info(f"Čekám {wait_time}s před dalším pokusem...")
                time.sleep(wait_time)
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """
        Extrahuje e-mailovou adresu z textu
        
        Args:
            text: Text k prohledání
            
        Returns:
            První nalezená e-mailová adresa nebo None
        """
        if not text:
            return None
            
        # Regex pattern pro e-mailové adresy
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if emails:
            # Filtrování běžných placeholder e-mailů
            filtered = [e for e in emails if not any(
                placeholder in e.lower() 
                for placeholder in ['example.com', 'domain.com', 'email.cz']
            )]
            return filtered[0] if filtered else None
        return None
    
    def _search_email_on_page(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Hledá e-mail na stránce společnosti
        
        Args:
            soup: BeautifulSoup objekt stránky
            
        Returns:
            Nalezená e-mailová adresa nebo None
        """
        # Hledání e-mailu v celém textu stránky
        page_text = soup.get_text()
        email = self._extract_email(page_text)
        
        if email:
            return email
        
        # Hledání v mailto: odkazech
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            href = link.get('href', '')
            email_match = re.search(r'mailto:([^\?]+)', href, re.I)
            if email_match:
                return email_match.group(1).strip()
        
        return None
    
    def _extract_company_website(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extrahuje oficiální webovou stránku společnosti z profilu na aleo.com
        
        Args:
            soup: BeautifulSoup objekt stránky
            
        Returns:
            URL webové stránky nebo None
        """
        # Hledání webových odkazů (různé možné CSS třídy a atributy)
        website_patterns = [
            {'class': re.compile(r'website', re.I)},
            {'class': re.compile(r'web', re.I)},
            {'class': re.compile(r'homepage', re.I)},
            {'itemprop': 'url'}
        ]
        
        for pattern in website_patterns:
            links = soup.find_all('a', pattern)
            for link in links:
                href = link.get('href', '')
                if href and href.startswith('http'):
                    # Ignorovat interní odkazy aleo.com
                    if 'aleo.com' not in href:
                        return href
        
        return None
    
    def _search_company_website(self, company_name: str) -> Optional[str]:
        """
        Vyhledá oficiální web společnosti pomocí vyhledávače (simulace)
        
        Args:
            company_name: Název společnosti
            
        Returns:
            Email nalezený na webu společnosti nebo None
        """
        logger.info(f"Hledám web pro společnost: {company_name}")
        
        # POZNÁMKA: Tato funkce by v produkční verzi mohla využít:
        # - Google Search API (vyžaduje API klíč)
        # - DuckDuckGo API
        # - Bing Search API
        # Pro demonstraci vrací None - uživatel může funkci rozšířit
        
        logger.warning("Vyhledávání webu společnosti není implementováno - vyžaduje API klíč")
        return None
    
    def scrape_company_list(self, start_url: str, max_pages: int = None) -> List[Dict]:
        """
        Získá seznam společností z katalogových stránek
        
        Args:
            start_url: Počáteční URL katalogu
            max_pages: Maximální počet stránek k procházení
            
        Returns:
            Seznam slovníků s informacemi o společnostech
        """
        companies = []
        current_url = start_url
        page_count = 0
        
        logger.info(f"Zahajuji scraping od: {start_url}")
        
        while current_url and (max_pages is None or page_count < max_pages):
            page_count += 1
            logger.info(f"Zpracovávám stránku {page_count}: {current_url}")
            
            html_content = self._make_request(current_url)
            if not html_content:
                logger.error(f"Nepodařilo se načíst stránku: {current_url}")
                
                # Dotaz na manuální zásah
                if self.config.get('manual_intervention', False):
                    user_input = input(
                        f"\n⚠️  Nepodařilo se načíst stránku.\n"
                        f"URL: {current_url}\n"
                        f"Pokračovat? (y/n/url pro zadání nové URL): "
                    )
                    if user_input.lower() == 'y':
                        break
                    elif user_input.startswith('http'):
                        current_url = user_input
                        continue
                break
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            # POZNÁMKA: Následující selektory jsou obecné a musí být přizpůsobeny
            # skutečné struktuře aleo.com. Tento kód slouží jako šablona.
            
            # Hledání odkazů na profily společností
            company_links = soup.find_all('a', href=re.compile(r'/firmy/|/company/|/profil/', re.I))
            
            for link in company_links:
                company_url = link.get('href', '')
                if company_url and not company_url.startswith('http'):
                    company_url = f"https://www.aleo.com{company_url}"
                
                company_name = link.get_text(strip=True)
                
                if company_url and company_name:
                    companies.append({
                        'name': company_name,
                        'url': company_url
                    })
            
            # Hledání dalšího odkazu na stránkování
            next_link = soup.find('a', text=re.compile(r'další|next|›|»', re.I))
            if not next_link:
                next_link = soup.find('a', {'class': re.compile(r'next|pagination', re.I)})
            
            if next_link:
                next_url = next_link.get('href', '')
                if next_url and not next_url.startswith('http'):
                    current_url = f"https://www.aleo.com{next_url}"
                elif next_url:
                    current_url = next_url
                else:
                    break
            else:
                logger.info("Žádná další stránka nebyla nalezena")
                break
            
            logger.info(f"Nalezeno {len(companies)} společností")
        
        return companies
    
    def scrape_company_details(self, company: Dict) -> Dict:
        """
        Získá detaily o společnosti včetně e-mailu
        
        Args:
            company: Slovník s name a url
            
        Returns:
            Rozšířený slovník s email a source
        """
        logger.info(f"Zpracovávám: {company['name']}")
        
        result = {
            'název_společnosti': company['name'],
            'email': None,
            'zdroj': None,
            'url_profilu': company['url']
        }
        
        # Načtení profilu společnosti
        html_content = self._make_request(company['url'])
        if not html_content:
            result['zdroj'] = 'Chyba načtení'
            return result
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Hledání e-mailu na profilu
        email = self._search_email_on_page(soup)
        if email:
            result['email'] = email
            result['zdroj'] = 'Profil na aleo.com'
            return result
        
        # Pokud e-mail nebyl nalezen, pokusit se najít web společnosti
        if self.config.get('search_company_website', False):
            website_url = self._extract_company_website(soup)
            
            if website_url:
                logger.info(f"Nalezen web společnosti: {website_url}")
                web_html = self._make_request(website_url)
                
                if web_html:
                    web_soup = BeautifulSoup(web_html, 'lxml')
                    email = self._search_email_on_page(web_soup)
                    
                    if email:
                        result['email'] = email
                        result['zdroj'] = f'Web společnosti ({website_url})'
                        return result
            
            # Pokus o vyhledání webu (vyžaduje API)
            if not email:
                email = self._search_company_website(company['name'])
                if email:
                    result['email'] = email
                    result['zdroj'] = 'Vyhledávání'
        
        if not result['email']:
            result['zdroj'] = 'E-mail nenalezen'
        
        return result
    
    def run(self, start_url: str, max_companies: int = None):
        """
        Hlavní metoda pro spuštění scraperu
        
        Args:
            start_url: Počáteční URL katalogu
            max_companies: Maximální počet společností k zpracování
        """
        logger.info("=" * 60)
        logger.info("ALEO.COM SCRAPER - START")
        logger.info("=" * 60)
        
        # Získání seznamu společností
        companies = self.scrape_company_list(
            start_url, 
            max_pages=self.config.get('max_pages')
        )
        
        if not companies:
            logger.error("Nebyly nalezeny žádné společnosti!")
            return
        
        logger.info(f"Celkem nalezeno {len(companies)} společností")
        
        # Omezení počtu společností
        if max_companies:
            companies = companies[:max_companies]
            logger.info(f"Zpracovávám prvních {max_companies} společností")
        
        # Zpracování jednotlivých společností
        for i, company in enumerate(companies, 1):
            logger.info(f"\n[{i}/{len(companies)}] Zpracovávám společnost...")
            
            try:
                result = self.scrape_company_details(company)
                self.results.append(result)
                
                logger.info(f"✓ {result['název_společnosti']}")
                if result['email']:
                    logger.info(f"  Email: {result['email']}")
                    logger.info(f"  Zdroj: {result['zdroj']}")
                else:
                    logger.info(f"  Email: Nenalezen")
                    
            except Exception as e:
                logger.error(f"Chyba při zpracování {company['name']}: {e}")
                self.failed_companies.append(company)
        
        # Uložení výsledků
        self.save_results()
        
        logger.info("=" * 60)
        logger.info("SCRAPING DOKONČEN")
        logger.info(f"Úspěšně zpracováno: {len(self.results)}")
        logger.info(f"Nezdařilo se: {len(self.failed_companies)}")
        logger.info("=" * 60)
    
    def save_results(self):
        """Uloží výsledky do CSV a Excel souboru"""
        if not self.results:
            logger.warning("Žádné výsledky k uložení")
            return
        
        # Vytvoření DataFrame
        df = pd.DataFrame(self.results)
        
        # Vytvoření výstupní složky
        output_dir = Path(self.config.get('output_dir', 'output'))
        output_dir.mkdir(exist_ok=True)
        
        # Časové razítko pro název souboru
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Uložení do CSV
        csv_path = output_dir / f'aleo_data_{timestamp}.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"✓ CSV uloženo: {csv_path}")
        
        # Uložení do Excel
        excel_path = output_dir / f'aleo_data_{timestamp}.xlsx'
        df.to_excel(excel_path, index=False, engine='openpyxl')
        logger.info(f"✓ Excel uloženo: {excel_path}")
        
        # Statistiky
        stats = {
            'celkem_zpracováno': len(self.results),
            'nalezeno_emailů': df['email'].notna().sum(),
            'nenalezeno_emailů': df['email'].isna().sum(),
            'úspěšnost': f"{(df['email'].notna().sum() / len(self.results) * 100):.1f}%"
        }
        
        stats_path = output_dir / f'stats_{timestamp}.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Statistiky uloženy: {stats_path}")
        logger.info(f"\nStatistiky:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
    
    def close(self):
        """Uzavře Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✓ Selenium driver uzavřen")
            except:
                pass


def main():
    """Hlavní funkce programu"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Aleo.com Web Scraper - Získávání veřejných dat o firmách'
    )
    parser.add_argument(
        '--url',
        type=str,
        default='https://www.aleo.com/firmy',
        help='Počáteční URL katalogu (výchozí: https://www.aleo.com/firmy)'
    )
    parser.add_argument(
        '--max-companies',
        type=int,
        help='Maximální počet společností k zpracování'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Cesta ke konfiguračnímu souboru (výchozí: config.json)'
    )
    
    args = parser.parse_args()
    
    scraper = None
    try:
        scraper = AleoScraper(config_file=args.config)
        scraper.run(start_url=args.url, max_companies=args.max_companies)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Scraping přerušen uživatelem")
    except Exception as e:
        logger.error(f"\n❌ Kritická chyba: {e}", exc_info=True)
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()
