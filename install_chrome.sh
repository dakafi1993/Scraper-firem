#!/bin/bash

# Instalace Chrome a ChromeDriver pro Linux server
echo "📦 Instalace Chrome..."

# Pro Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y wget gnupg2
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Instalace ChromeDriver
echo "🔧 Instalace ChromeDriver..."
CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -N http://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv -f chromedriver /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip

echo "✅ Instalace dokončena!"
