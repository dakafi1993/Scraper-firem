"""
Aleo.com URL Finder - Najde správnou strukturu stránky
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    options = Options()
    options.add_argument('--start-maximized')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

print("=" * 60)
print("ALEO.COM URL FINDER")
print("=" * 60)
print("\nOtevírám Chrome prohlížeč...")
print("\n📋 ÚKOLY:")
print("1. Přihlaste se na aleo.com (pokud je třeba)")
print("2. Najděte kategorii s firmami (např. IT)")
print("3. Najděte stránku se SEZNAMEM firem (ne category overview)")
print("4. Zkopírujte URL této stránky")
print("\n⚠️  HLEDÁTE stránku, kde vidíte:")
print("   - Seznam názvů firem")
print("   - Odkazy na profily firem")
print("   - Možnost stránkování (strana 1, 2, 3...)")
print("\n❌ NE category overview stránku s popisem kategorie!")
print("=" * 60)

driver = setup_driver()

try:
    # Otevřít aleo.com
    driver.get("https://aleo.com/int/")
    
    print("\n✅ Chrome otevřen na: https://aleo.com/int/")
    print("\nTEĎ:")
    print("1. Najděte SEZNAM firem (ne category overview)")
    print("2. Zkopírujte URL ze stránky se seznamem")
    print("3. Napište mi tu URL")
    print("\nPříklad správné URL:")
    print("  https://aleo.com/int/companies?category=IT")
    print("  https://aleo.com/int/search?q=IT")
    print("  https://aleo.com/int/directory/it")
    print("\n⏳ Nechávám Chrome otevřený... (Zavřete jej ručně až budete hotovi)")
    
    # Nechat otevřené
    input("\nStiskněte Enter až najdete správnou URL...")
    
finally:
    print("\n✅ Hotovo")
