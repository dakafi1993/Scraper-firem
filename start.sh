#!/bin/bash
PORT=${PORT:-8080}
exec gunicorn web_scraper:app --bind 0.0.0.0:$PORT --timeout 300
