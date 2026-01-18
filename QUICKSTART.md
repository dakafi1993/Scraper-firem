# 🎯 RYCHLÝ START - Email Finder

## ✅ 3 Funkční nástroje na získání emailů

### 1. **email_finder.py** ⭐ NEJJEDNODUŠŠÍ
**Pro kdy:** Máte seznam názvů firem a chcete najít jejich emaily

```powershell
python email_finder.py
```

**Jak to funguje:**
1. Zadáte názvy firem (jeden na řádek)
2. Skript pro každou firmu:
   - Zkusí odhadnout web (www.nazevfirmy.com apod.)
   - Otevře web
   - Najde kontaktní stránku
   - Extrahuje email
3. Uloží do CSV + Excel

**Příklad:**
```
>>> ABC Company
>>> XYZ Corporation
>>> Tech Solutions Ltd
>>> (prázdný řádek = konec)

Výsledek: email_finder_TIMESTAMP.csv
```

---

### 2. **aleo_scraper_int.py** 🌐 PRO ALEO.COM
**Pro kdy:** Chcete data přímo z aleo.com/int/

```powershell
python aleo_scraper_int.py --max 20
```

**Jak to funguje:**
1. Otevře aleo.com/int/
2. **VY vyřešíte Cloudflare** (klik na checkbox)
3. Skript automaticky:
   - Najde všechny firmy na stránce
   - Extrahuje jejich profily
   - Hledá emaily v profilech
   - Pokud nenajde → hledá na webu firmy

**Nově vylepšeno:**
- ✅ Extrahuje web firmy z profilu
- ✅ Prohledává kontaktní stránky
- ✅ Lepší detekce emailů
- ❌ Už NEpoužívá Google (nefungovalo)

---

### 3. **aleo_scraper_manual.py** 🎮 MANUÁLNÍ KONTROLA
**Pro kdy:** Chcete plnou kontrolu nad procesem

```powershell
python aleo_scraper_manual.py
```

---

## 🚀 Doporučené použití

### Scénář A: Máte seznam firem
```powershell
# 1. Vytvořit seznam.txt s názvy firem
# 2. Spustit:
python email_finder.py
# 3. Nebo zadat: csv
#    a použít existující CSV
```

### Scénář B: Chcete data z aleo.com
```powershell
# 1. Spustit
python aleo_scraper_int.py --max 30

# 2. V prohlížeči kliknout na Cloudflare checkbox
# 3. Počkat - skript udělá vše ostatní
```

---

## 📊 Očekávané výsledky

| Metoda | Úspěšnost | Rychlost |
|--------|-----------|----------|
| email_finder.py | 40-60% | ⚡⚡ Rychlá |
| aleo_scraper_int.py | 50-70% | ⚡ Střední |
| aleo_scraper_manual.py | 60-80% | 🐌 Pomalá |

---

## 💡 Tipy

### 1. Kombinovaný přístup
```powershell
# Krok 1: Získat názvy firem z aleo.com
python aleo_scraper_manual.py
# (volba 2 - pouze analýza stránky)

# Krok 2: Export do found_companies_*.csv

# Krok 3: Najít emaily
python email_finder.py
# (zadat: csv)
# (cesta: output/found_companies_*.csv)
```

### 2. Testování na malém vzorku
```powershell
# Vždy nejdřív vyzkoušet na 5-10 firmách
python aleo_scraper_int.py --max 5
```

### 3. Rychlé získání emailů z existujícího seznamu
```powershell
# Pokud máte CSV s názvy:
python email_finder.py
>>> csv
>>> cesta/k/vašemu/souboru.csv
```

---

## ❌ Řešení problémů

### "Web nenalezen"
→ Skript odhaduje URL, ne vždy správně  
→ Normální, ~40-50% firem se najde automaticky

### "Email nenalezen"
→ Mnoho firem nemá email veřejně dostupný  
→ Zkuste manuálně na LinkedIn/sociálních sítích

### "Cloudflare timeout"
→ Klikněte rychle na checkbox  
→ Nebo použijte email_finder.py místo toho

---

## 📁 Výstupy

Všechny výsledky v `output/`:
- `email_finder_*.csv` - Z email_finder.py
- `aleo_int_*.csv` - Z aleo_scraper_int.py
- `found_companies_*.csv` - Z manuálního režimu

Formát:
```csv
název_firmy,web,email,zdroj
ABC Company,https://abc.com,info@abc.com,Web společnosti
```

---

**Aktualizováno:** 2026-01-16  
**Verze:** 3.0 - Email Finder přidán  
**Status:** ✅ Plně funkční bez Google
