# 🌐 Ngrok Deployment - Nejrychlejší řešení

## Instalace Ngrok

1. Stáhněte ngrok: https://ngrok.com/download
2. Rozbalte do složky (např. `C:\ngrok`)
3. Zaregistrujte se zdarma: https://dashboard.ngrok.com/signup
4. Získejte authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
5. Spusťte: `ngrok config add-authtoken VAS_TOKEN`

## Spuštění

```powershell
# V prvním terminálu - spustit Flask aplikaci
cd d:\skript
.\venv\Scripts\Activate.ps1
python web_scraper.py

# V druhém terminálu - spustit ngrok
ngrok http 5000
```

## Výstup

Ngrok vám dá veřejnou URL typu:
```
https://abc123.ngrok-free.app
```

Tuto URL můžete sdílet s kýmkoliv a aplikace bude dostupná odkudkoliv!

## Výhody
✅ Funguje okamžitě (2 minuty setup)
✅ Plná podpora Selenium + Chrome
✅ Žádné problémy s buildpacky
✅ Zdarma (s omezeními - 1 concurrent user na free plánu)
✅ Změny v kódu se projeví okamžitě

## Nevýhody
⚠️ PC musí běžet
⚠️ Free plán - omezená rychlost
⚠️ URL se mění při každém restartu (pokud nemáte paid)

---

## Alternativa: Serveo (ještě jednodušší)

Bez registrace:
```powershell
ssh -R 80:localhost:5000 serveo.net
```

Získáte URL typu: `https://randomname.serveo.net`
