"""
Přímý manuální extraktor - vezme kategorie z konkrétní struktury stránky
"""
import requests
from bs4 import BeautifulSoup
import time

# Testovací URL - kategorie Budownictwo
url = "https://panoramafirm.pl/budownictwo"

print(f"Testuji URL: {url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Uložit HTML pro analýzu
with open('d:/skript/budownictwo_page.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

print("✅ HTML uložen do budownictwo_page.html")

# Najít všechny odkazy
all_links = soup.find_all('a', href=True)
print(f"\nCelkem odkazů: {len(all_links)}")

# Kategorie - odkazy začínající / a ne navigační
categories = set()
for link in all_links:
    href = link.get('href', '')
    text = link.get_text(strip=True)
    
    if (href.startswith('/') and 
        text and 
        len(text) > 2 and
        not any(skip in href for skip in ['branze', 'lista', 'regulamin', 'kontakt', 'polityka', 'wizytowki', ','])):
        
        # Zobrazit prvních 50
        if len(categories) < 50:
            print(f"  {text}: {href}")
        categories.add((text, href))

print(f"\n📊 Nalezeno {len(categories)} unikátních odkazů")
