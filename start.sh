#!/bin/bash
PORT=${PORT:-8080}
# --threads 2: Umožňuje paralelní požadavky (health check může běžet během scrapingu)
# --timeout 600: 10 minut timeout (pro dlouhé scrapingy)
# --worker-class gthread: Thread-based worker
exec gunicorn web_scraper:app --bind 0.0.0.0:$PORT --timeout 600 --threads 2 --worker-class gthread
