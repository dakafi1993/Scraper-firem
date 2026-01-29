"""
Stahování HTML pro všechny sekce pomocí requests + BeautifulSoup
"""

import requests
from bs4 import BeautifulSoup
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

def download_section(section_code, section_letter, section_name):
    """Stáhne HTML pro jednu sekci"""
    url = f"https://panoramafirm.pl/{section_code},{section_letter}/branze.html"
    
    print(f"\n📂 {section_name}")
    print(f"   URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        categories = extract_categories_from_html(response.text, section_name)
        print(f"   ✅ Nalezeno: {len(categories)} kategorií")
        
        return categories
        
    except Exception as e:
        print(f"   ❌ Chyba: {str(e)}")
        return []

def main():
    print("=" * 80)
    print("🔍 PANORAMA FIRM - Stahování všech kategorií (requests + BeautifulSoup)")
    print("=" * 80)
    
    all_categories = []
    
    for section_code, section_letter, section_name in SECTIONS:
        categories = download_section(section_code, section_letter, section_name)
        all_categories.extend(categories)
        time.sleep(2)  # Pauza mezi požadavky
    
    print("\n" + "=" * 80)
    print(f"📊 CELKEM NALEZENO: {len(all_categories)} kategorií")
    print("=" * 80)
    
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
        print(f"{section_name:50} {count:4} kategorií")
    
    print("\n" + "=" * 80)
    print("✅ HOTOVO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
