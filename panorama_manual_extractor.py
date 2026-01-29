"""
Manuální extraktor - stáhne HTML každé sekce a parsuje kategorie
"""
import requests
from bs4 import BeautifulSoup
import time
import re

SECTIONS = {
    'biuro,z': 'Biuro',
    'kancelaria,o': 'Kancelaria', 
    'budownictwo,b': 'Budownictwo',
    'dom_i_ogród,c': 'Dom i ogród',
    'dzieci,u': 'Dzieci',
    'finanse_i_ubezpieczenia,r': 'Finanse i ubezpieczenia',
    'instytucje_urzędy,f': 'Instytucje, urzędy',
    'motoryzacja_i_transport,h': 'Motoryzacja i transport',
    'nauka,i': 'Nauka',
    'odzież_i_tekstylia,g': 'Odzież i tekstylia',
    'porady,w': 'Porady',
    'przemysł_i_energetyka,k': 'Przemysł i energetyka',
    'rolnictwo_i_leśnictwo,j': 'Rolnictwo i leśnictwo',
    'rozrywka_i_rekreacja,l': 'Rozrywka i rekreacja',
    'telekomunikacja_internet_technologie,t': 'Telekomunikacja, internet, technologie',
    'turystyka,m': 'Turystyka',
    'usługi_dla_firm,n': 'Usługi dla firm',
    'usługi_dla_każdego,p': 'Usługi dla każdego',
    'zdrowie_i_uroda,s': 'Zdrowie i uroda',
    'żywność_i_używki,a': 'Żywność i używki',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

all_categories = {}

for url_key, section_name in SECTIONS.items():
    print(f"\n{'='*80}")
    print(f"📂 {section_name}")
    
    # Zkusit různé URL formáty
    urls_to_try = [
        f'https://panoramafirm.pl/{url_key}/branze.html',
        f'https://panoramafirm.pl/{url_key.split(",")[0]}',
        f'https://panoramafirm.pl/kategorie/{url_key}',
    ]
    
    found = False
    for url in urls_to_try:
        try:
            print(f"   Zkouším: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Uložit HTML pro debug
                with open(f'd:/skript/debug_{url_key.split(",")[0]}.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                
                # Najít všechny odkazy
                links = soup.find_all('a', href=True)
                section_cats = []
                
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Kategorie jsou odkazy začínající / a obsahující text
                    if (href.startswith('/') and 
                        text and 
                        len(text) > 2 and 
                        len(text) < 100 and
                        not href.endswith('.html') and
                        ',' not in href):
                        
                        full_url = f'https://panoramafirm.pl{href}'
                        category_key = f'panorama_{full_url}'
                        category_label = f'PANORAMA [{section_name}]: {text}'
                        
                        if category_key not in all_categories:
                            all_categories[category_key] = category_label
                            section_cats.append(text)
                
                if section_cats:
                    print(f"   ✅ Nalezeno {len(section_cats)} kategorií")
                    # Zobrazit prvních 5
                    for cat in section_cats[:5]:
                        print(f"      - {cat}")
                    if len(section_cats) > 5:
                        print(f"      ... a {len(section_cats) - 5} dalších")
                    found = True
                    break
                    
        except Exception as e:
            print(f"   ❌ Chyba: {e}")
            continue
    
    if not found:
        print(f"   ⚠️  Žádné kategorie nenalezeny")
    
    time.sleep(1)

print(f"\n{'='*80}")
print(f"📊 CELKEM: {len(all_categories)} kategorií")
print(f"📂 Z počtu sekcí: {len(SECTIONS)}")
print(f"{'='*80}")

# Seskupit podle sekcí
by_section = {}
for key, label in all_categories.items():
    if '[' in label and ']:' in label:
        section = label.split('[')[1].split(']')[0]
        if section not in by_section:
            by_section[section] = 0
        by_section[section] += 1

print("\n📋 Kategorie podle sekcí:")
for section in sorted(by_section.keys()):
    print(f"   {section}: {by_section[section]} kategorií")

# Uložit
output_file = 'd:/skript/panorama_manual_categories.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    for key, label in sorted(all_categories.items(), key=lambda x: x[1]):
        safe_label = label.replace("'", "\\'")
        safe_key = key.replace("'", "\\'")
        f.write(f"    '{safe_key}': '{safe_label}',\n")

print(f"\n💾 Uloženo do: {output_file}")
print("✅ HOTOVO!")
