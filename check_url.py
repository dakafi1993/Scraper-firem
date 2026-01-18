"""
Manuální test - otevře URL a čeká
"""

import webbrowser
import time

url = "https://aleo.com/pl/firmy/artykuly-dla-biur-i-wyposazenie-biurowe"

print(f"🔍 Otevírám URL v prohlížeči:")
print(f"   {url}")
print("\n📋 ÚKOL:")
print("1. Zkontrolujte, kam vás URL přesměruje")
print("2. Najděte stránku se SKUTEČNÝM seznamem firem")
print("3. Zkopírujte SPRÁVNOU URL (z adresního řádku)")
print("4. Ujistěte se, že vidíte tabulku/seznam firem s odkazy")
print("\n⚠️  Možné problémy:")
print("   - URL vyžaduje přihlášení")
print("   - Firmy se načítají přes JavaScript/AJAX")
print("   - Seznam firem je na jiné URL (např. s parametry)")

webbrowser.open(url)

print("\n✅ Prohlížeč otevřen")
print("Podívejte se na stránku a řekněte mi:")
print("  - Vidíte seznam firem?")
print("  - Nebo to přesměrovává jinam?")
print("  - Jaká je správná URL se seznamem?")
