"""
Panorama Firm - Extraktor VŠECH kategorií ze všech sekcí
Vytvořeno: 2026-01-29
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

# Hlavní kategorie Panorama Firm (s plnými URL názvy)
MAIN_CATEGORIES = {
    '%C5%BCywno%C5%9B%C4%87_i_u%C5%BCywki,a': 'Żywność i używki',
    'budownictwo,b': 'Budownictwo',
    'dom_i_ogr%C3%B3d,c': 'Dom i ogród',
    'dzieci,u': 'Dzieci',
    'finanse_i_ubezpieczenia,r': 'Finanse i ubezpieczenia',
    'instytucje_urz%C4%99dy,f': 'Instytucje, urzędy',
    'motoryzacja_i_transport,h': 'Motoryzacja i transport',
    'nauka,i': 'Nauka',
    'odzie%C5%BC_i_tekstylia,g': 'Odzież i tekstylia',
    'porady,w': 'Porady',
    'przemys%C5%82_i_energetyka,k': 'Przemysł i energetyka',
    'rolnictwo_i_le%C5%9Bnictwo,j': 'Rolnictwo i leśnictwo',
    'rozrywka_i_rekreacja,l': 'Rozrywka i rekreacja',
    'telekomunikacja_internet_technologie,t': 'Telekomunikacja, internet, technologie',
    'turystyka,m': 'Turystyka',
    'us%C5%82ugi_dla_firm,n': 'Usługi dla firm',
    'us%C5%82ugi_dla_ka%C5%BCdego,p': 'Usługi dla każdego',
    'zdrowie_i_uroda,s': 'Zdrowie i uroda',
}

def extract_subcategories(main_cat_url, main_cat_name):
    """Extrahuje všechny podkategorie z dané hlavní kategorie"""
    url = f'https://panoramafirm.pl/{main_cat_url}/branze.html'
    
    print(f"\n📂 {main_cat_name} ({url})")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Hledat všechny odkazy na kategorie
        categories = {}
        
        # Najít kontejner s kategoriemi - hledat div s třídou obsahující kategorie
        # nebo použít všechny li elementy v seznamu
        category_links = []
        
        # Strategie 1: Najít všechny li > a elementy v hlavní oblasti
        for li in soup.find_all('li'):
            link = li.find('a', href=True)
            if link:
                category_links.append(link)
        
        # Pokud jsme nenašli žádné, zkusit všechny odkazy
        if not category_links:
            category_links = soup.find_all('a', href=True)
        
        for link in category_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Filtrovat pouze platné kategorie branží
            # Branže mají URL typu /nazwa_branze nebo /nazwa_branze/miasto
            if (text and 
                len(text) > 2 and 
                href.startswith('/') and 
                not any(skip in href.lower() for skip in [
                    'branze.html', 'kategorie', 'lista', 'firma', 
                    'regiony', 'miasta', 'wizytowki', 'zapytania',
                    'regulamin', 'kontakt', 'polityka', 'cookies',
                    'obowiazkowy', 'dodaj', 'popularne', 'najnowsze',
                    'panorama'
                ]) and
                ',' not in href and  # Wykluczyć linki typu /kategoria,x
                href.count('/') <= 2 and  # Max 2 slashe = /kategoria lub /kategoria/miasto
                len(href) > 2):
                
                # Vytvořit celou URL
                full_url = f'https://panoramafirm.pl{href}'
                
                # Klíč pro slovník
                category_key = f'panorama_{full_url}'
                
                # Název kategorie
                category_label = f'PANORAMA [{main_cat_name}]: {text}'
                
                # Přidat pouze pokud ještě nemáme
                if category_key not in categories:
                    categories[category_key] = category_label
        
        print(f"   ✅ Nalezeno {len(categories)} podkategorií")
        time.sleep(1)  # Ochrana proti rate limitu
        
        return categories
        
    except Exception as e:
        print(f"   ❌ Chyba: {e}")
        return {}

def main():
    """Hlavní funkce - projde všechny sekce a extrahuje kategorie"""
    print("=" * 80)
    print("🔍 PANORAMA FIRM - EXTRAKTOR VŠECH KATEGORIÍ")
    print("=" * 80)
    
    all_categories = {}
    
    # Projít všechny hlavní kategorie
    for url_part, name in MAIN_CATEGORIES.items():
        subcats = extract_subcategories(url_part, name)
        all_categories.update(subcats)
    
    # Výstup
    print("\n" + "=" * 80)
    print(f"📊 CELKEM NALEZENO: {len(all_categories)} kategorií")
    print("=" * 80)
    
    # Uložit do souboru pro snadné zkopírování
    output_file = 'panorama_all_categories.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Všechny kategorie Panorama Firm\n")
        f.write("# Vygenerováno: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        f.write("CATEGORIES = {\n")
        
        for key, value in sorted(all_categories.items()):
            # Escape uvozovky v názvu
            safe_value = value.replace("'", "\\'")
            f.write(f"    '{key}': '{safe_value}',\n")
        
        f.write("}\n")
    
    print(f"\n💾 Uloženo do: {output_file}")
    print(f"\n📋 Ukázka prvních 10 kategorií:")
    for i, (key, value) in enumerate(list(all_categories.items())[:10]):
        print(f"  {i+1}. {value}")
    
    print("\n✅ HOTOVO!")

if __name__ == "__main__":
    main()
