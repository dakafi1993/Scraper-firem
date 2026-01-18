# Web Scraper - Panorama Firm

Flask aplikace pro vyhledávání firem z polského business adresáře Panorama Firm.

## 🚀 Nasazení na Render.com (ZDARMA)

### Krok 1: Připravit Git repository

```bash
cd d:\skript
git init
git add .
git commit -m "Initial commit"
```

### Krok 2: Nahrát na GitHub

1. Vytvořte nový repository na [github.com](https://github.com/new)
2. Pojmenujte ho např. `panorama-firm-scraper`
3. Spusťte v PowerShellu:

```powershell
git remote add origin https://github.com/VAS_USERNAME/panorama-firm-scraper.git
git branch -M main
git push -u origin main
```

### Krok 3: Nasadit na Render

1. Přejděte na [render.com](https://render.com)
2. Zaregistrujte se (zdarma)
3. Klikněte **New** → **Web Service**
4. Připojte váš GitHub repository
5. Nastavte:
   - **Name**: `panorama-scraper`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn web_scraper:app --bind 0.0.0.0:$PORT --timeout 300`
6. Klikněte **Create Web Service**

### Krok 4: Počkat na deployment (5-10 minut)

Render automaticky:
- Nainstaluje Python 3.11
- Nainstaluje závislosti z `requirements.txt`
- Spustí aplikaci
- Vygeneruje URL: `https://panorama-scraper.onrender.com`

---

## 🌐 Alternativa: Railway.app (ZDARMA)

1. Přejděte na [railway.app](https://railway.app)
2. Zaregistrujte se přes GitHub
3. **New Project** → **Deploy from GitHub repo**
4. Vyberte váš repository
5. Railway automaticky detekuje Flask a nasadí
6. URL bude: `https://panorama-scraper.up.railway.app`

---

## 💻 Alternativa: PythonAnywhere (ZDARMA s omezeními)

1. Registrace na [pythonanywhere.com](https://www.pythonanywhere.com)
2. **Web** → **Add a new web app**
3. Vyberte **Flask**
4. Nahrajte soubory přes **Files** nebo Git
5. Nastavte `/web_scraper.py` jako WSGI file
6. URL: `https://vasusername.pythonanywhere.com`

⚠️ **Omezení**: Selenium nefunguje na free plánu (potřebujete paid)

---

## ⚡ Nejrychlejší: Heroku (5$ měsíčně)

```bash
# Instalace Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

heroku login
heroku create panorama-scraper
git push heroku main
heroku open
```

---

## 🔧 Konfigurace pro produkci

Projekt obsahuje:
- ✅ `requirements.txt` - Python závislosti
- ✅ `Procfile` - Startup příkaz pro Gunicorn
- ✅ `runtime.txt` - Python verze
- ✅ `.gitignore` - Ignorované soubory

---

## ⚠️ Důležité upozornění

**Selenium na free serverech:**
- Většina free serverů (Render, Railway) **nepodporuje Chrome/Selenium**
- Kvůli Cloudflare je potřeba headless mode vypnutý
- **Doporučení**: Použít Heroku ($5/měsíc) nebo VPS server

**Alternativní řešení:**
1. Použít API místo Selenium (pokud existuje)
2. Nasadit na VPS (DigitalOcean, Linode - $5/měsíc)
3. Spouštět lokálně a pouze UI dát na server

---

## 📦 Instalace buildpack pro Chrome (Heroku/Render)

Pro Render přidejte do nastavení:
```
BUILDPACK_URL=https://github.com/heroku/heroku-buildpack-google-chrome
```

Pro Heroku:
```bash
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-google-chrome
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-chromedriver
```

---

## 🎯 Doporučené řešení pro tento projekt

**Varianta A - Plně v cloudu** (složitější, ale funguje odkudkoliv):
- VPS server (DigitalOcean, Linode) - $5-10/měsíc
- Instalace Chrome + ChromeDriver
- Plná funkčnost včetně Selenium

**Varianta B - Hybridní** (jednodušší):
- UI na Render/Railway (zdarma)
- Scraping spouštět lokálně na vašem PC
- Sdílet přes ngrok nebo lokální síť

Chcete pokračovat s některou variantou?
