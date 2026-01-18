# Použít Python 3.12
FROM python:3.12-slim

# Nainstalovat Chrome a závislosti
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
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
