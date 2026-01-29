"""
Rychlá analýza uloženého HTML pro získání kategorií
"""

from bs4 import BeautifulSoup

# Načíst uložené HTML
with open('branze_page_structure.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Najít všechny div elementy s id začínajícím na "letter-"
letter_divs = soup.find_all('div', id=lambda x: x and x.startswith('letter-'))

print(f"Nalezeno písmen: {len(letter_divs)}")
print("=" * 80)

categories = []

for letter_div in letter_divs:
    letter_id = letter_div.get('id', '')
    letter = letter_id.replace('letter-', '')
    
    # V každém letter-div najít všechny <a> linky v <h3>
    h3_elements = letter_div.find_all('h3')
    
    print(f"\nPísmeno {letter}: {len(h3_elements)} kategorií")
    
    for h3 in h3_elements:
        link = h3.find('a')
        if link:
            name = link.text.strip()
            href = link.get('href', '')
            
            # Najít popis (následující <p> v rodičovském <li>)
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
                'description': description
            })
            
            print(f"  • {name}")

print("\n" + "=" * 80)
print(f"CELKEM: {len(categories)} kategorií ze sekce 'Dom i ogród'")
print("=" * 80)

# Uložit do souboru
with open('dom_i_ogrod_categories.txt', 'w', encoding='utf-8') as f:
    f.write("DOM I OGRÓD - Kategorie\n")
    f.write("=" * 80 + "\n\n")
    
    by_letter = {}
    for cat in categories:
        if cat['letter'] not in by_letter:
            by_letter[cat['letter']] = []
        by_letter[cat['letter']].append(cat)
    
    for letter in sorted(by_letter.keys()):
        f.write(f"\n--- {letter} ---\n\n")
        for cat in by_letter[letter]:
            f.write(f"• {cat['name']}\n")
            f.write(f"  URL: {cat['url']}\n")
            if cat['description']:
                f.write(f"  {cat['description']}\n")
            f.write("\n")

print(f"\n✅ Uloženo do: dom_i_ogrod_categories.txt")

# Python seznam pro web_scraper.py
print("\n--- Python seznam pro CATEGORIES ---\n")
print('"Dom i ogród": [')
for cat in sorted(categories, key=lambda x: x['name']):
    print(f'    "{cat["name"]}",')
print(']')
