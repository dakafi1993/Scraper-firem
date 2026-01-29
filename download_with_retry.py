"""
Stahování kategorií s anti-blocking mechanismy
- Retry logika s exponenciálním backoffem
- Rotující User-Agents
- Session pro persistent cookies
- Delší timeouty a pauzy
"""

import requests
from bs4 import BeautifulSoup
import time
from collections import defaultdict
import random

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

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def extract_categories_from_html(html_content, section_name):
    """Extrahuje kategorie z HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Najít všechny div elementy s id začínajícím na "letter-"
    letter_divs = soup.find_all('div', id=lambda x: x and x.startswith('letter-'))
    
    categories = []
    
    for letter_div in letter_divs:
        letter_id = letter_div.get('id', '')
        letter = letter_id.replace('letter-', '')
        
        # V každém letter-div najít všechny <a> linky v <h3>
        h3_elements = letter_div.find_all('h3')
        
        for h3 in h3_elements:
            link = h3.find('a')
            if link:
                name = link.text.strip()
                href = link.get('href', '')
                
                # Najít popis
                parent_li = h3.find_parent('li')
                description = ""
                if parent_li:
                    p_tag = parent_li.find('p')
                    if p_tag:
                        description = p_tag.text.strip()
                
                categories.append({
                    'letter': letter,
                    'name': name,
                    'url': f"https://panoramafirm.pl{href}" if href.startswith('/') else href,
                    'description': description,
                    'section': section_name
                })
    
    return categories

def download_section(session, section_code, section_letter, section_name, attempt=1):
    """Stáhne HTML pro jednu sekci s retry logikou"""
    url = f"https://panoramafirm.pl/{section_code},{section_letter}/branze.html"
    
    if attempt == 1:
        print(f"\n📂 {section_name}")
        print(f"   URL: {url}")
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    max_retries = 5
    base_timeout = 60
    
    try:
        # Exponenciální backoff pro timeout
        timeout = base_timeout * (2 ** (attempt - 1))
        
        print(f"   🔄 Pokus {attempt}/{max_retries} (timeout: {timeout}s)...")
        
        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        categories = extract_categories_from_html(response.text, section_name)
        print(f"   ✅ Nalezeno: {len(categories)} kategorií")
        
        return categories, True
        
    except requests.exceptions.Timeout:
        print(f"   ⏱️ Timeout po {timeout}s")
        if attempt < max_retries:
            wait_time = 5 * attempt
            print(f"   ⏳ Čekám {wait_time}s před dalším pokusem...")
            time.sleep(wait_time)
            return download_section(session, section_code, section_letter, section_name, attempt + 1)
        else:
            print(f"   ❌ Všechny pokusy selhaly (timeout)")
            return [], False
            
    except requests.exceptions.ConnectionError as e:
        print(f"   🔌 Chyba připojení: {str(e)[:100]}")
        if attempt < max_retries:
            wait_time = 10 * attempt
            print(f"   ⏳ Čekám {wait_time}s před dalším pokusem...")
            time.sleep(wait_time)
            return download_section(session, section_code, section_letter, section_name, attempt + 1)
        else:
            print(f"   ❌ Všechny pokusy selhaly (connection error)")
            return [], False
            
    except Exception as e:
        print(f"   ❌ Chyba: {type(e).__name__}: {str(e)[:100]}")
        if attempt < max_retries:
            wait_time = 10 * attempt
            print(f"   ⏳ Čekám {wait_time}s před dalším pokusem...")
            time.sleep(wait_time)
            return download_section(session, section_code, section_letter, section_name, attempt + 1)
        else:
            print(f"   ❌ Všechny pokusy selhaly")
            return [], False

def main():
    print("=" * 80)
    print("🔍 PANORAMA FIRM - Stahování s anti-blocking mechanismy")
    print("=" * 80)
    
    # Vytvořit session pro persistent cookies
    session = requests.Session()
    
    all_categories = []
    failed_sections = []
    
    for i, (section_code, section_letter, section_name) in enumerate(SECTIONS, 1):
        print(f"\n[{i}/{len(SECTIONS)}]", end=" ")
        
        categories, success = download_section(session, section_code, section_letter, section_name)
        
        if success:
            all_categories.extend(categories)
        else:
            failed_sections.append(section_name)
        
        # Delší pauza mezi sekcemi
        if i < len(SECTIONS):
            wait_time = random.randint(3, 7)
            print(f"   💤 Pauza {wait_time}s před další sekcí...")
            time.sleep(wait_time)
    
    print("\n" + "=" * 80)
    print(f"📊 CELKEM NALEZENO: {len(all_categories)} kategorií")
    if failed_sections:
        print(f"⚠️  SELHALO: {len(failed_sections)} sekcí: {', '.join(failed_sections)}")
    print("=" * 80)
    
    if len(all_categories) == 0:
        print("\n❌ Nepodařilo se stáhnout žádné kategorie!")
        return
    
    # Seskupit podle sekcí
    by_section = defaultdict(list)
    for cat in all_categories:
        by_section[cat['section']].append(cat)
    
    # Uložit do textového souboru
    output_file = "panorama_ALL_categories.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PANORAMA FIRM - KOMPLETNÍ SEZNAM KATEGORIÍ\n")
        f.write("=" * 80 + "\n")
        f.write(f"Celkem: {len(all_categories)} kategorií z {len(SECTIONS)} sekcí\n")
        if failed_sections:
            f.write(f"SELHALO: {len(failed_sections)} sekcí: {', '.join(failed_sections)}\n")
        f.write("=" * 80 + "\n\n")
        
        for section_name in [s[2] for s in SECTIONS]:
            cats = by_section[section_name]
            if cats:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"{section_name} ({len(cats)} kategorií)\n")
                f.write(f"{'=' * 80}\n\n")
                
                for cat in sorted(cats, key=lambda x: x['name']):
                    f.write(f"• {cat['name']}\n")
                    f.write(f"  URL: {cat['url']}\n")
                    if cat['description']:
                        desc = cat['description'][:200] + "..." if len(cat['description']) > 200 else cat['description']
                        f.write(f"  {desc}\n")
                    f.write("\n")
    
    print(f"\n✅ Textový soubor: {output_file}")
    
    # Vytvořit Python dict pro web_scraper.py
    python_dict = "panorama_categories_dict.py"
    with open(python_dict, 'w', encoding='utf-8') as f:
        f.write('"""Auto-generovaný seznam kategorií pro web_scraper.py"""\n\n')
        f.write('CATEGORIES = {\n')
        
        for section_name in [s[2] for s in SECTIONS]:
            cats = by_section[section_name]
            if cats:
                f.write(f'    "{section_name}": [\n')
                for cat in sorted(cats, key=lambda x: x['name']):
                    f.write(f'        "{cat["name"]}",\n')
                f.write('    ],\n')
        
        f.write('}\n')
    
    print(f"✅ Python dict: {python_dict}")
    
    # Statistiky
    print("\n" + "=" * 80)
    print("📊 STATISTIKY PO SEKCÍCH:")
    print("=" * 80)
    for section_name in [s[2] for s in SECTIONS]:
        count = len(by_section[section_name])
        status = "❌ CHYBÍ" if count == 0 and section_name not in failed_sections else ""
        print(f"{section_name:50} {count:4} kategorií {status}")
    
    print("\n" + "=" * 80)
    print("✅ HOTOVO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
