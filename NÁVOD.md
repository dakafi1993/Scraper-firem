# 🚀 Aleo.com Scraper - Návod k použití

## ✅ FUNKČNÍ ŘEŠENÍ pro aleo.com/int/

Aleo.com je chráněn **Cloudflare** anti-bot systémem, který nelze automaticky obejít. Proto je nejlepší použít **semi-manuální režim**.

---

## 📋 Dostupné skripty

### 1. **aleo_scraper_int.py** ⭐ DOPORUČENO
**Funkční scraper s Google vyhledáváním**

```powershell
python aleo_scraper_int.py --url "https://aleo.com/int/" --max 20
```

**Jak to funguje:**
1. Otevře se Chrome prohlížeč
2. **VY ručně** vyřešíte Cloudflare CAPTCHA (checkbox)
3. Skript **automaticky** extrahuje všechny firmy ze stránky
4. Pro každou firmu:
   - Zkusí najít email na profilu
   - Pokud nenajde → vyhledá na **Google**
5. Uloží do CSV + Excel

**Parametry:**
- `--url` - URL stránky (výchozí: https://aleo.com/int/)
- `--max` - Kolik firem zpracovat (např. --max 50)
- `--no-google` - Nevyhledávat na Googlu (rychlejší)

---

### 2. **aleo_scraper_manual.py**
**Plně manuální režim - máte kontrolu**

```powershell
python aleo_scraper_manual.py
```

**Režimy:**
- **1** = Plný scraping (procházení profilů firem)
- **2** = Pouze analýza aktuální stránky

---

### 3. **aleo_scraper.py**
**Původní automatický scraper** (nefunguje kvůli Cloudflare)

---

## 🎯 Krok za krokem: Jak získat data firem

### METODA 1: Semi-automatická (nejlepší)

```powershell
# 1. Aktivovat prostředí
.\venv\Scripts\Activate.ps1

# 2. Spustit scraper
python aleo_scraper_int.py --max 30

# 3. V prohlížeči:
#    - Počkat na zobrazení CAPTCHA
#    - Kliknout na checkbox "I'm not a robot"
#    - Počkat na načtení stránky

# 4. Skript automaticky:
#    - Najde všechny firmy
#    - Prohledá jejich profily
#    - Vyhledá emaily na Google
#    - Uloží do output/aleo_int_TIMESTAMP.csv
```

### METODA 2: Plně manuální (maximální kontrola)

```powershell
python aleo_scraper_manual.py

# Volba: 1
# Pak postupovat podle instrukcí v terminálu
```

---

## 📊 Výstupy

Všechny výsledky se ukládají do složky `output/`:

- **aleo_int_YYYYMMDD_HHMMSS.csv** - Data v CSV
- **aleo_int_YYYYMMDD_HHMMSS.xlsx** - Data v Excel
- **stats_int_YYYYMMDD_HHMMSS.json** - Statistiky

### Formát CSV:
```csv
název_společnosti,email,zdroj,url_profilu
ABC Company,info@abc.com,Profil na aleo.com,https://aleo.com/int/...
XYZ Ltd,contact@xyz.com,Google vyhledávání,https://aleo.com/int/...
```

---

## ⚠️ Důležité upozornění

### Cloudflare ochrana
- Aleo.com má **pokročilou ochranu** proti botům
- **Nelze** automaticky obejít CAPTCHA (a to je dobře!)
- **Nutné** ruční vyřešení při prvním načtení
- Po vyřešení funguje vše automaticky

### Co dělat, když skript nenajde firmy?

1. **Otevřít aleo.com/int/ ručně** v prohlížeči
2. Zkontrolovat, zda stránka obsahuje seznam firem
3. Zkopírovat správnou URL (může být jiná kategorie)
4. Spustit: `python aleo_scraper_int.py --url "SPRÁVNÁ_URL"`

### HTML analýza
Pokud skript stále nenachází firmy:

```powershell
python test_int_structure.py
```

To uloží HTML stránky a zobrazí všechny nalezené odkazy. Pak můžete upravit CSS selektory v `aleo_scraper_int.py`.

---

## 🔧 Řešení problémů

### Problém: "Žádné společnosti nebyly nalezeny"
**Řešení:**
1. Ručně ověřte, že URL obsahuje seznam firem
2. Zkuste jinou URL kategorii
3. Použijte `aleo_scraper_manual.py` místo toho

### Problém: Cloudflare timeout
**Řešení:**
1. Rychle klikněte na CAPTCHA checkbox
2. Pokud se nezobrazí → stránka možná blokuje automatizaci
3. Zkuste restartovat a zkusit znovu

### Problém: Email nenalezen
**Řešení:**
- Firmy nemusí mít veřejný email
- Google vyhledávání není 100% spolehlivé
- Zvažte kontaktování firem jiným způsobem

### Problém: Google blokuje vyhledávání
**Řešení:**
```powershell
# Vypnout Google vyhledávání
python aleo_scraper_int.py --no-google --max 20
```

---

## 💡 Tipy pro efektivní využití

### 1. Testujte na malém vzorku
```powershell
python aleo_scraper_int.py --max 10
```

### 2. Postupné zpracování
```powershell
# První den: 50 firem
python aleo_scraper_int.py --max 50

# Další den: dalších 50
# (změnit URL na další stránku)
```

### 3. Kombinace metod
- Použít `aleo_scraper_manual.py` pro získání seznamu
- Manuálně upravit seznam
- Importovat do vlastního skriptu

---

## 📈 Očekávaná úspěšnost

- **Profil na aleo.com**: ~30-50% firem má email
- **Google vyhledávání**: +20-30% dodatečně
- **Celková úspěšnost**: ~50-70% firem

---

## ⚖️ Etické používání

✅ **Doporučeno:**
- Respektovat rate limiting (2-3s prodlevy)
- Zpracovávat rozumné množství dat
- Používat data odpovědně

❌ **Nedoporučeno:**
- Scraping 24/7
- Obcházení CAPTCHA nelegálními metodami
- Použití dat pro spam

---

## 📞 Podpora

Pokud máte problém:
1. Zkontrolujte `scraper_int.log`
2. Přečtěte si chybové hlášky
3. Zkuste test skript: `python test_int_structure.py`

---

**Vytvořeno:** 2026-01-16  
**Verze:** 2.0 - Semi-manuální režim  
**Status:** ✅ Plně funkční s Cloudflare podporou
