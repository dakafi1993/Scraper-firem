#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webové GUI pro ALEO scraper
"""

from flask import Flask, render_template, request, send_file, jsonify
import os
import pandas as pd
from datetime import datetime
import threading
import time
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import logging
import gc  # Garbage collector pro uvolnění paměti

# Nastavit logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Složka pro výstupy
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Email regex
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Globální stav
scraping_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_company': '',
    'category': '',
    'results': [],
    'output_file': None,
    'message': ''
}

CATEGORIES = {
CATEGORIES = {
    'panorama_https://panoramafirm.pl/administracja_obiektów_użyteczności_publicznej': 'PANORAMA [Instytucje, urzędy]: Administracja obiektów użyteczności publicznej',
    'panorama_https://panoramafirm.pl/adwokaci': 'PANORAMA [Usługi dla każdego]: Adwokaci',
    'panorama_https://panoramafirm.pl/aerozole': 'PANORAMA [Przemysł i energetyka]: Aerozole',
    'panorama_https://panoramafirm.pl/agencje_artystyczne': 'PANORAMA [Rozrywka i rekreacja]: Agencje artystyczne',
    'panorama_https://panoramafirm.pl/agencje_detektywistyczne': 'PANORAMA [Usługi dla każdego]: Agencje detektywistyczne',
    'panorama_https://panoramafirm.pl/agencje_fotograficzne': 'PANORAMA [Usługi dla każdego]: Agencje fotograficzne',
    'panorama_https://panoramafirm.pl/agencje_i_składy_celne': 'PANORAMA [Instytucje, urzędy]: Agencje i składy celne',
    'panorama_https://panoramafirm.pl/agencje_ochrony': 'PANORAMA [Usługi dla każdego]: Agencje ochrony',
    'panorama_https://panoramafirm.pl/agencje_pośrednictwa_pracy': 'PANORAMA [Usługi dla każdego]: Agencje pośrednictwa pracy',
    'panorama_https://panoramafirm.pl/agencje_pracy_tymczasowej': 'PANORAMA [Usługi dla każdego]: Agencje pracy tymczasowej',
    'panorama_https://panoramafirm.pl/agencje_tłumaczy': 'PANORAMA [Usługi dla każdego]: Agencje tłumaczy',
    'panorama_https://panoramafirm.pl/agregaty_komory_i_meble_chłodnicze': 'PANORAMA [Przemysł i energetyka]: Agregaty, komory i meble chłodnicze',
    'panorama_https://panoramafirm.pl/agregaty_prądotwórcze': 'PANORAMA [Przemysł i energetyka]: Agregaty prądotwórcze',
    'panorama_https://panoramafirm.pl/agroturystyka': 'PANORAMA [Turystyka]: Agroturystyka',
    'panorama_https://panoramafirm.pl/akcesoria_dla_artystów_i_plastyków': 'PANORAMA [Rozrywka i rekreacja]: Akcesoria dla artystów i plastyków',
    'panorama_https://panoramafirm.pl/akcesoria_do_butów': 'PANORAMA [Odzież i tekstylia]: Akcesoria do butów',
    'panorama_https://panoramafirm.pl/akcesoria_do_drzwi_i_okien': 'PANORAMA [Budownictwo]: Akcesoria do drzwi i okien',
    'panorama_https://panoramafirm.pl/akcesoria_meblowe': 'PANORAMA [Budownictwo]: Akcesoria meblowe',
    'panorama_https://panoramafirm.pl/akcesoria_szewskie_i_kaletnicze': 'PANORAMA [Odzież i tekstylia]: Akcesoria szewskie i kaletnicze',
    'panorama_https://panoramafirm.pl/akumulatory_i_baterie': 'PANORAMA [Przemysł i energetyka]: Akumulatory i baterie',
    'panorama_https://panoramafirm.pl/alarmy_samochodowe': 'PANORAMA [Budownictwo]: Alarmy samochodowe',
    'panorama_https://panoramafirm.pl/ambasady': 'PANORAMA [Instytucje, urzędy]: Ambasady',
    'panorama_https://panoramafirm.pl/amortyzatory_samochodowe': 'PANORAMA [Budownictwo]: Amortyzatory samochodowe',
    'panorama_https://panoramafirm.pl/anteny': 'PANORAMA [Telekomunikacja, internet, technologie]: Anteny',
    'panorama_https://panoramafirm.pl/antyki_i_dzieła_sztuki': 'PANORAMA [Rozrywka i rekreacja]: Antyki i dzieła sztuki',
    'panorama_https://panoramafirm.pl/antykwariaty': 'PANORAMA [Rozrywka i rekreacja]: Antykwariaty',
    'panorama_https://panoramafirm.pl/architektura_krajobrazu': 'PANORAMA [Budownictwo]: Architektura krajobrazu',
    'panorama_https://panoramafirm.pl/archiwa_i_archiwizacja_danych': 'PANORAMA [Instytucje, urzędy]: Archiwa i archiwizacja danych',
    'panorama_https://panoramafirm.pl/armatura_hydrauliczna': 'PANORAMA [Przemysł i energetyka]: Armatura hydrauliczna',
    'panorama_https://panoramafirm.pl/armatura_przemysłowa': 'PANORAMA [Przemysł i energetyka]: Armatura przemysłowa',
    'panorama_https://panoramafirm.pl/artykuly': 'PANORAMA [Zdrowie i uroda]: Artykuły',
    'panorama_https://panoramafirm.pl/artykuły_dziecięce': 'PANORAMA [Odzież i tekstylia]: Artykuły dziecięce',
    'panorama_https://panoramafirm.pl/artykuły_elektrotechniczne': 'PANORAMA [Przemysł i energetyka]: Artykuły elektrotechniczne',
    'panorama_https://panoramafirm.pl/artykuły_gumowe': 'PANORAMA [Budownictwo]: Artykuły gumowe',
    'panorama_https://panoramafirm.pl/artykuły_i_sprzęt_ogrodniczy': 'PANORAMA [Budownictwo]: Artykuły i sprzęt ogrodniczy',
    'panorama_https://panoramafirm.pl/artykuły_metalowe': 'PANORAMA [Przemysł i energetyka]: Artykuły metalowe',
    'panorama_https://panoramafirm.pl/artykuły_papiernicze': 'PANORAMA [Dzieci]: Artykuły papiernicze',
    'panorama_https://panoramafirm.pl/artykuły_szkolne': 'PANORAMA [Dzieci]: Artykuły szkolne',
    'panorama_https://panoramafirm.pl/artykuły_zoologiczne': 'PANORAMA [Rozrywka i rekreacja]: Artykuły zoologiczne',
    'panorama_https://panoramafirm.pl/astrologia': 'PANORAMA [Usługi dla każdego]: Astrologia',
    'panorama_https://panoramafirm.pl/audyty_oprogramowania_i_sprzętu_komputerowego': 'PANORAMA [Telekomunikacja, internet, technologie]: Audyty oprogramowania i sprzętu komputerowego',
    'panorama_https://panoramafirm.pl/automaty_do_gier': 'PANORAMA [Rozrywka i rekreacja]: Automaty do gier',
    'panorama_https://panoramafirm.pl/automatyka': 'PANORAMA [Przemysł i energetyka]: Automatyka',
    'panorama_https://panoramafirm.pl/autozłom': 'PANORAMA [Przemysł i energetyka]: Autozłom',
    'panorama_https://panoramafirm.pl/badania_i_usługi_archeologiczne': 'PANORAMA [Budownictwo]: Badania i usługi archeologiczne',
    'panorama_https://panoramafirm.pl/badania_i_uzdatnianie_wody': 'PANORAMA [Usługi dla każdego]: Badania i uzdatnianie wody',
    'panorama_https://panoramafirm.pl/badania_nieniszczące': 'PANORAMA [Przemysł i energetyka]: Badania nieniszczące',
    'panorama_https://panoramafirm.pl/balony': 'PANORAMA [Rozrywka i rekreacja]: Balony',
    'panorama_https://panoramafirm.pl/banki': 'PANORAMA [Finanse i ubezpieczenia]: Banki',
    'panorama_https://panoramafirm.pl/bankomaty': 'PANORAMA [Usługi dla każdego]: Bankomaty',
    'panorama_https://panoramafirm.pl/bary': 'PANORAMA [Rozrywka i rekreacja]: Bary',
    'panorama_https://panoramafirm.pl/baseny_i_parki_wodne': 'PANORAMA [Usługi dla każdego]: Baseny i parki wodne',
    'panorama_https://panoramafirm.pl/bazy_danych': 'PANORAMA [Usługi dla każdego]: Bazy danych',
    'panorama_https://panoramafirm.pl/beton': 'PANORAMA [Budownictwo]: Beton',
    'panorama_https://panoramafirm.pl/biblioteki_i_czytelnie': 'PANORAMA [Instytucje, urzędy]: Biblioteki i czytelnie',
    'panorama_https://panoramafirm.pl/bielizna': 'PANORAMA [Odzież i tekstylia]: Bielizna',
    'panorama_https://panoramafirm.pl/biopaliwa': 'PANORAMA [Przemysł i energetyka]: Biopaliwa',
    'panorama_https://panoramafirm.pl/biura_architektoniczne': 'PANORAMA [Budownictwo]: Biura architektoniczne',
    'panorama_https://panoramafirm.pl/biura_matrymonialne': 'PANORAMA [Usługi dla każdego]: Biura matrymonialne',
    'panorama_https://panoramafirm.pl/biura_podróży_i_agencje_turystyczne': 'PANORAMA [Turystyka]: Biura podróży i agencje turystyczne',
    'panorama_https://panoramafirm.pl/biura_projektowe': 'PANORAMA [Budownictwo]: Biura projektowe',
    'panorama_https://panoramafirm.pl/biura_rachunkowe': 'PANORAMA [Finanse i ubezpieczenia]: Biura rachunkowe',
    'panorama_https://panoramafirm.pl/blacharstwo_i_lakiernictwo': 'PANORAMA [Budownictwo]: Blacharstwo i lakiernictwo',
    'panorama_https://panoramafirm.pl/bony_i_kupony': 'PANORAMA [Usługi dla każdego]: Bony i kupony',
    'panorama_https://panoramafirm.pl/bramy_i_ogrodzenia': 'PANORAMA [Budownictwo]: Bramy i ogrodzenia',
    'panorama_https://panoramafirm.pl/broń_i_amunicja': 'PANORAMA [Rozrywka i rekreacja]: Broń i amunicja',
    'panorama_https://panoramafirm.pl/brukarstwo': 'PANORAMA [Budownictwo]: Brukarstwo',
    'panorama_https://panoramafirm.pl/brykiety_i_węgiel_drzewny': 'PANORAMA [Przemysł i energetyka]: Brykiety i węgiel drzewny',
    'panorama_https://panoramafirm.pl/budowa_i_eksploatacja_autostrad': 'PANORAMA [Budownictwo]: Budowa i eksploatacja autostrad',
    'panorama_https://panoramafirm.pl/budowa_i_eksploatacja_rurociągów': 'PANORAMA [Budownictwo]: Budowa i eksploatacja rurociągów',
    'panorama_https://panoramafirm.pl/budowa_i_sprzęt_drogowy': 'PANORAMA [Przemysł i energetyka]: Budowa i sprzęt drogowy',
    'panorama_https://panoramafirm.pl/budowa_i_wykończenia_pod_klucz': 'PANORAMA [Budownictwo]: Budowa i wykończenia pod klucz',
    'panorama_https://panoramafirm.pl/budowa_i_wynajem_hal_przemysłowych': 'PANORAMA [Budownictwo]: Budowa i wynajem hal przemysłowych',
    'panorama_https://panoramafirm.pl/budowa_i_wyposażenie_garaży': 'PANORAMA [Budownictwo]: Budowa i wyposażenie garaży',
    'panorama_https://panoramafirm.pl/budowa_i_wyposażenie_saun': 'PANORAMA [Usługi dla każdego]: Budowa i wyposażenie saun',
    'panorama_https://panoramafirm.pl/budowa_i_wyposażenie_stacji_paliw': 'PANORAMA [Przemysł i energetyka]: Budowa i wyposażenie stacji paliw',
    'panorama_https://panoramafirm.pl/budowa_obiektów_sportowych': 'PANORAMA [Budownictwo]: Budowa obiektów sportowych',
    'panorama_https://panoramafirm.pl/budowa_wyposażenie_i_remont_statków': 'PANORAMA [Przemysł i energetyka]: Budowa, wyposażenie i remont statków',
    'panorama_https://panoramafirm.pl/budownictwo_kolejowe': 'PANORAMA [Przemysł i energetyka]: Budownictwo kolejowe',
    'panorama_https://panoramafirm.pl/budownictwo_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Budownictwo przemysłowe',
    'panorama_https://panoramafirm.pl/car_audio': 'PANORAMA [Budownictwo]: Car audio',
    'panorama_https://panoramafirm.pl/cegły': 'PANORAMA [Budownictwo]: Cegły',
    'panorama_https://panoramafirm.pl/cement_i_wapno': 'PANORAMA [Budownictwo]: Cement i wapno',
    'panorama_https://panoramafirm.pl/centra_handlowe': 'PANORAMA [Usługi dla każdego]: Centra handlowe',
    'panorama_https://panoramafirm.pl/ceramika_budowlana': 'PANORAMA [Budownictwo]: Ceramika budowlana',
    'panorama_https://panoramafirm.pl/chemia_budowlana': 'PANORAMA [Budownictwo]: Chemia budowlana',
    'panorama_https://panoramafirm.pl/chemia_gospodarcza': 'PANORAMA [Przemysł i energetyka]: Chemia gospodarcza',
    'panorama_https://panoramafirm.pl/cięcie_i_wiercenie': 'PANORAMA [Budownictwo]: Cięcie i wiercenie',
    'panorama_https://panoramafirm.pl/cięcie_i_wiercenie_w_betonie': 'PANORAMA [Budownictwo]: Cięcie i wiercenie w betonie',
    'panorama_https://panoramafirm.pl/cięcie_i_zaginanie': 'PANORAMA [Budownictwo]: Cięcie i zaginanie',
    'panorama_https://panoramafirm.pl/cyrki_i_wesołe_miasteczka': 'PANORAMA [Rozrywka i rekreacja]: Cyrki i wesołe miasteczka',
    'panorama_https://panoramafirm.pl/czapki_i_kapelusze': 'PANORAMA [Odzież i tekstylia]: Czapki i kapelusze',
    'panorama_https://panoramafirm.pl/czyszczenie_i_renowacja_dywanów_i_wykładzin': 'PANORAMA [Usługi dla każdego]: Czyszczenie i renowacja dywanów i wykładzin',
    'panorama_https://panoramafirm.pl/czyszczenie_strumieniowo_ścierne': 'PANORAMA [Usługi dla każdego]: Czyszczenie strumieniowo-ścierne',
    'panorama_https://panoramafirm.pl/czyszczące_urządzenia_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Czyszczące urządzenia przemysłowe',
    'panorama_https://panoramafirm.pl/czyściwa_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Czyściwa przemysłowe',
    'panorama_https://panoramafirm.pl/dachy_i_rynny': 'PANORAMA [Budownictwo]: Dachy i rynny',
    'panorama_https://panoramafirm.pl/dachy_i_usługi_dekarskie': 'PANORAMA [Budownictwo]: Dachy i usługi dekarskie',
    'panorama_https://panoramafirm.pl/dealerzy_i_sprzedaż_samochodów': 'PANORAMA [Budownictwo]: Dealerzy i sprzedaż samochodów',
    'panorama_https://panoramafirm.pl/dekoratorstwo_i_architektura_wnętrz': 'PANORAMA [Budownictwo]: Dekoratorstwo i architektura wnętrz',
    'panorama_https://panoramafirm.pl/deweloperzy': 'PANORAMA [Usługi dla każdego]: Deweloperzy',
    'panorama_https://panoramafirm.pl/dewocjonalia': 'PANORAMA [Usługi dla każdego]: Dewocjonalia',
    'panorama_https://panoramafirm.pl/dezynfekcja_dezynsekcja_i_deratyzacja': 'PANORAMA [Usługi dla każdego]: Dezynfekcja dezynsekcja i deratyzacja',
    'panorama_https://panoramafirm.pl/dobry_start_300_zł_dla_ucznia': 'PANORAMA [Instytucje, urzędy]: Dobry Start - 300 zł dla ucznia',
    'panorama_https://panoramafirm.pl/dodaj-firme.html': 'PANORAMA [Zdrowie i uroda]: Dodaj firmę bezpłatnie',
    'panorama_https://panoramafirm.pl/domy_dziecka': 'PANORAMA [Dzieci]: Domy dziecka',
    'panorama_https://panoramafirm.pl/domy_kultury_i_kluby_osiedlowe': 'PANORAMA [Rozrywka i rekreacja]: Domy kultury i kluby osiedlowe',
    'panorama_https://panoramafirm.pl/doradztwo_finansowe_i_kredytowe': 'PANORAMA [Finanse i ubezpieczenia]: Doradztwo finansowe i kredytowe',
    'panorama_https://panoramafirm.pl/doradztwo_podatkowe': 'PANORAMA [Usługi dla każdego]: Doradztwo podatkowe',
    'panorama_https://panoramafirm.pl/doradztwo_prawne': 'PANORAMA [Usługi dla każdego]: Doradztwo prawne',
    'panorama_https://panoramafirm.pl/drabiny': 'PANORAMA [Przemysł i energetyka]: Drabiny',
    'panorama_https://panoramafirm.pl/drewno': 'PANORAMA [Przemysł i energetyka]: Drewno',
    'panorama_https://panoramafirm.pl/drewno_budowlane': 'PANORAMA [Przemysł i energetyka]: Drewno budowlane',
    'panorama_https://panoramafirm.pl/drewno_opałowe': 'PANORAMA [Przemysł i energetyka]: Drewno opałowe',
    'panorama_https://panoramafirm.pl/drut_i_liny_stalowe': 'PANORAMA [Przemysł i energetyka]: Drut i liny stalowe',
    'panorama_https://panoramafirm.pl/drzwi': 'PANORAMA [Budownictwo]: Drzwi',
    'panorama_https://panoramafirm.pl/drzwi_antywłamaniowe': 'PANORAMA [Budownictwo]: Drzwi antywłamaniowe',
    'panorama_https://panoramafirm.pl/dyskoteki': 'PANORAMA [Rozrywka i rekreacja]: Dyskoteki',
    'panorama_https://panoramafirm.pl/dystrybucja_energii_elektrycznej': 'PANORAMA [Przemysł i energetyka]: Dystrybucja energii elektrycznej',
    'panorama_https://panoramafirm.pl/dywany_i_wykładziny': 'PANORAMA [Budownictwo]: Dywany i wykładziny',
    'panorama_https://panoramafirm.pl/dźwigi_i_żurawie': 'PANORAMA [Przemysł i energetyka]: Dźwigi i żurawie',
    'panorama_https://panoramafirm.pl/dźwignice': 'PANORAMA [Budownictwo]: Dźwignice',
    'panorama_https://panoramafirm.pl/ekspertyzy_i_kosztorysy_budowlane': 'PANORAMA [Budownictwo]: Ekspertyzy i kosztorysy budowlane',
    'panorama_https://panoramafirm.pl/elektroakustyka': 'PANORAMA [Usługi dla każdego]: Elektroakustyka',
    'panorama_https://panoramafirm.pl/elektrociepłownie': 'PANORAMA [Przemysł i energetyka]: Elektrociepłownie',
    'panorama_https://panoramafirm.pl/elektroinstalatorstwo': 'PANORAMA [Usługi dla każdego]: Elektroinstalatorstwo',
    'panorama_https://panoramafirm.pl/elektromechanika': 'PANORAMA [Budownictwo]: Elektromechanika',
    'panorama_https://panoramafirm.pl/elektronarzędzia': 'PANORAMA [Przemysł i energetyka]: Elektronarzędzia',
    'panorama_https://panoramafirm.pl/elektronika_samochodowa': 'PANORAMA [Budownictwo]: Elektronika samochodowa',
    'panorama_https://panoramafirm.pl/energia_odnawialna': 'PANORAMA [Przemysł i energetyka]: Energia odnawialna',
    'panorama_https://panoramafirm.pl/escape_rooms': 'PANORAMA [Rozrywka i rekreacja]: Escape rooms',
    'panorama_https://panoramafirm.pl/farby_i_lakiery': 'PANORAMA [Przemysł i energetyka]: Farby i lakiery',
    'panorama_https://panoramafirm.pl/filatelistyka': 'PANORAMA [Rozrywka i rekreacja]: Filatelistyka',
    'panorama_https://panoramafirm.pl/filatelistyka_i_numizmatyka': 'PANORAMA [Rozrywka i rekreacja]: Filatelistyka i numizmatyka',
    'panorama_https://panoramafirm.pl/filtry': 'PANORAMA [Przemysł i energetyka]: Filtry',
    'panorama_https://panoramafirm.pl/firmy_konsultingowe': 'PANORAMA [Budownictwo]: Firmy konsultingowe',
    'panorama_https://panoramafirm.pl/flagi_i_artykuły_propagandowe': 'PANORAMA [Odzież i tekstylia]: Flagi i artykuły propagandowe',
    'panorama_https://panoramafirm.pl/folie_i_foliowanie': 'PANORAMA [Budownictwo]: Folie i foliowanie',
    'panorama_https://panoramafirm.pl/formy_wtryskowe': 'PANORAMA [Przemysł i energetyka]: Formy wtryskowe',
    'panorama_https://panoramafirm.pl/fryzjerzy_i_salony_fryzjerskie': 'PANORAMA [Usługi dla każdego]: Fryzjerzy i salony fryzjerskie',
    'panorama_https://panoramafirm.pl/fundacje_i_instytucje_charytatywne': 'PANORAMA [Instytucje, urzędy]: Fundacje i instytucje charytatywne',
    'panorama_https://panoramafirm.pl/fundusze_emerytalne': 'PANORAMA [Usługi dla każdego]: Fundusze emerytalne',
    'panorama_https://panoramafirm.pl/fundusze_inwestycyjne': 'PANORAMA [Finanse i ubezpieczenia]: Fundusze inwestycyjne',
    'panorama_https://panoramafirm.pl/futra_i_kożuchy': 'PANORAMA [Odzież i tekstylia]: Futra i kożuchy',
    'panorama_https://panoramafirm.pl/galanteria': 'PANORAMA [Odzież i tekstylia]: Galanteria',
    'panorama_https://panoramafirm.pl/galerie_sztuki': 'PANORAMA [Rozrywka i rekreacja]: Galerie sztuki',
    'panorama_https://panoramafirm.pl/galwanizacja': 'PANORAMA [Przemysł i energetyka]: Galwanizacja',
    'panorama_https://panoramafirm.pl/gaz_ziemny': 'PANORAMA [Przemysł i energetyka]: Gaz ziemny',
    'panorama_https://panoramafirm.pl/gazy_techniczne': 'PANORAMA [Przemysł i energetyka]: Gazy techniczne',
    'panorama_https://panoramafirm.pl/genealogia_i_heraldyka': 'PANORAMA [Usługi dla każdego]: Genealogia i heraldyka',
    'panorama_https://panoramafirm.pl/geodezja': 'PANORAMA [Budownictwo]: Geodezja',
    'panorama_https://panoramafirm.pl/geolodzy_i_geofizycy': 'PANORAMA [Budownictwo]: Geolodzy i geofizycy',
    'panorama_https://panoramafirm.pl/geosyntetyki': 'PANORAMA [Budownictwo]: Geosyntetyki',
    'panorama_https://panoramafirm.pl/giełdy': 'PANORAMA [Finanse i ubezpieczenia]: Giełdy',
    'panorama_https://panoramafirm.pl/grafika_komputerowa': 'PANORAMA [Usługi dla każdego]: Grafika komputerowa',
    'panorama_https://panoramafirm.pl/grawerowanie': 'PANORAMA [Usługi dla każdego]: Grawerowanie',
    'panorama_https://panoramafirm.pl/gres_terakota_i_płytki_ceramiczne': 'PANORAMA [Budownictwo]: Gres, terakota i płytki ceramiczne',
    'panorama_https://panoramafirm.pl/gry_komputerowe': 'PANORAMA [Rozrywka i rekreacja]: Gry komputerowe',
    'panorama_https://panoramafirm.pl/grzejnictwo_elektryczne': 'PANORAMA [Przemysł i energetyka]: Grzejnictwo elektryczne',
    'panorama_https://panoramafirm.pl/górnicze_materiały_wybuchowe': 'PANORAMA [Przemysł i energetyka]: Górnicze materiały wybuchowe',
    'panorama_https://panoramafirm.pl/hafciarstwo': 'PANORAMA [Odzież i tekstylia]: Hafciarstwo',
    'panorama_https://panoramafirm.pl/haki_holownicze': 'PANORAMA [Budownictwo]: Haki holownicze',
    'panorama_https://panoramafirm.pl/hale_widowiskowo_sportowe': 'PANORAMA [Rozrywka i rekreacja]: Hale widowiskowo-sportowe',
    'panorama_https://panoramafirm.pl/handel_obwoźny': 'PANORAMA [Usługi dla każdego]: Handel obwoźny',
    'panorama_https://panoramafirm.pl/handel_złotem_i_srebrem': 'PANORAMA [Usługi dla każdego]: Handel złotem i srebrem',
    'panorama_https://panoramafirm.pl/hotele': 'PANORAMA [Turystyka]: Hotele',
    'panorama_https://panoramafirm.pl/hotele_dla_zwierząt': 'PANORAMA [Usługi dla każdego]: Hotele dla zwierząt',
    'panorama_https://panoramafirm.pl/hurt_i_produkcja_zegarów_i_zegarków': 'PANORAMA [Usługi dla każdego]: Hurt i produkcja zegarów i zegarków',
    'panorama_https://panoramafirm.pl/hurtownie_artykułów_elektrotechnicznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie artykułów elektrotechnicznych',
    'panorama_https://panoramafirm.pl/hurtownie_artykułów_metalowych': 'PANORAMA [Przemysł i energetyka]: Hurtownie artykułów metalowych',
    'panorama_https://panoramafirm.pl/hurtownie_artykułów_papierniczych': 'PANORAMA [Dzieci]: Hurtownie artykułów papierniczych',
    'panorama_https://panoramafirm.pl/hurtownie_bielizny': 'PANORAMA [Odzież i tekstylia]: Hurtownie bielizny',
    'panorama_https://panoramafirm.pl/hurtownie_chemii_gospodarczej': 'PANORAMA [Przemysł i energetyka]: Hurtownie chemii gospodarczej',
    'panorama_https://panoramafirm.pl/hurtownie_części_elektronicznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie części elektronicznych',
    'panorama_https://panoramafirm.pl/hurtownie_części_samochodowych': 'PANORAMA [Budownictwo]: Hurtownie części samochodowych',
    'panorama_https://panoramafirm.pl/hurtownie_dywanów_i_wykładzin': 'PANORAMA [Budownictwo]: Hurtownie dywanów i wykładzin',
    'panorama_https://panoramafirm.pl/hurtownie_farb_lakierów_i_emalii': 'PANORAMA [Przemysł i energetyka]: Hurtownie farb, lakierów i emalii',
    'panorama_https://panoramafirm.pl/hurtownie_gresu_terakoty_i_płytek_ceramicznych': 'PANORAMA [Budownictwo]: Hurtownie gresu, terakoty i płytek ceramicznych',
    'panorama_https://panoramafirm.pl/hurtownie_i_producenci_artykułów_dziecięcych': 'PANORAMA [Dzieci]: Hurtownie i producenci artykułów dziecięcych',
    'panorama_https://panoramafirm.pl/hurtownie_książek': 'PANORAMA [Rozrywka i rekreacja]: Hurtownie książek',
    'panorama_https://panoramafirm.pl/hurtownie_obuwia': 'PANORAMA [Odzież i tekstylia]: Hurtownie obuwia',
    'panorama_https://panoramafirm.pl/hurtownie_odzieży': 'PANORAMA [Odzież i tekstylia]: Hurtownie odzieży',
    'panorama_https://panoramafirm.pl/hurtownie_parkietu_i_paneli_podłogowych': 'PANORAMA [Budownictwo]: Hurtownie parkietu i paneli podłogowych',
    'panorama_https://panoramafirm.pl/hurtownie_sprzętu_fotograficznego': 'PANORAMA [Usługi dla każdego]: Hurtownie sprzętu fotograficznego',
    'panorama_https://panoramafirm.pl/hurtownie_sprzętu_sportowego_i_turystycznego': 'PANORAMA [Rozrywka i rekreacja]: Hurtownie sprzętu sportowego i turystycznego',
    'panorama_https://panoramafirm.pl/hurtownie_tkanin_i_dzianin': 'PANORAMA [Odzież i tekstylia]: Hurtownie tkanin i dzianin',
    'panorama_https://panoramafirm.pl/hurtownie_urządzeń_elektrycznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie urządzeń elektrycznych',
    'panorama_https://panoramafirm.pl/hurtownie_urządzeń_sanitarnych': 'PANORAMA [Budownictwo]: Hurtownie urządzeń sanitarnych',
    'panorama_https://panoramafirm.pl/hurtownie_zabawek': 'PANORAMA [Rozrywka i rekreacja]: Hurtownie zabawek',
    'panorama_https://panoramafirm.pl/hurtownie_środków_chemicznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie środków chemicznych',
    'panorama_https://panoramafirm.pl/hurtownie_żaluzji_i_rolet': 'PANORAMA [Budownictwo]: Hurtownie żaluzji i rolet',
    'panorama_https://panoramafirm.pl/hydraulicy': 'PANORAMA [Usługi dla każdego]: Hydraulicy',
    'panorama_https://panoramafirm.pl/hydraulika_siłowa': 'PANORAMA [Przemysł i energetyka]: Hydraulika siłowa',
    'panorama_https://panoramafirm.pl/hydrotechnika': 'PANORAMA [Przemysł i energetyka]: Hydrotechnika',
    'panorama_https://panoramafirm.pl/inf/cookies.html': 'PANORAMA [Zdrowie i uroda]: Polityka cookies',
    'panorama_https://panoramafirm.pl/inf/obowiazek-informacyjny.html': 'PANORAMA [Zdrowie i uroda]: Obowiązek informacyjny',
    'panorama_https://panoramafirm.pl/inf/polityka-prywatnosci.html': 'PANORAMA [Zdrowie i uroda]: Polityka prywatności',
    'panorama_https://panoramafirm.pl/inf/popularne-zapytania.html': 'PANORAMA [Zdrowie i uroda]: Popularne zapytania',
    'panorama_https://panoramafirm.pl/inf/regulamin.html': 'PANORAMA [Zdrowie i uroda]: Regulamin',
    'panorama_https://panoramafirm.pl/informacja_turystyczna': 'PANORAMA [Turystyka]: Informacja turystyczna',
    'panorama_https://panoramafirm.pl/informatyka': 'PANORAMA [Telekomunikacja, internet, technologie]: Informatyka',
    'panorama_https://panoramafirm.pl/inkubatory_przedsiębiorczości': 'PANORAMA [Instytucje, urzędy]: Inkubatory przedsiębiorczości',
    'panorama_https://panoramafirm.pl/instalacja_i_serwis_ogrzewania': 'PANORAMA [Przemysł i energetyka]: Instalacja i serwis ogrzewania',
    'panorama_https://panoramafirm.pl/instalacja_systemów_alarmowych': 'PANORAMA [Budownictwo]: Instalacja systemów alarmowych',
    'panorama_https://panoramafirm.pl/instalacje_energetyczne_i_ciepłownicze': 'PANORAMA [Budownictwo]: Instalacje energetyczne i ciepłownicze',
    'panorama_https://panoramafirm.pl/instalacje_i_urządzenia_energetyczne': 'PANORAMA [Przemysł i energetyka]: Instalacje i urządzenia energetyczne',
    'panorama_https://panoramafirm.pl/instalacje_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Instalacje przemysłowe',
    'panorama_https://panoramafirm.pl/instalacje_systemów_teletechnicznych': 'PANORAMA [Budownictwo]: Instalacje systemów teletechnicznych',
    'panorama_https://panoramafirm.pl/instalacje_termoizolacyjne': 'PANORAMA [Budownictwo]: Instalacje termoizolacyjne',
    'panorama_https://panoramafirm.pl/instrumenty_i_sklepy_muzyczne': 'PANORAMA [Rozrywka i rekreacja]: Instrumenty i sklepy muzyczne',
    'panorama_https://panoramafirm.pl/internaty_i_akademiki': 'PANORAMA [Instytucje, urzędy]: Internaty i akademiki',
    'panorama_https://panoramafirm.pl/internet': 'PANORAMA [Usługi dla każdego]: Internet',
    'panorama_https://panoramafirm.pl/inwestycje_budowlane': 'PANORAMA [Przemysł i energetyka]: Inwestycje budowlane',
    'panorama_https://panoramafirm.pl/izolacja_akustyczna': 'PANORAMA [Budownictwo]: Izolacja akustyczna',
    'panorama_https://panoramafirm.pl/izolacja_termiczna': 'PANORAMA [Budownictwo]: Izolacja termiczna',
    'panorama_https://panoramafirm.pl/izolacja_wodochronna': 'PANORAMA [Budownictwo]: Izolacja wodochronna',
    'panorama_https://panoramafirm.pl/jachty': 'PANORAMA [Rozrywka i rekreacja]: Jachty',
    'panorama_https://panoramafirm.pl/jeździectwo': 'PANORAMA [Rozrywka i rekreacja]: Jeździectwo',
    'panorama_https://panoramafirm.pl/kaletnictwo_i_rymarstwo': 'PANORAMA [Usługi dla każdego]: Kaletnictwo i rymarstwo',
    'panorama_https://panoramafirm.pl/kamień_i_kruszywa': 'PANORAMA [Budownictwo]: Kamień i kruszywa',
    'panorama_https://panoramafirm.pl/kantory': 'PANORAMA [Usługi dla każdego]: Kantory',
    'panorama_https://panoramafirm.pl/karty_kredytowe_płatnicze_i_programy_lojalnościowe': 'PANORAMA [Finanse i ubezpieczenia]: Karty kredytowe, płatnicze i programy lojalnościowe',
    'panorama_https://panoramafirm.pl/kasyna_i_bukmacherzy': 'PANORAMA [Rozrywka i rekreacja]: Kasyna i bukmacherzy',
    'panorama_https://panoramafirm.pl/kawiarenki_internetowe': 'PANORAMA [Usługi dla każdego]: Kawiarenki internetowe',
    'panorama_https://panoramafirm.pl/kawiarnie': 'PANORAMA [Rozrywka i rekreacja]: Kawiarnie',
    'panorama_https://panoramafirm.pl/kempingi': 'PANORAMA [Turystyka]: Kempingi',
    'panorama_https://panoramafirm.pl/kina': 'PANORAMA [Rozrywka i rekreacja]: Kina',
    'panorama_https://panoramafirm.pl/kleje_i_żywice': 'PANORAMA [Przemysł i energetyka]: Kleje i żywice',
    'panorama_https://panoramafirm.pl/klimatyzacja': 'PANORAMA [Budownictwo]: Klimatyzacja',
    'panorama_https://panoramafirm.pl/klimatyzacja_samochodowa': 'PANORAMA [Budownictwo]: Klimatyzacja samochodowa',
    'panorama_https://panoramafirm.pl/kluby_muzyczne': 'PANORAMA [Rozrywka i rekreacja]: Kluby muzyczne',
    'panorama_https://panoramafirm.pl/kluby_nocne': 'PANORAMA [Rozrywka i rekreacja]: Kluby nocne',
    'panorama_https://panoramafirm.pl/kominiarze': 'PANORAMA [Usługi dla każdego]: Kominiarze',
    'panorama_https://panoramafirm.pl/kominki': 'PANORAMA [Budownictwo]: Kominki',
    'panorama_https://panoramafirm.pl/kominy': 'PANORAMA [Budownictwo]: Kominy',
    'panorama_https://panoramafirm.pl/komisy': 'PANORAMA [Usługi dla każdego]: Komisy',
    'panorama_https://panoramafirm.pl/kompresory': 'PANORAMA [Przemysł i energetyka]: Kompresory',
    'panorama_https://panoramafirm.pl/komunikacja_i_przewozy_pasażerskie': 'PANORAMA [Turystyka]: Komunikacja i przewozy pasażerskie',
    'panorama_https://panoramafirm.pl/konserwacja_zabytków': 'PANORAMA [Instytucje, urzędy]: Konserwacja zabytków',
    'panorama_https://panoramafirm.pl/konstrukcje_aluminiowe': 'PANORAMA [Przemysł i energetyka]: Konstrukcje aluminiowe',
    'panorama_https://panoramafirm.pl/konstrukcje_stalowe': 'PANORAMA [Przemysł i energetyka]: Konstrukcje stalowe',
    'panorama_https://panoramafirm.pl/kontakt.html': 'PANORAMA [Zdrowie i uroda]: Kontakt',
    'panorama_https://panoramafirm.pl/kontenery': 'PANORAMA [Przemysł i energetyka]: Kontenery',
    'panorama_https://panoramafirm.pl/korek_naturalny': 'PANORAMA [Budownictwo]: Korek naturalny',
    'panorama_https://panoramafirm.pl/korepetycje': 'PANORAMA [Usługi dla każdego]: Korepetycje',
    'panorama_https://panoramafirm.pl/kosmetyki_samochodowe': 'PANORAMA [Budownictwo]: Kosmetyki samochodowe',
    'panorama_https://panoramafirm.pl/kostka_brukowa': 'PANORAMA [Budownictwo]: Kostka brukowa',
    'panorama_https://panoramafirm.pl/koszule_i_krawaty': 'PANORAMA [Odzież i tekstylia]: Koszule i krawaty',
    'panorama_https://panoramafirm.pl/koła_i_zestawy_jezdne': 'PANORAMA [Budownictwo]: Koła i zestawy jezdne',
    'panorama_https://panoramafirm.pl/kraty_pomostowe': 'PANORAMA [Przemysł i energetyka]: Kraty pomostowe',
    'panorama_https://panoramafirm.pl/krawiectwo': 'PANORAMA [Usługi dla każdego]: Krawiectwo',
    'panorama_https://panoramafirm.pl/kredyty_i_finansowanie': 'PANORAMA [Finanse i ubezpieczenia]: Kredyty i finansowanie',
    'panorama_https://panoramafirm.pl/ksero': 'PANORAMA [Usługi dla każdego]: Ksero',
    'panorama_https://panoramafirm.pl/księgarnie': 'PANORAMA [Rozrywka i rekreacja]: Księgarnie',
    'panorama_https://panoramafirm.pl/kurierzy': 'PANORAMA [Usługi dla każdego]: Kurierzy',
    'panorama_https://panoramafirm.pl/kursy_i_nauka_jazdy': 'PANORAMA [Usługi dla każdego]: Kursy i nauka jazdy',
    'panorama_https://panoramafirm.pl/kwiaciarnie': 'PANORAMA [Usługi dla każdego]: Kwiaciarnie',
    'panorama_https://panoramafirm.pl/lakiery_samochodowe': 'PANORAMA [Budownictwo]: Lakiery samochodowe',
    'panorama_https://panoramafirm.pl/laminaty': 'PANORAMA [Przemysł i energetyka]: Laminaty',
    'panorama_https://panoramafirm.pl/lasery': 'PANORAMA [Przemysł i energetyka]: Lasery',
    'panorama_https://panoramafirm.pl/leasing': 'PANORAMA [Finanse i ubezpieczenia]: Leasing',
    'panorama_https://panoramafirm.pl/leczenie_uzależnień': 'PANORAMA [Usługi dla każdego]: Leczenie uzależnień',
    'panorama_https://panoramafirm.pl/lecznice_weterynaryjne': 'PANORAMA [Rozrywka i rekreacja]: Lecznice weterynaryjne',
    'panorama_https://panoramafirm.pl/liczniki_energii_elektrycznej': 'PANORAMA [Przemysł i energetyka]: Liczniki energii elektrycznej',
    'panorama_https://panoramafirm.pl/linie_lotnicze': 'PANORAMA [Turystyka]: Linie lotnicze',
    'panorama_https://panoramafirm.pl/logopedzi': 'PANORAMA [Dzieci]: Logopedzi',
    'panorama_https://panoramafirm.pl/lombardy': 'PANORAMA [Usługi dla każdego]: Lombardy',
    'panorama_https://panoramafirm.pl/lornetki_i_lunety': 'PANORAMA [Usługi dla każdego]: Lornetki i lunety',
    'panorama_https://panoramafirm.pl/lotniska': 'PANORAMA [Turystyka]: Lotniska',
    'panorama_https://panoramafirm.pl/lustra': 'PANORAMA [Budownictwo]: Lustra',
    'panorama_https://panoramafirm.pl/magiel': 'PANORAMA [Usługi dla każdego]: Magiel',
    'panorama_https://panoramafirm.pl/magnesy_i_elektromagnesy': 'PANORAMA [Przemysł i energetyka]: Magnesy i elektromagnesy',
    'panorama_https://panoramafirm.pl/maklerzy_giełdowi': 'PANORAMA [Finanse i ubezpieczenia]: Maklerzy giełdowi',
    'panorama_https://panoramafirm.pl/malowanie_i_lakierowanie_proszkowe': 'PANORAMA [Budownictwo]: Malowanie i lakierowanie proszkowe',
    'panorama_https://panoramafirm.pl/malowanie_i_lakierowanie_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Malowanie i lakierowanie przemysłowe',
    'panorama_https://panoramafirm.pl/malowanie_i_tapetowanie': 'PANORAMA [Usługi dla każdego]: Malowanie i tapetowanie',
    'panorama_https://panoramafirm.pl/mapy_i_plany': 'PANORAMA [Usługi dla każdego]: Mapy i plany',
    'panorama_https://panoramafirm.pl/marmur_granit_i_kamień_naturalny': 'PANORAMA [Budownictwo]: Marmur, granit i kamień naturalny',
    'panorama_https://panoramafirm.pl/maszty_i_słupy': 'PANORAMA [Przemysł i energetyka]: Maszty i słupy',
    'panorama_https://panoramafirm.pl/maszyny_do_obróbki_drewna': 'PANORAMA [Przemysł i energetyka]: Maszyny do obróbki drewna',
    'panorama_https://panoramafirm.pl/maszyny_do_obróbki_metali': 'PANORAMA [Przemysł i energetyka]: Maszyny do obróbki metali',
    'panorama_https://panoramafirm.pl/maszyny_do_szycia': 'PANORAMA [Usługi dla każdego]: Maszyny do szycia',
    'panorama_https://panoramafirm.pl/maszyny_dziewiarskie': 'PANORAMA [Przemysł i energetyka]: Maszyny dziewiarskie',
    'panorama_https://panoramafirm.pl/maszyny_hafciarskie': 'PANORAMA [Odzież i tekstylia]: Maszyny hafciarskie',
    'panorama_https://panoramafirm.pl/maszyny_i_sprzęt_górniczy': 'PANORAMA [Przemysł i energetyka]: Maszyny i sprzęt górniczy',
    'panorama_https://panoramafirm.pl/maszyny_pakujące': 'PANORAMA [Przemysł i energetyka]: Maszyny pakujące',
    'panorama_https://panoramafirm.pl/materiały_budowlane': 'PANORAMA [Budownictwo]: Materiały budowlane',
    'panorama_https://panoramafirm.pl/materiały_do_spawania_i_zgrzewania': 'PANORAMA [Przemysł i energetyka]: Materiały do spawania i zgrzewania',
    'panorama_https://panoramafirm.pl/materiały_do_wykańczania_wnętrz': 'PANORAMA [Budownictwo]: Materiały do wykańczania wnętrz',
    'panorama_https://panoramafirm.pl/materiały_drewnopochodne': 'PANORAMA [Przemysł i energetyka]: Materiały drewnopochodne',
    'panorama_https://panoramafirm.pl/materiały_elektryczne': 'PANORAMA [Przemysł i energetyka]: Materiały elektryczne',
    'panorama_https://panoramafirm.pl/materiały_elewacyjne': 'PANORAMA [Budownictwo]: Materiały elewacyjne',
    'panorama_https://panoramafirm.pl/materiały_izolacyjne': 'PANORAMA [Budownictwo]: Materiały izolacyjne',
    'panorama_https://panoramafirm.pl/materiały_ognioodporne': 'PANORAMA [Przemysł i energetyka]: Materiały ognioodporne',
    'panorama_https://panoramafirm.pl/materiały_opałowe': 'PANORAMA [Budownictwo]: Materiały opałowe',
    'panorama_https://panoramafirm.pl/materiały_tapicerskie': 'PANORAMA [Budownictwo]: Materiały tapicerskie',
    'panorama_https://panoramafirm.pl/materiały_ścierne_i_polerskie': 'PANORAMA [Przemysł i energetyka]: Materiały ścierne i polerskie',
    'panorama_https://panoramafirm.pl/meble': 'PANORAMA [Budownictwo]: Meble',
    'panorama_https://panoramafirm.pl/meble_biurowe': 'PANORAMA [Budownictwo]: Meble biurowe',
    'panorama_https://panoramafirm.pl/meble_kuchenne': 'PANORAMA [Budownictwo]: Meble kuchenne',
    'panorama_https://panoramafirm.pl/meble_metalowe': 'PANORAMA [Budownictwo]: Meble metalowe',
    'panorama_https://panoramafirm.pl/meble_na_zamówienie': 'PANORAMA [Budownictwo]: Meble na zamówienie',
    'panorama_https://panoramafirm.pl/meble_ogrodowe': 'PANORAMA [Budownictwo]: Meble ogrodowe',
    'panorama_https://panoramafirm.pl/mechanika_samochodowa': 'PANORAMA [Budownictwo]: Mechanika samochodowa',
    'panorama_https://panoramafirm.pl/metale_nieżelazne_i_kolorowe': 'PANORAMA [Przemysł i energetyka]: Metale nieżelazne i kolorowe',
    'panorama_https://panoramafirm.pl/metale_żelazne': 'PANORAMA [Przemysł i energetyka]: Metale żelazne',
    'panorama_https://panoramafirm.pl/metalizowanie_i_powlekanie_tworzyw': 'PANORAMA [Przemysł i energetyka]: Metalizowanie i powlekanie tworzyw',
    'panorama_https://panoramafirm.pl/metaloplastyka': 'PANORAMA [Rozrywka i rekreacja]: Metaloplastyka',
    'panorama_https://panoramafirm.pl/militaria': 'PANORAMA [Rozrywka i rekreacja]: Militaria',
    'panorama_https://panoramafirm.pl/modelarstwo': 'PANORAMA [Rozrywka i rekreacja]: Modelarstwo',
    'panorama_https://panoramafirm.pl/montaż_i_produkcja_basenów_i_fontann': 'PANORAMA [Budownictwo]: Montaż i produkcja basenów i fontann',
    'panorama_https://panoramafirm.pl/montaż_i_sprzedaż_żaluzji_i_rolet': 'PANORAMA [Budownictwo]: Montaż i sprzedaż żaluzji i rolet',
    'panorama_https://panoramafirm.pl/muzea': 'PANORAMA [Rozrywka i rekreacja]: Muzea',
    'panorama_https://panoramafirm.pl/myślistwo': 'PANORAMA [Rozrywka i rekreacja]: Myślistwo',
    'panorama_https://panoramafirm.pl/naczepy_samochodowe': 'PANORAMA [Budownictwo]: Naczepy samochodowe',
    'panorama_https://panoramafirm.pl/nadzór_budowlany': 'PANORAMA [Budownictwo]: Nadzór budowlany',
    'panorama_https://panoramafirm.pl/najnowsze_wizytowki.html': 'PANORAMA [Zdrowie i uroda]: Najnowsze wizytówki',
    'panorama_https://panoramafirm.pl/namioty_i_hale_namiotowe': 'PANORAMA [Turystyka]: Namioty i hale namiotowe',
    'panorama_https://panoramafirm.pl/napełnianie_butli_gazowych': 'PANORAMA [Przemysł i energetyka]: Napełnianie butli gazowych',
    'panorama_https://panoramafirm.pl/narodowy_fundusz_zdrowia': 'PANORAMA [Instytucje, urzędy]: Narodowy Fundusz Zdrowia',
    'panorama_https://panoramafirm.pl/narzędzia': 'PANORAMA [Przemysł i energetyka]: Narzędzia',
    'panorama_https://panoramafirm.pl/narzędzia_pneumatyczne': 'PANORAMA [Przemysł i energetyka]: Narzędzia pneumatyczne',
    'panorama_https://panoramafirm.pl/nauka_muzyki': 'PANORAMA [Rozrywka i rekreacja]: Nauka muzyki',
    'panorama_https://panoramafirm.pl/nieruchomości': 'PANORAMA [Usługi dla każdego]: Nieruchomości',
    'panorama_https://panoramafirm.pl/noclegi_i_kwatery_prywatne': 'PANORAMA [Turystyka]: Noclegi i kwatery prywatne',
    'panorama_https://panoramafirm.pl/noclegownie': 'PANORAMA [Turystyka]: Noclegownie',
    'panorama_https://panoramafirm.pl/notariusze': 'PANORAMA [Usługi dla każdego]: Notariusze',
    'panorama_https://panoramafirm.pl/nośniki_danych_i_płyty_cd_i_dvd': 'PANORAMA [Rozrywka i rekreacja]: Nośniki danych i płyty CD i DVD',
    'panorama_https://panoramafirm.pl/numizmatyka': 'PANORAMA [Rozrywka i rekreacja]: Numizmatyka',
    'panorama_https://panoramafirm.pl/obrusy': 'PANORAMA [Odzież i tekstylia]: Obrusy',
    'panorama_https://panoramafirm.pl/obróbka_metali': 'PANORAMA [Przemysł i energetyka]: Obróbka metali',
    'panorama_https://panoramafirm.pl/obróbka_tworzyw_sztucznych': 'PANORAMA [Przemysł i energetyka]: Obróbka tworzyw sztucznych',
    'panorama_https://panoramafirm.pl/obsługa_cudzoziemców': 'PANORAMA [Usługi dla każdego]: Obsługa cudzoziemców',
    'panorama_https://panoramafirm.pl/ochrona_środowiska': 'PANORAMA [Instytucje, urzędy]: Ochrona środowiska',
    'panorama_https://panoramafirm.pl/oczyszczanie_ścieków': 'PANORAMA [Usługi dla każdego]: Oczyszczanie ścieków',
    'panorama_https://panoramafirm.pl/oddłużanie': 'PANORAMA [Finanse i ubezpieczenia]: Oddłużanie',
    'panorama_https://panoramafirm.pl/odkurzacze_centralne': 'PANORAMA [Budownictwo]: Odkurzacze centralne',
    'panorama_https://panoramafirm.pl/odlewnie': 'PANORAMA [Przemysł i energetyka]: Odlewnie',
    'panorama_https://panoramafirm.pl/odszkodowania': 'PANORAMA [Usługi dla każdego]: Odszkodowania',
    'panorama_https://panoramafirm.pl/odzież_damska': 'PANORAMA [Odzież i tekstylia]: Odzież damska',
    'panorama_https://panoramafirm.pl/odzież_dziecięca': 'PANORAMA [Odzież i tekstylia]: Odzież dziecięca',
    'panorama_https://panoramafirm.pl/odzież_męska': 'PANORAMA [Odzież i tekstylia]: Odzież męska',
    'panorama_https://panoramafirm.pl/odzież_robocza': 'PANORAMA [Odzież i tekstylia]: Odzież robocza',
    'panorama_https://panoramafirm.pl/odzież_skórzana': 'PANORAMA [Odzież i tekstylia]: Odzież skórzana',
    'panorama_https://panoramafirm.pl/odzież_sportowa': 'PANORAMA [Rozrywka i rekreacja]: Odzież sportowa',
    'panorama_https://panoramafirm.pl/odzież_używana': 'PANORAMA [Odzież i tekstylia]: Odzież używana',
    'panorama_https://panoramafirm.pl/odzyskiwanie_i_ochrona_danych_komputerowych': 'PANORAMA [Usługi dla każdego]: Odzyskiwanie i ochrona danych komputerowych',
    'panorama_https://panoramafirm.pl/ogrodnictwo': 'PANORAMA [Budownictwo]: Ogrodnictwo',
    'panorama_https://panoramafirm.pl/ogrody_zoologiczne_i_botaniczne': 'PANORAMA [Rozrywka i rekreacja]: Ogrody zoologiczne i botaniczne',
    'panorama_https://panoramafirm.pl/ogrzewanie_elektryczne': 'PANORAMA [Przemysł i energetyka]: Ogrzewanie elektryczne',
    'panorama_https://panoramafirm.pl/okleiny': 'PANORAMA [Budownictwo]: Okleiny',
    'panorama_https://panoramafirm.pl/oklejanie_samochodów': 'PANORAMA [Budownictwo]: Oklejanie samochodów',
    'panorama_https://panoramafirm.pl/okna': 'PANORAMA [Budownictwo]: Okna',
    'panorama_https://panoramafirm.pl/okna_dachowe': 'PANORAMA [Budownictwo]: Okna dachowe',
    'panorama_https://panoramafirm.pl/okna_drewniane': 'PANORAMA [Budownictwo]: Okna drewniane',
    'panorama_https://panoramafirm.pl/okucia': 'PANORAMA [Przemysł i energetyka]: Okucia',
    'panorama_https://panoramafirm.pl/olej_opałowy': 'PANORAMA [Przemysł i energetyka]: Olej opałowy',
    'panorama_https://panoramafirm.pl/oleje_techniczne_i_smary': 'PANORAMA [Przemysł i energetyka]: Oleje techniczne i smary',
    'panorama_https://panoramafirm.pl/opakowania': 'PANORAMA [Przemysł i energetyka]: Opakowania',
    'panorama_https://panoramafirm.pl/opakowania_foliowe': 'PANORAMA [Przemysł i energetyka]: Opakowania foliowe',
    'panorama_https://panoramafirm.pl/opakowania_jednorazowe': 'PANORAMA [Przemysł i energetyka]: Opakowania jednorazowe',
    'panorama_https://panoramafirm.pl/opakowania_papierowe_i_tekturowe': 'PANORAMA [Budownictwo]: Opakowania papierowe i tekturowe',
    'panorama_https://panoramafirm.pl/opakowania_z_tworzyw_sztucznych': 'PANORAMA [Przemysł i energetyka]: Opakowania z tworzyw sztucznych',
    'panorama_https://panoramafirm.pl/operatorzy_pocztowi': 'PANORAMA [Usługi dla każdego]: Operatorzy pocztowi',
    'panorama_https://panoramafirm.pl/operatorzy_telekomunikacyjni': 'PANORAMA [Usługi dla każdego]: Operatorzy telekomunikacyjni',
    'panorama_https://panoramafirm.pl/opieka_nad_dziećmi': 'PANORAMA [Dzieci]: Opieka nad dziećmi',
    'panorama_https://panoramafirm.pl/oprogramowanie_komputerowe': 'PANORAMA [Telekomunikacja, internet, technologie]: Oprogramowanie komputerowe',
    'panorama_https://panoramafirm.pl/organizacja_imprez_i_konferencji': 'PANORAMA [Usługi dla każdego]: Organizacja imprez i konferencji',
    'panorama_https://panoramafirm.pl/ostrzenie': 'PANORAMA [Usługi dla każdego]: Ostrzenie',
    'panorama_https://panoramafirm.pl/osuszanie_budynków': 'PANORAMA [Usługi dla każdego]: Osuszanie budynków',
    'panorama_https://panoramafirm.pl/oznakowanie_i_sygnalizacja_dróg': 'PANORAMA [Budownictwo]: Oznakowanie i sygnalizacja dróg',
    'panorama_https://panoramafirm.pl/ośrodki_adopcyjno_wychowawcze': 'PANORAMA [Instytucje, urzędy]: Ośrodki adopcyjno-wychowawcze',
    'panorama_https://panoramafirm.pl/ośrodki_i_kluby_sportowo_rekreacyjne': 'PANORAMA [Rozrywka i rekreacja]: Ośrodki i kluby sportowo-rekreacyjne',
    'panorama_https://panoramafirm.pl/ośrodki_szkolno_wychowawcze': 'PANORAMA [Dzieci]: Ośrodki szkolno-wychowawcze',
    'panorama_https://panoramafirm.pl/ośrodki_wychowawcze': 'PANORAMA [Instytucje, urzędy]: Ośrodki wychowawcze',
    'panorama_https://panoramafirm.pl/oświetlenie': 'PANORAMA [Budownictwo]: Oświetlenie',
    'panorama_https://panoramafirm.pl/palety': 'PANORAMA [Przemysł i energetyka]: Palety',
    'panorama_https://panoramafirm.pl/paliwa': 'PANORAMA [Budownictwo]: Paliwa',
    'panorama_https://panoramafirm.pl/paliwa_i_opał_ekologiczny': 'PANORAMA [Przemysł i energetyka]: Paliwa i opał ekologiczny',
    'panorama_https://panoramafirm.pl/pamiątki_i_upominki': 'PANORAMA [Usługi dla każdego]: Pamiątki i upominki',
    'panorama_https://panoramafirm.pl/panele_i_podłogi': 'PANORAMA [Budownictwo]: Panele i podłogi',
    'panorama_https://panoramafirm.pl/panorama_miast': 'PANORAMA [Zdrowie i uroda]: Panorama miast',
    'panorama_https://panoramafirm.pl/panorama_regionow': 'PANORAMA [Zdrowie i uroda]: Panorama regionów',
    'panorama_https://panoramafirm.pl/papierosy_elektroniczne': 'PANORAMA [Usługi dla każdego]: Papierosy elektroniczne',
    'panorama_https://panoramafirm.pl/parapety': 'PANORAMA [Budownictwo]: Parapety',
    'panorama_https://panoramafirm.pl/parasole': 'PANORAMA [Odzież i tekstylia]: Parasole',
    'panorama_https://panoramafirm.pl/parki_rozrywki': 'PANORAMA [Rozrywka i rekreacja]: Parki rozrywki',
    'panorama_https://panoramafirm.pl/parkiet_i_panele_podłogowe': 'PANORAMA [Budownictwo]: Parkiet i panele podłogowe',
    'panorama_https://panoramafirm.pl/pasmanteria_i_dodatki_krawieckie': 'PANORAMA [Odzież i tekstylia]: Pasmanteria i dodatki krawieckie',
    'panorama_https://panoramafirm.pl/pasy_napędowe_i_transportujące': 'PANORAMA [Przemysł i energetyka]: Pasy napędowe i transportujące',
    'panorama_https://panoramafirm.pl/pensjonaty_hostele_i_ośrodki_wypoczynkowe': 'PANORAMA [Turystyka]: Pensjonaty, hostele i ośrodki wypoczynkowe',
    'panorama_https://panoramafirm.pl/piece': 'PANORAMA [Przemysł i energetyka]: Piece',
    'panorama_https://panoramafirm.pl/pirotechnika': 'PANORAMA [Rozrywka i rekreacja]: Pirotechnika',
    'panorama_https://panoramafirm.pl/pizzerie': 'PANORAMA [Rozrywka i rekreacja]: Pizzerie',
    'panorama_https://panoramafirm.pl/place_i_hale_targowe': 'PANORAMA [Usługi dla każdego]: Place i hale targowe',
    'panorama_https://panoramafirm.pl/plandeki': 'PANORAMA [Budownictwo]: Plandeki',
    'panorama_https://panoramafirm.pl/pneumatyka_siłowa': 'PANORAMA [Przemysł i energetyka]: Pneumatyka siłowa',
    'panorama_https://panoramafirm.pl/poczta_i_urzędy_pocztowe': 'PANORAMA [Instytucje, urzędy]: Poczta i urzędy pocztowe',
    'panorama_https://panoramafirm.pl/pocztówki_i_widokówki': 'PANORAMA [Usługi dla każdego]: Pocztówki i widokówki',
    'panorama_https://panoramafirm.pl/podnośniki': 'PANORAMA [Przemysł i energetyka]: Podnośniki',
    'panorama_https://panoramafirm.pl/podzespoły_elektroniczne': 'PANORAMA [Przemysł i energetyka]: Podzespoły elektroniczne',
    'panorama_https://panoramafirm.pl/pogotowie_ratunkowe': 'PANORAMA [Instytucje, urzędy]: Pogotowie ratunkowe',
    'panorama_https://panoramafirm.pl/pojazdy_specjalistyczne': 'PANORAMA [Budownictwo]: Pojazdy specjalistyczne',
    'panorama_https://panoramafirm.pl/pojazdy_zabytkowe_i_dorożki': 'PANORAMA [Rozrywka i rekreacja]: Pojazdy zabytkowe i dorożki',
    'panorama_https://panoramafirm.pl/policja': 'PANORAMA [Instytucje, urzędy]: Policja',
    'panorama_https://panoramafirm.pl/pomoc_domowa': 'PANORAMA [Usługi dla każdego]: Pomoc domowa',
    'panorama_https://panoramafirm.pl/pompy': 'PANORAMA [Przemysł i energetyka]: Pompy',
    'panorama_https://panoramafirm.pl/poradniki': 'PANORAMA [Zdrowie i uroda]: Poradniki',
    'panorama_https://panoramafirm.pl/poręcze_i_balustrady': 'PANORAMA [Budownictwo]: Poręcze i balustrady',
    'panorama_https://panoramafirm.pl/posadzki_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Posadzki przemysłowe',
    'panorama_https://panoramafirm.pl/pośrednicy_ubezpieczeniowi': 'PANORAMA [Usługi dla każdego]: Pośrednicy ubezpieczeniowi',
    'panorama_https://panoramafirm.pl/prace_elewacyjne': 'PANORAMA [Budownictwo]: Prace elewacyjne',
    'panorama_https://panoramafirm.pl/prace_podwodne': 'PANORAMA [Przemysł i energetyka]: Prace podwodne',
    'panorama_https://panoramafirm.pl/prace_wysokościowe': 'PANORAMA [Budownictwo]: Prace wysokościowe',
    'panorama_https://panoramafirm.pl/pralnie_i_farbiarnie': 'PANORAMA [Odzież i tekstylia]: Pralnie i farbiarnie',
    'panorama_https://panoramafirm.pl/prefabrykaty_budowlane': 'PANORAMA [Budownictwo]: Prefabrykaty budowlane',
    'panorama_https://panoramafirm.pl/producenci_domów_drewnianych': 'PANORAMA [Budownictwo]: Producenci domów drewnianych',
    'panorama_https://panoramafirm.pl/producenci_farb_i_lakierów': 'PANORAMA [Przemysł i energetyka]: Producenci farb i lakierów',
    'panorama_https://panoramafirm.pl/producenci_sprzętu_sportowego_i_turystycznego': 'PANORAMA [Rozrywka i rekreacja]: Producenci sprzętu sportowego i turystycznego',
    'panorama_https://panoramafirm.pl/produkcja_artykułów_elektrotechnicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja artykułów elektrotechnicznych',
    'panorama_https://panoramafirm.pl/produkcja_artykułów_higienicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja artykułów higienicznych',
    'panorama_https://panoramafirm.pl/produkcja_artykułów_metalowych': 'PANORAMA [Przemysł i energetyka]: Produkcja artykułów metalowych',
    'panorama_https://panoramafirm.pl/produkcja_artykułów_papierniczych': 'PANORAMA [Dzieci]: Produkcja artykułów papierniczych',
    'panorama_https://panoramafirm.pl/produkcja_bielizny': 'PANORAMA [Odzież i tekstylia]: Produkcja bielizny',
    'panorama_https://panoramafirm.pl/produkcja_chemii_gospodarczej': 'PANORAMA [Przemysł i energetyka]: Produkcja chemii gospodarczej',
    'panorama_https://panoramafirm.pl/produkcja_części_elektronicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja części elektronicznych',
    'panorama_https://panoramafirm.pl/produkcja_części_samochodowych': 'PANORAMA [Budownictwo]: Produkcja części samochodowych',
    'panorama_https://panoramafirm.pl/produkcja_i_hurtownie_narzędzi': 'PANORAMA [Budownictwo]: Produkcja i hurtownie narzędzi',
    'panorama_https://panoramafirm.pl/produkcja_i_montaż_domofonów': 'PANORAMA [Budownictwo]: Produkcja i montaż domofonów',
    'panorama_https://panoramafirm.pl/produkcja_i_montaż_szamb': 'PANORAMA [Budownictwo]: Produkcja i montaż szamb',
    'panorama_https://panoramafirm.pl/produkcja_i_sprzedaż_opon': 'PANORAMA [Budownictwo]: Produkcja i sprzedaż opon',
    'panorama_https://panoramafirm.pl/produkcja_kosmetyków': 'PANORAMA [Usługi dla każdego]: Produkcja kosmetyków',
    'panorama_https://panoramafirm.pl/produkcja_kryształów_i_szkła_ozdobnego': 'PANORAMA [Budownictwo]: Produkcja kryształów i szkła ozdobnego',
    'panorama_https://panoramafirm.pl/produkcja_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Produkcja maszyn budowlanych',
    'panorama_https://panoramafirm.pl/produkcja_obuwia': 'PANORAMA [Odzież i tekstylia]: Produkcja obuwia',
    'panorama_https://panoramafirm.pl/produkcja_odzieży': 'PANORAMA [Odzież i tekstylia]: Produkcja odzieży',
    'panorama_https://panoramafirm.pl/produkcja_parkietu_i_paneli_podłogowych': 'PANORAMA [Budownictwo]: Produkcja parkietu i paneli podłogowych',
    'panorama_https://panoramafirm.pl/produkcja_sprężyn': 'PANORAMA [Przemysł i energetyka]: Produkcja sprężyn',
    'panorama_https://panoramafirm.pl/produkcja_systemów_alarmowych': 'PANORAMA [Budownictwo]: Produkcja systemów alarmowych',
    'panorama_https://panoramafirm.pl/produkcja_tkanin_i_dzianin': 'PANORAMA [Odzież i tekstylia]: Produkcja tkanin i dzianin',
    'panorama_https://panoramafirm.pl/produkcja_urządzeń_elektronicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja urządzeń elektronicznych',
    'panorama_https://panoramafirm.pl/produkcja_urządzeń_elektrycznych': 'PANORAMA [Przemysł i energetyka]: Produkcja urządzeń elektrycznych',
    'panorama_https://panoramafirm.pl/produkcja_urządzeń_sanitarnych': 'PANORAMA [Budownictwo]: Produkcja urządzeń sanitarnych',
    'panorama_https://panoramafirm.pl/produkcja_zabawek': 'PANORAMA [Rozrywka i rekreacja]: Produkcja zabawek',
    'panorama_https://panoramafirm.pl/produkcja_zasłon_firanek_i_karniszy': 'PANORAMA [Przemysł i energetyka]: Produkcja zasłon, firanek i karniszy',
    'panorama_https://panoramafirm.pl/produkcja_środków_chemicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja środków chemicznych',
    'panorama_https://panoramafirm.pl/produkcja_żaluzji_i_rolet': 'PANORAMA [Budownictwo]: Produkcja żaluzji i rolet',
    'panorama_https://panoramafirm.pl/projektowanie_i_montaż_placów_zabaw': 'PANORAMA [Rozrywka i rekreacja]: Projektowanie i montaż placów zabaw',
    'panorama_https://panoramafirm.pl/prokuratury': 'PANORAMA [Instytucje, urzędy]: Prokuratury',
    'panorama_https://panoramafirm.pl/przedszkola_prywatne': 'PANORAMA [Dzieci]: Przedszkola prywatne',
    'panorama_https://panoramafirm.pl/przedszkola_publiczne': 'PANORAMA [Dzieci]: Przedszkola publiczne',
    'panorama_https://panoramafirm.pl/przekładnie': 'PANORAMA [Budownictwo]: Przekładnie',
    'panorama_https://panoramafirm.pl/przemysłowe_urządzenia_elektryczne': 'PANORAMA [Przemysł i energetyka]: Przemysłowe urządzenia elektryczne',
    'panorama_https://panoramafirm.pl/przenośniki': 'PANORAMA [Przemysł i energetyka]: Przenośniki',
    'panorama_https://panoramafirm.pl/przeprowadzki': 'PANORAMA [Usługi dla każdego]: Przeprowadzki',
    'panorama_https://panoramafirm.pl/przewody_kable_i_światłowody': 'PANORAMA [Przemysł i energetyka]: Przewody, kable i światłowody',
    'panorama_https://panoramafirm.pl/przyczepy_samochodowe': 'PANORAMA [Budownictwo]: Przyczepy samochodowe',
    'panorama_https://panoramafirm.pl/puby': 'PANORAMA [Rozrywka i rekreacja]: Puby',
    'panorama_https://panoramafirm.pl/puch_i_pierze': 'PANORAMA [Odzież i tekstylia]: Puch i pierze',
    'panorama_https://panoramafirm.pl/pędzle_i_szczotki': 'PANORAMA [Przemysł i energetyka]: Pędzle i szczotki',
    'panorama_https://panoramafirm.pl/radcy_prawni': 'PANORAMA [Usługi dla każdego]: Radcy prawni',
    'panorama_https://panoramafirm.pl/rajstopy_pończochy_i_skarpety': 'PANORAMA [Odzież i tekstylia]: Rajstopy, pończochy i skarpety',
    'panorama_https://panoramafirm.pl/ramy_i_oprawy_obrazów': 'PANORAMA [Rozrywka i rekreacja]: Ramy i oprawy obrazów',
    'panorama_https://panoramafirm.pl/recykling': 'PANORAMA [Przemysł i energetyka]: Recykling',
    'panorama_https://panoramafirm.pl/regeneracja_części_samochodowych': 'PANORAMA [Budownictwo]: Regeneracja części samochodowych',
    'panorama_https://panoramafirm.pl/reklama.html': 'PANORAMA [Zdrowie i uroda]: Reklamuj się u nas',
    'panorama_https://panoramafirm.pl/renowacja_mebli': 'PANORAMA [Budownictwo]: Renowacja mebli',
    'panorama_https://panoramafirm.pl/renowacje_i_remonty': 'PANORAMA [Budownictwo]: Renowacje i remonty',
    'panorama_https://panoramafirm.pl/restauracje': 'PANORAMA [Rozrywka i rekreacja]: Restauracje',
    'panorama_https://panoramafirm.pl/rodzina_500_plus': 'PANORAMA [Instytucje, urzędy]: Rodzina 500 Plus',
    'panorama_https://panoramafirm.pl/rowery': 'PANORAMA [Rozrywka i rekreacja]: Rowery',
    'panorama_https://panoramafirm.pl/rury': 'PANORAMA [Przemysł i energetyka]: Rury',
    'panorama_https://panoramafirm.pl/rusztowania_i_szalunki': 'PANORAMA [Budownictwo]: Rusztowania i szalunki',
    'panorama_https://panoramafirm.pl/rzecznicy_patentowi': 'PANORAMA [Instytucje, urzędy]: Rzecznicy patentowi',
    'panorama_https://panoramafirm.pl/rzeczoznawcy': 'PANORAMA [Usługi dla każdego]: Rzeczoznawcy',
    'panorama_https://panoramafirm.pl/ręczniki_koce_i_pościel': 'PANORAMA [Odzież i tekstylia]: Ręczniki, koce i pościel',
    'panorama_https://panoramafirm.pl/rękodzieło_artystyczne': 'PANORAMA [Rozrywka i rekreacja]: Rękodzieło artystyczne',
    'panorama_https://panoramafirm.pl/sale_weselne_i_organizacja_wesel': 'PANORAMA [Rozrywka i rekreacja]: Sale weselne i organizacja wesel',
    'panorama_https://panoramafirm.pl/sale_zabaw': 'PANORAMA [Rozrywka i rekreacja]: Sale zabaw',
    'panorama_https://panoramafirm.pl/salony_bilardowe': 'PANORAMA [Rozrywka i rekreacja]: Salony bilardowe',
    'panorama_https://panoramafirm.pl/salony_spa_i_odnowa_biologiczna': 'PANORAMA [Usługi dla każdego]: Salony SPA i odnowa biologiczna',
    'panorama_https://panoramafirm.pl/samochodowe_agregaty_chłodnicze': 'PANORAMA [Budownictwo]: Samochodowe agregaty chłodnicze',
    'panorama_https://panoramafirm.pl/samochodowe_instalacje_gazowe': 'PANORAMA [Budownictwo]: Samochodowe instalacje gazowe',
    'panorama_https://panoramafirm.pl/samochody_używane': 'PANORAMA [Budownictwo]: Samochody używane',
    'panorama_https://panoramafirm.pl/schody': 'PANORAMA [Budownictwo]: Schody',
    'panorama_https://panoramafirm.pl/schroniska_dla_zwierząt': 'PANORAMA [Rozrywka i rekreacja]: Schroniska dla zwierząt',
    'panorama_https://panoramafirm.pl/sejfy_i_kasy_pancerne': 'PANORAMA [Usługi dla każdego]: Sejfy i kasy pancerne',
    'panorama_https://panoramafirm.pl/serwis_i_części_do_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Serwis i części do maszyn budowlanych',
    'panorama_https://panoramafirm.pl/serwis_i_instalacja_klimatyzacji': 'PANORAMA [Usługi dla każdego]: Serwis i instalacja klimatyzacji',
    'panorama_https://panoramafirm.pl/serwis_komputerów': 'PANORAMA [Telekomunikacja, internet, technologie]: Serwis komputerów',
    'panorama_https://panoramafirm.pl/serwis_samochodów_ciężarowych_i_dostawczych': 'PANORAMA [Budownictwo]: Serwis samochodów ciężarowych i dostawczych',
    'panorama_https://panoramafirm.pl/serwis_urządzeń_chłodniczych': 'PANORAMA [Przemysł i energetyka]: Serwis urządzeń chłodniczych',
    'panorama_https://panoramafirm.pl/serwis_urządzeń_elektrycznych': 'PANORAMA [Przemysł i energetyka]: Serwis urządzeń elektrycznych',
    'panorama_https://panoramafirm.pl/serwisy_informacyjne': 'PANORAMA [Telekomunikacja, internet, technologie]: Serwisy informacyjne',
    'panorama_https://panoramafirm.pl/sex_shopy': 'PANORAMA [Usługi dla każdego]: Sex shopy',
    'panorama_https://panoramafirm.pl/sieci_komputerowe_i_integracja_systemów': 'PANORAMA [Telekomunikacja, internet, technologie]: Sieci komputerowe i integracja systemów',
    'panorama_https://panoramafirm.pl/silikon': 'PANORAMA [Przemysł i energetyka]: Silikon',
    'panorama_https://panoramafirm.pl/silniki_i_prądnice': 'PANORAMA [Przemysł i energetyka]: Silniki i prądnice',
    'panorama_https://panoramafirm.pl/siłownie_i_fitness': 'PANORAMA [Usługi dla każdego]: Siłownie i fitness',
    'panorama_https://panoramafirm.pl/siłowniki_i_automatyczne_napędy_do_bram': 'PANORAMA [Budownictwo]: Siłowniki i automatyczne napędy do bram',
    'panorama_https://panoramafirm.pl/sklepy_obuwnicze': 'PANORAMA [Odzież i tekstylia]: Sklepy obuwnicze',
    'panorama_https://panoramafirm.pl/sklepy_odzieżowe': 'PANORAMA [Odzież i tekstylia]: Sklepy odzieżowe',
    'panorama_https://panoramafirm.pl/sklepy_wielobranżowe': 'PANORAMA [Usługi dla każdego]: Sklepy wielobranżowe',
    'panorama_https://panoramafirm.pl/sklepy_z_częściami_elektronicznymi': 'PANORAMA [Przemysł i energetyka]: Sklepy z częściami elektronicznymi',
    'panorama_https://panoramafirm.pl/sklepy_z_zabawkami': 'PANORAMA [Rozrywka i rekreacja]: Sklepy z zabawkami',
    'panorama_https://panoramafirm.pl/skrzynie_biegów': 'PANORAMA [Budownictwo]: Skrzynie biegów',
    'panorama_https://panoramafirm.pl/skóry_naturalne_i_sztuczne': 'PANORAMA [Odzież i tekstylia]: Skóry naturalne i sztuczne',
    'panorama_https://panoramafirm.pl/solaria': 'PANORAMA [Usługi dla każdego]: Solaria',
    'panorama_https://panoramafirm.pl/sołectwa': 'PANORAMA [Instytucje, urzędy]: Sołectwa',
    'panorama_https://panoramafirm.pl/specjalne_strefy_ekonomiczne': 'PANORAMA [Instytucje, urzędy]: Specjalne strefy ekonomiczne',
    'panorama_https://panoramafirm.pl/spedycja': 'PANORAMA [Budownictwo]: Spedycja',
    'panorama_https://panoramafirm.pl/spedycja_międzynarodowa': 'PANORAMA [Budownictwo]: Spedycja międzynarodowa',
    'panorama_https://panoramafirm.pl/sprzedaż_i_rezerwacja_biletów': 'PANORAMA [Turystyka]: Sprzedaż i rezerwacja biletów',
    'panorama_https://panoramafirm.pl/sprzedaż_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Sprzedaż maszyn budowlanych',
    'panorama_https://panoramafirm.pl/sprzedaż_samochodów_ciężarowych_i_dostawczych': 'PANORAMA [Budownictwo]: Sprzedaż samochodów ciężarowych i dostawczych',
    'panorama_https://panoramafirm.pl/sprzedaż_wysyłkowa': 'PANORAMA [Usługi dla każdego]: Sprzedaż wysyłkowa',
    'panorama_https://panoramafirm.pl/sprzątanie_terenu': 'PANORAMA [Budownictwo]: Sprzątanie terenu',
    'panorama_https://panoramafirm.pl/sprzątanie_wnętrz_i_mycie_okien': 'PANORAMA [Usługi dla każdego]: Sprzątanie wnętrz i mycie okien',
    'panorama_https://panoramafirm.pl/sprzęt_do_malowania_i_tapetowania': 'PANORAMA [Budownictwo]: Sprzęt do malowania i tapetowania',
    'panorama_https://panoramafirm.pl/sprzęt_do_produkcji_opakowań': 'PANORAMA [Przemysł i energetyka]: Sprzęt do produkcji opakowań',
    'panorama_https://panoramafirm.pl/sprzęt_do_utylizacji_odpadów': 'PANORAMA [Przemysł i energetyka]: Sprzęt do utylizacji odpadów',
    'panorama_https://panoramafirm.pl/sprzęt_fotograficzny': 'PANORAMA [Usługi dla każdego]: Sprzęt fotograficzny',
    'panorama_https://panoramafirm.pl/sprzęt_i_centrale_telefoniczne': 'PANORAMA [Telekomunikacja, internet, technologie]: Sprzęt i centrale telefoniczne',
    'panorama_https://panoramafirm.pl/sprzęt_i_materiały_hydrauliczne': 'PANORAMA [Przemysł i energetyka]: Sprzęt i materiały hydrauliczne',
    'panorama_https://panoramafirm.pl/sprzęt_i_wyposażenie_banków': 'PANORAMA [Finanse i ubezpieczenia]: Sprzęt i wyposażenie banków',
    'panorama_https://panoramafirm.pl/sprzęt_i_wyposażenie_kręgielni': 'PANORAMA [Rozrywka i rekreacja]: Sprzęt i wyposażenie kręgielni',
    'panorama_https://panoramafirm.pl/sprzęt_i_wyposażenie_weterynaryjne': 'PANORAMA [Rozrywka i rekreacja]: Sprzęt i wyposażenie weterynaryjne',
    'panorama_https://panoramafirm.pl/sprzęt_i_zabezpieczenia_przeciwpożarowe': 'PANORAMA [Przemysł i energetyka]: Sprzęt i zabezpieczenia przeciwpożarowe',
    'panorama_https://panoramafirm.pl/sprzęt_lotniczy': 'PANORAMA [Przemysł i energetyka]: Sprzęt lotniczy',
    'panorama_https://panoramafirm.pl/sprzęt_radiokomunikacyjny': 'PANORAMA [Telekomunikacja, internet, technologie]: Sprzęt radiokomunikacyjny',
    'panorama_https://panoramafirm.pl/sprzęt_sportowy_i_turystyczny': 'PANORAMA [Rozrywka i rekreacja]: Sprzęt sportowy i turystyczny',
    'panorama_https://panoramafirm.pl/sprzęt_torowy_i_kolejowy': 'PANORAMA [Przemysł i energetyka]: Sprzęt torowy i kolejowy',
    'panorama_https://panoramafirm.pl/spółdzielnie_i_administracje_mieszkaniowe': 'PANORAMA [Instytucje, urzędy]: Spółdzielnie i administracje mieszkaniowe',
    'panorama_https://panoramafirm.pl/stacje_diagnostyczne_i_przeglądy_techniczne': 'PANORAMA [Budownictwo]: Stacje diagnostyczne i przeglądy techniczne',
    'panorama_https://panoramafirm.pl/stacje_obsługi_i_warsztaty_samochodowe': 'PANORAMA [Budownictwo]: Stacje obsługi i warsztaty samochodowe',
    'panorama_https://panoramafirm.pl/stacje_paliw': 'PANORAMA [Przemysł i energetyka]: Stacje paliw',
    'panorama_https://panoramafirm.pl/stacje_radiowe_i_telewizyjne': 'PANORAMA [Telekomunikacja, internet, technologie]: Stacje radiowe i telewizyjne',
    'panorama_https://panoramafirm.pl/stacje_sanitarno_epidemiologiczne': 'PANORAMA [Instytucje, urzędy]: Stacje sanitarno-epidemiologiczne',
    'panorama_https://panoramafirm.pl/stadiony_sportowe': 'PANORAMA [Rozrywka i rekreacja]: Stadiony sportowe',
    'panorama_https://panoramafirm.pl/stal_i_wyroby_stalowe': 'PANORAMA [Przemysł i energetyka]: Stal i wyroby stalowe',
    'panorama_https://panoramafirm.pl/starostwa_powiatowe': 'PANORAMA [Instytucje, urzędy]: Starostwa powiatowe',
    'panorama_https://panoramafirm.pl/stolarze': 'PANORAMA [Budownictwo]: Stolarze',
    'panorama_https://panoramafirm.pl/stowarzyszenia_kluby_i_związki': 'PANORAMA [Instytucje, urzędy]: Stowarzyszenia, kluby i związki',
    'panorama_https://panoramafirm.pl/straż_miejska': 'PANORAMA [Instytucje, urzędy]: Straż miejska',
    'panorama_https://panoramafirm.pl/straż_pożarna': 'PANORAMA [Instytucje, urzędy]: Straż pożarna',
    'panorama_https://panoramafirm.pl/studnie': 'PANORAMA [Przemysł i energetyka]: Studnie',
    'panorama_https://panoramafirm.pl/styliści_wizażyści_i_projektanci_mody': 'PANORAMA [Usługi dla każdego]: Styliści, wizażyści i projektanci mody',
    'panorama_https://panoramafirm.pl/styropian': 'PANORAMA [Budownictwo]: Styropian',
    'panorama_https://panoramafirm.pl/sufity_podwieszane': 'PANORAMA [Budownictwo]: Sufity podwieszane',
    'panorama_https://panoramafirm.pl/suknie_ślubne_i_komunijne': 'PANORAMA [Odzież i tekstylia]: Suknie ślubne i komunijne',
    'panorama_https://panoramafirm.pl/supermarkety_i_hipermarkety': 'PANORAMA [Usługi dla każdego]: Supermarkety i hipermarkety',
    'panorama_https://panoramafirm.pl/surowce_mineralne': 'PANORAMA [Przemysł i energetyka]: Surowce mineralne',
    'panorama_https://panoramafirm.pl/suwnice': 'PANORAMA [Przemysł i energetyka]: Suwnice',
    'panorama_https://panoramafirm.pl/syndycy_i_likwidatorzy': 'PANORAMA [Instytucje, urzędy]: Syndycy i likwidatorzy',
    'panorama_https://panoramafirm.pl/systemy_dźwiękowe_i_audio': 'PANORAMA [Rozrywka i rekreacja]: Systemy dźwiękowe i audio',
    'panorama_https://panoramafirm.pl/systemy_i_technologie_multimedialne': 'PANORAMA [Telekomunikacja, internet, technologie]: Systemy i technologie multimedialne',
    'panorama_https://panoramafirm.pl/systemy_i_usługi_telekomunikacyjne': 'PANORAMA [Usługi dla każdego]: Systemy i usługi telekomunikacyjne',
    'panorama_https://panoramafirm.pl/systemy_zabudowy_wnętrz': 'PANORAMA [Budownictwo]: Systemy zabudowy wnętrz',
    'panorama_https://panoramafirm.pl/systemy_zamocowań': 'PANORAMA [Przemysł i energetyka]: Systemy zamocowań',
    'panorama_https://panoramafirm.pl/szewc': 'PANORAMA [Usługi dla każdego]: Szewc',
    'panorama_https://panoramafirm.pl/szklarze': 'PANORAMA [Budownictwo]: Szklarze',
    'panorama_https://panoramafirm.pl/szkoły_tańca': 'PANORAMA [Rozrywka i rekreacja]: Szkoły tańca',
    'panorama_https://panoramafirm.pl/szkło_budowlane': 'PANORAMA [Przemysł i energetyka]: Szkło budowlane',
    'panorama_https://panoramafirm.pl/szkło_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Szkło przemysłowe',
    'panorama_https://panoramafirm.pl/sznury_liny_i_nici': 'PANORAMA [Przemysł i energetyka]: Sznury, liny i nici',
    'panorama_https://panoramafirm.pl/szyberdachy': 'PANORAMA [Budownictwo]: Szyberdachy',
    'panorama_https://panoramafirm.pl/szyby_samochodowe': 'PANORAMA [Budownictwo]: Szyby samochodowe',
    'panorama_https://panoramafirm.pl/sól_przemysłowa': 'PANORAMA [Przemysł i energetyka]: Sól przemysłowa',
    'panorama_https://panoramafirm.pl/sądy': 'PANORAMA [Instytucje, urzędy]: Sądy',
    'panorama_https://panoramafirm.pl/tablice_rejestracyjne': 'PANORAMA [Budownictwo]: Tablice rejestracyjne',
    'panorama_https://panoramafirm.pl/tabor_kolejowy': 'PANORAMA [Budownictwo]: Tabor kolejowy',
    'panorama_https://panoramafirm.pl/taksometry_tachometry_i_tachografy': 'PANORAMA [Budownictwo]: Taksometry, tachometry i tachografy',
    'panorama_https://panoramafirm.pl/tapety': 'PANORAMA [Budownictwo]: Tapety',
    'panorama_https://panoramafirm.pl/tapicerka_i_pokrowce_samochodowe': 'PANORAMA [Budownictwo]: Tapicerka i pokrowce samochodowe',
    'panorama_https://panoramafirm.pl/tartaki': 'PANORAMA [Przemysł i energetyka]: Tartaki',
    'panorama_https://panoramafirm.pl/tatuaże': 'PANORAMA [Usługi dla każdego]: Tatuaże',
    'panorama_https://panoramafirm.pl/taxi': 'PANORAMA [Usługi dla każdego]: Taxi',
    'panorama_https://panoramafirm.pl/teatry_i_filharmonie': 'PANORAMA [Rozrywka i rekreacja]: Teatry i filharmonie',
    'panorama_https://panoramafirm.pl/technika_liniowa': 'PANORAMA [Przemysł i energetyka]: Technika liniowa',
    'panorama_https://panoramafirm.pl/techniki_bezwykopowe': 'PANORAMA [Przemysł i energetyka]: Techniki bezwykopowe',
    'panorama_https://panoramafirm.pl/technologie_budowlane': 'PANORAMA [Budownictwo]: Technologie budowlane',
    'panorama_https://panoramafirm.pl/telefony_alarmowe': 'PANORAMA [Usługi dla każdego]: Telefony alarmowe',
    'panorama_https://panoramafirm.pl/telefony_komórkowe': 'PANORAMA [Usługi dla każdego]: Telefony komórkowe',
    'panorama_https://panoramafirm.pl/telefony_zaufania': 'PANORAMA [Usługi dla każdego]: Telefony zaufania',
    'panorama_https://panoramafirm.pl/telewizja_kablowa': 'PANORAMA [Usługi dla każdego]: Telewizja kablowa',
    'panorama_https://panoramafirm.pl/telewizja_przemysłowa': 'PANORAMA [Usługi dla każdego]: Telewizja przemysłowa',
    'panorama_https://panoramafirm.pl/telewizja_satelitarna': 'PANORAMA [Usługi dla każdego]: Telewizja satelitarna',
    'panorama_https://panoramafirm.pl/tkaniny_i_dzianiny': 'PANORAMA [Odzież i tekstylia]: Tkaniny i dzianiny',
    'panorama_https://panoramafirm.pl/toalety_przenośne': 'PANORAMA [Przemysł i energetyka]: Toalety przenośne',
    'panorama_https://panoramafirm.pl/torby_walizki_i_teczki': 'PANORAMA [Usługi dla każdego]: Torby, walizki i teczki',
    'panorama_https://panoramafirm.pl/transport_kolejowy': 'PANORAMA [Budownictwo]: Transport kolejowy',
    'panorama_https://panoramafirm.pl/transport_lotniczy': 'PANORAMA [Budownictwo]: Transport lotniczy',
    'panorama_https://panoramafirm.pl/transport_międzynarodowy': 'PANORAMA [Budownictwo]: Transport międzynarodowy',
    'panorama_https://panoramafirm.pl/transport_morski_i_śródlądowy': 'PANORAMA [Budownictwo]: Transport morski i śródlądowy',
    'panorama_https://panoramafirm.pl/transport_nadgabarytowy': 'PANORAMA [Budownictwo]: Transport nadgabarytowy',
    'panorama_https://panoramafirm.pl/transport_samochodowy': 'PANORAMA [Budownictwo]: Transport samochodowy',
    'panorama_https://panoramafirm.pl/transport_ładunków_niebezpiecznych': 'PANORAMA [Budownictwo]: Transport ładunków niebezpiecznych',
    'panorama_https://panoramafirm.pl/tworzywa_sztuczne': 'PANORAMA [Przemysł i energetyka]: Tworzywa sztuczne',
    'panorama_https://panoramafirm.pl/tłumacze': 'PANORAMA [Usługi dla każdego]: Tłumacze',
    'panorama_https://panoramafirm.pl/tłumacze_przysięgli': 'PANORAMA [Usługi dla każdego]: Tłumacze przysięgli',
    'panorama_https://panoramafirm.pl/tłumiki_i_układy_wydechowe': 'PANORAMA [Budownictwo]: Tłumiki i układy wydechowe',
    'panorama_https://panoramafirm.pl/ubezpieczenia': 'PANORAMA [Usługi dla każdego]: Ubezpieczenia',
    'panorama_https://panoramafirm.pl/ubezpieczenia_społeczne': 'PANORAMA [Finanse i ubezpieczenia]: Ubezpieczenia społeczne',
    'panorama_https://panoramafirm.pl/układanie_gresu_i_płytek_ceramicznych': 'PANORAMA [Usługi dla każdego]: Układanie gresu i płytek ceramicznych',
    'panorama_https://panoramafirm.pl/układanie_wykładzin_podłogowych': 'PANORAMA [Usługi dla każdego]: Układanie wykładzin podłogowych',
    'panorama_https://panoramafirm.pl/unia_europejska': 'PANORAMA [Instytucje, urzędy]: Unia Europejska',
    'panorama_https://panoramafirm.pl/urządzenia_do_produkcji_obuwia': 'PANORAMA [Przemysł i energetyka]: Urządzenia do produkcji obuwia',
    'panorama_https://panoramafirm.pl/urządzenia_elektroniczne': 'PANORAMA [Przemysł i energetyka]: Urządzenia elektroniczne',
    'panorama_https://panoramafirm.pl/urządzenia_elektryczne': 'PANORAMA [Przemysł i energetyka]: Urządzenia elektryczne',
    'panorama_https://panoramafirm.pl/urządzenia_gazowe': 'PANORAMA [Budownictwo]: Urządzenia gazowe',
    'panorama_https://panoramafirm.pl/urządzenia_grzewcze': 'PANORAMA [Przemysł i energetyka]: Urządzenia grzewcze',
    'panorama_https://panoramafirm.pl/urządzenia_i_maszyny_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Urządzenia i maszyny przemysłowe',
    'panorama_https://panoramafirm.pl/urządzenia_lakiernicze': 'PANORAMA [Przemysł i energetyka]: Urządzenia lakiernicze',
    'panorama_https://panoramafirm.pl/urządzenia_pneumatyczne': 'PANORAMA [Przemysł i energetyka]: Urządzenia pneumatyczne',
    'panorama_https://panoramafirm.pl/urządzenia_pomiarowe': 'PANORAMA [Przemysł i energetyka]: Urządzenia pomiarowe',
    'panorama_https://panoramafirm.pl/urządzenia_sanitarne': 'PANORAMA [Budownictwo]: Urządzenia sanitarne',
    'panorama_https://panoramafirm.pl/urządzenia_spawalnicze_i_zgrzewające': 'PANORAMA [Przemysł i energetyka]: Urządzenia spawalnicze i zgrzewające',
    'panorama_https://panoramafirm.pl/urzędy_celne': 'PANORAMA [Instytucje, urzędy]: Urzędy celne',
    'panorama_https://panoramafirm.pl/urzędy_centralne': 'PANORAMA [Instytucje, urzędy]: Urzędy centralne',
    'panorama_https://panoramafirm.pl/urzędy_marszałkowskie': 'PANORAMA [Instytucje, urzędy]: Urzędy marszałkowskie',
    'panorama_https://panoramafirm.pl/urzędy_miast_i_gmin': 'PANORAMA [Instytucje, urzędy]: Urzędy miast i gmin',
    'panorama_https://panoramafirm.pl/urzędy_pracy': 'PANORAMA [Instytucje, urzędy]: Urzędy pracy',
    'panorama_https://panoramafirm.pl/urzędy_skarbowe': 'PANORAMA [Instytucje, urzędy]: Urzędy skarbowe',
    'panorama_https://panoramafirm.pl/urzędy_terenowe': 'PANORAMA [Instytucje, urzędy]: Urzędy terenowe',
    'panorama_https://panoramafirm.pl/urzędy_wojewódzkie': 'PANORAMA [Instytucje, urzędy]: Urzędy wojewódzkie',
    'panorama_https://panoramafirm.pl/usuwanie_i_neutralizacja_azbestu': 'PANORAMA [Budownictwo]: Usuwanie i neutralizacja azbestu',
    'panorama_https://panoramafirm.pl/uszczelki_i_uszczelnienia': 'PANORAMA [Przemysł i energetyka]: Uszczelki i uszczelnienia',
    'panorama_https://panoramafirm.pl/usługi_fotograficzne': 'PANORAMA [Usługi dla każdego]: Usługi fotograficzne',
    'panorama_https://panoramafirm.pl/usługi_gazownicze': 'PANORAMA [Usługi dla każdego]: Usługi gazownicze',
    'panorama_https://panoramafirm.pl/usługi_i_projekty_górnicze': 'PANORAMA [Przemysł i energetyka]: Usługi i projekty górnicze',
    'panorama_https://panoramafirm.pl/usługi_kamieniarskie': 'PANORAMA [Usługi dla każdego]: Usługi kamieniarskie',
    'panorama_https://panoramafirm.pl/usługi_pogrzebowe': 'PANORAMA [Usługi dla każdego]: Usługi pogrzebowe',
    'panorama_https://panoramafirm.pl/usługi_posadzkarskie': 'PANORAMA [Budownictwo]: Usługi posadzkarskie',
    'panorama_https://panoramafirm.pl/usługi_saperskie': 'PANORAMA [Budownictwo]: Usługi saperskie',
    'panorama_https://panoramafirm.pl/usługi_spawania_i_zgrzewania': 'PANORAMA [Przemysł i energetyka]: Usługi spawania i zgrzewania',
    'panorama_https://panoramafirm.pl/usługi_tapicerskie': 'PANORAMA [Usługi dla każdego]: Usługi tapicerskie',
    'panorama_https://panoramafirm.pl/usługi_wodno_kanalizacyjne': 'PANORAMA [Budownictwo]: Usługi wodno-kanalizacyjne',
    'panorama_https://panoramafirm.pl/utylizacja_odpadów': 'PANORAMA [Przemysł i energetyka]: Utylizacja odpadów',
    'panorama_https://panoramafirm.pl/uzbrajanie_terenu': 'PANORAMA [Budownictwo]: Uzbrajanie terenu',
    'panorama_https://panoramafirm.pl/używane_części_samochodowe': 'PANORAMA [Budownictwo]: Używane części samochodowe',
    'panorama_https://panoramafirm.pl/wagi': 'PANORAMA [Przemysł i energetyka]: Wagi',
    'panorama_https://panoramafirm.pl/ważne_telefony': 'PANORAMA [Usługi dla każdego]: Ważne telefony',
    'panorama_https://panoramafirm.pl/wentylacja': 'PANORAMA [Budownictwo]: Wentylacja',
    'panorama_https://panoramafirm.pl/wełna_i_przędza': 'PANORAMA [Odzież i tekstylia]: Wełna i przędza',
    'panorama_https://panoramafirm.pl/wideofilmowanie': 'PANORAMA [Usługi dla każdego]: Wideofilmowanie',
    'panorama_https://panoramafirm.pl/windy_i_urządzenia_dźwigowe': 'PANORAMA [Budownictwo]: Windy i urządzenia dźwigowe',
    'panorama_https://panoramafirm.pl/windykacja_długów_i_należności': 'PANORAMA [Finanse i ubezpieczenia]: Windykacja długów i należności',
    'panorama_https://panoramafirm.pl/witraże': 'PANORAMA [Budownictwo]: Witraże',
    'panorama_https://panoramafirm.pl/więzienia_i_zakłady_penitencjarne': 'PANORAMA [Instytucje, urzędy]: Więzienia i zakłady penitencjarne',
    'panorama_https://panoramafirm.pl/wodociągi_i_kanalizacja': 'PANORAMA [Przemysł i energetyka]: Wodociągi i kanalizacja',
    'panorama_https://panoramafirm.pl/wulkanizacja_i_serwis_opon': 'PANORAMA [Budownictwo]: Wulkanizacja i serwis opon',
    'panorama_https://panoramafirm.pl/wyburzenia_i_rozbiórki': 'PANORAMA [Budownictwo]: Wyburzenia i rozbiórki',
    'panorama_https://panoramafirm.pl/wycena_nieruchomości': 'PANORAMA [Usługi dla każdego]: Wycena nieruchomości',
    'panorama_https://panoramafirm.pl/wycieraczki_i_maty': 'PANORAMA [Budownictwo]: Wycieraczki i maty',
    'panorama_https://panoramafirm.pl/wyciągi_i_koleje_linowe': 'PANORAMA [Przemysł i energetyka]: Wyciągi i koleje linowe',
    'panorama_https://panoramafirm.pl/wydobycie_i_sprzedaż_węgla': 'PANORAMA [Przemysł i energetyka]: Wydobycie i sprzedaż węgla',
    'panorama_https://panoramafirm.pl/wykopy_i_roboty_fundamentowe': 'PANORAMA [Budownictwo]: Wykopy i roboty fundamentowe',
    'panorama_https://panoramafirm.pl/wykończenia_wnętrz': 'PANORAMA [Budownictwo]: Wykończenia wnętrz',
    'panorama_https://panoramafirm.pl/wynajem_dźwigów_i_żurawi': 'PANORAMA [Budownictwo]: Wynajem dźwigów i żurawi',
    'panorama_https://panoramafirm.pl/wynajem_i_serwis_sprzętu_sportowego_i_turystycznego': 'PANORAMA [Rozrywka i rekreacja]: Wynajem i serwis sprzętu sportowego i turystycznego',
    'panorama_https://panoramafirm.pl/wynajem_magazynów': 'PANORAMA [Budownictwo]: Wynajem magazynów',
    'panorama_https://panoramafirm.pl/wynajem_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Wynajem maszyn budowlanych',
    'panorama_https://panoramafirm.pl/wynajem_maszyn_i_narzędzi': 'PANORAMA [Przemysł i energetyka]: Wynajem maszyn i narzędzi',
    'panorama_https://panoramafirm.pl/wynajem_samochodów_ciężarowych_i_dostawczych': 'PANORAMA [Budownictwo]: Wynajem samochodów ciężarowych i dostawczych',
    'panorama_https://panoramafirm.pl/wynajem_samochodów_i_zarządzanie_flotą': 'PANORAMA [Budownictwo]: Wynajem samochodów i zarządzanie flotą',
    'panorama_https://panoramafirm.pl/wyposażenie_dodatkowe_samochodów': 'PANORAMA [Budownictwo]: Wyposażenie dodatkowe samochodów',
    'panorama_https://panoramafirm.pl/wyposażenie_hoteli': 'PANORAMA [Turystyka]: Wyposażenie hoteli',
    'panorama_https://panoramafirm.pl/wyposażenie_kuchni': 'PANORAMA [Budownictwo]: Wyposażenie kuchni',
    'panorama_https://panoramafirm.pl/wyposażenie_magazynów': 'PANORAMA [Budownictwo]: Wyposażenie magazynów',
    'panorama_https://panoramafirm.pl/wyposażenie_obiektów_sportowych': 'PANORAMA [Rozrywka i rekreacja]: Wyposażenie obiektów sportowych',
    'panorama_https://panoramafirm.pl/wyposażenie_pralni_i_farbiarni': 'PANORAMA [Odzież i tekstylia]: Wyposażenie pralni i farbiarni',
    'panorama_https://panoramafirm.pl/wyposażenie_sklepów': 'PANORAMA [Budownictwo]: Wyposażenie sklepów',
    'panorama_https://panoramafirm.pl/wyposażenie_sprzęt_i_instalacje_chłodnicze': 'PANORAMA [Przemysł i energetyka]: Wyposażenie, sprzęt i instalacje chłodnicze',
    'panorama_https://panoramafirm.pl/wyposażenie_warsztatów_i_myjni_samochodowych': 'PANORAMA [Budownictwo]: Wyposażenie warsztatów i myjni samochodowych',
    'panorama_https://panoramafirm.pl/wyposażenie_łazienek': 'PANORAMA [Budownictwo]: Wyposażenie łazienek',
    'panorama_https://panoramafirm.pl/wypożyczalnie_filmów_wideo_i_dvd': 'PANORAMA [Usługi dla każdego]: Wypożyczalnie filmów wideo i DVD',
    'panorama_https://panoramafirm.pl/wypożyczalnie_strojów': 'PANORAMA [Usługi dla każdego]: Wypożyczalnie strojów',
    'panorama_https://panoramafirm.pl/wyroby_hutnicze': 'PANORAMA [Przemysł i energetyka]: Wyroby hutnicze',
    'panorama_https://panoramafirm.pl/wytwarzanie_energii_odnawialnej': 'PANORAMA [Przemysł i energetyka]: Wytwarzanie energii odnawialnej',
    'panorama_https://panoramafirm.pl/wywóz_śmieci_i_odpadów': 'PANORAMA [Usługi dla każdego]: Wywóz śmieci i odpadów',
    'panorama_https://panoramafirm.pl/wzornictwo_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Wzornictwo przemysłowe',
    'panorama_https://panoramafirm.pl/wózki_widłowe': 'PANORAMA [Przemysł i energetyka]: Wózki widłowe',
    'panorama_https://panoramafirm.pl/wędkarstwo': 'PANORAMA [Rozrywka i rekreacja]: Wędkarstwo',
    'panorama_https://panoramafirm.pl/węże_przemysłowe': 'PANORAMA [Przemysł i energetyka]: Węże przemysłowe',
    'panorama_https://panoramafirm.pl/zabawki_edukacyjne': 'PANORAMA [Dzieci]: Zabawki edukacyjne',
    'panorama_https://panoramafirm.pl/zabezpieczenia_antykorozyjne': 'PANORAMA [Przemysł i energetyka]: Zabezpieczenia antykorozyjne',
    'panorama_https://panoramafirm.pl/zabezpieczenia_antykorozyjne_samochodów': 'PANORAMA [Budownictwo]: Zabezpieczenia antykorozyjne samochodów',
    'panorama_https://panoramafirm.pl/zabudowy_nadwozi_samochodowych': 'PANORAMA [Budownictwo]: Zabudowy nadwozi samochodowych',
    'panorama_https://panoramafirm.pl/zakłady_sztukatorskie': 'PANORAMA [Budownictwo]: Zakłady sztukatorskie',
    'panorama_https://panoramafirm.pl/zamki_i_kłódki': 'PANORAMA [Budownictwo]: Zamki i kłódki',
    'panorama_https://panoramafirm.pl/zamki_i_zabezpieczenia_antywłamaniowe': 'PANORAMA [Usługi dla każdego]: Zamki i zabezpieczenia antywłamaniowe',
    'panorama_https://panoramafirm.pl/zapalniczki_i_zapałki': 'PANORAMA [Przemysł i energetyka]: Zapalniczki i zapałki',
    'panorama_https://panoramafirm.pl/zarządy_cmentarzy_i_cmentarze': 'PANORAMA [Instytucje, urzędy]: Zarządy cmentarzy i cmentarze',
    'panorama_https://panoramafirm.pl/zarządzanie_nieruchomościami': 'PANORAMA [Budownictwo]: Zarządzanie nieruchomościami',
    'panorama_https://panoramafirm.pl/zawiesia_linowe_łańcuchowe_i_pasowe': 'PANORAMA [Przemysł i energetyka]: Zawiesia linowe, łańcuchowe i pasowe',
    'panorama_https://panoramafirm.pl/zbiorniki_i_pojemniki': 'PANORAMA [Przemysł i energetyka]: Zbiorniki i pojemniki',
    'panorama_https://panoramafirm.pl/zegarmistrzowie': 'PANORAMA [Usługi dla każdego]: Zegarmistrzowie',
    'panorama_https://panoramafirm.pl/zespoły_muzyczne': 'PANORAMA [Rozrywka i rekreacja]: Zespoły muzyczne',
    'panorama_https://panoramafirm.pl/znakowanie_i_monitorowanie_samochodów': 'PANORAMA [Budownictwo]: Znakowanie i monitorowanie samochodów',
    'panorama_https://panoramafirm.pl/zwierzęta_domowe': 'PANORAMA [Rozrywka i rekreacja]: Zwierzęta domowe',
    'panorama_https://panoramafirm.pl/złom_i_surowce_wtórne': 'PANORAMA [Przemysł i energetyka]: Złom i surowce wtórne',
    'panorama_https://panoramafirm.pl/łańcuchy': 'PANORAMA [Przemysł i energetyka]: Łańcuchy',
    'panorama_https://panoramafirm.pl/łożyska': 'PANORAMA [Przemysł i energetyka]: Łożyska',
    'panorama_https://panoramafirm.pl/ślusarstwo_i_dorabianie_kluczy': 'PANORAMA [Usługi dla każdego]: Ślusarstwo i dorabianie kluczy',
    'panorama_https://panoramafirm.pl/ślusarze': 'PANORAMA [Usługi dla każdego]: Ślusarze',
    'panorama_https://panoramafirm.pl/świadectwa_energetyczne': 'PANORAMA [Budownictwo]: Świadectwa energetyczne',
    'panorama_https://panoramafirm.pl/świece_i_znicze': 'PANORAMA [Przemysł i energetyka]: Świece i znicze',
    'panorama_https://panoramafirm.pl/świetlice_środowiskowe': 'PANORAMA [Rozrywka i rekreacja]: Świetlice środowiskowe',
    'panorama_https://panoramafirm.pl/żegluga': 'PANORAMA [Rozrywka i rekreacja]: Żegluga',
    'panorama_https://panoramafirm.pl/żłobki_prywatne': 'PANORAMA [Dzieci]: Żłobki prywatne',
    'panorama_https://panoramafirm.pl/żłobki_publiczne': 'PANORAMA [Dzieci]: Żłobki publiczne',
}



def setup_driver():
    """Nastavení Chrome driveru"""
    chrome_options = Options()
    
    # Docker/Server nastavení - MAXIMÁLNÍ OPTIMALIZACE PRO NÍZKOU PAMĚŤ (512MB)
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')
    
    # Maximální snížení paměti
    chrome_options.add_argument('--disable-dev-tools')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--metrics-recording-only')
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--disable-permissions-api')
    chrome_options.add_argument('--single-process')
    
    # NOVÉ - ještě více úspor paměti
    chrome_options.add_argument('--disable-images')  # Nenačítat obrázky
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disk-cache-size=1')
    chrome_options.add_argument('--media-cache-size=1')
    chrome_options.add_argument('--aggressive-cache-discard')
    chrome_options.add_argument('--disable-application-cache')
    
    # CRITICAL pro 512MB RAM - limit Chrome paměti
    chrome_options.add_argument('--max-old-space-size=256')  # Max 256MB pro V8
    chrome_options.add_argument('--disable-backing-store-limit')
    chrome_options.add_argument('--disable-javascript-harmony-shipping')
    chrome_options.add_argument('--js-flags=--max-old-space-size=256')
    
    # Anti-detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Menší okno = méně paměti
    chrome_options.add_argument('--window-size=800,600')
    chrome_options.add_argument('--start-maximized')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # KRITICKÉ: Timeout pro načítání stránek (proti zamrznutí)
    driver.set_page_load_timeout(30)  # Max 30 sekund na načtení stránky
    
    return driver

def extract_company_names(driver, category_url, max_companies, source='aleo'):
    """Extrahuje názvy firem z aleo.com nebo panoramafirm.pl
    
    Returns:
        - ALEO: list of strings (názvy firem)
        - PANORAMA: tuple (list of dicts {'name': str, 'website': str, 'email': str}, driver)
    """
    try:
        # Načíst stránku s timeout ochranou
        try:
            driver.get(category_url)
            logger.info("Stránka načtena úspěšně")
        except TimeoutException:
            logger.warning("Timeout při načítání - pokračuji s částečně načtenou stránkou")
        time.sleep(5)
        
        all_data = []
        seen_names = set()
        
        if source == 'aleo':
            # ALEO.com - pouze názvy
            scroll_attempts = max_companies // 25 + 2
            
            for i in range(scroll_attempts):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                companies = driver.find_elements(By.CLASS_NAME, "catalog-row-first-line__company-name")
                for company in companies:
                    name = company.text.strip()
                    if name and name not in seen_names:
                        all_data.append(name)
                        seen_names.add(name)
                
                scraping_status['message'] = f'📂 Načteno {len(all_data)} firem... (scroll {i+1}/{scroll_attempts})'
                
                if len(all_data) >= max_companies:
                    break
            
            return all_data[:max_companies]
            
        else:  # panorama
            # KROK 1: Scrollovat a načíst seznam firem s jejich detail URL
            company_details = []
            seen_names = set()
            
            # NOVÁ STRATEGIE: Načítat stránky přímo přes URL parametr ?page=X
            # Panorama Firm má 20-25 firem na stránku
            pages_needed = (max_companies // 20) + 2
            logger.info(f"Budu načítat {pages_needed} stránek pro získání {max_companies} firem")
            
            for page_num in range(1, pages_needed + 1):
                # Sestavit URL pro konkrétní stránku
                # Panorama Firm používá: /kategorie/firmy,5.html
                if page_num == 1:
                    page_url = category_url
                else:
                    # Odebrat .html z konce a přidat ,X.html
                    if category_url.endswith('.html'):
                        base_url = category_url[:-5]  # Odebrat .html
                        page_url = f"{base_url}/firmy,{page_num}.html"
                    else:
                        page_url = f"{category_url}/firmy,{page_num}.html"
                
                logger.info(f"Načítám stránku {page_num}/{pages_needed}: {page_url}")
                
                try:
                    driver.get(page_url)
                    logger.info(f"  Stránka {page_num} načtena")
                    time.sleep(2)
                except TimeoutException:
                    logger.warning(f"Timeout při načítání stránky {page_num} - pokračuji s částečně načtenou stránkou")
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Chyba při načítání stránky {page_num}: {e}")
                    break
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # NOVÁ STRATEGIE: Použít H2 přímo a najít odkaz v nadřazeném elementu
                h2_elements = soup.find_all('h2', class_=lambda c: c and 'text-h1' in c if c else False)
                
                companies_on_page = 0
                for h2 in h2_elements:
                    name = h2.get_text(strip=True)
                    
                    # Filtrovat nerelevantní názvy
                    if not name or name in seen_names or name.startswith('Wyniki') or name.startswith('Jakie') or len(name) < 3:
                        continue
                    
                    # Najít odkaz na detail firmy - NOVÁ LOGIKA
                    # Panorama používá: /miasto,okres,ulica,cislo/nazev-firmy
                    detail_link = None
                    parent = h2.parent
                    
                    for level in range(10):
                        if parent:
                            # Hledat PRVNÍ link, který není kategorie
                            links = parent.find_all('a', href=True)
                            for link in links:
                                href = link.get('href')
                                # Skip kategorie a jiné interní linky
                                if (href and 
                                    href.startswith('/') and 
                                    ',' in href and  # Obsahuje čárku (město,okres,...)
                                    not href.startswith('/kategoria') and
                                    not href.startswith('/branze')):
                                    detail_link = f"https://panoramafirm.pl{href}"
                                    break
                            
                            if detail_link:
                                break
                            parent = parent.parent
                        else:
                            break
                    
                    if detail_link and name not in seen_names:
                        company_details.append({'name': name, 'url': detail_link})
                        seen_names.add(name)
                        companies_on_page += 1
                    elif not detail_link:
                        logger.warning(f"Nenašel jsem link pro firmu: {name[:50]}")
                
                logger.info(f"  Stránka {page_num}: Našel jsem {companies_on_page} nových firem (celkem {len(company_details)})")
                scraping_status['message'] = f'📂 Načteno {len(company_details)} firem... (stránka {page_num}/{pages_needed})'
                
                # RESTART CHROME PO KAŽDÉ STRÁNCE! (512MB RAM CRITICAL)
                if page_num < pages_needed:
                    logger.info(f"⚠️ Restartuji Chrome po stránce {page_num} (uvolnění RAM)")
                    try:
                        driver.quit()
                    except:
                        pass
                    gc.collect()
                    time.sleep(2)
                    driver = setup_driver()
                    logger.info(f"✅ Chrome restartován")
                
                # Pokud na stránce nejsou žádné firmy, asi jsme na konci
                if companies_on_page == 0:
                    logger.info(f"  Stránka {page_num} neobsahuje firmy - končím")
                    break
                
                if len(company_details) >= max_companies:
                    break
            
            logger.info(f"Fáze 1 dokončena: Našel jsem {len(company_details)} firem")
            logger.info(f"Zahajuji Fáze 2: Procházení detailů {min(len(company_details), max_companies)} firem")
            
            # KROK 2: Projít detail každé firmy - RESTARTOVAT CHROME PO KAŽDÉ FIRMĚ!
            # CRITICAL: 512MB RAM = musíme restartovat velmi často!
            
            for idx, company in enumerate(company_details[:max_companies], 1):
                scraping_status['message'] = f'🔍 Zpracovávám {idx}/{min(len(company_details), max_companies)}: {company["name"]}'
                logger.info(f"[{idx}/{min(len(company_details), max_companies)}] Otevírám detail: {company['name']}")
                
                website = None
                email = None
                
                try:
                    # Otevřít detail firmy s timeoutem
                    driver.set_page_load_timeout(3)  # Max 3 sekundy (kratší timeout)
                    try:
                        driver.get(company['url'])
                        logger.info(f"  Detail načten: {company['url'][:80]}")
                    except TimeoutException:
                        logger.warning(f"  Timeout při načítání detailu - pokračuji s částečně načtenou stránkou")
                    time.sleep(0.1)  # Velmi krátké čekání
                    
                    # Získat HTML a parsovat BeautifulSoup
                    html = driver.page_source
                    detail_soup = BeautifulSoup(html, 'html.parser')
                    
                    # Hledat web - všechny externí linky (IGNOROVAT mapy a social media)
                    for link in detail_soup.find_all('a', href=True):
                        href = link.get('href', '')
                        
                        # Najít web link - POUZE skutečný web firmy
                        if (href.startswith('http') and 
                            'panoramafirm.pl' not in href and
                            '/firma/' not in href and
                            'openstreetmap.org' not in href and
                            'maps.google' not in href and
                            'google.com/maps' not in href and
                            'facebook.com' not in href and
                            'linkedin.com' not in href and
                            'instagram.com' not in href and
                            'twitter.com' not in href and
                            'youtube.com' not in href):
                            website = href
                            logger.info(f"  Nalezen web: {website}")
                            break
                    
                    # Hledat email na celé stránce
                    all_emails = EMAIL_PATTERN.findall(html)
                    for potential_email in all_emails:
                        # Filtrovat nerelevantní emaily
                        if not any(skip in potential_email.lower() for skip in ['example', 'test@', 'noreply', '@panorama', '@google', '@facebook']):
                            email = potential_email
                            logger.info(f"  Nalezen email: {email}")
                            break
                    
                    del html  # Uvolnit paměť IHNED
                    del detail_soup
                    gc.collect()  # Garbage collection po každé firmě
                    
                    # Pokud web nenalezen, neukládat firmu
                    if not website:
                        logger.info(f"  ⚠️ Web nenalezen - přeskakuji firmu")
                        continue
                    
                    # Pokud email nenalezen, TAKÉ přeskočit
                    if not email:
                        logger.info(f"  ⚠️ Email nenalezen - přeskakuji firmu")
                        continue
                    
                except Exception as e:
                    logger.error(f"  Chyba při zpracování {company['name']}: {str(e)}")
                    scraping_status['message'] = f'⚠️ Chyba u {company["name"]}: {str(e)}'
                    time.sleep(1)
                    continue  # Přeskočit firmu při chybě
                
                # ULOŽIT pouze firmy S WEBEM a EMAILEM
                if website and email:
                    all_data.append({
                        'name': company['name'],
                        'website': website,
                        'email': email
                    })
                
                # RESTART CHROME PO KAŽDÉ FIRMĚ! (512MB RAM CRITICAL)
                if idx < min(len(company_details), max_companies):
                    logger.info(f"⚠️ Restartuji Chrome po firmě {idx}")
                    try:
                        driver.delete_all_cookies()
                        driver.quit()
                    except:
                        pass
                    gc.collect()
                    time.sleep(2)
                    driver = setup_driver()
                    logger.info(f"✅ Chrome restartován")
            
            return (all_data, driver)  # Vrátit data I nový driver
        
    except Exception as e:
        scraping_status['message'] = f'❌ Chyba: {str(e)}'
        return []

def google_search_website(driver, company_name):
    """Najde web firmy přes Google"""
    try:
        short_name = company_name.split('SPÓŁKA')[0].strip()
        short_name = short_name.split(' SP.')[0].strip()
        short_name = short_name.split(' S.A.')[0].strip()
        
        query = f"{short_name} Poland"
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=pl"
        
        driver.set_page_load_timeout(10)  # Max 10s na načtení
        try:
            driver.get(url)
            logger.info("Google search načten")
        except TimeoutException:
            logger.warning("Timeout při Google search - pokračuji s částečně načtenou stránkou")
        time.sleep(1)  # Zkráceno z 2s
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = soup.find_all('a')
        
        for link in links:
            href = link.get('href', '')
            
            if '/url?q=' in href:
                match = re.search(r'/url\?q=([^&]+)', href)
                if match:
                    found_url = requests.utils.unquote(match.group(1))
                    skip_domains = ['google.', 'facebook.', 'linkedin.', 'wikipedia.', 'aleo.com', 'youtube.']
                    if not any(skip in found_url.lower() for skip in skip_domains):
                        if found_url.startswith('http'):
                            return found_url
            
            elif href.startswith('http'):
                skip_domains = ['google.', 'facebook.', 'linkedin.', 'wikipedia.', 'aleo.com', 'youtube.']
                if not any(skip in href.lower() for skip in skip_domains):
                    return href
        
        return None
    except:
        return None

def google_search_email(driver, company_name):
    """Hledá email přes Google"""
    try:
        short_name = company_name.split('SPÓŁKA')[0].strip()
        short_name = short_name.split(' SP.')[0].strip()
        
        query = f"{short_name} email kontakt Poland"
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=pl"
        
        driver.set_page_load_timeout(10)  # Max 10s na načtení
        try:
            driver.get(url)
            logger.info("Google email search načten")
        except TimeoutException:
            logger.warning("Timeout při Google email search - pokračuji s částečně načtenou stránkou")
        time.sleep(1)  # Zkráceno z 2s
        
        emails = EMAIL_PATTERN.findall(driver.page_source)
        
        for email in emails:
            skip = ['google.', 'youtube.', 'example.', 'noreply', 'privacy', '@gstatic']
            if not any(skip in email.lower() for skip in skip):
                return email
        
        return None
    except:
        return None

def find_email_on_website(url):
    """Hledá email na webu firmy"""
    if not url:
        return None
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        pages = [url, f"{url}/kontakt", f"{url}/contact", f"{url}/kontakty", f"{url}/o-nas"]
        
        for page_url in pages:
            try:
                response = requests.get(page_url, headers=headers, timeout=5)  # Zkráceno z 10s
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()
                    emails = EMAIL_PATTERN.findall(text)
                    
                    for email in emails:
                        if not any(skip in email.lower() for skip in ['example.', 'test@', 'noreply', 'wix.com', 'domain.']):
                            return email
            except:
                continue
        
        return None
    except:
        return None

def scrape_category_thread(category_slug, category_title, max_companies):
    """Hlavní scraping funkce (běží v threadu)"""
    global scraping_status
    
    logger.info(f"=== ZAČÁTEK SCRAPOVÁNÍ ===")
    logger.info(f"Kategorie: {category_title}")
    logger.info(f"Slug: {category_slug}")
    logger.info(f"Max firem: {max_companies}")
    
    scraping_status['running'] = True
    scraping_status['progress'] = 0
    scraping_status['total'] = max_companies
    scraping_status['category'] = category_title
    scraping_status['results'] = []
    scraping_status['output_file'] = None
    scraping_status['excel_file'] = None
    scraping_status['message'] = '🚀 Spouštím scraping...'
    
    driver = None
    
    try:
        # Pokus o inicializaci Chrome
        try:
            logger.info("Inicializuji Chrome driver...")
            driver = setup_driver()
            logger.info("Chrome driver úspěšně inicializován")
            scraping_status['message'] = '✅ Chrome spuštěn'
        except Exception as e:
            logger.error(f"Chyba při spuštění Chrome: {str(e)}", exc_info=True)
            scraping_status['message'] = f'❌ Chyba při spuštění Chrome: {str(e)}'
            scraping_status['running'] = False
            return
        
        # Rozpoznat zdroj
        if category_slug.startswith('aleo_'):
            source = 'aleo'
            category_name = category_slug.replace('aleo_', '')
            category_url = f"https://aleo.com/pl/firmy/{category_name}"
            logger.info(f"Zdroj: ALEO, URL: {category_url}")
        elif category_slug.startswith('panorama_'):
            source = 'panorama'
            # Panorama má celý URL ve slugu
            category_url = category_slug.replace('panorama_', '')
            logger.info(f"Zdroj: PANORAMA, URL: {category_url}")
        else:
            logger.error(f"Neznámý zdroj kategorie: {category_slug}")
            scraping_status['message'] = '❌ Neznámý zdroj'
            scraping_status['running'] = False
            return
        
        # KROK 1: Otevřít stránku
        logger.info(f"Otevírám URL: {category_url}")
        scraping_status['message'] = f'🔓 Otevírám {source.upper()}...'
        
        try:
            driver.get(category_url)
            logger.info("Stránka načtena úspěšně")
        except TimeoutException:
            logger.warning("Timeout při načítání kategorie - pokračuji s částečně načtenou stránkou")
        time.sleep(5)  # Počkat na načtení stránky
        
        # KROK 2: Načíst firmy
        scraping_status['message'] = f'📂 Načítám firmy z kategorie...'
        logger.info(f"Volám extract_company_names() pro zdroj: {source}")
        
        result = extract_company_names(driver, category_url, max_companies, source)
        
        # Pro Panorama vrací tuple (data, driver), pro Aleo jen list
        if source == 'panorama':
            company_names, driver = result  # Rozbalit tuple a aktualizovat driver
        else:
            company_names = result
        
        logger.info(f"extract_company_names() vrátilo {len(company_names) if company_names else 0} firem")
        
        if not company_names:
            logger.warning("Žádné firmy nenalezeny!")
            scraping_status['message'] = '❌ Žádné firmy nenalezeny'
            scraping_status['running'] = False
            return
        
        scraping_status['total'] = len(company_names)
        scraping_status['message'] = f'✅ Nalezeno {len(company_names)} firem, zpracovávám...'
        logger.info(f"Celkem nalezeno {len(company_names)} firem")
        
        # KROK 3: Zpracovat firmy podle zdroje
        if source == 'panorama':
            logger.info("Zpracovávám firmy z Panorama (používám data přímo z extract_company_names)")
            # Panorama - data už jsou z detailů
            for idx, company_data in enumerate(company_names, 1):
                scraping_status['current_company'] = company_data['name']
                scraping_status['progress'] = len(scraping_status['results']) + 1
                logger.info(f"[{idx}/{len(company_names)}] {company_data['name']} - Web: {company_data['website']}, Email: {company_data['email']}")
                
                # Použít přímo data z Panorama
                result = {
                    'category': category_title,
                    'name': company_data['name'],
                    'website': company_data['website'] or '',
                    'email': company_data['email'] or ''
                }
                scraping_status['results'].append(result)
        else:
            # ALEO - hledat web a email pro každou firmu
            for idx, company_name in enumerate(company_names, 1):
                scraping_status['current_company'] = company_name
                scraping_status['progress'] = idx
                
                website = google_search_website(driver, company_name)
                
                email = None
                if website:
                    email = find_email_on_website(website)
                
                if not email:
                    email = google_search_email(driver, company_name)
                
                scraping_status['results'].append({
                    'category': category_title,
                    'name': company_name,
                    'website': website or '',
                    'email': email or ''
                })
                
                time.sleep(1)
        
        # Uložit CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Vyčistit název souboru - odebrat nepovolené znaky
        safe_filename = category_slug.replace('https://', '').replace('http://', '').replace('/', '_').replace('\\', '_').replace(':', '_')
        output_file = os.path.join(OUTPUT_DIR, f'{source}_{safe_filename}_{timestamp}.csv')
        
        os.makedirs('output', exist_ok=True)
        
        # Vyčistit data - odebrat čárky a problémové znaky z emailů
        clean_results = []
        for result in scraping_status['results']:
            clean_results.append({
                'Kategorie': result.get('category', ''),
                'Název firmy': result['name'],
                'Web': result['website'],
                'Email': result['email']
            })
        
        df = pd.DataFrame(clean_results)
        
        # Uložit CSV s středníkem jako oddělovač (Excel v ČR/PL standard)
        df.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';', quoting=1)
        
        # Uložit také Excel pro lepší přehlednost
        excel_file = output_file.replace('.csv', '.xlsx')
        
        # Vytvořit Excel s automatickou šířkou sloupců
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Firmy')
            
            # Získat worksheet a nastavit šířku sloupců
            worksheet = writer.sheets['Firmy']
            
            # Nastavit šířku podle obsahu
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                # Přidat trochu prostoru navíc
                adjusted_width = min(max_length + 2, 100)  # Max 100 znaků
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        scraping_status['output_file'] = output_file
        scraping_status['excel_file'] = excel_file
        scraping_status['message'] = f'✅ Hotovo! Nalezeno {len(scraping_status["results"])} firem'
        logger.info(f"=== KONEC SCRAPOVÁNÍ - ÚSPĚCH ===")
        
    except Exception as e:
        logger.error(f"=== CHYBA BĚHEM SCRAPOVÁNÍ ===", exc_info=True)
        scraping_status['message'] = f'❌ Chyba: {str(e)}'
    
    finally:
        logger.info("Zavírám Chrome driver...")
        if driver:
            try:
                driver.quit()
                logger.info("Chrome driver zavřen")
            except Exception as e:
                logger.error(f"Chyba při zavírání Chrome: {str(e)}")
        scraping_status['running'] = False
        logger.info(f"=== KONEC SCRAPOVÁNÍ - running=False ===")

@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES)

@app.route('/start', methods=['POST'])
def start_scraping():
    if scraping_status['running']:
        logger.warning("Scraping již běží - odmítám nový požadavek")
        return jsonify({'error': 'Scraping již běží'}), 400
    
    try:
        data = request.json
        category = data.get('category')
        max_companies = int(data.get('max_companies', 10))
        
        logger.info(f"Přijat požadavek na scraping: kategorie={category}, max_companies={max_companies}")
        
        if category not in CATEGORIES:
            logger.error(f"Neplatná kategorie: {category}")
            return jsonify({'error': 'Neplatná kategorie'}), 400
        
        category_title = CATEGORIES[category]
        
        logger.info(f"Spouštím scraping thread pro: {category_title}")
        # Spustit v threadu
        thread = threading.Thread(target=scrape_category_thread, args=(category, category_title, max_companies))
        thread.start()
        logger.info("Thread spuštěn")
        
        return jsonify({'status': 'started'})
    except Exception as e:
        logger.error(f"Chyba při startu scrapingu: {str(e)}", exc_info=True)
        return jsonify({'error': f'Chyba při spuštění: {str(e)}'}), 500

@app.route('/status')
def get_status():
    return jsonify(scraping_status)

@app.route('/health')
def health():
    """Health check endpoint pro Render.com"""
    return jsonify({'status': 'healthy', 'running': scraping_status.get('running', False)}), 200

@app.route('/download')
def download():
    if scraping_status['output_file'] and os.path.exists(scraping_status['output_file']):
        return send_file(scraping_status['output_file'], as_attachment=True)
    return "Soubor nenalezen", 404

@app.route('/download/excel')
def download_excel():
    if scraping_status.get('excel_file') and os.path.exists(scraping_status['excel_file']):
        return send_file(scraping_status['excel_file'], as_attachment=True)
    return "Soubor nenalezen", 404

if __name__ == '__main__':
    logger.info("=== APLIKACE STARTUJE ===")
    logger.info(f"Počet kategorií: {len(CATEGORIES)}")
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Spouštím Flask na portu {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

