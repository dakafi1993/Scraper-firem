"""
Aktualizace web_scraper.py s novými kategoriemi
"""

import re

# Načíst nové kategorie
with open('panorama_manual_dict.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extrahovat CATEGORIES dict
exec(content)

# Vytvořit nový formát
new_categories_lines = []

for section_name, categories in CATEGORIES.items():
    for category in categories:
        # Vytvořit URL slug (lowercase, replace spaces and special chars)
        slug = category.lower()
        slug = slug.replace(' ', '_')
        slug = slug.replace(',', '')
        slug = slug.replace('.', '')
        slug = slug.replace('-', '_')
        # URL encode polských znaků
        slug = slug.replace('ą', '%C4%85')
        slug = slug.replace('ć', '%C4%87')
        slug = slug.replace('ę', '%C4%99')
        slug = slug.replace('ł', '%C5%82')
        slug = slug.replace('ń', '%C5%84')
        slug = slug.replace('ó', '%C3%B3')
        slug = slug.replace('ś', '%C5%9B')
        slug = slug.replace('ź', '%C5%BA')
        slug = slug.replace('ż', '%C5%BC')
        
        url = f"https://panoramafirm.pl/{slug}"
        key = f"panorama_{slug}"
        value = f"PANORAMA [{section_name}]: {category}"
        
        new_categories_lines.append(f"    '{key}': '{value}',")

# Přidat speciální sekce
new_categories_lines.append("    # Speciální sekce bez podkategorií (přímé seznamy firem)")
new_categories_lines.append("    'panorama_biuro_z': 'PANORAMA [Biuro]: Wszystkie firmy',")
new_categories_lines.append("    'panorama_kancelaria_o': 'PANORAMA [Kancelaria]: Wszystkie firmy',")

# Načíst web_scraper.py
with open('web_scraper.py', 'r', encoding='utf-8') as f:
    scraper_content = f.read()

# Najít začátek a konec CATEGORIES
start_marker = 'CATEGORIES = {'
end_marker = '}\n\n\ndef setup_driver():'

start_idx = scraper_content.find(start_marker)
end_idx = scraper_content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("❌ Nelze najít CATEGORIES dict!")
    exit(1)

# Vytvořit nový obsah
new_categories_str = start_marker + '\n' + '\n'.join(new_categories_lines) + '\n}'

# Spojit části
new_scraper_content = scraper_content[:start_idx] + new_categories_str + scraper_content[end_idx+1:]

# Uložit
with open('web_scraper.py', 'w', encoding='utf-8') as f:
    f.write(new_scraper_content)

total_categories = sum(len(cats) for cats in CATEGORIES.values())
total_sections = len(CATEGORIES)

print("=" * 80)
print("✅ AKTUALIZOVÁNO!")
print("=" * 80)
print(f"📊 Nový počet kategorií: {total_categories}")
print(f"📊 Zpracováno sekcí: {total_sections}/20")
print("=" * 80)
print("\n🎯 STATISTIKY:")
for section_name, categories in sorted(CATEGORIES.items()):
    print(f"   {section_name:40} {len(categories):4} kategorií")

# Očekávané sekce
expected_sections = {
    'Biuro', 'Budownictwo', 'Dom i ogród', 'Dzieci', 
    'Finanse i ubezpieczenia', 'Instytucje, urzędy', 'Kancelaria',
    'Motoryzacja i transport', 'Nauka', 'Odzież i tekstylia', 'Porady',
    'Przemysł i energetyka', 'Rolnictwo i leśnictwo', 'Rozrywka i rekreacja',
    'Telekomunikacja, Internet, technologie', 'Turystyka',
    'Usługi dla firm', 'Usługi dla każdego', 'Zdrowie i uroda', 'Żywność i używki'
}
missing = expected_sections - set(CATEGORIES.keys())

if missing:
    print("\n⚠️  CHYBĚJÍCÍ SEKCE:")
    for section in sorted(missing):
        print(f"   - {section}")
else:
    print("\n🎉 VŠECH 20 SEKCÍ KOMPLETNÍ!")

print("\n💡 DALŠÍ KROK:")
print("   Restartuj Flask server: python web_scraper.py")
print("=" * 80)
