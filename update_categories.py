"""
Aktualizuje CATEGORIES v web_scraper.py s novými kategoriemi
"""

# Načti nové kategorie
with open('panorama_complete_categories.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Najdi řádek kde začíná CATEGORIES = {
new_categories = []
capture = False
for line in lines:
    if line.strip().startswith('CATEGORIES = {'):
        capture = True
    if capture:
        new_categories.append(line.rstrip())
    if capture and line.strip() == '}':
        break

# Načti web_scraper.py
with open('web_scraper.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Najdi a nahraď CATEGORIES sekci
import re
pattern = r'CATEGORIES = \{.*?\n\}'
replacement = '\n'.join(new_categories)

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Ulož
with open('web_scraper.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ CATEGORIES aktualizovány!")
print(f"📊 Nový počet kategorií: {len(new_categories) - 2}")  # -2 pro první a poslední řádek
