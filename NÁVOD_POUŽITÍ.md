# 📖 Návod k použití - Scraper firem

## 🚀 Jak začít

1. **Otevřete aplikaci** ve webovém prohlížeči
2. **Vyberte kategorii** ze seznamu (např. "Aerozole", "Artykuły chemiczne")
3. **Zadejte počet firem** (max 10000)
4. **Klikněte na tlačítko "Začít scraping"**
5. **Počkejte** na dokončení (aplikace zpracovává firmy postupně)
6. **Stáhněte výsledky** pomocí tlačítka "Stáhnout CSV" nebo "Stáhnout Excel"

---

## ✅ Co aplikace dělá

- Vyhledává **firmy v dané kategorii** na Panorama Firm
- Automaticky **navštíví každou firmu** a zjistí:
  - ✉️ **Email** kontakt
  - 🌐 **Web** stránky
- Uloží **pouze firmy s webem I emailem**
- Vytvoří **CSV a Excel soubory** ke stažení

---

## 📊 Výstup

**CSV a Excel soubory obsahují 4 sloupce:**
```
Kategorie | Název firmy | Web | Email
```

**Příklad:**
```
PANORAMA: Aerozole | Bronisław Jackowiak | https://roal-sklep.pl/ | biuro@upph.pl
PANORAMA: Aerozole | "Koh-i-Noor Polska" | http://www.kohinoor.pl | kontakt@wenet.pl
```

---

## ⚠️ Důležité upozornění

- **Zpracování trvá čas** - cca 10-30 sekund na jednu firmu
- **Sledujte progress bar** - ukazuje aktuální stav
- **Server může spadnout** - to je normální při velkých objemech dat
- **Firmy bez emailu** se automaticky přeskakují
- **Při pádu serveru**: Spusťte scraping znovu - stáhne se nová část dat

---

## 🎯 Tipy

✅ **Nastavte počet firem 50-100** - bezpečnější pro stabilitu  
✅ **Velké kategorie rozdělte** - lepší než stahovat 500 firem najednou  
✅ **Stahujte průběžně** - po každém dokončení  
✅ **Server spadl?** - Žádný problém, spusťte znovu a stáhněte další část  

---

## 🆘 Problémy?

**Aplikace nic nenašla:**
- Zkontrolujte, zda kategorie obsahuje firmy
- Zkuste jinou kategorii

**Scraping se zastavil:**
- Server pravděpodobně spadl (512MB RAM limit)
- Stáhněte co se stihlo
- Spusťte znovu pro další část

**Málo výsledků:**
- Mnoho firem nemá veřejný email - to je normální
- Aplikace ukládá JEN firmy s webem i emailem

---

## 💡 Praktické rady

- **Malé kategorie (50-100 firem)**: Obvykle projde na první pokus
- **Velké kategorie (200+ firem)**: Rozdělte na více běhů
- **Server spadne často**: Snižte počet firem na 50
- **CSV vs Excel**: Excel má lepší formátování, CSV je menší

---

**Vytvořeno pro scraping polských firem z Panorama Firm** 🇵🇱
