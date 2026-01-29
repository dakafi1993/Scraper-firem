import requests
from bs4 import BeautifulSoup

url = 'https://panoramafirm.pl/biuro,z/branze.html'
print(f'Načítám: {url}')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
response = requests.get(url, headers=headers)
print(f'Status: {response.status_code}')
print(f'Přesměrováno na: {response.url}')

soup = BeautifulSoup(response.text, 'html.parser')
title = soup.find('title')
if title:
    print(f'Title: {title.text}')

# Hledám kategorie
links = soup.find_all('a', href=True)
biuro_links = [l for l in links if '/biuro' in l.get('href', '') and l.get_text(strip=True)]

print(f'\nNalezeno {len(biuro_links)} odkazů s /biuro')
for link in biuro_links[:15]:
    href = link.get('href')
    text = link.get_text(strip=True)
    if text and len(text) < 80:
        print(f'  {text}: {href}')
