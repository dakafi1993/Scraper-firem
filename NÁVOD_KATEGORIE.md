# 🎯 NÁVOD: Scraping pomocí kategorií

## ✅ Perfektní! Máte kategorie z aleo.com

Ze screenshotu jsem vytvořil soubor `kategorie.txt` se všemi URL.

---

## 🚀 SPUŠTĚNÍ

### Varianta 1: Prohledat VŠECHNY kategorie (max 10 firem z každé)
```powershell
.\venv\Scripts\Activate.ps1
python aleo_category_scraper.py --file kategorie.txt --max 10
```

### Varianta 2: Prohledat vybrané kategorie
```powershell
.\venv\Scripts\Activate.ps1
python aleo_category_scraper.py --categories https://aleo.com/int/categories/it-i-telekomunikacja https://aleo.com/int/categories/marketing-reklama-i-pr --max 20
```

### Varianta 3: Interaktivní režim (zadáte URL ručně)
```powershell
.\venv\Scripts\Activate.ps1
python aleo_category_scraper.py
# Pak zadáte URL kategorií (jedna na řádek)
# Prázdný řádek = start
```

---

## 📊 KATEGORIE Z OBRÁZKU

Ze screenshotu máte **26 kategorií**:

| Kategorie | Počet firem |
|-----------|-------------|
| IT i telekomunikacja | 26,902 |
| Logistyka, spedycja, transport | 47,957 |
| Marketing, reklama i PR | 34,702 |
| Energia, paliwa, media | 23,910 |
| Pojazdy i środki transportu | 25,740 |
| Pozostałe | 65,398 |
| Przemysł spożywczy | 26,931 |
| Edukacja, sport i rozrywka | 34,098 |
| Medycyna, farmacja i kosmetyki | 22,863 |
| ... a další ... | ... |

**CELKEM: ~500 000+ firem!** 🎉

---

## ⚙️ DOPORUČENÉ NASTAVENÍ

### Pro rychlý test (10 minut)
```powershell
python aleo_category_scraper.py --file kategorie.txt --max 5
```
- Každá kategorie: max 5 firem
- Celkem: ~130 firem (26 kategorií × 5)
- Čas: ~10-15 minut

### Pro střední dataset (1-2 hodiny)
```powershell
python aleo_category_scraper.py --file kategorie.txt --max 50
```
- Každá kategorie: max 50 firem
- Celkem: ~1300 firem
- Čas: ~1-2 hodiny

### Pro velký dataset (celý den)
```powershell
python aleo_category_scraper.py --file kategorie.txt --max 500
```
- Každá kategorie: max 500 firem
- Celkem: ~13 000 firem
- Čas: ~8-12 hodin

### Pro MAXIMUM (několik dní)
```powershell
python aleo_category_scraper.py --file kategorie.txt
```
- BEZ limitu - všechny firmy
- Celkem: potenciálně 500 000+ firem
- Čas: několik dní až týdnů

---

## 📝 CO SE STANE

1. **Otevře Chrome** (uvidíte okno prohlížeče)
2. **Načte kategorii** (např. IT i telekomunikacja)
3. **CLOUDFLARE CHECKPOINT:**
   - ⚠️ Zobrazí se výzva
   - ✅ **VY kliknete checkbox** "Verify you are human"
   - ⏳ Počká 120 sekund
4. **Načte firmy** z kategorie (seznam odkazů)
5. **Projde každou firmu:**
   - Název firmy
   - Najde web firmy
   - Vyhledá email na webu
6. **Uloží CSV + Excel** do složky `output/`
7. **Další kategorie** - opakuje proces

---

## 📂 VÝSLEDNÝ SOUBOR

```
output/aleo_categories_20260116_143022.csv
```

**Sloupce:**
- `název_společnosti` - Název firmy
- `email` - Email (pokud nalezen)
- `web` - Webová stránka
- `zdroj` - Odkud email (Web firmy / Kontaktní stránka)
- `url_profilu` - Odkaz na profil aleo.com
- `kategorie` - URL kategorie

---

## 💡 TIPY

### 1. Vyfiltrovat jen důležité kategorie
Upravte `kategorie.txt` - odstraňte `#` před URL:
```txt
# Jen IT a Marketing:
https://aleo.com/int/categories/it-i-telekomunikacja
https://aleo.com/int/categories/marketing-reklama-i-pr
```

### 2. Přerušení a pokračování
Pokud skript přerušíte (Ctrl+C), **uloží co má** a můžete pokračovat ručně dalšími kategoriemi.

### 3. Kontrola průběhu
Sledujte terminál - uvidíte:
```
[15/50] Zpracovávám: https://aleo.com/int/firma/example-company
  🏢 Example Company s.r.o.
  🌐 Web: https://example.com
  ✉️  Email: info@example.com (Web firmy)
```

### 4. Cloudflare - jednou za kategorii
Pro každou kategorii musíte **jednou** kliknout Cloudflare checkbox. Pak už jen běží automaticky.

---

## 🎯 RYCHLÝ START - DOPORUČENO

```powershell
# 1. Aktivovat prostředí
.\venv\Scripts\Activate.ps1

# 2. Test na 5 firmách z každé kategorie
python aleo_category_scraper.py --file kategorie.txt --max 5

# 3. Počkat ~15 minut

# 4. Otevřít output/aleo_categories_*.xlsx
```

Tím získáte **~130 testovacích firem** ze všech kategorií!

---

## ❓ PROBLÉMY?

### "Žádné firmy nenalezeny"
- Zkontrolujte URL kategorie
- Možná chybí `/int/` v URL

### "Cloudflare timeout"
- Klikněte rychleji na checkbox
- Zkuste znovu (Ctrl+C a restart)

### "Email nenalezen"
- Normální - ne všechny firmy mají email na webu
- Očekávaná úspěšnost: **40-60%**

---

**Připraveno! Spusťte test:** 🚀
```powershell
.\venv\Scripts\Activate.ps1
python aleo_category_scraper.py --file kategorie.txt --max 5
```
