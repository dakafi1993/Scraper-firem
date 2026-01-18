# Použít Python 3.12
FROM python:3.12-slim

# Nastavit proměnné prostředí
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# Nainstalovat Chrome a závislosti
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Pracovní adresář
WORKDIR /app

# Kopírovat requirements
COPY requirements.txt .

# Instalovat Python balíčky
RUN pip install --no-cache-dir -r requirements.txt

# Kopírovat aplikaci
COPY . .

# Nastavit executable permission
RUN chmod +x start.sh

# Vytvořit output složku
RUN mkdir -p output

# Exponovat port
EXPOSE 8080

# Spustit
CMD ["bash", "start.sh"]
