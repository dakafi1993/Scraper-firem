"""
PANORAMA FIRM - Extrakce podle písmen
======================================
Správná extrakce kategorií podle struktury stránky:
- Sekce jsou rozděleny podle písmen (A, B, C...)
- V každém divu s id="letter-X" jsou kategorie
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from collections import defaultdict

# 20 sekcí Panorama Firm
SECTIONS = [
    ("biuro", "z", "Biuro"),
    ("budownictwo", "b", "Budownictwo"),
    ("dom_i_ogród", "c", "Dom i ogród"),
    ("dzieci", "u", "Dzieci"),
    ("finanse_i_ubezpieczenia", "r", "Finanse i ubezpieczenia"),
    ("instytucje_urzędy", "f", "Instytucje, urzędy"),
    ("kancelaria", "y", "Kancelaria"),
    ("motoryzacja_i_transport", "h", "Motoryzacja i transport"),
    ("nauka", "i", "Nauka"),
    ("odzież_i_tekstylia", "g", "Odzież i tekstylia"),
    ("porady", "w", "Porady"),
    ("przemysł_i_energetyka", "k", "Przemysł i energetyka"),
    ("rolnictwo_i_leśnictwo", "j", "Rolnictwo i leśnictwo"),
    ("rozrywka_i_rekreacja", "l", "Rozrywka i rekreacja"),
    ("telekomunikacja_internet_technologie", "t", "Telekomunikacja, Internet, technologie"),
    ("turystyka", "m", "Turystyka"),
    ("usługi_dla_firm", "n", "Usługi dla firm"),
    ("usługi_dla_każdego", "p", "Usługi dla każdego"),
    ("zdrowie_i_uroda", "s", "Zdrowie i uroda"),
    ("żywność_i_używki", "a", "Żywność i używki"),
]

def setup_driver():
    """Nastavení Chrome driveru"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.page_load_strategy = 'eager'  # Rychlejší načítání
    return webdriver.Chrome(options=chrome_options)

def extract_categories_from_section(driver, section_code, section_letter, section_name):
    """
    Extrahuje všechny kategorie z jedné sekce
    """
    url = f"https://panoramafirm.pl/{section_code},{section_letter}/branze.html"
    
    print(f"\n📂 {section_name}")
    print(f"   URL: {url}")
    
    # Retry logika
    max_retries = 3
    for attempt in range(max_retries):
        try:
            driver.get(url)
            time.sleep(5)  # Počkat na načtení
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   ⚠️ Pokus {attempt + 1} selhal, zkouším znovu...")
                time.sleep(3)
            else:
                print(f"   ❌ Všechny pokusy selhaly: {str(e)}")
                return []
    
    try:
        
        categories = []
        
        # Najít všechny div elementy s id="letter-X"
        letter_divs = driver.find_elements(By.CSS_SELECTOR, "div[id^='letter-']")
        
        print(f"   🔤 Nalezeno písmen: {len(letter_divs)}")
        
        for letter_div in letter_divs:
            letter_id = letter_div.get_attribute('id')
            letter = letter_id.replace('letter-', '')
            
            # V každém letter-div najít všechny <a> linky v <h3>
            category_links = letter_div.find_elements(By.CSS_SELECTOR, "h3 a")
            
            for link in category_links:
                href = link.get_attribute('href')
                name = link.text.strip()
                
                if href and name and 'panoramafirm.pl' in href:
                    # Získat popis kategorie (následující <p>)
                    try:
                        parent_li = link.find_element(By.XPATH, "./ancestor::li")
                        description = parent_li.find_element(By.TAG_NAME, "p").text.strip()
                    except:
                        description = ""
                    
                    categories.append({
                        'name': name,
                        'url': href,
                        'letter': letter,
                        'description': description,
                        'section': section_name
                    })
        
        print(f"   ✅ Nalezeno: {len(categories)} kategorií")
        return categories
        
    except Exception as e:
        print(f"   ❌ Chyba: {str(e)}")
        return []

def main():
    print("=" * 80)
    print("🔍 PANORAMA FIRM - Extrakce podle písmen (správná struktura)")
    print("=" * 80)
    
    driver = setup_driver()
    all_categories = []
    
    try:
        for section_code, section_letter, section_name in SECTIONS:
            categories = extract_categories_from_section(
                driver, section_code, section_letter, section_name
            )
            all_categories.extend(categories)
            time.sleep(2)  # Delší pauza mezi sekcemi
        
        print("\n" + "=" * 80)
        print(f"📊 CELKEM NALEZENO: {len(all_categories)} kategorií")
        print("=" * 80)
        
        # Uložit do souboru
        output_file = "panorama_complete_by_letters.txt"
        
        # Seskupit podle sekcí
        by_section = defaultdict(list)
        for cat in all_categories:
            by_section[cat['section']].append(cat)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PANORAMA FIRM - Kompletní seznam kategorií\n")
            f.write("=" * 80 + "\n")
            f.write(f"Celkem: {len(all_categories)} kategorií\n")
            f.write("=" * 80 + "\n\n")
            
            for section_name in [s[2] for s in SECTIONS]:
                cats = by_section[section_name]
                if cats:
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"{section_name} ({len(cats)} kategorií)\n")
                    f.write(f"{'=' * 80}\n\n")
                    
                    # Seskupit podle písmen
                    by_letter = defaultdict(list)
                    for cat in cats:
                        by_letter[cat['letter']].append(cat)
                    
                    for letter in sorted(by_letter.keys()):
                        f.write(f"\n--- {letter} ---\n\n")
                        for cat in by_letter[letter]:
                            f.write(f"• {cat['name']}\n")
                            f.write(f"  URL: {cat['url']}\n")
                            if cat['description']:
                                f.write(f"  Popis: {cat['description']}\n")
                            f.write("\n")
        
        print(f"\n✅ Uloženo do: {output_file}")
        
        # Vytvořit Python dict pro web_scraper.py
        python_dict = "panorama_categories_dict.py"
        with open(python_dict, 'w', encoding='utf-8') as f:
            f.write('"""Auto-generovaný seznam kategorií pro web_scraper.py"""\n\n')
            f.write('CATEGORIES = {\n')
            
            for section_name in [s[2] for s in SECTIONS]:
                cats = by_section[section_name]
                if cats:
                    f.write(f'    "{section_name}": [\n')
                    for cat in cats:
                        f.write(f'        "{cat["name"]}",\n')
                    f.write('    ],\n')
            
            f.write('}\n')
        
        print(f"✅ Python dict uložen do: {python_dict}")
        
        # Statistiky
        print("\n" + "=" * 80)
        print("📊 STATISTIKY PO SEKCÍCH:")
        print("=" * 80)
        for section_name in [s[2] for s in SECTIONS]:
            count = len(by_section[section_name])
            print(f"{section_name:40} {count:4} kategorií")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
