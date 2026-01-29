"""
Parser sitemap.xml pro extrakci všech kategorií
"""
import re
from collections import defaultdict

# Načíst sitemap
with open('d:/skript/sitemap.xml', 'r', encoding='utf-8') as f:
    content = f.read()

# Najít všechny URL
urls = re.findall(r'<loc>(https://panoramafirm\.pl/[^<]+)</loc>', content)

print(f"Celkem URL v sitemap: {len(urls)}")

# Filtrovat jen kategorie (ne města, ne firmy)
categories = []
for url in urls:
    # Kategorie nemají /miasto/ nebo čísla na konci
    if '/firmy' not in url and '/lista' not in url and not re.search(r'/\d+$', url):
        # Odstranit https://panoramafirm.pl/
        cat = url.replace('https://panoramafirm.pl/', '')
        if cat and len(cat) > 1 and ',' not in cat:
            categories.append(url)

print(f"Nalezeno kategorií: {len(categories)}")

# Zobrazit vzorky
print("\nPrvních 20 kategorií:")
for i, cat in enumerate(categories[:20], 1):
    print(f"  {i}. {cat}")

# Uložit všechny
with open('d:/skript/sitemap_categories.txt', 'w', encoding='utf-8') as f:
    for cat in sorted(set(categories)):
        f.write(f"{cat}\n")

print(f"\n✅ Uloženo do sitemap_categories.txt")
