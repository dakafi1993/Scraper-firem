# 🔍 Aleo.com Web Scraper

Profesionální Python skript pro automatické získávání veřejně dostupných dat o firmách z webového katalogu aleo.com.

## ✨ Funkce

- ✅ Automatické procházení katalogových stránek aleo.com
- ✅ Získávání názvů společností
- ✅ Extrakce e-mailových adres z profilů společností
- ✅ Vyhledávání e-mailů na oficiálních webech společností
- ✅ Ochrana proti blokaci (rate limiting, timeout, retry mechanismus)
- ✅ Detekce a řešení problémů (CAPTCHA, 403, 429)
- ✅ Možnost manuálního zásahu při blokaci
- ✅ Export do CSV a Excel formátu
- ✅ Podrobné logování a statistiky
- ✅ Konfigurovatelné chování

## 📋 Požadavky

- Python 3.8 nebo novější
- Přístup k internetu
- Nainstalované závislosti (viz níže)

## 🚀 Instalace

### 1. Stažení projektu

```powershell
cd d:\skript
```

### 2. Vytvoření virtuálního prostředí (doporučeno)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalace závislostí

```powershell
pip install -r requirements.txt
```

## ⚙️ Konfigurace

Před spuštěním upravte soubor `config.json` podle vašich potřeb:

```json
{
  "request_delay": 2.0,        // Prodleva mezi požadavky (sekundy)
  "timeout": 15,                // Timeout pro HTTP požadavky
  "rate_limit_wait": 60,        // Čekání při rate limit (sekundy)
  "max_pages": 10,              // Max. počet stránek (null = bez limitu)
  "search_company_website": true,  // Hledat email na webu firmy
  "manual_intervention": true,  // Povolit manuální zásah
  "output_dir": "output"        // Složka pro výstupy
}
```

### Doporučené nastavení

**Pro opatrné použití (nízké riziko blokace):**
```json
{
  "request_delay": 3.0,
  "max_pages": 5
}
```

**Pro rychlejší scraping (vyšší riziko):**
```json
{
  "request_delay": 1.0,
  "max_pages": 20
}
```

## 📖 Použití

### Základní použití

```powershell
python aleo_scraper.py
```

### Pokročilé použití

```powershell
# Zpracování pouze 50 společností
python aleo_scraper.py --max-companies 50

# Vlastní počáteční URL
python aleo_scraper.py --url "https://www.aleo.com/firmy/kategorie"

# Vlastní konfigurační soubor
python aleo_scraper.py --config custom_config.json
```

### Parametry příkazové řádky

| Parametr | Popis | Výchozí hodnota |
|----------|-------|-----------------|
| `--url` | Počáteční URL katalogu | https://www.aleo.com/firmy |
| `--max-companies` | Max. počet společností k zpracování | Bez limitu |
| `--config` | Cesta ke konfiguračnímu souboru | config.json |

## 📊 Výstupy

Skript vytváří složku `output/` s následujícími soubory:

### 1. CSV soubor (`aleo_data_YYYYMMDD_HHMMSS.csv`)
```csv
název_společnosti,email,zdroj,url_profilu
ABC s.r.o.,info@abc.cz,Profil na aleo.com,https://www.aleo.com/firmy/abc
XYZ a.s.,,E-mail nenalezen,https://www.aleo.com/firmy/xyz
```

### 2. Excel soubor (`aleo_data_YYYYMMDD_HHMMSS.xlsx`)
Stejná data jako CSV, ale ve formátu Excel pro pohodlnější práci.

### 3. Statistiky (`stats_YYYYMMDD_HHMMSS.json`)
```json
{
  "celkem_zpracováno": 100,
  "nalezeno_emailů": 67,
  "nenalezeno_emailů": 33,
  "úspěšnost": "67.0%"
}
```

### 4. Log soubor (`scraper.log`)
Obsahuje detailní záznam běhu skriptu včetně chyb a varování.

## 🛡️ Bezpečnostní mechanismy

### 1. Rate Limiting
- Automatická prodleva mezi požadavky (konfigurovatelná)
- Detekce HTTP 429 (Too Many Requests)
- Automatické čekání při rate limit

### 2. Retry mechanismus
- Až 3 pokusy při neúspěšném požadavku
- Exponenciální backoff (2s, 4s, 6s)
- Přeskočení při trvalé chybě

### 3. Detekce blokace
- Rozpoznání HTTP 403 (Forbidden)
- Detekce CAPTCHA (skript se zastaví)
- Možnost manuálního zásahu

### 4. Manuální intervence
Pokud je `manual_intervention: true`, skript se při problému zeptá:
```
⚠️  Nepodařilo se načíst stránku.
URL: https://www.aleo.com/...
Pokračovat? (y/n/url pro zadání nové URL):
```

## ⚖️ Právní upozornění a etika

### ✅ Co skript DĚLÁ
- Pracuje pouze s veřejně dostupnými daty
- Respektuje rate limiting
- Umožňuje manuální kontrolu
- Dodržuje prodlevy mezi požadavky

### ⚠️ Co skript NEDĚLÁ
- Neobchází CAPTCHA nebo jiné bezpečnostní mechanismy
- Nepoužívá tvrdě zakódované exploity
- Nepřetěžuje server nadměrnými požadavky

### 📜 Zodpovědnost uživatele
Uživatel skriptu je odpovědný za:
1. Dodržování smluvních podmínek služby aleo.com
2. Respektování GDPR a dalších zákonů o ochraně osobních údajů
3. Etické použití získaných dat

**Nedoporučujeme:**
- Scraping v komerčním měřítku bez souhlasu
- Použití dat pro spam nebo obtěžování

## 🔧 Řešení problémů

### Problém: HTTP 403 (Přístup zakázán)
**Řešení:**
1. Zvyšte `request_delay` v config.json (např. na 5 sekund)
2. Snižte `max_pages`
3. Použijte skript v jiný čas

### Problém: Žádné společnosti nebyly nalezeny
**Řešení:**
1. Zkontrolujte, zda je URL správná
2. Webová stránka mohla změnit strukturu HTML
3. Upravte CSS selektory v kódu (viz sekce Přizpůsobení)

### Problém: E-maily se nenacházejí
**Řešení:**
1. Zkontrolujte `search_company_website: true` v config.json
2. E-maily nemusí být veřejně dostupné
3. Upravte regex pattern pro detekci e-mailů

### Problém: ConnectionError
**Řešení:**
1. Zkontrolujte připojení k internetu
2. Použijte VPN pokud je stránka blokována
3. Zvyšte `timeout` v config.json

## 🛠️ Přizpůsobení

### Úprava CSS selektorů

Pokud se struktura aleo.com změní, upravte tyto části v `aleo_scraper.py`:

```python
# Řádek ~245 - Hledání odkazů na společnosti
company_links = soup.find_all('a', href=re.compile(r'/firmy/|/company/|/profil/', re.I))

# Řádek ~258 - Hledání dalšího odkazu stránkování
next_link = soup.find('a', text=re.compile(r'další|next|›|»', re.I))
```

### Přidání vlastní logiky

Můžete rozšířit metodu `scrape_company_details` o další data:
```python
def scrape_company_details(self, company: Dict) -> Dict:
    # ... existující kód ...
    
    # Přidání telefonního čísla
    phone = soup.find('span', {'class': 'phone'})
    result['telefon'] = phone.get_text() if phone else None
    
    return result
```

## 📝 Příklad výstupu

```
2026-01-16 10:15:23 - INFO - ============================================================
2026-01-16 10:15:23 - INFO - ALEO.COM SCRAPER - START
2026-01-16 10:15:23 - INFO - ============================================================
2026-01-16 10:15:23 - INFO - Zahajuji scraping od: https://www.aleo.com/firmy
2026-01-16 10:15:25 - INFO - Zpracovávám stránku 1: https://www.aleo.com/firmy
2026-01-16 10:15:28 - INFO - Nalezeno 50 společností
2026-01-16 10:15:30 - INFO - [1/50] Zpracovávám společnost...
2026-01-16 10:15:32 - INFO - ✓ ABC s.r.o.
2026-01-16 10:15:32 - INFO -   Email: info@abc.cz
2026-01-16 10:15:32 - INFO -   Zdroj: Profil na aleo.com
...
2026-01-16 10:25:45 - INFO - ✓ CSV uloženo: output/aleo_data_20260116_102545.csv
2026-01-16 10:25:45 - INFO - ✓ Excel uloženo: output/aleo_data_20260116_102545.xlsx
2026-01-16 10:25:45 - INFO - Statistiky:
2026-01-16 10:25:45 - INFO -   celkem_zpracováno: 50
2026-01-16 10:25:45 - INFO -   nalezeno_emailů: 34
2026-01-16 10:25:45 - INFO -   nenalezeno_emailů: 16
2026-01-16 10:25:45 - INFO -   úspěšnost: 68.0%
```

## 🤝 Podpora

Pokud narazíte na problém:
1. Zkontrolujte log soubor `scraper.log`
2. Ověřte konfiguraci v `config.json`
3. Zkuste upravit CSS selektory (struktura webu se mohla změnit)

## 📄 Licence

Tento skript je poskytován "tak jak je" bez jakýchkoli záruk. Používejte zodpovědně a v souladu se zákony.

## 🔄 Aktualizace

**Verze 1.0** (2026-01-16)
- Základní funkcionalita
- Export do CSV/Excel
- Ochrana proti blokaci
- Konfigurovatelné parametry
