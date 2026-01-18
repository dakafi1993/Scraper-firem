"""
Zachycení API požadavků z aleo.com pomocí Selenium
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
import time
import json

def setup_driver():
    """Nastavení Chrome driveru s loggingem síťových požadavků"""
    chrome_options = Options()
    
    # Povolení zachytávání síťových požadavků
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--v=1')
    
    # Anti-detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Odstranění webdriver property
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
    print("\n⚠️  CLOUDFLARE - Klikněte na checkbox a počkejte")
    print("Čekám 120 sekund...")
    
    start_time = time.time()
    while time.time() - start_time < 120:
        if "cloudflare" not in driver.page_source.lower():
            print("✅ Cloudflare vyřešena!")
            return True
        time.sleep(1)
    return False

def extract_api_calls(driver):
    """Extrahuje API calls z Chrome performance logu"""
    print("\n📡 Analyzuji síťové požadavky...")
    
    logs = driver.get_log('performance')
    api_calls = []
    
    for entry in logs:
        try:
            log = json.loads(entry['message'])
            message = log.get('message', {})
            method = message.get('method', '')
            
            # Hledáme network requesty
            if method == 'Network.requestWillBeSent':
                params = message.get('params', {})
                request = params.get('request', {})
                url = request.get('url', '')
                
                # Filtrujeme zajímavé požadavky
                if any(keyword in url.lower() for keyword in ['api', 'company', 'firma', 'catalog', 'search']):
                    if not any(skip in url.lower() for skip in ['.css', '.js', '.png', '.jpg', '.svg', '.woff', 'google', 'facebook', 'cloudflare']):
                        api_calls.append({
                            'url': url,
                            'method': request.get('method', 'GET'),
                            'headers': request.get('headers', {})
                        })
        except:
            continue
    
    return api_calls

def main():
    url = "https://aleo.com/pl/firmy/artykuly-dla-biur-i-wyposazenie-biurowe"
    
    print("🚀 Spouštím Chrome s network loggingem...")
    driver = setup_driver()
    
    try:
        print(f"\n📂 Načítám: {url}")
        driver.get(url)
        
        # Cloudflare
        if "cloudflare" in driver.page_source.lower():
            if not wait_for_cloudflare(driver):
                print("❌ Cloudflare timeout")
                return
        
        # Čekání na načtení stránky
        print("\n⏳ Čekám 10 sekund na načtení API požadavků...")
        time.sleep(10)
        
        # Scrollování pro trigger lazy loading
        print("📜 Scrolluji stránku...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # Extrakce API calls
        api_calls = extract_api_calls(driver)
        
        # Výpis nalezených API
        print(f"\n✅ Nalezeno {len(api_calls)} API požadavků:")
        print("="*80)
        
        seen_urls = set()
        for call in api_calls:
            if call['url'] not in seen_urls:
                seen_urls.add(call['url'])
                print(f"\n{call['method']}: {call['url']}")
                
                # Výpis důležitých headerů
                if 'authorization' in str(call['headers']).lower():
                    print(f"  Authorization: {call['headers'].get('authorization', 'N/A')}")
        
        # Uložení do souboru
        with open('api_calls.json', 'w', encoding='utf-8') as f:
            json.dump(api_calls, f, indent=2, ensure_ascii=False)
        
        print("\n💾 API požadavky uloženy do: api_calls.json")
        
    finally:
        print("\n🔒 Zavírám browser za 5 sekund...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()
