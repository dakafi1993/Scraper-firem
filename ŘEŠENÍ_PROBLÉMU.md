# ŘEŠENÍ PROBLÉMU - "Žádné firmy nenalezeny"

## ❌ Problém
Aleo.com/int/ **NEMÁ** veřejně dostupný seznam firem na hlavní stránce.  
Skript našel pouze systémové odkazy (Cookie Policy, Privacy Policy).

---

## ✅ ŘEŠENÍ 1: Použijte email_finder.py s vlastním seznamem

### Postup:
1. **Vytvořte seznam firem** (ručně nebo ze zdroje)
2. **Spusťte email_finder.py**
3. **Zadejte názvy** nebo **importujte CSV**

```powershell
.\venv\Scripts\Activate.ps1
python email_finder.py
```

### Příklad:
```
>>> Microsoft Corporation
>>> Apple Inc
>>> Google LLC
>>> 
(prázdný řádek = start)
```

---

## ✅ ŘEŠENÍ 2: Najděte správnou URL na aleo.com

Spusťte pomocný skript:
```powershell
python find_url.py
```

**Co udělá:**
1. Otevře prohlížeč
2. VY ručně najdete stránku se seznamem firem
3. Zkopírujete URL
4. Skript analyzuje stránku a řekne, jak pokračovat

---

## ✅ ŘEŠENÍ 3: Alternativní zdroje firem

### A) Veřejné registry (ČR)
```
https://ares.gov.cz - Český rejstřík firem (ZDARMA)
https://or.justice.cz - Obchodní rejstřík
```

### B) Exportovat z jiných zdrojů
- LinkedIn Sales Navigator
- Google Maps + export
- Firmy.cz
- Evropské obchodní registry

### C) Koupit databázi
- Bisnode
- Hoppenstedt
- Dun & Bradstreet

---

## 🎯 DOPORUČENÝ POSTUP

### Varianta A: Máte seznam názvů firem
```powershell
# 1. Vytvořit seznam.txt:
Microsoft
Apple
Google

# 2. Spustit
python email_finder.py

# 3. Zadat názvy (nebo csv)
```

### Varianta B: Export z Excel/CSV
```powershell
# Máte Excel s názvy v sloupci "Company Name"

python email_finder.py
>>> csv
>>> cesta/k/vašemu/souboru.xlsx
```

### Varianta C: Získat data z ARES (české firmy)
```python
# Stáhnout seznam z ARES API (zdarma, legální)
# Pak použít email_finder.py
```

---

## 🔍 Proč aleo.com/int/ nefunguje?

1. **Cloudflare ochrana** - blokuje automatické nástroje
2. **Dynamický obsah** - firmy se načítají přes JavaScript
3. **Přihlášení nutné** - možná vyžaduje účet
4. **Není veřejný katalog** - /int/ není seznam firem

---

## 💡 Co funguje NEJLÉPE

### 1. Email Finder + vlastní seznam (60-70% úspěšnost)
```powershell
python email_finder.py
```

### 2. Export z LinkedIn + Email Finder
- Export kontaktů/firem z LinkedIn
- Spustit email_finder.py s CSV

### 3. Google Maps Scraper
- Najít firmy na Google Maps
- Export názvy
- Email finder

---

## 📞 PRAKTICKÝ PŘÍKLAD

Chcete emaily 50 tech firem:

```powershell
# 1. Vytvořit seznam (ručně nebo Google)
# seznam.txt:
# Microsoft
# Apple
# Google
# ...

# 2. Spustit
python email_finder.py

# 3. Jeden název na řádek
>>> Microsoft
>>> Apple
>>> Google
>>> (prázdný řádek)

# 4. Získáte CSV s emaily
```

---

**ZÁVĚR:** Aleo.com není vhodný zdroj pro automatické stahování.  
Použijte **email_finder.py** s vlastním seznamem firem! 🎯
