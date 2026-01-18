# Použít Python 3.12
FROM python:3.12-slim

# Nainstalovat Chrome a závislosti
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    curl \
    ca-certificates \
    && wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/google-chrome.deb \
    && rm /tmp/google-chrome.deb \
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
