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

# Vytvořit output složku
RUN mkdir -p output

# Exponovat port
EXPOSE ${PORT:-8080}

# Nastavit proměnné prostředí
ENV FLASK_APP=web_scraper.py
ENV PYTHONUNBUFFERED=1
ENV PORT=${PORT:-8080}

# Spustit pomocí Gunicorn
CMD gunicorn web_scraper:app --bind 0.0.0.0:${PORT:-8080} --timeout 300
