# 📖 Návod k použití - Scraper firem

## 🚀 Jak začít

1. **Otevřete aplikaci** ve webovém prohlížeči
2. **Vyberte kategorii** ze seznamu (např. "Aerozole", "Artykuły chemiczne")
3. **Klikněte na tlačítko "Začít scraping"**
4. **Počkejte** na dokončení (aplikace zpracovává firmy postupně)
5. **Stáhněte výsledky** pomocí tlačítka "Stáhnout CSV"

---

## ✅ Co aplikace dělá

- Vyhledává **firmy v dané kategorii** na Panorama Firm
- Automaticky **navštíví každou firmu** a zjistí:
  - ✉️ **Email** kontakt
  - 🌐 **Web** stránky
- Uloží **pouze firmy s webem I emailem**
- Vytvoří **CSV soubor** ke stažení

---

## 📊 Výstup

**CSV soubor obsahuje 3 sloupce:**
```
Název firmy | Web | Email
```

**Příklad:**
```
Bronisław Jackowiak Formy wtryskowe | https://roal-sklep.pl/ | biuro@upph.pl
"Koh-i-Noor Polska" Sp. z o.o. | http://www.kohinoor.pl | kontakt@wenet.pl
```

---

## ⚠️ Důležité upozornění

- **Zpracování trvá čas** - cca 10-30 sekund na jednu firmu
- **Sledujte progress bar** - ukazuje aktuální stav
- **Nevypínejte prohlížeč** během scrapingu
- **Firmy bez emailu** se automaticky přeskakují

---

## 🎯 Tipy

✅ **Vyberte správnou kategorii** - čím přesnější, tím lepší výsledky  
✅ **Nechte aplikaci doběhnout** - neklikejte opakovaně na "Začít"  
✅ **Stahujte ihned** - CSV soubor se smaže po opuštění stránky  

---

## 🆘 Problémy?

**Aplikace nic nenašla:**
- Zkontrolujte, zda kategorie obsahuje firmy
- Zkuste jinou kategorii

**Scraping se zastavil:**
- Obnovte stránku a zkuste znovu

**Málo výsledků:**
- Mnoho firem nemá veřejný email - to je normální
- Aplikace ukládá JEN firmy s webem i emailem

---

**Vytvořeno pro scraping polských firem z Panorama Firm** 🇵🇱
