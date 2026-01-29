"""
Zpracování ručně stažených HTML souborů
Najde všechny *_branze.html soubory ve složce a extrahuje kategorie
"""

import os
import glob
from bs4 import BeautifulSoup
from collections import defaultdict

# Mapování názvů souborů na názvy sekcí
FILE_TO_SECTION = {
    'biuro_branze.html': 'Biuro',
    'budownictwo_branze.html': 'Budownictwo',
    'dom_i_ogrod_branze.html': 'Dom i ogród',
    'branze_page_structure.html': 'Dom i ogród',  # Už máme!
    'dzieci_branze.html': 'Dzieci',
    'finanse_branze.html': 'Finanse i ubezpieczenia',
    'instytucje_branze.html': 'Instytucje, urzędy',
    'kancelaria_branze.html': 'Kancelaria',
    'motoryzacja_branze.html': 'Motoryzacja i transport',
    'nauka_branze.html': 'Nauka',
    'odziez_branze.html': 'Odzież i tekstylia',
    'porady_branze.html': 'Porady',
    'przemysl_branze.html': 'Przemysł i energetyka',
    'rolnictwo_branze.html': 'Rolnictwo i leśnictwo',
    'rozrywka_branze.html': 'Rozrywka i rekreacja',
    'telekomunikacja_branze.html': 'Telekomunikacja, Internet, technologie',
    'turystyka_branze.html': 'Turystyka',
    'uslugi_dla_firm_branze.html': 'Usługi dla firm',
    'uslugi_dla_kazdego_branze.html': 'Usługi dla każdego',
    'zdrowie_branze.html': 'Zdrowie i uroda',
    'zdrowie_i_uroda_branze.html': 'Zdrowie i uroda',  # Nově stažený
    'zywnosc_branze.html': 'Żywność i używki',
    'zywnosc_i_uzywki_branze.html': 'Żywność i używki',  # Nově stažený
}

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

def main():
    print("=" * 80)
    print("🔍 ZPRACOVÁNÍ RUČNĚ STAŽENÝCH HTML SOUBORŮ")
    print("=" * 80)
    
    # Najít všechny HTML soubory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_files = glob.glob(os.path.join(script_dir, '*_branze.html'))
    html_files.extend(glob.glob(os.path.join(script_dir, 'branze_page_structure.html')))
    
    print(f"\n📁 Nalezeno HTML souborů: {len(html_files)}")
    
    all_categories = []
    processed_sections = set()
    
    for html_file in html_files:
        filename = os.path.basename(html_file)
        
        if filename not in FILE_TO_SECTION:
            print(f"\n⚠️  Neznámý soubor: {filename} (přeskakuji)")
            continue
        
        section_name = FILE_TO_SECTION[filename]
        
        # Přeskoč duplicity
        if section_name in processed_sections:
            print(f"\n⏭️  {section_name} - už zpracováno (přeskakuji)")
            continue
        
        print(f"\n📂 {section_name}")
        print(f"   Soubor: {filename}")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            categories = extract_categories_from_html(html_content, section_name)
            print(f"   ✅ Nalezeno: {len(categories)} kategorií")
            
            all_categories.extend(categories)
            processed_sections.add(section_name)
            
        except Exception as e:
            print(f"   ❌ Chyba: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"📊 CELKEM NALEZENO: {len(all_categories)} kategorií")
    print(f"📊 ZPRACOVÁNO SEKCÍ: {len(processed_sections)}/20")
    print("=" * 80)
    
    if len(all_categories) == 0:
        print("\n❌ Žádné kategorie nenalezeny!")
        print("\n💡 NÁVOD:")
        print("   1. Otevři prohlížeč")
        print("   2. Jdi na https://panoramafirm.pl/dom_i_ogród,c/branze.html")
        print("   3. Ulož stránku (Ctrl+S) jako 'dom_i_ogrod_branze.html'")
        print("   4. Umísti soubor do d:\\skript\\")
        print("   5. Spusť tento skript znovu")
        print("\n   Nebo spusť: python NAVOD_RUCNI_STAHOVANI.py")
        return
    
    # Seskupit podle sekcí
    by_section = defaultdict(list)
    for cat in all_categories:
        by_section[cat['section']].append(cat)
    
    # Uložit do textového souboru
    output_file = "panorama_MANUAL_categories.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PANORAMA FIRM - MANUÁLNĚ EXTRAHOVANÉ KATEGORIE\n")
        f.write("=" * 80 + "\n")
        f.write(f"Celkem: {len(all_categories)} kategorií z {len(processed_sections)}/20 sekcí\n")
        f.write("=" * 80 + "\n\n")
        
        for section_name in sorted(by_section.keys()):
            cats = by_section[section_name]
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
    python_dict = "panorama_manual_dict.py"
    with open(python_dict, 'w', encoding='utf-8') as f:
        f.write('"""Auto-generovaný seznam kategorií z manuálně stažených HTML"""\n\n')
        f.write(f'# Zpracováno {len(processed_sections)}/20 sekcí\n')
        f.write(f'# Celkem {len(all_categories)} kategorií\n\n')
        f.write('CATEGORIES = {\n')
        
        for section_name in sorted(by_section.keys()):
            cats = by_section[section_name]
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
    for section_name in sorted(by_section.keys()):
        count = len(by_section[section_name])
        print(f"{section_name:50} {count:4} kategorií")
    
    # Chybějící sekce
    all_sections = set(FILE_TO_SECTION.values())
    missing = all_sections - processed_sections
    if missing:
        print("\n" + "=" * 80)
        print("⚠️  CHYBĚJÍCÍ SEKCE:")
        print("=" * 80)
        for section in sorted(missing):
            print(f"   - {section}")
        print("\n💡 Pro stažení chybějících sekcí spusť: python NAVOD_RUCNI_STAHOVANI.py")
    
    print("\n" + "=" * 80)
    print("✅ HOTOVO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
