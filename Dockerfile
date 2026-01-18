# Použít Python 3.12 s Chrome
FROM selenium/standalone-chrome:latest

USER root

# Nainstalovat Python a závislosti
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Pracovní adresář
WORKDIR /app

# Kopírovat requirements
COPY requirements.txt .

# Instalovat Python balíčky
RUN pip3 install --no-cache-dir -r requirements.txt

# Kopírovat aplikaci
COPY . .

# Nastavit executable permission na start script
RUN chmod +x start.sh

# Vytvořit output složku
RUN mkdir -p output

# Exponovat port
EXPOSE 8080

# Nastavit proměnné prostředí
ENV FLASK_APP=web_scraper.py
ENV PYTHONUNBUFFERED=1

# Spustit pomocí start scriptu
CMD ["./start.sh"]
