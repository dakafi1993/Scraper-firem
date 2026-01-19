# 💾 Nastavení Render Disk pro trvalé uložení dat

## Proč potřebujeme Render Disk?

- **Bez disku**: Server se restartuje → veškerý progress se **smaže**
- **S diskem**: Progress a výsledky se **zachovají** i po restartu

---

## 🔧 Jak nastavit Render Disk

### 1. **Vytvořte disk v Render.com**

1. Přihlaste se na [Render.com](https://render.com)
2. Jděte na **Dashboard** → váš web service
3. Klikněte na **Disks** (v levém menu)
4. Klikněte **Add Disk**
5. Nastavte:
   - **Name**: `scraper-data`
   - **Mount Path**: `/mnt/data`
   - **Size**: `1 GB` (minimum)
6. Klikněte **Save**

### 2. **Nastavte environment variable**

1. V Render Dashboard → **Environment**
2. Přidejte novou proměnnou:
   - **Key**: `OUTPUT_DIR`
   - **Value**: `/mnt/data`
3. Klikněte **Save Changes**

### 3. **Restartujte aplikaci**

Server se automaticky restartuje po přidání disku.

---

## ✅ Co se ukládá na disk

📁 **/mnt/data/**
- `progress/` - Progress scrapování (pokračuje po restartu)
- `*.csv` - CSV výstupy
- `*.xlsx` - Excel výstupy

---

## 🔄 Jak to funguje

1. **První běh**: Scrapu
je kategorie "Aerozole" → stáhne 10 firem
2. **Server spadne** (512MB RAM)
3. **Restart**: Načte progress → **pokračuje od 11. firmy**
4. **Dokončení**: Všechny firmy uloženy do jednoho CSV

---

## 💰 Cena

- **Render Disk**: ~$0.25/GB/měsíc
- **1 GB disk**: ~$0.25/měsíc
- **Celkem**: Prakticky zdarma

---

## 🆘 Troubleshooting

**Progress se pořád maže:**
- Zkontrolujte, že `OUTPUT_DIR=/mnt/data` je nastaveno
- Zkontrolujte, že disk je správně připojený

**Disk je plný:**
- Smažte staré CSV/progress soubory
- Zvětšete disk na 2-5 GB

---

**Poznámka**: Bez Render Disk aplikace **funguje**, ale po každém restartu **začíná od začátku**.
