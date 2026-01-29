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
    'message': '',
    'stopped': False
}

CATEGORIES = {
    'panorama_akcesoria_do_komputer%C3%B3w': 'PANORAMA [Biuro]: Akcesoria do komputerów',
    'panorama_artyku%C5%82y_biurowe': 'PANORAMA [Biuro]: Artykuły biurowe',
    'panorama_artyku%C5%82y_i_sprz%C4%99t_bhp': 'PANORAMA [Biuro]: Artykuły i sprzęt BHP',
    'panorama_artyku%C5%82y_papiernicze': 'PANORAMA [Biuro]: Artykuły papiernicze',
    'panorama_artyku%C5%82y_szkolne': 'PANORAMA [Biuro]: Artykuły szkolne',
    'panorama_audyty_oprogramowania_i_sprz%C4%99tu_komputerowego': 'PANORAMA [Biuro]: Audyty oprogramowania i sprzętu komputerowego',
    'panorama_cz%C4%99%C5%9Bci_komputerowe': 'PANORAMA [Biuro]: Części komputerowe',
    'panorama_drukarki_i_urz%C4%85dzenia_peryferyjne': 'PANORAMA [Biuro]: Drukarki i urządzenia peryferyjne',
    'panorama_etykiety_i_naklejki': 'PANORAMA [Biuro]: Etykiety i naklejki',
    'panorama_folie_i_foliowanie': 'PANORAMA [Biuro]: Folie i foliowanie',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_biurowych': 'PANORAMA [Biuro]: Hurtownie artykułów biurowych',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Biuro]: Hurtownie artykułów papierniczych',
    'panorama_hurtownie_dywan%C3%B3w_i_wyk%C5%82adzin': 'PANORAMA [Biuro]: Hurtownie dywanów i wykładzin',
    'panorama_ksero': 'PANORAMA [Biuro]: Ksero',
    'panorama_meble_biurowe': 'PANORAMA [Biuro]: Meble biurowe',
    'panorama_meble_metalowe': 'PANORAMA [Biuro]: Meble metalowe',
    'panorama_oprogramowanie_komputerowe': 'PANORAMA [Biuro]: Oprogramowanie komputerowe',
    'panorama_papier': 'PANORAMA [Biuro]: Papier',
    'panorama_piecz%C4%85tki_i_stemple': 'PANORAMA [Biuro]: Pieczątki i stemple',
    'panorama_pomiary_konsultacje_i_badania_bhp': 'PANORAMA [Biuro]: Pomiary, konsultacje i badania BHP',
    'panorama_producenci_artyku%C5%82%C3%B3w_biurowych': 'PANORAMA [Biuro]: Producenci artykułów biurowych',
    'panorama_produkcja_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Biuro]: Produkcja artykułów papierniczych',
    'panorama_serwis_komputer%C3%B3w': 'PANORAMA [Biuro]: Serwis komputerów',
    'panorama_serwis_kserokopiarek': 'PANORAMA [Biuro]: Serwis kserokopiarek',
    'panorama_sieci_komputerowe_i_integracja_system%C3%B3w': 'PANORAMA [Biuro]: Sieci komputerowe i integracja systemów',
    'panorama_sprzeda%C5%BC_komputer%C3%B3w': 'PANORAMA [Biuro]: Sprzedaż komputerów',
    'panorama_sprz%C4%99t_i_centrale_telefoniczne': 'PANORAMA [Biuro]: Sprzęt i centrale telefoniczne',
    'panorama_systemy_audiowizualne': 'PANORAMA [Biuro]: Systemy audiowizualne',
    'panorama_systemy_i_technologie_multimedialne': 'PANORAMA [Biuro]: Systemy i technologie multimedialne',
    'panorama_ta%C5%9Bmy_samoprzylepne': 'PANORAMA [Biuro]: Taśmy samoprzylepne',
    'panorama_wynajem_i_sprzeda%C5%BC_kserokopiarek': 'PANORAMA [Biuro]: Wynajem i sprzedaż kserokopiarek',
    'panorama_wyposa%C5%BCenie_biur': 'PANORAMA [Biuro]: Wyposażenie biur',
    'panorama_zaopatrzenie_biur': 'PANORAMA [Biuro]: Zaopatrzenie biur',
    'panorama_adwokaci': 'PANORAMA [Budownictwo]: Adwokaci',
    'panorama_agencje_ochrony': 'PANORAMA [Budownictwo]: Agencje ochrony',
    'panorama_agregaty_pr%C4%85dotw%C3%B3rcze': 'PANORAMA [Budownictwo]: Agregaty prądotwórcze',
    'panorama_agregaty_komory_i_meble_ch%C5%82odnicze': 'PANORAMA [Budownictwo]: Agregaty, komory i meble chłodnicze',
    'panorama_akcesoria_do_drzwi_i_okien': 'PANORAMA [Budownictwo]: Akcesoria do drzwi i okien',
    'panorama_akcesoria_meblowe': 'PANORAMA [Budownictwo]: Akcesoria meblowe',
    'panorama_alarmy_samochodowe': 'PANORAMA [Budownictwo]: Alarmy samochodowe',
    'panorama_amortyzatory_samochodowe': 'PANORAMA [Budownictwo]: Amortyzatory samochodowe',
    'panorama_architektura_krajobrazu': 'PANORAMA [Budownictwo]: Architektura krajobrazu',
    'panorama_armatura_hydrauliczna': 'PANORAMA [Budownictwo]: Armatura hydrauliczna',
    'panorama_armatura_przemys%C5%82owa': 'PANORAMA [Budownictwo]: Armatura przemysłowa',
    'panorama_artyku%C5%82y_elektrotechniczne': 'PANORAMA [Budownictwo]: Artykuły elektrotechniczne',
    'panorama_artyku%C5%82y_gumowe': 'PANORAMA [Budownictwo]: Artykuły gumowe',
    'panorama_artyku%C5%82y_i_sprz%C4%99t_ogrodniczy': 'PANORAMA [Budownictwo]: Artykuły i sprzęt ogrodniczy',
    'panorama_artyku%C5%82y_metalowe': 'PANORAMA [Budownictwo]: Artykuły metalowe',
    'panorama_automatyka': 'PANORAMA [Budownictwo]: Automatyka',
    'panorama_badania_i_us%C5%82ugi_archeologiczne': 'PANORAMA [Budownictwo]: Badania i usługi archeologiczne',
    'panorama_badania_i_uzdatnianie_wody': 'PANORAMA [Budownictwo]: Badania i uzdatnianie wody',
    'panorama_badania_nieniszcz%C4%85ce': 'PANORAMA [Budownictwo]: Badania nieniszczące',
    'panorama_beton': 'PANORAMA [Budownictwo]: Beton',
    'panorama_biura_architektoniczne': 'PANORAMA [Budownictwo]: Biura architektoniczne',
    'panorama_biura_projektowe': 'PANORAMA [Budownictwo]: Biura projektowe',
    'panorama_blacharstwo_i_lakiernictwo': 'PANORAMA [Budownictwo]: Blacharstwo i lakiernictwo',
    'panorama_bramy_i_ogrodzenia': 'PANORAMA [Budownictwo]: Bramy i ogrodzenia',
    'panorama_brukarstwo': 'PANORAMA [Budownictwo]: Brukarstwo',
    'panorama_budowa_i_eksploatacja_autostrad': 'PANORAMA [Budownictwo]: Budowa i eksploatacja autostrad',
    'panorama_budowa_i_eksploatacja_ruroci%C4%85g%C3%B3w': 'PANORAMA [Budownictwo]: Budowa i eksploatacja rurociągów',
    'panorama_budowa_i_sprz%C4%99t_drogowy': 'PANORAMA [Budownictwo]: Budowa i sprzęt drogowy',
    'panorama_budowa_i_wyko%C5%84czenia_pod_klucz': 'PANORAMA [Budownictwo]: Budowa i wykończenia pod klucz',
    'panorama_budowa_i_wynajem_hal_przemys%C5%82owych': 'PANORAMA [Budownictwo]: Budowa i wynajem hal przemysłowych',
    'panorama_budowa_i_wyposa%C5%BCenie_gara%C5%BCy': 'PANORAMA [Budownictwo]: Budowa i wyposażenie garaży',
    'panorama_budowa_i_wyposa%C5%BCenie_saun': 'PANORAMA [Budownictwo]: Budowa i wyposażenie saun',
    'panorama_budowa_i_wyposa%C5%BCenie_stacji_paliw': 'PANORAMA [Budownictwo]: Budowa i wyposażenie stacji paliw',
    'panorama_budowa_obiekt%C3%B3w_sportowych': 'PANORAMA [Budownictwo]: Budowa obiektów sportowych',
    'panorama_budowa_wyposa%C5%BCenie_i_remont_statk%C3%B3w': 'PANORAMA [Budownictwo]: Budowa, wyposażenie i remont statków',
    'panorama_budownictwo_kolejowe': 'PANORAMA [Budownictwo]: Budownictwo kolejowe',
    'panorama_budownictwo_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Budownictwo przemysłowe',
    'panorama_car_audio': 'PANORAMA [Budownictwo]: Car audio',
    'panorama_ceg%C5%82y': 'PANORAMA [Budownictwo]: Cegły',
    'panorama_cement_i_wapno': 'PANORAMA [Budownictwo]: Cement i wapno',
    'panorama_ceramika_budowlana': 'PANORAMA [Budownictwo]: Ceramika budowlana',
    'panorama_chemia_budowlana': 'PANORAMA [Budownictwo]: Chemia budowlana',
    'panorama_chemia_gospodarcza': 'PANORAMA [Budownictwo]: Chemia gospodarcza',
    'panorama_ci%C4%99cie_i_wiercenie': 'PANORAMA [Budownictwo]: Cięcie i wiercenie',
    'panorama_ci%C4%99cie_i_wiercenie_w_betonie': 'PANORAMA [Budownictwo]: Cięcie i wiercenie w betonie',
    'panorama_ci%C4%99cie_i_zaginanie': 'PANORAMA [Budownictwo]: Cięcie i zaginanie',
    'panorama_czyszczenie_i_renowacja_dywan%C3%B3w_i_wyk%C5%82adzin': 'PANORAMA [Budownictwo]: Czyszczenie i renowacja dywanów i wykładzin',
    'panorama_czyszczenie_strumieniowo_%C5%9Bcierne': 'PANORAMA [Budownictwo]: Czyszczenie strumieniowo-ścierne',
    'panorama_czyszcz%C4%85ce_urz%C4%85dzenia_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Czyszczące urządzenia przemysłowe',
    'panorama_dachy_i_rynny': 'PANORAMA [Budownictwo]: Dachy i rynny',
    'panorama_dachy_i_us%C5%82ugi_dekarskie': 'PANORAMA [Budownictwo]: Dachy i usługi dekarskie',
    'panorama_dealerzy_i_sprzeda%C5%BC_samochod%C3%B3w': 'PANORAMA [Budownictwo]: Dealerzy i sprzedaż samochodów',
    'panorama_dekoratorstwo_i_architektura_wn%C4%99trz': 'PANORAMA [Budownictwo]: Dekoratorstwo i architektura wnętrz',
    'panorama_deweloperzy': 'PANORAMA [Budownictwo]: Deweloperzy',
    'panorama_doradztwo_finansowe_i_kredytowe': 'PANORAMA [Budownictwo]: Doradztwo finansowe i kredytowe',
    'panorama_drabiny': 'PANORAMA [Budownictwo]: Drabiny',
    'panorama_drewno': 'PANORAMA [Budownictwo]: Drewno',
    'panorama_drewno_budowlane': 'PANORAMA [Budownictwo]: Drewno budowlane',
    'panorama_drewno_opa%C5%82owe': 'PANORAMA [Budownictwo]: Drewno opałowe',
    'panorama_drut_i_liny_stalowe': 'PANORAMA [Budownictwo]: Drut i liny stalowe',
    'panorama_drzwi': 'PANORAMA [Budownictwo]: Drzwi',
    'panorama_drzwi_antyw%C5%82amaniowe': 'PANORAMA [Budownictwo]: Drzwi antywłamaniowe',
    'panorama_dystrybucja_energii_elektrycznej': 'PANORAMA [Budownictwo]: Dystrybucja energii elektrycznej',
    'panorama_dywany_i_wyk%C5%82adziny': 'PANORAMA [Budownictwo]: Dywany i wykładziny',
    'panorama_d%C5%BAwigi_i_%C5%BCurawie': 'PANORAMA [Budownictwo]: Dźwigi i żurawie',
    'panorama_d%C5%BAwignice': 'PANORAMA [Budownictwo]: Dźwignice',
    'panorama_ekspertyzy_i_kosztorysy_budowlane': 'PANORAMA [Budownictwo]: Ekspertyzy i kosztorysy budowlane',
    'panorama_elektroinstalatorstwo': 'PANORAMA [Budownictwo]: Elektroinstalatorstwo',
    'panorama_elektromechanika': 'PANORAMA [Budownictwo]: Elektromechanika',
    'panorama_elektronarz%C4%99dzia': 'PANORAMA [Budownictwo]: Elektronarzędzia',
    'panorama_elektronika_samochodowa': 'PANORAMA [Budownictwo]: Elektronika samochodowa',
    'panorama_farby_i_lakiery': 'PANORAMA [Budownictwo]: Farby i lakiery',
    'panorama_filtry': 'PANORAMA [Budownictwo]: Filtry',
    'panorama_firmy_konsultingowe': 'PANORAMA [Budownictwo]: Firmy konsultingowe',
    'panorama_folie_i_foliowanie': 'PANORAMA [Budownictwo]: Folie i foliowanie',
    'panorama_formy_wtryskowe': 'PANORAMA [Budownictwo]: Formy wtryskowe',
    'panorama_galwanizacja': 'PANORAMA [Budownictwo]: Galwanizacja',
    'panorama_gaz_ziemny': 'PANORAMA [Budownictwo]: Gaz ziemny',
    'panorama_gazy_techniczne': 'PANORAMA [Budownictwo]: Gazy techniczne',
    'panorama_geodezja': 'PANORAMA [Budownictwo]: Geodezja',
    'panorama_geolodzy_i_geofizycy': 'PANORAMA [Budownictwo]: Geolodzy i geofizycy',
    'panorama_geosyntetyki': 'PANORAMA [Budownictwo]: Geosyntetyki',
    'panorama_gres_terakota_i_p%C5%82ytki_ceramiczne': 'PANORAMA [Budownictwo]: Gres, terakota i płytki ceramiczne',
    'panorama_haki_holownicze': 'PANORAMA [Budownictwo]: Haki holownicze',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_elektrotechnicznych': 'PANORAMA [Budownictwo]: Hurtownie artykułów elektrotechnicznych',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_metalowych': 'PANORAMA [Budownictwo]: Hurtownie artykułów metalowych',
    'panorama_hurtownie_chemii_gospodarczej': 'PANORAMA [Budownictwo]: Hurtownie chemii gospodarczej',
    'panorama_hurtownie_cz%C4%99%C5%9Bci_samochodowych': 'PANORAMA [Budownictwo]: Hurtownie części samochodowych',
    'panorama_hurtownie_dywan%C3%B3w_i_wyk%C5%82adzin': 'PANORAMA [Budownictwo]: Hurtownie dywanów i wykładzin',
    'panorama_hurtownie_farb_lakier%C3%B3w_i_emalii': 'PANORAMA [Budownictwo]: Hurtownie farb, lakierów i emalii',
    'panorama_hurtownie_gresu_terakoty_i_p%C5%82ytek_ceramicznych': 'PANORAMA [Budownictwo]: Hurtownie gresu, terakoty i płytek ceramicznych',
    'panorama_hurtownie_parkietu_i_paneli_pod%C5%82ogowych': 'PANORAMA [Budownictwo]: Hurtownie parkietu i paneli podłogowych',
    'panorama_hurtownie_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Budownictwo]: Hurtownie urządzeń elektrycznych',
    'panorama_hurtownie_urz%C4%85dze%C5%84_sanitarnych': 'PANORAMA [Budownictwo]: Hurtownie urządzeń sanitarnych',
    'panorama_hurtownie_%C5%BCaluzji_i_rolet': 'PANORAMA [Budownictwo]: Hurtownie żaluzji i rolet',
    'panorama_hydraulicy': 'PANORAMA [Budownictwo]: Hydraulicy',
    'panorama_hydraulika_si%C5%82owa': 'PANORAMA [Budownictwo]: Hydraulika siłowa',
    'panorama_hydrotechnika': 'PANORAMA [Budownictwo]: Hydrotechnika',
    'panorama_instalacja_i_serwis_ogrzewania': 'PANORAMA [Budownictwo]: Instalacja i serwis ogrzewania',
    'panorama_instalacja_system%C3%B3w_alarmowych': 'PANORAMA [Budownictwo]: Instalacja systemów alarmowych',
    'panorama_instalacje_energetyczne_i_ciep%C5%82ownicze': 'PANORAMA [Budownictwo]: Instalacje energetyczne i ciepłownicze',
    'panorama_instalacje_i_urz%C4%85dzenia_energetyczne': 'PANORAMA [Budownictwo]: Instalacje i urządzenia energetyczne',
    'panorama_instalacje_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Instalacje przemysłowe',
    'panorama_instalacje_system%C3%B3w_teletechnicznych': 'PANORAMA [Budownictwo]: Instalacje systemów teletechnicznych',
    'panorama_instalacje_termoizolacyjne': 'PANORAMA [Budownictwo]: Instalacje termoizolacyjne',
    'panorama_inwestycje_budowlane': 'PANORAMA [Budownictwo]: Inwestycje budowlane',
    'panorama_izolacja_akustyczna': 'PANORAMA [Budownictwo]: Izolacja akustyczna',
    'panorama_izolacja_termiczna': 'PANORAMA [Budownictwo]: Izolacja termiczna',
    'panorama_izolacja_wodochronna': 'PANORAMA [Budownictwo]: Izolacja wodochronna',
    'panorama_kamie%C5%84_i_kruszywa': 'PANORAMA [Budownictwo]: Kamień i kruszywa',
    'panorama_kleje_i_%C5%BCywice': 'PANORAMA [Budownictwo]: Kleje i żywice',
    'panorama_klimatyzacja': 'PANORAMA [Budownictwo]: Klimatyzacja',
    'panorama_klimatyzacja_samochodowa': 'PANORAMA [Budownictwo]: Klimatyzacja samochodowa',
    'panorama_kominiarze': 'PANORAMA [Budownictwo]: Kominiarze',
    'panorama_kominki': 'PANORAMA [Budownictwo]: Kominki',
    'panorama_kominy': 'PANORAMA [Budownictwo]: Kominy',
    'panorama_kompresory': 'PANORAMA [Budownictwo]: Kompresory',
    'panorama_konserwacja_zabytk%C3%B3w': 'PANORAMA [Budownictwo]: Konserwacja zabytków',
    'panorama_konstrukcje_aluminiowe': 'PANORAMA [Budownictwo]: Konstrukcje aluminiowe',
    'panorama_konstrukcje_stalowe': 'PANORAMA [Budownictwo]: Konstrukcje stalowe',
    'panorama_kontenery': 'PANORAMA [Budownictwo]: Kontenery',
    'panorama_korek_naturalny': 'PANORAMA [Budownictwo]: Korek naturalny',
    'panorama_kosmetyki_samochodowe': 'PANORAMA [Budownictwo]: Kosmetyki samochodowe',
    'panorama_kostka_brukowa': 'PANORAMA [Budownictwo]: Kostka brukowa',
    'panorama_ko%C5%82a_i_zestawy_jezdne': 'PANORAMA [Budownictwo]: Koła i zestawy jezdne',
    'panorama_kraty_pomostowe': 'PANORAMA [Budownictwo]: Kraty pomostowe',
    'panorama_kredyty_i_finansowanie': 'PANORAMA [Budownictwo]: Kredyty i finansowanie',
    'panorama_lakiery_samochodowe': 'PANORAMA [Budownictwo]: Lakiery samochodowe',
    'panorama_laminaty': 'PANORAMA [Budownictwo]: Laminaty',
    'panorama_liczniki_energii_elektrycznej': 'PANORAMA [Budownictwo]: Liczniki energii elektrycznej',
    'panorama_lustra': 'PANORAMA [Budownictwo]: Lustra',
    'panorama_magnesy_i_elektromagnesy': 'PANORAMA [Budownictwo]: Magnesy i elektromagnesy',
    'panorama_malowanie_i_lakierowanie_proszkowe': 'PANORAMA [Budownictwo]: Malowanie i lakierowanie proszkowe',
    'panorama_malowanie_i_lakierowanie_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Malowanie i lakierowanie przemysłowe',
    'panorama_malowanie_i_tapetowanie': 'PANORAMA [Budownictwo]: Malowanie i tapetowanie',
    'panorama_mapy_i_plany': 'PANORAMA [Budownictwo]: Mapy i plany',
    'panorama_marmur_granit_i_kamie%C5%84_naturalny': 'PANORAMA [Budownictwo]: Marmur, granit i kamień naturalny',
    'panorama_maszty_i_s%C5%82upy': 'PANORAMA [Budownictwo]: Maszty i słupy',
    'panorama_maszyny_do_obr%C3%B3bki_drewna': 'PANORAMA [Budownictwo]: Maszyny do obróbki drewna',
    'panorama_maszyny_do_obr%C3%B3bki_metali': 'PANORAMA [Budownictwo]: Maszyny do obróbki metali',
    'panorama_maszyny_pakuj%C4%85ce': 'PANORAMA [Budownictwo]: Maszyny pakujące',
    'panorama_materia%C5%82y_budowlane': 'PANORAMA [Budownictwo]: Materiały budowlane',
    'panorama_materia%C5%82y_do_spawania_i_zgrzewania': 'PANORAMA [Budownictwo]: Materiały do spawania i zgrzewania',
    'panorama_materia%C5%82y_do_wyka%C5%84czania_wn%C4%99trz': 'PANORAMA [Budownictwo]: Materiały do wykańczania wnętrz',
    'panorama_materia%C5%82y_drewnopochodne': 'PANORAMA [Budownictwo]: Materiały drewnopochodne',
    'panorama_materia%C5%82y_elektryczne': 'PANORAMA [Budownictwo]: Materiały elektryczne',
    'panorama_materia%C5%82y_elewacyjne': 'PANORAMA [Budownictwo]: Materiały elewacyjne',
    'panorama_materia%C5%82y_izolacyjne': 'PANORAMA [Budownictwo]: Materiały izolacyjne',
    'panorama_materia%C5%82y_ognioodporne': 'PANORAMA [Budownictwo]: Materiały ognioodporne',
    'panorama_materia%C5%82y_opa%C5%82owe': 'PANORAMA [Budownictwo]: Materiały opałowe',
    'panorama_materia%C5%82y_tapicerskie': 'PANORAMA [Budownictwo]: Materiały tapicerskie',
    'panorama_materia%C5%82y_%C5%9Bcierne_i_polerskie': 'PANORAMA [Budownictwo]: Materiały ścierne i polerskie',
    'panorama_meble': 'PANORAMA [Budownictwo]: Meble',
    'panorama_meble_biurowe': 'PANORAMA [Budownictwo]: Meble biurowe',
    'panorama_meble_kuchenne': 'PANORAMA [Budownictwo]: Meble kuchenne',
    'panorama_meble_metalowe': 'PANORAMA [Budownictwo]: Meble metalowe',
    'panorama_meble_na_zam%C3%B3wienie': 'PANORAMA [Budownictwo]: Meble na zamówienie',
    'panorama_meble_ogrodowe': 'PANORAMA [Budownictwo]: Meble ogrodowe',
    'panorama_mechanika_samochodowa': 'PANORAMA [Budownictwo]: Mechanika samochodowa',
    'panorama_metale_nie%C5%BCelazne_i_kolorowe': 'PANORAMA [Budownictwo]: Metale nieżelazne i kolorowe',
    'panorama_metale_%C5%BCelazne': 'PANORAMA [Budownictwo]: Metale żelazne',
    'panorama_metalizowanie_i_powlekanie_tworzyw': 'PANORAMA [Budownictwo]: Metalizowanie i powlekanie tworzyw',
    'panorama_metaloplastyka': 'PANORAMA [Budownictwo]: Metaloplastyka',
    'panorama_monta%C5%BC_i_produkcja_basen%C3%B3w_i_fontann': 'PANORAMA [Budownictwo]: Montaż i produkcja basenów i fontann',
    'panorama_monta%C5%BC_i_sprzeda%C5%BC_%C5%BCaluzji_i_rolet': 'PANORAMA [Budownictwo]: Montaż i sprzedaż żaluzji i rolet',
    'panorama_naczepy_samochodowe': 'PANORAMA [Budownictwo]: Naczepy samochodowe',
    'panorama_nadz%C3%B3r_budowlany': 'PANORAMA [Budownictwo]: Nadzór budowlany',
    'panorama_nape%C5%82nianie_butli_gazowych': 'PANORAMA [Budownictwo]: Napełnianie butli gazowych',
    'panorama_narz%C4%99dzia': 'PANORAMA [Budownictwo]: Narzędzia',
    'panorama_nieruchomo%C5%9Bci': 'PANORAMA [Budownictwo]: Nieruchomości',
    'panorama_obr%C3%B3bka_metali': 'PANORAMA [Budownictwo]: Obróbka metali',
    'panorama_obr%C3%B3bka_tworzyw_sztucznych': 'PANORAMA [Budownictwo]: Obróbka tworzyw sztucznych',
    'panorama_oczyszczanie_%C5%9Bciek%C3%B3w': 'PANORAMA [Budownictwo]: Oczyszczanie ścieków',
    'panorama_odkurzacze_centralne': 'PANORAMA [Budownictwo]: Odkurzacze centralne',
    'panorama_odlewnie': 'PANORAMA [Budownictwo]: Odlewnie',
    'panorama_odzie%C5%BC_robocza': 'PANORAMA [Budownictwo]: Odzież robocza',
    'panorama_ogrodnictwo': 'PANORAMA [Budownictwo]: Ogrodnictwo',
    'panorama_ogrzewanie_elektryczne': 'PANORAMA [Budownictwo]: Ogrzewanie elektryczne',
    'panorama_okleiny': 'PANORAMA [Budownictwo]: Okleiny',
    'panorama_oklejanie_samochod%C3%B3w': 'PANORAMA [Budownictwo]: Oklejanie samochodów',
    'panorama_okna': 'PANORAMA [Budownictwo]: Okna',
    'panorama_okna_dachowe': 'PANORAMA [Budownictwo]: Okna dachowe',
    'panorama_okna_drewniane': 'PANORAMA [Budownictwo]: Okna drewniane',
    'panorama_okucia': 'PANORAMA [Budownictwo]: Okucia',
    'panorama_olej_opa%C5%82owy': 'PANORAMA [Budownictwo]: Olej opałowy',
    'panorama_oleje_techniczne_i_smary': 'PANORAMA [Budownictwo]: Oleje techniczne i smary',
    'panorama_opakowania': 'PANORAMA [Budownictwo]: Opakowania',
    'panorama_opakowania_foliowe': 'PANORAMA [Budownictwo]: Opakowania foliowe',
    'panorama_opakowania_papierowe_i_tekturowe': 'PANORAMA [Budownictwo]: Opakowania papierowe i tekturowe',
    'panorama_opakowania_z_tworzyw_sztucznych': 'PANORAMA [Budownictwo]: Opakowania z tworzyw sztucznych',
    'panorama_osuszanie_budynk%C3%B3w': 'PANORAMA [Budownictwo]: Osuszanie budynków',
    'panorama_oznakowanie_i_sygnalizacja_dr%C3%B3g': 'PANORAMA [Budownictwo]: Oznakowanie i sygnalizacja dróg',
    'panorama_o%C5%9Bwietlenie': 'PANORAMA [Budownictwo]: Oświetlenie',
    'panorama_palety': 'PANORAMA [Budownictwo]: Palety',
    'panorama_paliwa': 'PANORAMA [Budownictwo]: Paliwa',
    'panorama_panele_i_pod%C5%82ogi': 'PANORAMA [Budownictwo]: Panele i podłogi',
    'panorama_parapety': 'PANORAMA [Budownictwo]: Parapety',
    'panorama_parkiet_i_panele_pod%C5%82ogowe': 'PANORAMA [Budownictwo]: Parkiet i panele podłogowe',
    'panorama_pasy_nap%C4%99dowe_i_transportuj%C4%85ce': 'PANORAMA [Budownictwo]: Pasy napędowe i transportujące',
    'panorama_piece': 'PANORAMA [Budownictwo]: Piece',
    'panorama_plandeki': 'PANORAMA [Budownictwo]: Plandeki',
    'panorama_pneumatyka_si%C5%82owa': 'PANORAMA [Budownictwo]: Pneumatyka siłowa',
    'panorama_podno%C5%9Bniki': 'PANORAMA [Budownictwo]: Podnośniki',
    'panorama_pojazdy_specjalistyczne': 'PANORAMA [Budownictwo]: Pojazdy specjalistyczne',
    'panorama_pompy': 'PANORAMA [Budownictwo]: Pompy',
    'panorama_por%C4%99cze_i_balustrady': 'PANORAMA [Budownictwo]: Poręcze i balustrady',
    'panorama_posadzki_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Posadzki przemysłowe',
    'panorama_po%C5%9Brednicy_ubezpieczeniowi': 'PANORAMA [Budownictwo]: Pośrednicy ubezpieczeniowi',
    'panorama_prace_elewacyjne': 'PANORAMA [Budownictwo]: Prace elewacyjne',
    'panorama_prace_podwodne': 'PANORAMA [Budownictwo]: Prace podwodne',
    'panorama_prace_wysoko%C5%9Bciowe': 'PANORAMA [Budownictwo]: Prace wysokościowe',
    'panorama_prefabrykaty_budowlane': 'PANORAMA [Budownictwo]: Prefabrykaty budowlane',
    'panorama_producenci_dom%C3%B3w_drewnianych': 'PANORAMA [Budownictwo]: Producenci domów drewnianych',
    'panorama_producenci_farb_i_lakier%C3%B3w': 'PANORAMA [Budownictwo]: Producenci farb i lakierów',
    'panorama_produkcja_artyku%C5%82%C3%B3w_elektrotechnicznych': 'PANORAMA [Budownictwo]: Produkcja artykułów elektrotechnicznych',
    'panorama_produkcja_artyku%C5%82%C3%B3w_metalowych': 'PANORAMA [Budownictwo]: Produkcja artykułów metalowych',
    'panorama_produkcja_cz%C4%99%C5%9Bci_samochodowych': 'PANORAMA [Budownictwo]: Produkcja części samochodowych',
    'panorama_produkcja_i_hurtownie_narz%C4%99dzi': 'PANORAMA [Budownictwo]: Produkcja i hurtownie narzędzi',
    'panorama_produkcja_i_monta%C5%BC_domofon%C3%B3w': 'PANORAMA [Budownictwo]: Produkcja i montaż domofonów',
    'panorama_produkcja_i_monta%C5%BC_szamb': 'PANORAMA [Budownictwo]: Produkcja i montaż szamb',
    'panorama_produkcja_i_sprzeda%C5%BC_opon': 'PANORAMA [Budownictwo]: Produkcja i sprzedaż opon',
    'panorama_produkcja_kryszta%C5%82%C3%B3w_i_szk%C5%82a_ozdobnego': 'PANORAMA [Budownictwo]: Produkcja kryształów i szkła ozdobnego',
    'panorama_produkcja_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Produkcja maszyn budowlanych',
    'panorama_produkcja_parkietu_i_paneli_pod%C5%82ogowych': 'PANORAMA [Budownictwo]: Produkcja parkietu i paneli podłogowych',
    'panorama_produkcja_spr%C4%99%C5%BCyn': 'PANORAMA [Budownictwo]: Produkcja sprężyn',
    'panorama_produkcja_system%C3%B3w_alarmowych': 'PANORAMA [Budownictwo]: Produkcja systemów alarmowych',
    'panorama_produkcja_urz%C4%85dze%C5%84_elektronicznych': 'PANORAMA [Budownictwo]: Produkcja urządzeń elektronicznych',
    'panorama_produkcja_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Budownictwo]: Produkcja urządzeń elektrycznych',
    'panorama_produkcja_urz%C4%85dze%C5%84_sanitarnych': 'PANORAMA [Budownictwo]: Produkcja urządzeń sanitarnych',
    'panorama_produkcja_zas%C5%82on_firanek_i_karniszy': 'PANORAMA [Budownictwo]: Produkcja zasłon, firanek i karniszy',
    'panorama_produkcja_%C5%BCaluzji_i_rolet': 'PANORAMA [Budownictwo]: Produkcja żaluzji i rolet',
    'panorama_projektowanie_i_monta%C5%BC_plac%C3%B3w_zabaw': 'PANORAMA [Budownictwo]: Projektowanie i montaż placów zabaw',
    'panorama_przek%C5%82adnie': 'PANORAMA [Budownictwo]: Przekładnie',
    'panorama_przemys%C5%82owe_urz%C4%85dzenia_elektryczne': 'PANORAMA [Budownictwo]: Przemysłowe urządzenia elektryczne',
    'panorama_przeno%C5%9Bniki': 'PANORAMA [Budownictwo]: Przenośniki',
    'panorama_przeprowadzki': 'PANORAMA [Budownictwo]: Przeprowadzki',
    'panorama_przewody_kable_i_%C5%9Bwiat%C5%82owody': 'PANORAMA [Budownictwo]: Przewody, kable i światłowody',
    'panorama_przyczepy_samochodowe': 'PANORAMA [Budownictwo]: Przyczepy samochodowe',
    'panorama_p%C4%99dzle_i_szczotki': 'PANORAMA [Budownictwo]: Pędzle i szczotki',
    'panorama_radcy_prawni': 'PANORAMA [Budownictwo]: Radcy prawni',
    'panorama_regeneracja_cz%C4%99%C5%9Bci_samochodowych': 'PANORAMA [Budownictwo]: Regeneracja części samochodowych',
    'panorama_renowacja_mebli': 'PANORAMA [Budownictwo]: Renowacja mebli',
    'panorama_renowacje_i_remonty': 'PANORAMA [Budownictwo]: Renowacje i remonty',
    'panorama_rury': 'PANORAMA [Budownictwo]: Rury',
    'panorama_rusztowania_i_szalunki': 'PANORAMA [Budownictwo]: Rusztowania i szalunki',
    'panorama_rzeczoznawcy': 'PANORAMA [Budownictwo]: Rzeczoznawcy',
    'panorama_samochodowe_agregaty_ch%C5%82odnicze': 'PANORAMA [Budownictwo]: Samochodowe agregaty chłodnicze',
    'panorama_samochodowe_instalacje_gazowe': 'PANORAMA [Budownictwo]: Samochodowe instalacje gazowe',
    'panorama_samochody_u%C5%BCywane': 'PANORAMA [Budownictwo]: Samochody używane',
    'panorama_schody': 'PANORAMA [Budownictwo]: Schody',
    'panorama_serwis_i_cz%C4%99%C5%9Bci_do_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Serwis i części do maszyn budowlanych',
    'panorama_serwis_i_instalacja_klimatyzacji': 'PANORAMA [Budownictwo]: Serwis i instalacja klimatyzacji',
    'panorama_serwis_samochod%C3%B3w_ci%C4%99%C5%BCarowych_i_dostawczych': 'PANORAMA [Budownictwo]: Serwis samochodów ciężarowych i dostawczych',
    'panorama_serwis_urz%C4%85dze%C5%84_ch%C5%82odniczych': 'PANORAMA [Budownictwo]: Serwis urządzeń chłodniczych',
    'panorama_serwis_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Budownictwo]: Serwis urządzeń elektrycznych',
    'panorama_silikon': 'PANORAMA [Budownictwo]: Silikon',
    'panorama_silniki_i_pr%C4%85dnice': 'PANORAMA [Budownictwo]: Silniki i prądnice',
    'panorama_si%C5%82owniki_i_automatyczne_nap%C4%99dy_do_bram': 'PANORAMA [Budownictwo]: Siłowniki i automatyczne napędy do bram',
    'panorama_skrzynie_bieg%C3%B3w': 'PANORAMA [Budownictwo]: Skrzynie biegów',
    'panorama_spedycja': 'PANORAMA [Budownictwo]: Spedycja',
    'panorama_spedycja_mi%C4%99dzynarodowa': 'PANORAMA [Budownictwo]: Spedycja międzynarodowa',
    'panorama_sprzeda%C5%BC_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Sprzedaż maszyn budowlanych',
    'panorama_sprzeda%C5%BC_samochod%C3%B3w_ci%C4%99%C5%BCarowych_i_dostawczych': 'PANORAMA [Budownictwo]: Sprzedaż samochodów ciężarowych i dostawczych',
    'panorama_sprz%C4%85tanie_terenu': 'PANORAMA [Budownictwo]: Sprzątanie terenu',
    'panorama_sprz%C4%85tanie_wn%C4%99trz_i_mycie_okien': 'PANORAMA [Budownictwo]: Sprzątanie wnętrz i mycie okien',
    'panorama_sprz%C4%99t_do_malowania_i_tapetowania': 'PANORAMA [Budownictwo]: Sprzęt do malowania i tapetowania',
    'panorama_sprz%C4%99t_do_produkcji_opakowa%C5%84': 'PANORAMA [Budownictwo]: Sprzęt do produkcji opakowań',
    'panorama_sprz%C4%99t_i_materia%C5%82y_hydrauliczne': 'PANORAMA [Budownictwo]: Sprzęt i materiały hydrauliczne',
    'panorama_sprz%C4%99t_i_zabezpieczenia_przeciwpo%C5%BCarowe': 'PANORAMA [Budownictwo]: Sprzęt i zabezpieczenia przeciwpożarowe',
    'panorama_sprz%C4%99t_torowy_i_kolejowy': 'PANORAMA [Budownictwo]: Sprzęt torowy i kolejowy',
    'panorama_sp%C3%B3%C5%82dzielnie_i_administracje_mieszkaniowe': 'PANORAMA [Budownictwo]: Spółdzielnie i administracje mieszkaniowe',
    'panorama_stacje_diagnostyczne_i_przegl%C4%85dy_techniczne': 'PANORAMA [Budownictwo]: Stacje diagnostyczne i przeglądy techniczne',
    'panorama_stacje_obs%C5%82ugi_i_warsztaty_samochodowe': 'PANORAMA [Budownictwo]: Stacje obsługi i warsztaty samochodowe',
    'panorama_stal_i_wyroby_stalowe': 'PANORAMA [Budownictwo]: Stal i wyroby stalowe',
    'panorama_stolarze': 'PANORAMA [Budownictwo]: Stolarze',
    'panorama_studnie': 'PANORAMA [Budownictwo]: Studnie',
    'panorama_styropian': 'PANORAMA [Budownictwo]: Styropian',
    'panorama_sufity_podwieszane': 'PANORAMA [Budownictwo]: Sufity podwieszane',
    'panorama_surowce_mineralne': 'PANORAMA [Budownictwo]: Surowce mineralne',
    'panorama_suwnice': 'PANORAMA [Budownictwo]: Suwnice',
    'panorama_systemy_d%C5%BAwi%C4%99kowe_i_audio': 'PANORAMA [Budownictwo]: Systemy dźwiękowe i audio',
    'panorama_systemy_zabudowy_wn%C4%99trz': 'PANORAMA [Budownictwo]: Systemy zabudowy wnętrz',
    'panorama_systemy_zamocowa%C5%84': 'PANORAMA [Budownictwo]: Systemy zamocowań',
    'panorama_szklarze': 'PANORAMA [Budownictwo]: Szklarze',
    'panorama_szk%C5%82o_budowlane': 'PANORAMA [Budownictwo]: Szkło budowlane',
    'panorama_szk%C5%82o_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Szkło przemysłowe',
    'panorama_sznury_liny_i_nici': 'PANORAMA [Budownictwo]: Sznury, liny i nici',
    'panorama_szyberdachy': 'PANORAMA [Budownictwo]: Szyberdachy',
    'panorama_szyby_samochodowe': 'PANORAMA [Budownictwo]: Szyby samochodowe',
    'panorama_tablice_rejestracyjne': 'PANORAMA [Budownictwo]: Tablice rejestracyjne',
    'panorama_tabor_kolejowy': 'PANORAMA [Budownictwo]: Tabor kolejowy',
    'panorama_taksometry_tachometry_i_tachografy': 'PANORAMA [Budownictwo]: Taksometry, tachometry i tachografy',
    'panorama_tapety': 'PANORAMA [Budownictwo]: Tapety',
    'panorama_tapicerka_i_pokrowce_samochodowe': 'PANORAMA [Budownictwo]: Tapicerka i pokrowce samochodowe',
    'panorama_tartaki': 'PANORAMA [Budownictwo]: Tartaki',
    'panorama_techniki_bezwykopowe': 'PANORAMA [Budownictwo]: Techniki bezwykopowe',
    'panorama_technologie_budowlane': 'PANORAMA [Budownictwo]: Technologie budowlane',
    'panorama_telewizja_przemys%C5%82owa': 'PANORAMA [Budownictwo]: Telewizja przemysłowa',
    'panorama_transport_kolejowy': 'PANORAMA [Budownictwo]: Transport kolejowy',
    'panorama_transport_lotniczy': 'PANORAMA [Budownictwo]: Transport lotniczy',
    'panorama_transport_mi%C4%99dzynarodowy': 'PANORAMA [Budownictwo]: Transport międzynarodowy',
    'panorama_transport_morski_i_%C5%9Br%C3%B3dl%C4%85dowy': 'PANORAMA [Budownictwo]: Transport morski i śródlądowy',
    'panorama_transport_nadgabarytowy': 'PANORAMA [Budownictwo]: Transport nadgabarytowy',
    'panorama_transport_samochodowy': 'PANORAMA [Budownictwo]: Transport samochodowy',
    'panorama_transport_%C5%82adunk%C3%B3w_niebezpiecznych': 'PANORAMA [Budownictwo]: Transport ładunków niebezpiecznych',
    'panorama_tworzywa_sztuczne': 'PANORAMA [Budownictwo]: Tworzywa sztuczne',
    'panorama_t%C5%82umiki_i_uk%C5%82ady_wydechowe': 'PANORAMA [Budownictwo]: Tłumiki i układy wydechowe',
    'panorama_ubezpieczenia': 'PANORAMA [Budownictwo]: Ubezpieczenia',
    'panorama_uk%C5%82adanie_gresu_i_p%C5%82ytek_ceramicznych': 'PANORAMA [Budownictwo]: Układanie gresu i płytek ceramicznych',
    'panorama_uk%C5%82adanie_wyk%C5%82adzin_pod%C5%82ogowych': 'PANORAMA [Budownictwo]: Układanie wykładzin podłogowych',
    'panorama_urz%C4%85dzenia_elektroniczne': 'PANORAMA [Budownictwo]: Urządzenia elektroniczne',
    'panorama_urz%C4%85dzenia_elektryczne': 'PANORAMA [Budownictwo]: Urządzenia elektryczne',
    'panorama_urz%C4%85dzenia_gazowe': 'PANORAMA [Budownictwo]: Urządzenia gazowe',
    'panorama_urz%C4%85dzenia_grzewcze': 'PANORAMA [Budownictwo]: Urządzenia grzewcze',
    'panorama_urz%C4%85dzenia_i_maszyny_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Urządzenia i maszyny przemysłowe',
    'panorama_urz%C4%85dzenia_lakiernicze': 'PANORAMA [Budownictwo]: Urządzenia lakiernicze',
    'panorama_urz%C4%85dzenia_pneumatyczne': 'PANORAMA [Budownictwo]: Urządzenia pneumatyczne',
    'panorama_urz%C4%85dzenia_pomiarowe': 'PANORAMA [Budownictwo]: Urządzenia pomiarowe',
    'panorama_urz%C4%85dzenia_sanitarne': 'PANORAMA [Budownictwo]: Urządzenia sanitarne',
    'panorama_urz%C4%85dzenia_spawalnicze_i_zgrzewaj%C4%85ce': 'PANORAMA [Budownictwo]: Urządzenia spawalnicze i zgrzewające',
    'panorama_usuwanie_i_neutralizacja_azbestu': 'PANORAMA [Budownictwo]: Usuwanie i neutralizacja azbestu',
    'panorama_uszczelki_i_uszczelnienia': 'PANORAMA [Budownictwo]: Uszczelki i uszczelnienia',
    'panorama_us%C5%82ugi_gazownicze': 'PANORAMA [Budownictwo]: Usługi gazownicze',
    'panorama_us%C5%82ugi_i_projekty_g%C3%B3rnicze': 'PANORAMA [Budownictwo]: Usługi i projekty górnicze',
    'panorama_us%C5%82ugi_kamieniarskie': 'PANORAMA [Budownictwo]: Usługi kamieniarskie',
    'panorama_us%C5%82ugi_posadzkarskie': 'PANORAMA [Budownictwo]: Usługi posadzkarskie',
    'panorama_us%C5%82ugi_saperskie': 'PANORAMA [Budownictwo]: Usługi saperskie',
    'panorama_us%C5%82ugi_spawania_i_zgrzewania': 'PANORAMA [Budownictwo]: Usługi spawania i zgrzewania',
    'panorama_us%C5%82ugi_tapicerskie': 'PANORAMA [Budownictwo]: Usługi tapicerskie',
    'panorama_us%C5%82ugi_wodno_kanalizacyjne': 'PANORAMA [Budownictwo]: Usługi wodno-kanalizacyjne',
    'panorama_utylizacja_odpad%C3%B3w': 'PANORAMA [Budownictwo]: Utylizacja odpadów',
    'panorama_uzbrajanie_terenu': 'PANORAMA [Budownictwo]: Uzbrajanie terenu',
    'panorama_u%C5%BCywane_cz%C4%99%C5%9Bci_samochodowe': 'PANORAMA [Budownictwo]: Używane części samochodowe',
    'panorama_wagi': 'PANORAMA [Budownictwo]: Wagi',
    'panorama_wentylacja': 'PANORAMA [Budownictwo]: Wentylacja',
    'panorama_windy_i_urz%C4%85dzenia_d%C5%BAwigowe': 'PANORAMA [Budownictwo]: Windy i urządzenia dźwigowe',
    'panorama_witra%C5%BCe': 'PANORAMA [Budownictwo]: Witraże',
    'panorama_wodoci%C4%85gi_i_kanalizacja': 'PANORAMA [Budownictwo]: Wodociągi i kanalizacja',
    'panorama_wulkanizacja_i_serwis_opon': 'PANORAMA [Budownictwo]: Wulkanizacja i serwis opon',
    'panorama_wyburzenia_i_rozbi%C3%B3rki': 'PANORAMA [Budownictwo]: Wyburzenia i rozbiórki',
    'panorama_wycena_nieruchomo%C5%9Bci': 'PANORAMA [Budownictwo]: Wycena nieruchomości',
    'panorama_wycieraczki_i_maty': 'PANORAMA [Budownictwo]: Wycieraczki i maty',
    'panorama_wykopy_i_roboty_fundamentowe': 'PANORAMA [Budownictwo]: Wykopy i roboty fundamentowe',
    'panorama_wyko%C5%84czenia_wn%C4%99trz': 'PANORAMA [Budownictwo]: Wykończenia wnętrz',
    'panorama_wynajem_d%C5%BAwig%C3%B3w_i_%C5%BCurawi': 'PANORAMA [Budownictwo]: Wynajem dźwigów i żurawi',
    'panorama_wynajem_magazyn%C3%B3w': 'PANORAMA [Budownictwo]: Wynajem magazynów',
    'panorama_wynajem_maszyn_budowlanych': 'PANORAMA [Budownictwo]: Wynajem maszyn budowlanych',
    'panorama_wynajem_maszyn_i_narz%C4%99dzi': 'PANORAMA [Budownictwo]: Wynajem maszyn i narzędzi',
    'panorama_wynajem_samochod%C3%B3w_ci%C4%99%C5%BCarowych_i_dostawczych': 'PANORAMA [Budownictwo]: Wynajem samochodów ciężarowych i dostawczych',
    'panorama_wynajem_samochod%C3%B3w_i_zarz%C4%85dzanie_flot%C4%85': 'PANORAMA [Budownictwo]: Wynajem samochodów i zarządzanie flotą',
    'panorama_wyposa%C5%BCenie_dodatkowe_samochod%C3%B3w': 'PANORAMA [Budownictwo]: Wyposażenie dodatkowe samochodów',
    'panorama_wyposa%C5%BCenie_hoteli': 'PANORAMA [Budownictwo]: Wyposażenie hoteli',
    'panorama_wyposa%C5%BCenie_kuchni': 'PANORAMA [Budownictwo]: Wyposażenie kuchni',
    'panorama_wyposa%C5%BCenie_magazyn%C3%B3w': 'PANORAMA [Budownictwo]: Wyposażenie magazynów',
    'panorama_wyposa%C5%BCenie_obiekt%C3%B3w_sportowych': 'PANORAMA [Budownictwo]: Wyposażenie obiektów sportowych',
    'panorama_wyposa%C5%BCenie_sklep%C3%B3w': 'PANORAMA [Budownictwo]: Wyposażenie sklepów',
    'panorama_wyposa%C5%BCenie_warsztat%C3%B3w_i_myjni_samochodowych': 'PANORAMA [Budownictwo]: Wyposażenie warsztatów i myjni samochodowych',
    'panorama_wyposa%C5%BCenie_%C5%82azienek': 'PANORAMA [Budownictwo]: Wyposażenie łazienek',
    'panorama_wyroby_hutnicze': 'PANORAMA [Budownictwo]: Wyroby hutnicze',
    'panorama_wytwarzanie_energii_odnawialnej': 'PANORAMA [Budownictwo]: Wytwarzanie energii odnawialnej',
    'panorama_wyw%C3%B3z_%C5%9Bmieci_i_odpad%C3%B3w': 'PANORAMA [Budownictwo]: Wywóz śmieci i odpadów',
    'panorama_wzornictwo_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Wzornictwo przemysłowe',
    'panorama_w%C3%B3zki_wid%C5%82owe': 'PANORAMA [Budownictwo]: Wózki widłowe',
    'panorama_w%C4%99%C5%BCe_przemys%C5%82owe': 'PANORAMA [Budownictwo]: Węże przemysłowe',
    'panorama_zabezpieczenia_antykorozyjne': 'PANORAMA [Budownictwo]: Zabezpieczenia antykorozyjne',
    'panorama_zabezpieczenia_antykorozyjne_samochod%C3%B3w': 'PANORAMA [Budownictwo]: Zabezpieczenia antykorozyjne samochodów',
    'panorama_zabudowy_nadwozi_samochodowych': 'PANORAMA [Budownictwo]: Zabudowy nadwozi samochodowych',
    'panorama_zak%C5%82ady_sztukatorskie': 'PANORAMA [Budownictwo]: Zakłady sztukatorskie',
    'panorama_zamki_i_k%C5%82%C3%B3dki': 'PANORAMA [Budownictwo]: Zamki i kłódki',
    'panorama_zamki_i_zabezpieczenia_antyw%C5%82amaniowe': 'PANORAMA [Budownictwo]: Zamki i zabezpieczenia antywłamaniowe',
    'panorama_zarz%C4%85dzanie_nieruchomo%C5%9Bciami': 'PANORAMA [Budownictwo]: Zarządzanie nieruchomościami',
    'panorama_zawiesia_linowe_%C5%82a%C5%84cuchowe_i_pasowe': 'PANORAMA [Budownictwo]: Zawiesia linowe, łańcuchowe i pasowe',
    'panorama_zbiorniki_i_pojemniki': 'PANORAMA [Budownictwo]: Zbiorniki i pojemniki',
    'panorama_znakowanie_i_monitorowanie_samochod%C3%B3w': 'PANORAMA [Budownictwo]: Znakowanie i monitorowanie samochodów',
    'panorama_z%C5%82om_i_surowce_wt%C3%B3rne': 'PANORAMA [Budownictwo]: Złom i surowce wtórne',
    'panorama_%C5%82a%C5%84cuchy': 'PANORAMA [Budownictwo]: Łańcuchy',
    'panorama_%C5%82o%C5%BCyska': 'PANORAMA [Budownictwo]: Łożyska',
    'panorama_%C5%9Blusarze': 'PANORAMA [Budownictwo]: Ślusarze',
    'panorama_%C5%9Bwiadectwa_energetyczne': 'PANORAMA [Budownictwo]: Świadectwa energetyczne',
    'panorama_akcesoria_do_drzwi_i_okien': 'PANORAMA [Dom i ogród]: Akcesoria do drzwi i okien',
    'panorama_akcesoria_meblowe': 'PANORAMA [Dom i ogród]: Akcesoria meblowe',
    'panorama_anteny': 'PANORAMA [Dom i ogród]: Anteny',
    'panorama_architektura_krajobrazu': 'PANORAMA [Dom i ogród]: Architektura krajobrazu',
    'panorama_armatura_hydrauliczna': 'PANORAMA [Dom i ogród]: Armatura hydrauliczna',
    'panorama_artyku%C5%82y_i_sprz%C4%99t_ogrodniczy': 'PANORAMA [Dom i ogród]: Artykuły i sprzęt ogrodniczy',
    'panorama_biura_architektoniczne': 'PANORAMA [Dom i ogród]: Biura architektoniczne',
    'panorama_biura_projektowe': 'PANORAMA [Dom i ogród]: Biura projektowe',
    'panorama_bramy_i_ogrodzenia': 'PANORAMA [Dom i ogród]: Bramy i ogrodzenia',
    'panorama_brykiety_i_w%C4%99giel_drzewny': 'PANORAMA [Dom i ogród]: Brykiety i węgiel drzewny',
    'panorama_budowa_i_wyko%C5%84czenia_pod_klucz': 'PANORAMA [Dom i ogród]: Budowa i wykończenia pod klucz',
    'panorama_budowa_i_wyposa%C5%BCenie_gara%C5%BCy': 'PANORAMA [Dom i ogród]: Budowa i wyposażenie garaży',
    'panorama_ceramika_ozdobna': 'PANORAMA [Dom i ogród]: Ceramika ozdobna',
    'panorama_chemia_gospodarcza': 'PANORAMA [Dom i ogród]: Chemia gospodarcza',
    'panorama_czyszczenie_i_renowacja_dywan%C3%B3w_i_wyk%C5%82adzin': 'PANORAMA [Dom i ogród]: Czyszczenie i renowacja dywanów i wykładzin',
    'panorama_dachy_i_rynny': 'PANORAMA [Dom i ogród]: Dachy i rynny',
    'panorama_dekoratorstwo_i_architektura_wn%C4%99trz': 'PANORAMA [Dom i ogród]: Dekoratorstwo i architektura wnętrz',
    'panorama_deweloperzy': 'PANORAMA [Dom i ogród]: Deweloperzy',
    'panorama_dozowniki_myd%C5%82a': 'PANORAMA [Dom i ogród]: Dozowniki mydła',
    'panorama_drewno_opa%C5%82owe': 'PANORAMA [Dom i ogród]: Drewno opałowe',
    'panorama_drzwi': 'PANORAMA [Dom i ogród]: Drzwi',
    'panorama_drzwi_antyw%C5%82amaniowe': 'PANORAMA [Dom i ogród]: Drzwi antywłamaniowe',
    'panorama_dywany_i_wyk%C5%82adziny': 'PANORAMA [Dom i ogród]: Dywany i wykładziny',
    'panorama_elektroinstalatorstwo': 'PANORAMA [Dom i ogród]: Elektroinstalatorstwo',
    'panorama_filtry': 'PANORAMA [Dom i ogród]: Filtry',
    'panorama_folie_i_foliowanie': 'PANORAMA [Dom i ogród]: Folie i foliowanie',
    'panorama_gres_terakota_i_p%C5%82ytki_ceramiczne': 'PANORAMA [Dom i ogród]: Gres, terakota i płytki ceramiczne',
    'panorama_grzejnictwo_elektryczne': 'PANORAMA [Dom i ogród]: Grzejnictwo elektryczne',
    'panorama_hurtownie_rtv': 'PANORAMA [Dom i ogród]: Hurtownie RTV',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_higienicznych': 'PANORAMA [Dom i ogród]: Hurtownie artykułów higienicznych',
    'panorama_hurtownie_dywan%C3%B3w_i_wyk%C5%82adzin': 'PANORAMA [Dom i ogród]: Hurtownie dywanów i wykładzin',
    'panorama_hurtownie_gresu_terakoty_i_p%C5%82ytek_ceramicznych': 'PANORAMA [Dom i ogród]: Hurtownie gresu, terakoty i płytek ceramicznych',
    'panorama_hurtownie_parkietu_i_paneli_pod%C5%82ogowych': 'PANORAMA [Dom i ogród]: Hurtownie parkietu i paneli podłogowych',
    'panorama_hurtownie_sprz%C4%99tu_agd': 'PANORAMA [Dom i ogród]: Hurtownie sprzętu AGD',
    'panorama_hurtownie_szk%C5%82a_ozdobnego_i_kryszta%C5%82%C3%B3w': 'PANORAMA [Dom i ogród]: Hurtownie szkła ozdobnego i kryształów',
    'panorama_hurtownie_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Dom i ogród]: Hurtownie urządzeń elektrycznych',
    'panorama_hurtownie_urz%C4%85dze%C5%84_sanitarnych': 'PANORAMA [Dom i ogród]: Hurtownie urządzeń sanitarnych',
    'panorama_hurtownie_zas%C5%82on_firanek_i_karniszy': 'PANORAMA [Dom i ogród]: Hurtownie zasłon, firanek i karniszy',
    'panorama_hurtownie_%C5%BCaluzji_i_rolet': 'PANORAMA [Dom i ogród]: Hurtownie żaluzji i rolet',
    'panorama_hydraulicy': 'PANORAMA [Dom i ogród]: Hydraulicy',
    'panorama_hydraulika_si%C5%82owa': 'PANORAMA [Dom i ogród]: Hydraulika siłowa',
    'panorama_instalacja_i_serwis_ogrzewania': 'PANORAMA [Dom i ogród]: Instalacja i serwis ogrzewania',
    'panorama_instalacja_system%C3%B3w_alarmowych': 'PANORAMA [Dom i ogród]: Instalacja systemów alarmowych',
    'panorama_kominiarze': 'PANORAMA [Dom i ogród]: Kominiarze',
    'panorama_kominki': 'PANORAMA [Dom i ogród]: Kominki',
    'panorama_kominy': 'PANORAMA [Dom i ogród]: Kominy',
    'panorama_kryszta%C5%82y_i_szk%C5%82o_ozdobne': 'PANORAMA [Dom i ogród]: Kryształy i szkło ozdobne',
    'panorama_lampy_i_o%C5%9Bwietlenie_wn%C4%99trz': 'PANORAMA [Dom i ogród]: Lampy i oświetlenie wnętrz',
    'panorama_lustra': 'PANORAMA [Dom i ogród]: Lustra',
    'panorama_magiel': 'PANORAMA [Dom i ogród]: Magiel',
    'panorama_malowanie_i_tapetowanie': 'PANORAMA [Dom i ogród]: Malowanie i tapetowanie',
    'panorama_maszyny_dziewiarskie': 'PANORAMA [Dom i ogród]: Maszyny dziewiarskie',
    'panorama_materace': 'PANORAMA [Dom i ogród]: Materace',
    'panorama_materia%C5%82y_do_wyka%C5%84czania_wn%C4%99trz': 'PANORAMA [Dom i ogród]: Materiały do wykańczania wnętrz',
    'panorama_materia%C5%82y_drewnopochodne': 'PANORAMA [Dom i ogród]: Materiały drewnopochodne',
    'panorama_materia%C5%82y_elektryczne': 'PANORAMA [Dom i ogród]: Materiały elektryczne',
    'panorama_materia%C5%82y_tapicerskie': 'PANORAMA [Dom i ogród]: Materiały tapicerskie',
    'panorama_meble': 'PANORAMA [Dom i ogród]: Meble',
    'panorama_meble_biurowe': 'PANORAMA [Dom i ogród]: Meble biurowe',
    'panorama_meble_kuchenne': 'PANORAMA [Dom i ogród]: Meble kuchenne',
    'panorama_meble_metalowe': 'PANORAMA [Dom i ogród]: Meble metalowe',
    'panorama_meble_na_zam%C3%B3wienie': 'PANORAMA [Dom i ogród]: Meble na zamówienie',
    'panorama_meble_ogrodowe': 'PANORAMA [Dom i ogród]: Meble ogrodowe',
    'panorama_meble_specjalistyczne': 'PANORAMA [Dom i ogród]: Meble specjalistyczne',
    'panorama_monta%C5%BC_i_produkcja_basen%C3%B3w_i_fontann': 'PANORAMA [Dom i ogród]: Montaż i produkcja basenów i fontann',
    'panorama_monta%C5%BC_i_sprzeda%C5%BC_%C5%BCaluzji_i_rolet': 'PANORAMA [Dom i ogród]: Montaż i sprzedaż żaluzji i rolet',
    'panorama_nape%C5%82nianie_butli_gazowych': 'PANORAMA [Dom i ogród]: Napełnianie butli gazowych',
    'panorama_no%C5%9Bniki_danych_i_p%C5%82yty_cd_i_dvd': 'PANORAMA [Dom i ogród]: Nośniki danych i płyty CD i DVD',
    'panorama_obrusy': 'PANORAMA [Dom i ogród]: Obrusy',
    'panorama_oczyszczanie_%C5%9Bciek%C3%B3w': 'PANORAMA [Dom i ogród]: Oczyszczanie ścieków',
    'panorama_odkurzacze_centralne': 'PANORAMA [Dom i ogród]: Odkurzacze centralne',
    'panorama_ogrodnictwo': 'PANORAMA [Dom i ogród]: Ogrodnictwo',
    'panorama_ogrzewanie_elektryczne': 'PANORAMA [Dom i ogród]: Ogrzewanie elektryczne',
    'panorama_okleiny': 'PANORAMA [Dom i ogród]: Okleiny',
    'panorama_okna': 'PANORAMA [Dom i ogród]: Okna',
    'panorama_okna_dachowe': 'PANORAMA [Dom i ogród]: Okna dachowe',
    'panorama_okna_drewniane': 'PANORAMA [Dom i ogród]: Okna drewniane',
    'panorama_ozdoby_%C5%9Bwi%C4%85teczne': 'PANORAMA [Dom i ogród]: Ozdoby świąteczne',
    'panorama_o%C5%9Bwietlenie': 'PANORAMA [Dom i ogród]: Oświetlenie',
    'panorama_panele_i_pod%C5%82ogi': 'PANORAMA [Dom i ogród]: Panele i podłogi',
    'panorama_parapety': 'PANORAMA [Dom i ogród]: Parapety',
    'panorama_parkiet_i_panele_pod%C5%82ogowe': 'PANORAMA [Dom i ogród]: Parkiet i panele podłogowe',
    'panorama_pomoc_domowa': 'PANORAMA [Dom i ogród]: Pomoc domowa',
    'panorama_porcelana_i_fajans': 'PANORAMA [Dom i ogród]: Porcelana i fajans',
    'panorama_por%C4%99cze_i_balustrady': 'PANORAMA [Dom i ogród]: Poręcze i balustrady',
    'panorama_posadzki_przemys%C5%82owe': 'PANORAMA [Dom i ogród]: Posadzki przemysłowe',
    'panorama_producenci_dom%C3%B3w_drewnianych': 'PANORAMA [Dom i ogród]: Producenci domów drewnianych',
    'panorama_produkcja_artyku%C5%82%C3%B3w_higienicznych': 'PANORAMA [Dom i ogród]: Produkcja artykułów higienicznych',
    'panorama_produkcja_i_hurtownie_narz%C4%99dzi': 'PANORAMA [Dom i ogród]: Produkcja i hurtownie narzędzi',
    'panorama_produkcja_i_monta%C5%BC_domofon%C3%B3w': 'PANORAMA [Dom i ogród]: Produkcja i montaż domofonów',
    'panorama_produkcja_kryszta%C5%82%C3%B3w_i_szk%C5%82a_ozdobnego': 'PANORAMA [Dom i ogród]: Produkcja kryształów i szkła ozdobnego',
    'panorama_produkcja_parkietu_i_paneli_pod%C5%82ogowych': 'PANORAMA [Dom i ogród]: Produkcja parkietu i paneli podłogowych',
    'panorama_produkcja_ro%C5%9Blin_i_nasion': 'PANORAMA [Dom i ogród]: Produkcja roślin i nasion',
    'panorama_produkcja_sprz%C4%99tu_agd': 'PANORAMA [Dom i ogród]: Produkcja sprzętu AGD',
    'panorama_produkcja_sprz%C4%99tu_rtv': 'PANORAMA [Dom i ogród]: Produkcja sprzętu RTV',
    'panorama_produkcja_system%C3%B3w_alarmowych': 'PANORAMA [Dom i ogród]: Produkcja systemów alarmowych',
    'panorama_produkcja_urz%C4%85dze%C5%84_elektronicznych': 'PANORAMA [Dom i ogród]: Produkcja urządzeń elektronicznych',
    'panorama_produkcja_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Dom i ogród]: Produkcja urządzeń elektrycznych',
    'panorama_produkcja_urz%C4%85dze%C5%84_sanitarnych': 'PANORAMA [Dom i ogród]: Produkcja urządzeń sanitarnych',
    'panorama_produkcja_zas%C5%82on_firanek_i_karniszy': 'PANORAMA [Dom i ogród]: Produkcja zasłon, firanek i karniszy',
    'panorama_produkcja_%C5%BCaluzji_i_rolet': 'PANORAMA [Dom i ogród]: Produkcja żaluzji i rolet',
    'panorama_ramy_i_oprawy_obraz%C3%B3w': 'PANORAMA [Dom i ogród]: Ramy i oprawy obrazów',
    'panorama_renowacja_mebli': 'PANORAMA [Dom i ogród]: Renowacja mebli',
    'panorama_renowacje_i_remonty': 'PANORAMA [Dom i ogród]: Renowacje i remonty',
    'panorama_ro%C5%9Bliny_sztuczne': 'PANORAMA [Dom i ogród]: Rośliny sztuczne',
    'panorama_ro%C5%9Bliny_nasiona_i_cebulki': 'PANORAMA [Dom i ogród]: Rośliny, nasiona i cebulki',
    'panorama_r%C4%99czniki_koce_i_po%C5%9Bciel': 'PANORAMA [Dom i ogród]: Ręczniki, koce i pościel',
    'panorama_schody': 'PANORAMA [Dom i ogród]: Schody',
    'panorama_serwis_rtv': 'PANORAMA [Dom i ogród]: Serwis RTV',
    'panorama_serwis_sprz%C4%99tu_agd': 'PANORAMA [Dom i ogród]: Serwis sprzętu AGD',
    'panorama_serwis_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Dom i ogród]: Serwis urządzeń elektrycznych',
    'panorama_sklepy_ze_sprz%C4%99tem_agd': 'PANORAMA [Dom i ogród]: Sklepy ze sprzętem AGD',
    'panorama_sklepy_ze_sprz%C4%99tem_rtv': 'PANORAMA [Dom i ogród]: Sklepy ze sprzętem RTV',
    'panorama_sprz%C4%85tanie_wn%C4%99trz_i_mycie_okien': 'PANORAMA [Dom i ogród]: Sprzątanie wnętrz i mycie okien',
    'panorama_sprz%C4%99t_do_malowania_i_tapetowania': 'PANORAMA [Dom i ogród]: Sprzęt do malowania i tapetowania',
    'panorama_sprz%C4%99t_i_materia%C5%82y_hydrauliczne': 'PANORAMA [Dom i ogród]: Sprzęt i materiały hydrauliczne',
    'panorama_sprz%C4%99t_i_zabezpieczenia_przeciwpo%C5%BCarowe': 'PANORAMA [Dom i ogród]: Sprzęt i zabezpieczenia przeciwpożarowe',
    'panorama_stolarze': 'PANORAMA [Dom i ogród]: Stolarze',
    'panorama_studnie': 'PANORAMA [Dom i ogród]: Studnie',
    'panorama_sufity_podwieszane': 'PANORAMA [Dom i ogród]: Sufity podwieszane',
    'panorama_systemy_audiowizualne': 'PANORAMA [Dom i ogród]: Systemy audiowizualne',
    'panorama_systemy_d%C5%BAwi%C4%99kowe_i_audio': 'PANORAMA [Dom i ogród]: Systemy dźwiękowe i audio',
    'panorama_systemy_zabudowy_wn%C4%99trz': 'PANORAMA [Dom i ogród]: Systemy zabudowy wnętrz',
    'panorama_szklarze': 'PANORAMA [Dom i ogród]: Szklarze',
    'panorama_tapety': 'PANORAMA [Dom i ogród]: Tapety',
    'panorama_telewizja_kablowa': 'PANORAMA [Dom i ogród]: Telewizja kablowa',
    'panorama_telewizja_satelitarna': 'PANORAMA [Dom i ogród]: Telewizja satelitarna',
    'panorama_uk%C5%82adanie_gresu_i_p%C5%82ytek_ceramicznych': 'PANORAMA [Dom i ogród]: Układanie gresu i płytek ceramicznych',
    'panorama_uk%C5%82adanie_wyk%C5%82adzin_pod%C5%82ogowych': 'PANORAMA [Dom i ogród]: Układanie wykładzin podłogowych',
    'panorama_urz%C4%85dzenia_elektroniczne': 'PANORAMA [Dom i ogród]: Urządzenia elektroniczne',
    'panorama_urz%C4%85dzenia_elektryczne': 'PANORAMA [Dom i ogród]: Urządzenia elektryczne',
    'panorama_urz%C4%85dzenia_grzewcze': 'PANORAMA [Dom i ogród]: Urządzenia grzewcze',
    'panorama_urz%C4%85dzenia_sanitarne': 'PANORAMA [Dom i ogród]: Urządzenia sanitarne',
    'panorama_uszczelki_i_uszczelnienia': 'PANORAMA [Dom i ogród]: Uszczelki i uszczelnienia',
    'panorama_us%C5%82ugi_gazownicze': 'PANORAMA [Dom i ogród]: Usługi gazownicze',
    'panorama_us%C5%82ugi_kamieniarskie': 'PANORAMA [Dom i ogród]: Usługi kamieniarskie',
    'panorama_us%C5%82ugi_posadzkarskie': 'PANORAMA [Dom i ogród]: Usługi posadzkarskie',
    'panorama_us%C5%82ugi_tapicerskie': 'PANORAMA [Dom i ogród]: Usługi tapicerskie',
    'panorama_witra%C5%BCe': 'PANORAMA [Dom i ogród]: Witraże',
    'panorama_wodoci%C4%85gi_i_kanalizacja': 'PANORAMA [Dom i ogród]: Wodociągi i kanalizacja',
    'panorama_wycieraczki_i_maty': 'PANORAMA [Dom i ogród]: Wycieraczki i maty',
    'panorama_wyko%C5%84czenia_wn%C4%99trz': 'PANORAMA [Dom i ogród]: Wykończenia wnętrz',
    'panorama_wyposa%C5%BCenie_kuchni': 'PANORAMA [Dom i ogród]: Wyposażenie kuchni',
    'panorama_wyposa%C5%BCenie_%C5%82azienek': 'PANORAMA [Dom i ogród]: Wyposażenie łazienek',
    'panorama_wyroby_wiklinowe_i_bambusowe': 'PANORAMA [Dom i ogród]: Wyroby wiklinowe i bambusowe',
    'panorama_wyw%C3%B3z_%C5%9Bmieci_i_odpad%C3%B3w': 'PANORAMA [Dom i ogród]: Wywóz śmieci i odpadów',
    'panorama_zamki_i_k%C5%82%C3%B3dki': 'PANORAMA [Dom i ogród]: Zamki i kłódki',
    'panorama_zamki_i_zabezpieczenia_antyw%C5%82amaniowe': 'PANORAMA [Dom i ogród]: Zamki i zabezpieczenia antywłamaniowe',
    'panorama_zapalniczki_i_zapa%C5%82ki': 'PANORAMA [Dom i ogród]: Zapalniczki i zapałki',
    'panorama_zas%C5%82ony_firanki_i_karnisze': 'PANORAMA [Dom i ogród]: Zasłony, firanki i karnisze',
    'panorama_zawiesia_linowe_%C5%82a%C5%84cuchowe_i_pasowe': 'PANORAMA [Dom i ogród]: Zawiesia linowe, łańcuchowe i pasowe',
    'panorama_%C5%9Blusarstwo_i_dorabianie_kluczy': 'PANORAMA [Dom i ogród]: Ślusarstwo i dorabianie kluczy',
    'panorama_%C5%9Blusarze': 'PANORAMA [Dom i ogród]: Ślusarze',
    'panorama_%C5%9Brodki_ochrony_ro%C5%9Blin': 'PANORAMA [Dom i ogród]: Środki ochrony roślin',
    'panorama_%C5%9Bwiece_i_znicze': 'PANORAMA [Dom i ogród]: Świece i znicze',
    'panorama_artyku%C5%82y_dzieci%C4%99ce': 'PANORAMA [Dzieci]: Artykuły dziecięce',
    'panorama_artyku%C5%82y_papiernicze': 'PANORAMA [Dzieci]: Artykuły papiernicze',
    'panorama_artyku%C5%82y_szkolne': 'PANORAMA [Dzieci]: Artykuły szkolne',
    'panorama_domy_dziecka': 'PANORAMA [Dzieci]: Domy dziecka',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Dzieci]: Hurtownie artykułów papierniczych',
    'panorama_hurtownie_i_producenci_artyku%C5%82%C3%B3w_dzieci%C4%99cych': 'PANORAMA [Dzieci]: Hurtownie i producenci artykułów dziecięcych',
    'panorama_hurtownie_zabawek': 'PANORAMA [Dzieci]: Hurtownie zabawek',
    'panorama_logopedzi': 'PANORAMA [Dzieci]: Logopedzi',
    'panorama_odzie%C5%BC_dzieci%C4%99ca': 'PANORAMA [Dzieci]: Odzież dziecięca',
    'panorama_opieka_nad_dzie%C4%87mi': 'PANORAMA [Dzieci]: Opieka nad dziećmi',
    'panorama_o%C5%9Brodki_adopcyjno_wychowawcze': 'PANORAMA [Dzieci]: Ośrodki adopcyjno-wychowawcze',
    'panorama_o%C5%9Brodki_szkolno_wychowawcze': 'PANORAMA [Dzieci]: Ośrodki szkolno-wychowawcze',
    'panorama_o%C5%9Brodki_wychowawcze': 'PANORAMA [Dzieci]: Ośrodki wychowawcze',
    'panorama_parki_rozrywki': 'PANORAMA [Dzieci]: Parki rozrywki',
    'panorama_produkcja_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Dzieci]: Produkcja artykułów papierniczych',
    'panorama_produkcja_zabawek': 'PANORAMA [Dzieci]: Produkcja zabawek',
    'panorama_projektowanie_i_monta%C5%BC_plac%C3%B3w_zabaw': 'PANORAMA [Dzieci]: Projektowanie i montaż placów zabaw',
    'panorama_przedszkola_prywatne': 'PANORAMA [Dzieci]: Przedszkola prywatne',
    'panorama_przedszkola_publiczne': 'PANORAMA [Dzieci]: Przedszkola publiczne',
    'panorama_sale_zabaw': 'PANORAMA [Dzieci]: Sale zabaw',
    'panorama_sklepy_z_zabawkami': 'PANORAMA [Dzieci]: Sklepy z zabawkami',
    'panorama_zabawki_edukacyjne': 'PANORAMA [Dzieci]: Zabawki edukacyjne',
    'panorama_%C5%9Bwietlice_%C5%9Brodowiskowe': 'PANORAMA [Dzieci]: Świetlice środowiskowe',
    'panorama_%C5%BC%C5%82obki_prywatne': 'PANORAMA [Dzieci]: Żłobki prywatne',
    'panorama_%C5%BC%C5%82obki_publiczne': 'PANORAMA [Dzieci]: Żłobki publiczne',
    'panorama_banki': 'PANORAMA [Finanse i ubezpieczenia]: Banki',
    'panorama_bankomaty': 'PANORAMA [Finanse i ubezpieczenia]: Bankomaty',
    'panorama_biura_rachunkowe': 'PANORAMA [Finanse i ubezpieczenia]: Biura rachunkowe',
    'panorama_doradztwo_finansowe_i_kredytowe': 'PANORAMA [Finanse i ubezpieczenia]: Doradztwo finansowe i kredytowe',
    'panorama_doradztwo_podatkowe': 'PANORAMA [Finanse i ubezpieczenia]: Doradztwo podatkowe',
    'panorama_fundusze_emerytalne': 'PANORAMA [Finanse i ubezpieczenia]: Fundusze emerytalne',
    'panorama_fundusze_inwestycyjne': 'PANORAMA [Finanse i ubezpieczenia]: Fundusze inwestycyjne',
    'panorama_gie%C5%82dy': 'PANORAMA [Finanse i ubezpieczenia]: Giełdy',
    'panorama_kantory': 'PANORAMA [Finanse i ubezpieczenia]: Kantory',
    'panorama_karty_kredytowe_p%C5%82atnicze_i_programy_lojalno%C5%9Bciowe': 'PANORAMA [Finanse i ubezpieczenia]: Karty kredytowe, płatnicze i programy lojalnościowe',
    'panorama_kredyty_i_finansowanie': 'PANORAMA [Finanse i ubezpieczenia]: Kredyty i finansowanie',
    'panorama_leasing': 'PANORAMA [Finanse i ubezpieczenia]: Leasing',
    'panorama_maklerzy_gie%C5%82dowi': 'PANORAMA [Finanse i ubezpieczenia]: Maklerzy giełdowi',
    'panorama_odd%C5%82u%C5%BCanie': 'PANORAMA [Finanse i ubezpieczenia]: Oddłużanie',
    'panorama_po%C5%9Brednicy_ubezpieczeniowi': 'PANORAMA [Finanse i ubezpieczenia]: Pośrednicy ubezpieczeniowi',
    'panorama_sprz%C4%99t_i_wyposa%C5%BCenie_bank%C3%B3w': 'PANORAMA [Finanse i ubezpieczenia]: Sprzęt i wyposażenie banków',
    'panorama_ubezpieczenia': 'PANORAMA [Finanse i ubezpieczenia]: Ubezpieczenia',
    'panorama_ubezpieczenia_spo%C5%82eczne': 'PANORAMA [Finanse i ubezpieczenia]: Ubezpieczenia społeczne',
    'panorama_windykacja_d%C5%82ug%C3%B3w_i_nale%C5%BCno%C5%9Bci': 'PANORAMA [Finanse i ubezpieczenia]: Windykacja długów i należności',
    'panorama_administracja_obiekt%C3%B3w_u%C5%BCyteczno%C5%9Bci_publicznej': 'PANORAMA [Instytucje, urzędy]: Administracja obiektów użyteczności publicznej',
    'panorama_agencje_i_sk%C5%82ady_celne': 'PANORAMA [Instytucje, urzędy]: Agencje i składy celne',
    'panorama_ambasady': 'PANORAMA [Instytucje, urzędy]: Ambasady',
    'panorama_archiwa_i_archiwizacja_danych': 'PANORAMA [Instytucje, urzędy]: Archiwa i archiwizacja danych',
    'panorama_biblioteki_i_czytelnie': 'PANORAMA [Instytucje, urzędy]: Biblioteki i czytelnie',
    'panorama_dobry_start___300_z%C5%82_dla_ucznia': 'PANORAMA [Instytucje, urzędy]: Dobry Start - 300 zł dla ucznia',
    'panorama_fundacje_i_instytucje_charytatywne': 'PANORAMA [Instytucje, urzędy]: Fundacje i instytucje charytatywne',
    'panorama_inkubatory_przedsi%C4%99biorczo%C5%9Bci': 'PANORAMA [Instytucje, urzędy]: Inkubatory przedsiębiorczości',
    'panorama_internaty_i_akademiki': 'PANORAMA [Instytucje, urzędy]: Internaty i akademiki',
    'panorama_konserwacja_zabytk%C3%B3w': 'PANORAMA [Instytucje, urzędy]: Konserwacja zabytków',
    'panorama_militaria': 'PANORAMA [Instytucje, urzędy]: Militaria',
    'panorama_narodowy_fundusz_zdrowia': 'PANORAMA [Instytucje, urzędy]: Narodowy Fundusz Zdrowia',
    'panorama_ochrona_%C5%9Brodowiska': 'PANORAMA [Instytucje, urzędy]: Ochrona środowiska',
    'panorama_o%C5%9Brodki_adopcyjno_wychowawcze': 'PANORAMA [Instytucje, urzędy]: Ośrodki adopcyjno-wychowawcze',
    'panorama_o%C5%9Brodki_wychowawcze': 'PANORAMA [Instytucje, urzędy]: Ośrodki wychowawcze',
    'panorama_poczta_i_urz%C4%99dy_pocztowe': 'PANORAMA [Instytucje, urzędy]: Poczta i urzędy pocztowe',
    'panorama_pogotowie_ratunkowe': 'PANORAMA [Instytucje, urzędy]: Pogotowie ratunkowe',
    'panorama_policja': 'PANORAMA [Instytucje, urzędy]: Policja',
    'panorama_prokuratury': 'PANORAMA [Instytucje, urzędy]: Prokuratury',
    'panorama_rodzina_500_plus': 'PANORAMA [Instytucje, urzędy]: Rodzina 500 Plus',
    'panorama_rzecznicy_patentowi': 'PANORAMA [Instytucje, urzędy]: Rzecznicy patentowi',
    'panorama_so%C5%82ectwa': 'PANORAMA [Instytucje, urzędy]: Sołectwa',
    'panorama_specjalne_strefy_ekonomiczne': 'PANORAMA [Instytucje, urzędy]: Specjalne strefy ekonomiczne',
    'panorama_sp%C3%B3%C5%82dzielnie_i_administracje_mieszkaniowe': 'PANORAMA [Instytucje, urzędy]: Spółdzielnie i administracje mieszkaniowe',
    'panorama_stacje_sanitarno_epidemiologiczne': 'PANORAMA [Instytucje, urzędy]: Stacje sanitarno-epidemiologiczne',
    'panorama_starostwa_powiatowe': 'PANORAMA [Instytucje, urzędy]: Starostwa powiatowe',
    'panorama_stowarzyszenia_kluby_i_zwi%C4%85zki': 'PANORAMA [Instytucje, urzędy]: Stowarzyszenia, kluby i związki',
    'panorama_stra%C5%BC_miejska': 'PANORAMA [Instytucje, urzędy]: Straż miejska',
    'panorama_stra%C5%BC_po%C5%BCarna': 'PANORAMA [Instytucje, urzędy]: Straż pożarna',
    'panorama_syndycy_i_likwidatorzy': 'PANORAMA [Instytucje, urzędy]: Syndycy i likwidatorzy',
    'panorama_s%C4%85dy': 'PANORAMA [Instytucje, urzędy]: Sądy',
    'panorama_telefony_alarmowe': 'PANORAMA [Instytucje, urzędy]: Telefony alarmowe',
    'panorama_telefony_zaufania': 'PANORAMA [Instytucje, urzędy]: Telefony zaufania',
    'panorama_unia_europejska': 'PANORAMA [Instytucje, urzędy]: Unia Europejska',
    'panorama_urz%C4%99dy_celne': 'PANORAMA [Instytucje, urzędy]: Urzędy celne',
    'panorama_urz%C4%99dy_centralne': 'PANORAMA [Instytucje, urzędy]: Urzędy centralne',
    'panorama_urz%C4%99dy_marsza%C5%82kowskie': 'PANORAMA [Instytucje, urzędy]: Urzędy marszałkowskie',
    'panorama_urz%C4%99dy_miast_i_gmin': 'PANORAMA [Instytucje, urzędy]: Urzędy miast i gmin',
    'panorama_urz%C4%99dy_pracy': 'PANORAMA [Instytucje, urzędy]: Urzędy pracy',
    'panorama_urz%C4%99dy_skarbowe': 'PANORAMA [Instytucje, urzędy]: Urzędy skarbowe',
    'panorama_urz%C4%99dy_terenowe': 'PANORAMA [Instytucje, urzędy]: Urzędy terenowe',
    'panorama_urz%C4%99dy_wojew%C3%B3dzkie': 'PANORAMA [Instytucje, urzędy]: Urzędy wojewódzkie',
    'panorama_wi%C4%99zienia_i_zak%C5%82ady_penitencjarne': 'PANORAMA [Instytucje, urzędy]: Więzienia i zakłady penitencjarne',
    'panorama_zarz%C4%85dy_cmentarzy_i_cmentarze': 'PANORAMA [Instytucje, urzędy]: Zarządy cmentarzy i cmentarze',
    'panorama_akcesoria_do_komputer%C3%B3w': 'PANORAMA [Kancelaria]: Akcesoria do komputerów',
    'panorama_artyku%C5%82y_biurowe': 'PANORAMA [Kancelaria]: Artykuły biurowe',
    'panorama_artyku%C5%82y_i_sprz%C4%99t_bhp': 'PANORAMA [Kancelaria]: Artykuły i sprzęt BHP',
    'panorama_artyku%C5%82y_papiernicze': 'PANORAMA [Kancelaria]: Artykuły papiernicze',
    'panorama_artyku%C5%82y_szkolne': 'PANORAMA [Kancelaria]: Artykuły szkolne',
    'panorama_audyty_oprogramowania_i_sprz%C4%99tu_komputerowego': 'PANORAMA [Kancelaria]: Audyty oprogramowania i sprzętu komputerowego',
    'panorama_cz%C4%99%C5%9Bci_komputerowe': 'PANORAMA [Kancelaria]: Części komputerowe',
    'panorama_drukarki_i_urz%C4%85dzenia_peryferyjne': 'PANORAMA [Kancelaria]: Drukarki i urządzenia peryferyjne',
    'panorama_etykiety_i_naklejki': 'PANORAMA [Kancelaria]: Etykiety i naklejki',
    'panorama_folie_i_foliowanie': 'PANORAMA [Kancelaria]: Folie i foliowanie',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_biurowych': 'PANORAMA [Kancelaria]: Hurtownie artykułów biurowych',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Kancelaria]: Hurtownie artykułów papierniczych',
    'panorama_hurtownie_dywan%C3%B3w_i_wyk%C5%82adzin': 'PANORAMA [Kancelaria]: Hurtownie dywanów i wykładzin',
    'panorama_ksero': 'PANORAMA [Kancelaria]: Ksero',
    'panorama_meble_biurowe': 'PANORAMA [Kancelaria]: Meble biurowe',
    'panorama_meble_metalowe': 'PANORAMA [Kancelaria]: Meble metalowe',
    'panorama_oprogramowanie_komputerowe': 'PANORAMA [Kancelaria]: Oprogramowanie komputerowe',
    'panorama_papier': 'PANORAMA [Kancelaria]: Papier',
    'panorama_piecz%C4%85tki_i_stemple': 'PANORAMA [Kancelaria]: Pieczątki i stemple',
    'panorama_pomiary_konsultacje_i_badania_bhp': 'PANORAMA [Kancelaria]: Pomiary, konsultacje i badania BHP',
    'panorama_producenci_artyku%C5%82%C3%B3w_biurowych': 'PANORAMA [Kancelaria]: Producenci artykułów biurowych',
    'panorama_produkcja_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Kancelaria]: Produkcja artykułów papierniczych',
    'panorama_serwis_komputer%C3%B3w': 'PANORAMA [Kancelaria]: Serwis komputerów',
    'panorama_serwis_kserokopiarek': 'PANORAMA [Kancelaria]: Serwis kserokopiarek',
    'panorama_sieci_komputerowe_i_integracja_system%C3%B3w': 'PANORAMA [Kancelaria]: Sieci komputerowe i integracja systemów',
    'panorama_sprzeda%C5%BC_komputer%C3%B3w': 'PANORAMA [Kancelaria]: Sprzedaż komputerów',
    'panorama_sprz%C4%99t_i_centrale_telefoniczne': 'PANORAMA [Kancelaria]: Sprzęt i centrale telefoniczne',
    'panorama_systemy_audiowizualne': 'PANORAMA [Kancelaria]: Systemy audiowizualne',
    'panorama_systemy_i_technologie_multimedialne': 'PANORAMA [Kancelaria]: Systemy i technologie multimedialne',
    'panorama_ta%C5%9Bmy_samoprzylepne': 'PANORAMA [Kancelaria]: Taśmy samoprzylepne',
    'panorama_wynajem_i_sprzeda%C5%BC_kserokopiarek': 'PANORAMA [Kancelaria]: Wynajem i sprzedaż kserokopiarek',
    'panorama_wyposa%C5%BCenie_biur': 'PANORAMA [Kancelaria]: Wyposażenie biur',
    'panorama_zaopatrzenie_biur': 'PANORAMA [Kancelaria]: Zaopatrzenie biur',
    'panorama_agenci_okr%C4%99towi_i_morscy': 'PANORAMA [Motoryzacja i transport]: Agenci okrętowi i morscy',
    'panorama_alarmy_samochodowe': 'PANORAMA [Motoryzacja i transport]: Alarmy samochodowe',
    'panorama_amortyzatory_samochodowe': 'PANORAMA [Motoryzacja i transport]: Amortyzatory samochodowe',
    'panorama_artyku%C5%82y_pogrzebowe': 'PANORAMA [Motoryzacja i transport]: Artykuły pogrzebowe',
    'panorama_autoz%C5%82om': 'PANORAMA [Motoryzacja i transport]: Autozłom',
    'panorama_blacharstwo_i_lakiernictwo': 'PANORAMA [Motoryzacja i transport]: Blacharstwo i lakiernictwo',
    'panorama_budowa_i_wyposa%C5%BCenie_gara%C5%BCy': 'PANORAMA [Motoryzacja i transport]: Budowa i wyposażenie garaży',
    'panorama_car_audio': 'PANORAMA [Motoryzacja i transport]: Car audio',
    'panorama_dealerzy_i_sprzeda%C5%BC_samochod%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Dealerzy i sprzedaż samochodów',
    'panorama_elektromechanika': 'PANORAMA [Motoryzacja i transport]: Elektromechanika',
    'panorama_elektronika_samochodowa': 'PANORAMA [Motoryzacja i transport]: Elektronika samochodowa',
    'panorama_folie_i_foliowanie': 'PANORAMA [Motoryzacja i transport]: Folie i foliowanie',
    'panorama_gie%C5%82dy': 'PANORAMA [Motoryzacja i transport]: Giełdy',
    'panorama_haki_holownicze': 'PANORAMA [Motoryzacja i transport]: Haki holownicze',
    'panorama_hurtownie_cz%C4%99%C5%9Bci_samochodowych': 'PANORAMA [Motoryzacja i transport]: Hurtownie części samochodowych',
    'panorama_instalacja_system%C3%B3w_alarmowych': 'PANORAMA [Motoryzacja i transport]: Instalacja systemów alarmowych',
    'panorama_kampery_i_przyczepy_kempingowe': 'PANORAMA [Motoryzacja i transport]: Kampery i przyczepy kempingowe',
    'panorama_klimatyzacja_samochodowa': 'PANORAMA [Motoryzacja i transport]: Klimatyzacja samochodowa',
    'panorama_komunikacja_i_przewozy_pasa%C5%BCerskie': 'PANORAMA [Motoryzacja i transport]: Komunikacja i przewozy pasażerskie',
    'panorama_kosmetyki_samochodowe': 'PANORAMA [Motoryzacja i transport]: Kosmetyki samochodowe',
    'panorama_ko%C5%82a_i_zestawy_jezdne': 'PANORAMA [Motoryzacja i transport]: Koła i zestawy jezdne',
    'panorama_lakiery_samochodowe': 'PANORAMA [Motoryzacja i transport]: Lakiery samochodowe',
    'panorama_linie_lotnicze': 'PANORAMA [Motoryzacja i transport]: Linie lotnicze',
    'panorama_lotniska': 'PANORAMA [Motoryzacja i transport]: Lotniska',
    'panorama_mechanika_samochodowa': 'PANORAMA [Motoryzacja i transport]: Mechanika samochodowa',
    'panorama_mobilne_myjnie_samochodowe': 'PANORAMA [Motoryzacja i transport]: Mobilne myjnie samochodowe',
    'panorama_motocykle_skutery_i_quady': 'PANORAMA [Motoryzacja i transport]: Motocykle, skutery i quady',
    'panorama_myjnie_samochodowe': 'PANORAMA [Motoryzacja i transport]: Myjnie samochodowe',
    'panorama_naczepy_samochodowe': 'PANORAMA [Motoryzacja i transport]: Naczepy samochodowe',
    'panorama_nawigacja_i_lokalizacja_satelitarna': 'PANORAMA [Motoryzacja i transport]: Nawigacja i lokalizacja satelitarna',
    'panorama_oklejanie_samochod%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Oklejanie samochodów',
    'panorama_operatorzy_logistyczni': 'PANORAMA [Motoryzacja i transport]: Operatorzy logistyczni',
    'panorama_paliwa': 'PANORAMA [Motoryzacja i transport]: Paliwa',
    'panorama_parkingi': 'PANORAMA [Motoryzacja i transport]: Parkingi',
    'panorama_plandeki': 'PANORAMA [Motoryzacja i transport]: Plandeki',
    'panorama_pojazdy_specjalistyczne': 'PANORAMA [Motoryzacja i transport]: Pojazdy specjalistyczne',
    'panorama_pojazdy_zabytkowe_i_doro%C5%BCki': 'PANORAMA [Motoryzacja i transport]: Pojazdy zabytkowe i dorożki',
    'panorama_pomoc_drogowa': 'PANORAMA [Motoryzacja i transport]: Pomoc drogowa',
    'panorama_produkcja_cz%C4%99%C5%9Bci_samochodowych': 'PANORAMA [Motoryzacja i transport]: Produkcja części samochodowych',
    'panorama_produkcja_i_sprzeda%C5%BC_opon': 'PANORAMA [Motoryzacja i transport]: Produkcja i sprzedaż opon',
    'panorama_przek%C5%82adnie': 'PANORAMA [Motoryzacja i transport]: Przekładnie',
    'panorama_przeprowadzki': 'PANORAMA [Motoryzacja i transport]: Przeprowadzki',
    'panorama_przewozy_autokarowe': 'PANORAMA [Motoryzacja i transport]: Przewozy autokarowe',
    'panorama_przewozy_os%C3%B3b_niepe%C5%82nosprawnych': 'PANORAMA [Motoryzacja i transport]: Przewozy osób niepełnosprawnych',
    'panorama_przyczepy_samochodowe': 'PANORAMA [Motoryzacja i transport]: Przyczepy samochodowe',
    'panorama_punkty_%C5%82adowania_samochod%C3%B3w_elektrycznych': 'PANORAMA [Motoryzacja i transport]: Punkty ładowania samochodów elektrycznych',
    'panorama_regeneracja_cz%C4%99%C5%9Bci_samochodowych': 'PANORAMA [Motoryzacja i transport]: Regeneracja części samochodowych',
    'panorama_rejestracja_pojazd%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Rejestracja pojazdów',
    'panorama_samochodowe_agregaty_ch%C5%82odnicze': 'PANORAMA [Motoryzacja i transport]: Samochodowe agregaty chłodnicze',
    'panorama_samochodowe_instalacje_gazowe': 'PANORAMA [Motoryzacja i transport]: Samochodowe instalacje gazowe',
    'panorama_samochody_u%C5%BCywane': 'PANORAMA [Motoryzacja i transport]: Samochody używane',
    'panorama_serwis_samochod%C3%B3w_ci%C4%99%C5%BCarowych_i_dostawczych': 'PANORAMA [Motoryzacja i transport]: Serwis samochodów ciężarowych i dostawczych',
    'panorama_silniki_i_pr%C4%85dnice': 'PANORAMA [Motoryzacja i transport]: Silniki i prądnice',
    'panorama_skrzynie_bieg%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Skrzynie biegów',
    'panorama_spedycja': 'PANORAMA [Motoryzacja i transport]: Spedycja',
    'panorama_spedycja_mi%C4%99dzynarodowa': 'PANORAMA [Motoryzacja i transport]: Spedycja międzynarodowa',
    'panorama_sprzeda%C5%BC_cz%C4%99%C5%9Bci_samochodowych': 'PANORAMA [Motoryzacja i transport]: Sprzedaż części samochodowych',
    'panorama_sprzeda%C5%BC_i_rezerwacja_bilet%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Sprzedaż i rezerwacja biletów',
    'panorama_sprzeda%C5%BC_samochod%C3%B3w_ci%C4%99%C5%BCarowych_i_dostawczych': 'PANORAMA [Motoryzacja i transport]: Sprzedaż samochodów ciężarowych i dostawczych',
    'panorama_sprz%C4%99t_lotniczy': 'PANORAMA [Motoryzacja i transport]: Sprzęt lotniczy',
    'panorama_sprz%C4%99t_torowy_i_kolejowy': 'PANORAMA [Motoryzacja i transport]: Sprzęt torowy i kolejowy',
    'panorama_stacje_diagnostyczne_i_przegl%C4%85dy_techniczne': 'PANORAMA [Motoryzacja i transport]: Stacje diagnostyczne i przeglądy techniczne',
    'panorama_stacje_obs%C5%82ugi_i_warsztaty_samochodowe': 'PANORAMA [Motoryzacja i transport]: Stacje obsługi i warsztaty samochodowe',
    'panorama_stacje_paliw': 'PANORAMA [Motoryzacja i transport]: Stacje paliw',
    'panorama_szyberdachy': 'PANORAMA [Motoryzacja i transport]: Szyberdachy',
    'panorama_szyby_samochodowe': 'PANORAMA [Motoryzacja i transport]: Szyby samochodowe',
    'panorama_tablice_rejestracyjne': 'PANORAMA [Motoryzacja i transport]: Tablice rejestracyjne',
    'panorama_tabor_kolejowy': 'PANORAMA [Motoryzacja i transport]: Tabor kolejowy',
    'panorama_taksometry_tachometry_i_tachografy': 'PANORAMA [Motoryzacja i transport]: Taksometry, tachometry i tachografy',
    'panorama_tapicerka_i_pokrowce_samochodowe': 'PANORAMA [Motoryzacja i transport]: Tapicerka i pokrowce samochodowe',
    'panorama_taxi': 'PANORAMA [Motoryzacja i transport]: Taxi',
    'panorama_transport_kolejowy': 'PANORAMA [Motoryzacja i transport]: Transport kolejowy',
    'panorama_transport_lotniczy': 'PANORAMA [Motoryzacja i transport]: Transport lotniczy',
    'panorama_transport_mi%C4%99dzynarodowy': 'PANORAMA [Motoryzacja i transport]: Transport międzynarodowy',
    'panorama_transport_morski_i_%C5%9Br%C3%B3dl%C4%85dowy': 'PANORAMA [Motoryzacja i transport]: Transport morski i śródlądowy',
    'panorama_transport_nadgabarytowy': 'PANORAMA [Motoryzacja i transport]: Transport nadgabarytowy',
    'panorama_transport_samochodowy': 'PANORAMA [Motoryzacja i transport]: Transport samochodowy',
    'panorama_transport_%C5%82adunk%C3%B3w_niebezpiecznych': 'PANORAMA [Motoryzacja i transport]: Transport ładunków niebezpiecznych',
    'panorama_tuning_samochod%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Tuning samochodów',
    'panorama_turbospr%C4%99%C5%BCarki': 'PANORAMA [Motoryzacja i transport]: Turbosprężarki',
    'panorama_t%C5%82umiki_i_uk%C5%82ady_wydechowe': 'PANORAMA [Motoryzacja i transport]: Tłumiki i układy wydechowe',
    'panorama_urz%C4%85dzenia_parkingowe': 'PANORAMA [Motoryzacja i transport]: Urządzenia parkingowe',
    'panorama_us%C5%82ugi_portowe_i_prze%C5%82adunkowe': 'PANORAMA [Motoryzacja i transport]: Usługi portowe i przeładunkowe',
    'panorama_u%C5%BCywane_cz%C4%99%C5%9Bci_samochodowe': 'PANORAMA [Motoryzacja i transport]: Używane części samochodowe',
    'panorama_wulkanizacja_i_serwis_opon': 'PANORAMA [Motoryzacja i transport]: Wulkanizacja i serwis opon',
    'panorama_wyci%C4%85gi_i_koleje_linowe': 'PANORAMA [Motoryzacja i transport]: Wyciągi i koleje linowe',
    'panorama_wynajem_samochod%C3%B3w_ci%C4%99%C5%BCarowych_i_dostawczych': 'PANORAMA [Motoryzacja i transport]: Wynajem samochodów ciężarowych i dostawczych',
    'panorama_wynajem_samochod%C3%B3w_i_zarz%C4%85dzanie_flot%C4%85': 'PANORAMA [Motoryzacja i transport]: Wynajem samochodów i zarządzanie flotą',
    'panorama_wynajem_serwis_i_sprzeda%C5%BC_autobus%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Wynajem, serwis i sprzedaż autobusów',
    'panorama_wyposa%C5%BCenie_dodatkowe_samochod%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Wyposażenie dodatkowe samochodów',
    'panorama_wyposa%C5%BCenie_warsztat%C3%B3w_i_myjni_samochodowych': 'PANORAMA [Motoryzacja i transport]: Wyposażenie warsztatów i myjni samochodowych',
    'panorama_zabezpieczenia_antykorozyjne_samochod%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Zabezpieczenia antykorozyjne samochodów',
    'panorama_zabudowy_nadwozi_samochodowych': 'PANORAMA [Motoryzacja i transport]: Zabudowy nadwozi samochodowych',
    'panorama_znakowanie_i_monitorowanie_samochod%C3%B3w': 'PANORAMA [Motoryzacja i transport]: Znakowanie i monitorowanie samochodów',
    'panorama_antykwariaty': 'PANORAMA [Nauka]: Antykwariaty',
    'panorama_artyku%C5%82y_biurowe': 'PANORAMA [Nauka]: Artykuły biurowe',
    'panorama_artyku%C5%82y_papiernicze': 'PANORAMA [Nauka]: Artykuły papiernicze',
    'panorama_artyku%C5%82y_szkolne': 'PANORAMA [Nauka]: Artykuły szkolne',
    'panorama_badania_i_us%C5%82ugi_archeologiczne': 'PANORAMA [Nauka]: Badania i usługi archeologiczne',
    'panorama_biblioteki_i_czytelnie': 'PANORAMA [Nauka]: Biblioteki i czytelnie',
    'panorama_geolodzy_i_geofizycy': 'PANORAMA [Nauka]: Geolodzy i geofizycy',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_biurowych': 'PANORAMA [Nauka]: Hurtownie artykułów biurowych',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Nauka]: Hurtownie artykułów papierniczych',
    'panorama_hurtownie_ksi%C4%85%C5%BCek': 'PANORAMA [Nauka]: Hurtownie książek',
    'panorama_instrumenty_optyczne': 'PANORAMA [Nauka]: Instrumenty optyczne',
    'panorama_instytuty_i_o%C5%9Brodki_badawcze': 'PANORAMA [Nauka]: Instytuty i ośrodki badawcze',
    'panorama_internaty_i_akademiki': 'PANORAMA [Nauka]: Internaty i akademiki',
    'panorama_korepetycje': 'PANORAMA [Nauka]: Korepetycje',
    'panorama_ksi%C4%99garnie': 'PANORAMA [Nauka]: Księgarnie',
    'panorama_kursy_i_nauka_jazdy': 'PANORAMA [Nauka]: Kursy i nauka jazdy',
    'panorama_kursy_i_szkolenia': 'PANORAMA [Nauka]: Kursy i szkolenia',
    'panorama_o%C5%9Brodki_szkolno_wychowawcze': 'PANORAMA [Nauka]: Ośrodki szkolno-wychowawcze',
    'panorama_producenci_artyku%C5%82%C3%B3w_biurowych': 'PANORAMA [Nauka]: Producenci artykułów biurowych',
    'panorama_produkcja_artyku%C5%82%C3%B3w_papierniczych': 'PANORAMA [Nauka]: Produkcja artykułów papierniczych',
    'panorama_prywatne_szko%C5%82y_podstawowe': 'PANORAMA [Nauka]: Prywatne szkoły podstawowe',
    'panorama_prywatne_szko%C5%82y_pomaturalne_i_policealne': 'PANORAMA [Nauka]: Prywatne szkoły pomaturalne i policealne',
    'panorama_prywatne_szko%C5%82y_ponadgimnazjalne': 'PANORAMA [Nauka]: Prywatne szkoły ponadgimnazjalne',
    'panorama_prywatne_uniwersytety_i_szko%C5%82y_wy%C5%BCsze': 'PANORAMA [Nauka]: Prywatne uniwersytety i szkoły wyższe',
    'panorama_przedszkola_prywatne': 'PANORAMA [Nauka]: Przedszkola prywatne',
    'panorama_przedszkola_publiczne': 'PANORAMA [Nauka]: Przedszkola publiczne',
    'panorama_publiczne_szko%C5%82y_podstawowe': 'PANORAMA [Nauka]: Publiczne szkoły podstawowe',
    'panorama_publiczne_szko%C5%82y_pomaturalne_i_policealne': 'PANORAMA [Nauka]: Publiczne szkoły pomaturalne i policealne',
    'panorama_publiczne_uniwersytety_i_szko%C5%82y_wy%C5%BCsze': 'PANORAMA [Nauka]: Publiczne uniwersytety i szkoły wyższe',
    'panorama_sprz%C4%99t_i_wyposa%C5%BCenie_laboratori%C3%B3w': 'PANORAMA [Nauka]: Sprzęt i wyposażenie laboratoriów',
    'panorama_szkolenia_zawodowe': 'PANORAMA [Nauka]: Szkolenia zawodowe',
    'panorama_szko%C5%82y_artystyczne': 'PANORAMA [Nauka]: Szkoły artystyczne',
    'panorama_szko%C5%82y_i_kursy_j%C4%99zykowe': 'PANORAMA [Nauka]: Szkoły i kursy językowe',
    'panorama_szko%C5%82y_ponadpodstawowe': 'PANORAMA [Nauka]: Szkoły ponadpodstawowe',
    'panorama_szko%C5%82y_ta%C5%84ca': 'PANORAMA [Nauka]: Szkoły tańca',
    'panorama_ta%C5%9Bmy_samoprzylepne': 'PANORAMA [Nauka]: Taśmy samoprzylepne',
    'panorama_%C5%BC%C5%82obki_publiczne': 'PANORAMA [Nauka]: Żłobki publiczne',
    'panorama_akcesoria_do_but%C3%B3w': 'PANORAMA [Odzież i tekstylia]: Akcesoria do butów',
    'panorama_akcesoria_szewskie_i_kaletnicze': 'PANORAMA [Odzież i tekstylia]: Akcesoria szewskie i kaletnicze',
    'panorama_artyku%C5%82y_dzieci%C4%99ce': 'PANORAMA [Odzież i tekstylia]: Artykuły dziecięce',
    'panorama_bielizna': 'PANORAMA [Odzież i tekstylia]: Bielizna',
    'panorama_czapki_i_kapelusze': 'PANORAMA [Odzież i tekstylia]: Czapki i kapelusze',
    'panorama_flagi_i_artyku%C5%82y_propagandowe': 'PANORAMA [Odzież i tekstylia]: Flagi i artykuły propagandowe',
    'panorama_futra_i_ko%C5%BCuchy': 'PANORAMA [Odzież i tekstylia]: Futra i kożuchy',
    'panorama_galanteria': 'PANORAMA [Odzież i tekstylia]: Galanteria',
    'panorama_hafciarstwo': 'PANORAMA [Odzież i tekstylia]: Hafciarstwo',
    'panorama_hurtownie_bielizny': 'PANORAMA [Odzież i tekstylia]: Hurtownie bielizny',
    'panorama_hurtownie_obuwia': 'PANORAMA [Odzież i tekstylia]: Hurtownie obuwia',
    'panorama_hurtownie_odzie%C5%BCy': 'PANORAMA [Odzież i tekstylia]: Hurtownie odzieży',
    'panorama_hurtownie_tkanin_i_dzianin': 'PANORAMA [Odzież i tekstylia]: Hurtownie tkanin i dzianin',
    'panorama_kaletnictwo_i_rymarstwo': 'PANORAMA [Odzież i tekstylia]: Kaletnictwo i rymarstwo',
    'panorama_koszule_i_krawaty': 'PANORAMA [Odzież i tekstylia]: Koszule i krawaty',
    'panorama_krawiectwo': 'PANORAMA [Odzież i tekstylia]: Krawiectwo',
    'panorama_maszyny_dziewiarskie': 'PANORAMA [Odzież i tekstylia]: Maszyny dziewiarskie',
    'panorama_maszyny_hafciarskie': 'PANORAMA [Odzież i tekstylia]: Maszyny hafciarskie',
    'panorama_obrusy': 'PANORAMA [Odzież i tekstylia]: Obrusy',
    'panorama_odzie%C5%BC_damska': 'PANORAMA [Odzież i tekstylia]: Odzież damska',
    'panorama_odzie%C5%BC_dzieci%C4%99ca': 'PANORAMA [Odzież i tekstylia]: Odzież dziecięca',
    'panorama_odzie%C5%BC_m%C4%99ska': 'PANORAMA [Odzież i tekstylia]: Odzież męska',
    'panorama_odzie%C5%BC_robocza': 'PANORAMA [Odzież i tekstylia]: Odzież robocza',
    'panorama_odzie%C5%BC_sk%C3%B3rzana': 'PANORAMA [Odzież i tekstylia]: Odzież skórzana',
    'panorama_odzie%C5%BC_sportowa': 'PANORAMA [Odzież i tekstylia]: Odzież sportowa',
    'panorama_odzie%C5%BC_u%C5%BCywana': 'PANORAMA [Odzież i tekstylia]: Odzież używana',
    'panorama_parasole': 'PANORAMA [Odzież i tekstylia]: Parasole',
    'panorama_pasmanteria_i_dodatki_krawieckie': 'PANORAMA [Odzież i tekstylia]: Pasmanteria i dodatki krawieckie',
    'panorama_pralnie_i_farbiarnie': 'PANORAMA [Odzież i tekstylia]: Pralnie i farbiarnie',
    'panorama_produkcja_bielizny': 'PANORAMA [Odzież i tekstylia]: Produkcja bielizny',
    'panorama_produkcja_obuwia': 'PANORAMA [Odzież i tekstylia]: Produkcja obuwia',
    'panorama_produkcja_odzie%C5%BCy': 'PANORAMA [Odzież i tekstylia]: Produkcja odzieży',
    'panorama_produkcja_tkanin_i_dzianin': 'PANORAMA [Odzież i tekstylia]: Produkcja tkanin i dzianin',
    'panorama_puch_i_pierze': 'PANORAMA [Odzież i tekstylia]: Puch i pierze',
    'panorama_rajstopy_po%C5%84czochy_i_skarpety': 'PANORAMA [Odzież i tekstylia]: Rajstopy, pończochy i skarpety',
    'panorama_r%C4%99czniki_koce_i_po%C5%9Bciel': 'PANORAMA [Odzież i tekstylia]: Ręczniki, koce i pościel',
    'panorama_sklepy_obuwnicze': 'PANORAMA [Odzież i tekstylia]: Sklepy obuwnicze',
    'panorama_sklepy_odzie%C5%BCowe': 'PANORAMA [Odzież i tekstylia]: Sklepy odzieżowe',
    'panorama_sk%C3%B3ry_naturalne_i_sztuczne': 'PANORAMA [Odzież i tekstylia]: Skóry naturalne i sztuczne',
    'panorama_styli%C5%9Bci_wiza%C5%BCy%C5%9Bci_i_projektanci_mody': 'PANORAMA [Odzież i tekstylia]: Styliści, wizażyści i projektanci mody',
    'panorama_suknie_%C5%9Blubne_i_komunijne': 'PANORAMA [Odzież i tekstylia]: Suknie ślubne i komunijne',
    'panorama_szewc': 'PANORAMA [Odzież i tekstylia]: Szewc',
    'panorama_tkaniny_i_dzianiny': 'PANORAMA [Odzież i tekstylia]: Tkaniny i dzianiny',
    'panorama_urz%C4%85dzenia_do_produkcji_obuwia': 'PANORAMA [Odzież i tekstylia]: Urządzenia do produkcji obuwia',
    'panorama_we%C5%82na_i_prz%C4%99dza': 'PANORAMA [Odzież i tekstylia]: Wełna i przędza',
    'panorama_wyposa%C5%BCenie_pralni_i_farbiarni': 'PANORAMA [Odzież i tekstylia]: Wyposażenie pralni i farbiarni',
    'panorama_wypo%C5%BCyczalnie_stroj%C3%B3w': 'PANORAMA [Odzież i tekstylia]: Wypożyczalnie strojów',
    'panorama_pomys%C5%82_na_biznes': 'PANORAMA [Porady]: Pomysł na biznes',
    'panorama_aerozole': 'PANORAMA [Przemysł i energetyka]: Aerozole',
    'panorama_agregaty_pr%C4%85dotw%C3%B3rcze': 'PANORAMA [Przemysł i energetyka]: Agregaty prądotwórcze',
    'panorama_agregaty_komory_i_meble_ch%C5%82odnicze': 'PANORAMA [Przemysł i energetyka]: Agregaty, komory i meble chłodnicze',
    'panorama_akumulatory_i_baterie': 'PANORAMA [Przemysł i energetyka]: Akumulatory i baterie',
    'panorama_armatura_hydrauliczna': 'PANORAMA [Przemysł i energetyka]: Armatura hydrauliczna',
    'panorama_armatura_przemys%C5%82owa': 'PANORAMA [Przemysł i energetyka]: Armatura przemysłowa',
    'panorama_artyku%C5%82y_elektrotechniczne': 'PANORAMA [Przemysł i energetyka]: Artykuły elektrotechniczne',
    'panorama_artyku%C5%82y_metalowe': 'PANORAMA [Przemysł i energetyka]: Artykuły metalowe',
    'panorama_automatyka': 'PANORAMA [Przemysł i energetyka]: Automatyka',
    'panorama_autoz%C5%82om': 'PANORAMA [Przemysł i energetyka]: Autozłom',
    'panorama_badania_nieniszcz%C4%85ce': 'PANORAMA [Przemysł i energetyka]: Badania nieniszczące',
    'panorama_biopaliwa': 'PANORAMA [Przemysł i energetyka]: Biopaliwa',
    'panorama_bro%C5%84_i_amunicja': 'PANORAMA [Przemysł i energetyka]: Broń i amunicja',
    'panorama_brykiety_i_w%C4%99giel_drzewny': 'PANORAMA [Przemysł i energetyka]: Brykiety i węgiel drzewny',
    'panorama_budowa_i_sprz%C4%99t_drogowy': 'PANORAMA [Przemysł i energetyka]: Budowa i sprzęt drogowy',
    'panorama_budowa_i_wyposa%C5%BCenie_stacji_paliw': 'PANORAMA [Przemysł i energetyka]: Budowa i wyposażenie stacji paliw',
    'panorama_budowa_wyposa%C5%BCenie_i_remont_statk%C3%B3w': 'PANORAMA [Przemysł i energetyka]: Budowa, wyposażenie i remont statków',
    'panorama_budownictwo_kolejowe': 'PANORAMA [Przemysł i energetyka]: Budownictwo kolejowe',
    'panorama_budownictwo_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Budownictwo przemysłowe',
    'panorama_chemia_gospodarcza': 'PANORAMA [Przemysł i energetyka]: Chemia gospodarcza',
    'panorama_czyszcz%C4%85ce_urz%C4%85dzenia_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Czyszczące urządzenia przemysłowe',
    'panorama_czy%C5%9Bciwa_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Czyściwa przemysłowe',
    'panorama_drabiny': 'PANORAMA [Przemysł i energetyka]: Drabiny',
    'panorama_drewno': 'PANORAMA [Przemysł i energetyka]: Drewno',
    'panorama_drewno_budowlane': 'PANORAMA [Przemysł i energetyka]: Drewno budowlane',
    'panorama_drewno_opa%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Drewno opałowe',
    'panorama_drut_i_liny_stalowe': 'PANORAMA [Przemysł i energetyka]: Drut i liny stalowe',
    'panorama_dystrybucja_energii_elektrycznej': 'PANORAMA [Przemysł i energetyka]: Dystrybucja energii elektrycznej',
    'panorama_d%C5%BAwigi_i_%C5%BCurawie': 'PANORAMA [Przemysł i energetyka]: Dźwigi i żurawie',
    'panorama_elektrociep%C5%82ownie': 'PANORAMA [Przemysł i energetyka]: Elektrociepłownie',
    'panorama_elektronarz%C4%99dzia': 'PANORAMA [Przemysł i energetyka]: Elektronarzędzia',
    'panorama_energia_odnawialna': 'PANORAMA [Przemysł i energetyka]: Energia odnawialna',
    'panorama_farby_i_lakiery': 'PANORAMA [Przemysł i energetyka]: Farby i lakiery',
    'panorama_filtry': 'PANORAMA [Przemysł i energetyka]: Filtry',
    'panorama_formy_wtryskowe': 'PANORAMA [Przemysł i energetyka]: Formy wtryskowe',
    'panorama_galwanizacja': 'PANORAMA [Przemysł i energetyka]: Galwanizacja',
    'panorama_gaz_ziemny': 'PANORAMA [Przemysł i energetyka]: Gaz ziemny',
    'panorama_gazy_techniczne': 'PANORAMA [Przemysł i energetyka]: Gazy techniczne',
    'panorama_grzejnictwo_elektryczne': 'PANORAMA [Przemysł i energetyka]: Grzejnictwo elektryczne',
    'panorama_g%C3%B3rnicze_materia%C5%82y_wybuchowe': 'PANORAMA [Przemysł i energetyka]: Górnicze materiały wybuchowe',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_elektrotechnicznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie artykułów elektrotechnicznych',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_metalowych': 'PANORAMA [Przemysł i energetyka]: Hurtownie artykułów metalowych',
    'panorama_hurtownie_chemii_gospodarczej': 'PANORAMA [Przemysł i energetyka]: Hurtownie chemii gospodarczej',
    'panorama_hurtownie_cz%C4%99%C5%9Bci_elektronicznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie części elektronicznych',
    'panorama_hurtownie_farb_lakier%C3%B3w_i_emalii': 'PANORAMA [Przemysł i energetyka]: Hurtownie farb, lakierów i emalii',
    'panorama_hurtownie_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie urządzeń elektrycznych',
    'panorama_hurtownie_%C5%9Brodk%C3%B3w_chemicznych': 'PANORAMA [Przemysł i energetyka]: Hurtownie środków chemicznych',
    'panorama_hydraulika_si%C5%82owa': 'PANORAMA [Przemysł i energetyka]: Hydraulika siłowa',
    'panorama_hydrotechnika': 'PANORAMA [Przemysł i energetyka]: Hydrotechnika',
    'panorama_instalacja_i_serwis_ogrzewania': 'PANORAMA [Przemysł i energetyka]: Instalacja i serwis ogrzewania',
    'panorama_instalacje_i_urz%C4%85dzenia_energetyczne': 'PANORAMA [Przemysł i energetyka]: Instalacje i urządzenia energetyczne',
    'panorama_instalacje_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Instalacje przemysłowe',
    'panorama_inwestycje_budowlane': 'PANORAMA [Przemysł i energetyka]: Inwestycje budowlane',
    'panorama_kleje_i_%C5%BCywice': 'PANORAMA [Przemysł i energetyka]: Kleje i żywice',
    'panorama_kompresory': 'PANORAMA [Przemysł i energetyka]: Kompresory',
    'panorama_konstrukcje_aluminiowe': 'PANORAMA [Przemysł i energetyka]: Konstrukcje aluminiowe',
    'panorama_konstrukcje_stalowe': 'PANORAMA [Przemysł i energetyka]: Konstrukcje stalowe',
    'panorama_kontenery': 'PANORAMA [Przemysł i energetyka]: Kontenery',
    'panorama_kraty_pomostowe': 'PANORAMA [Przemysł i energetyka]: Kraty pomostowe',
    'panorama_laminaty': 'PANORAMA [Przemysł i energetyka]: Laminaty',
    'panorama_lasery': 'PANORAMA [Przemysł i energetyka]: Lasery',
    'panorama_liczniki_energii_elektrycznej': 'PANORAMA [Przemysł i energetyka]: Liczniki energii elektrycznej',
    'panorama_magnesy_i_elektromagnesy': 'PANORAMA [Przemysł i energetyka]: Magnesy i elektromagnesy',
    'panorama_malowanie_i_lakierowanie_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Malowanie i lakierowanie przemysłowe',
    'panorama_maszty_i_s%C5%82upy': 'PANORAMA [Przemysł i energetyka]: Maszty i słupy',
    'panorama_maszyny_do_obr%C3%B3bki_drewna': 'PANORAMA [Przemysł i energetyka]: Maszyny do obróbki drewna',
    'panorama_maszyny_do_obr%C3%B3bki_metali': 'PANORAMA [Przemysł i energetyka]: Maszyny do obróbki metali',
    'panorama_maszyny_dziewiarskie': 'PANORAMA [Przemysł i energetyka]: Maszyny dziewiarskie',
    'panorama_maszyny_i_sprz%C4%99t_g%C3%B3rniczy': 'PANORAMA [Przemysł i energetyka]: Maszyny i sprzęt górniczy',
    'panorama_maszyny_pakuj%C4%85ce': 'PANORAMA [Przemysł i energetyka]: Maszyny pakujące',
    'panorama_materia%C5%82y_do_spawania_i_zgrzewania': 'PANORAMA [Przemysł i energetyka]: Materiały do spawania i zgrzewania',
    'panorama_materia%C5%82y_drewnopochodne': 'PANORAMA [Przemysł i energetyka]: Materiały drewnopochodne',
    'panorama_materia%C5%82y_elektryczne': 'PANORAMA [Przemysł i energetyka]: Materiały elektryczne',
    'panorama_materia%C5%82y_ognioodporne': 'PANORAMA [Przemysł i energetyka]: Materiały ognioodporne',
    'panorama_materia%C5%82y_%C5%9Bcierne_i_polerskie': 'PANORAMA [Przemysł i energetyka]: Materiały ścierne i polerskie',
    'panorama_metale_nie%C5%BCelazne_i_kolorowe': 'PANORAMA [Przemysł i energetyka]: Metale nieżelazne i kolorowe',
    'panorama_metale_%C5%BCelazne': 'PANORAMA [Przemysł i energetyka]: Metale żelazne',
    'panorama_metalizowanie_i_powlekanie_tworzyw': 'PANORAMA [Przemysł i energetyka]: Metalizowanie i powlekanie tworzyw',
    'panorama_nape%C5%82nianie_butli_gazowych': 'PANORAMA [Przemysł i energetyka]: Napełnianie butli gazowych',
    'panorama_narz%C4%99dzia': 'PANORAMA [Przemysł i energetyka]: Narzędzia',
    'panorama_narz%C4%99dzia_pneumatyczne': 'PANORAMA [Przemysł i energetyka]: Narzędzia pneumatyczne',
    'panorama_obr%C3%B3bka_metali': 'PANORAMA [Przemysł i energetyka]: Obróbka metali',
    'panorama_obr%C3%B3bka_tworzyw_sztucznych': 'PANORAMA [Przemysł i energetyka]: Obróbka tworzyw sztucznych',
    'panorama_odlewnie': 'PANORAMA [Przemysł i energetyka]: Odlewnie',
    'panorama_ogrzewanie_elektryczne': 'PANORAMA [Przemysł i energetyka]: Ogrzewanie elektryczne',
    'panorama_okucia': 'PANORAMA [Przemysł i energetyka]: Okucia',
    'panorama_olej_opa%C5%82owy': 'PANORAMA [Przemysł i energetyka]: Olej opałowy',
    'panorama_oleje_techniczne_i_smary': 'PANORAMA [Przemysł i energetyka]: Oleje techniczne i smary',
    'panorama_opakowania': 'PANORAMA [Przemysł i energetyka]: Opakowania',
    'panorama_opakowania_foliowe': 'PANORAMA [Przemysł i energetyka]: Opakowania foliowe',
    'panorama_opakowania_jednorazowe': 'PANORAMA [Przemysł i energetyka]: Opakowania jednorazowe',
    'panorama_opakowania_z_tworzyw_sztucznych': 'PANORAMA [Przemysł i energetyka]: Opakowania z tworzyw sztucznych',
    'panorama_palety': 'PANORAMA [Przemysł i energetyka]: Palety',
    'panorama_paliwa_i_opa%C5%82_ekologiczny': 'PANORAMA [Przemysł i energetyka]: Paliwa i opał ekologiczny',
    'panorama_pasy_nap%C4%99dowe_i_transportuj%C4%85ce': 'PANORAMA [Przemysł i energetyka]: Pasy napędowe i transportujące',
    'panorama_piece': 'PANORAMA [Przemysł i energetyka]: Piece',
    'panorama_pirotechnika': 'PANORAMA [Przemysł i energetyka]: Pirotechnika',
    'panorama_pneumatyka_si%C5%82owa': 'PANORAMA [Przemysł i energetyka]: Pneumatyka siłowa',
    'panorama_podno%C5%9Bniki': 'PANORAMA [Przemysł i energetyka]: Podnośniki',
    'panorama_podzespo%C5%82y_elektroniczne': 'PANORAMA [Przemysł i energetyka]: Podzespoły elektroniczne',
    'panorama_pompy': 'PANORAMA [Przemysł i energetyka]: Pompy',
    'panorama_posadzki_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Posadzki przemysłowe',
    'panorama_prace_podwodne': 'PANORAMA [Przemysł i energetyka]: Prace podwodne',
    'panorama_producenci_farb_i_lakier%C3%B3w': 'PANORAMA [Przemysł i energetyka]: Producenci farb i lakierów',
    'panorama_produkcja_artyku%C5%82%C3%B3w_elektrotechnicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja artykułów elektrotechnicznych',
    'panorama_produkcja_artyku%C5%82%C3%B3w_higienicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja artykułów higienicznych',
    'panorama_produkcja_artyku%C5%82%C3%B3w_metalowych': 'PANORAMA [Przemysł i energetyka]: Produkcja artykułów metalowych',
    'panorama_produkcja_chemii_gospodarczej': 'PANORAMA [Przemysł i energetyka]: Produkcja chemii gospodarczej',
    'panorama_produkcja_cz%C4%99%C5%9Bci_elektronicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja części elektronicznych',
    'panorama_produkcja_kosmetyk%C3%B3w': 'PANORAMA [Przemysł i energetyka]: Produkcja kosmetyków',
    'panorama_produkcja_spr%C4%99%C5%BCyn': 'PANORAMA [Przemysł i energetyka]: Produkcja sprężyn',
    'panorama_produkcja_urz%C4%85dze%C5%84_elektronicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja urządzeń elektronicznych',
    'panorama_produkcja_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Przemysł i energetyka]: Produkcja urządzeń elektrycznych',
    'panorama_produkcja_zas%C5%82on_firanek_i_karniszy': 'PANORAMA [Przemysł i energetyka]: Produkcja zasłon, firanek i karniszy',
    'panorama_produkcja_%C5%9Brodk%C3%B3w_chemicznych': 'PANORAMA [Przemysł i energetyka]: Produkcja środków chemicznych',
    'panorama_przemys%C5%82owe_urz%C4%85dzenia_elektryczne': 'PANORAMA [Przemysł i energetyka]: Przemysłowe urządzenia elektryczne',
    'panorama_przeno%C5%9Bniki': 'PANORAMA [Przemysł i energetyka]: Przenośniki',
    'panorama_przewody_kable_i_%C5%9Bwiat%C5%82owody': 'PANORAMA [Przemysł i energetyka]: Przewody, kable i światłowody',
    'panorama_p%C4%99dzle_i_szczotki': 'PANORAMA [Przemysł i energetyka]: Pędzle i szczotki',
    'panorama_recykling': 'PANORAMA [Przemysł i energetyka]: Recykling',
    'panorama_rury': 'PANORAMA [Przemysł i energetyka]: Rury',
    'panorama_sejfy_i_kasy_pancerne': 'PANORAMA [Przemysł i energetyka]: Sejfy i kasy pancerne',
    'panorama_serwis_urz%C4%85dze%C5%84_ch%C5%82odniczych': 'PANORAMA [Przemysł i energetyka]: Serwis urządzeń chłodniczych',
    'panorama_serwis_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA [Przemysł i energetyka]: Serwis urządzeń elektrycznych',
    'panorama_silikon': 'PANORAMA [Przemysł i energetyka]: Silikon',
    'panorama_silniki_i_pr%C4%85dnice': 'PANORAMA [Przemysł i energetyka]: Silniki i prądnice',
    'panorama_sklepy_z_cz%C4%99%C5%9Bciami_elektronicznymi': 'PANORAMA [Przemysł i energetyka]: Sklepy z częściami elektronicznymi',
    'panorama_sprz%C4%99t_do_produkcji_opakowa%C5%84': 'PANORAMA [Przemysł i energetyka]: Sprzęt do produkcji opakowań',
    'panorama_sprz%C4%99t_do_utylizacji_odpad%C3%B3w': 'PANORAMA [Przemysł i energetyka]: Sprzęt do utylizacji odpadów',
    'panorama_sprz%C4%99t_i_materia%C5%82y_hydrauliczne': 'PANORAMA [Przemysł i energetyka]: Sprzęt i materiały hydrauliczne',
    'panorama_sprz%C4%99t_i_zabezpieczenia_przeciwpo%C5%BCarowe': 'PANORAMA [Przemysł i energetyka]: Sprzęt i zabezpieczenia przeciwpożarowe',
    'panorama_sprz%C4%99t_lotniczy': 'PANORAMA [Przemysł i energetyka]: Sprzęt lotniczy',
    'panorama_sprz%C4%99t_radiokomunikacyjny': 'PANORAMA [Przemysł i energetyka]: Sprzęt radiokomunikacyjny',
    'panorama_sprz%C4%99t_torowy_i_kolejowy': 'PANORAMA [Przemysł i energetyka]: Sprzęt torowy i kolejowy',
    'panorama_stacje_paliw': 'PANORAMA [Przemysł i energetyka]: Stacje paliw',
    'panorama_stal_i_wyroby_stalowe': 'PANORAMA [Przemysł i energetyka]: Stal i wyroby stalowe',
    'panorama_studnie': 'PANORAMA [Przemysł i energetyka]: Studnie',
    'panorama_surowce_mineralne': 'PANORAMA [Przemysł i energetyka]: Surowce mineralne',
    'panorama_suwnice': 'PANORAMA [Przemysł i energetyka]: Suwnice',
    'panorama_systemy_zamocowa%C5%84': 'PANORAMA [Przemysł i energetyka]: Systemy zamocowań',
    'panorama_szk%C5%82o_budowlane': 'PANORAMA [Przemysł i energetyka]: Szkło budowlane',
    'panorama_szk%C5%82o_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Szkło przemysłowe',
    'panorama_sznury_liny_i_nici': 'PANORAMA [Przemysł i energetyka]: Sznury, liny i nici',
    'panorama_s%C3%B3l_przemys%C5%82owa': 'PANORAMA [Przemysł i energetyka]: Sól przemysłowa',
    'panorama_tartaki': 'PANORAMA [Przemysł i energetyka]: Tartaki',
    'panorama_technika_liniowa': 'PANORAMA [Przemysł i energetyka]: Technika liniowa',
    'panorama_techniki_bezwykopowe': 'PANORAMA [Przemysł i energetyka]: Techniki bezwykopowe',
    'panorama_toalety_przeno%C5%9Bne': 'PANORAMA [Przemysł i energetyka]: Toalety przenośne',
    'panorama_tworzywa_sztuczne': 'PANORAMA [Przemysł i energetyka]: Tworzywa sztuczne',
    'panorama_urz%C4%85dzenia_do_produkcji_obuwia': 'PANORAMA [Przemysł i energetyka]: Urządzenia do produkcji obuwia',
    'panorama_urz%C4%85dzenia_elektroniczne': 'PANORAMA [Przemysł i energetyka]: Urządzenia elektroniczne',
    'panorama_urz%C4%85dzenia_elektryczne': 'PANORAMA [Przemysł i energetyka]: Urządzenia elektryczne',
    'panorama_urz%C4%85dzenia_grzewcze': 'PANORAMA [Przemysł i energetyka]: Urządzenia grzewcze',
    'panorama_urz%C4%85dzenia_i_maszyny_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Urządzenia i maszyny przemysłowe',
    'panorama_urz%C4%85dzenia_lakiernicze': 'PANORAMA [Przemysł i energetyka]: Urządzenia lakiernicze',
    'panorama_urz%C4%85dzenia_pneumatyczne': 'PANORAMA [Przemysł i energetyka]: Urządzenia pneumatyczne',
    'panorama_urz%C4%85dzenia_pomiarowe': 'PANORAMA [Przemysł i energetyka]: Urządzenia pomiarowe',
    'panorama_urz%C4%85dzenia_spawalnicze_i_zgrzewaj%C4%85ce': 'PANORAMA [Przemysł i energetyka]: Urządzenia spawalnicze i zgrzewające',
    'panorama_uszczelki_i_uszczelnienia': 'PANORAMA [Przemysł i energetyka]: Uszczelki i uszczelnienia',
    'panorama_us%C5%82ugi_i_projekty_g%C3%B3rnicze': 'PANORAMA [Przemysł i energetyka]: Usługi i projekty górnicze',
    'panorama_us%C5%82ugi_kamieniarskie': 'PANORAMA [Przemysł i energetyka]: Usługi kamieniarskie',
    'panorama_us%C5%82ugi_spawania_i_zgrzewania': 'PANORAMA [Przemysł i energetyka]: Usługi spawania i zgrzewania',
    'panorama_utylizacja_odpad%C3%B3w': 'PANORAMA [Przemysł i energetyka]: Utylizacja odpadów',
    'panorama_wagi': 'PANORAMA [Przemysł i energetyka]: Wagi',
    'panorama_wodoci%C4%85gi_i_kanalizacja': 'PANORAMA [Przemysł i energetyka]: Wodociągi i kanalizacja',
    'panorama_wyci%C4%85gi_i_koleje_linowe': 'PANORAMA [Przemysł i energetyka]: Wyciągi i koleje linowe',
    'panorama_wydobycie_i_sprzeda%C5%BC_w%C4%99gla': 'PANORAMA [Przemysł i energetyka]: Wydobycie i sprzedaż węgla',
    'panorama_wynajem_maszyn_i_narz%C4%99dzi': 'PANORAMA [Przemysł i energetyka]: Wynajem maszyn i narzędzi',
    'panorama_wyposa%C5%BCenie_sprz%C4%99t_i_instalacje_ch%C5%82odnicze': 'PANORAMA [Przemysł i energetyka]: Wyposażenie, sprzęt i instalacje chłodnicze',
    'panorama_wyroby_hutnicze': 'PANORAMA [Przemysł i energetyka]: Wyroby hutnicze',
    'panorama_wytwarzanie_energii_odnawialnej': 'PANORAMA [Przemysł i energetyka]: Wytwarzanie energii odnawialnej',
    'panorama_wzornictwo_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Wzornictwo przemysłowe',
    'panorama_w%C3%B3zki_wid%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Wózki widłowe',
    'panorama_w%C4%99%C5%BCe_przemys%C5%82owe': 'PANORAMA [Przemysł i energetyka]: Węże przemysłowe',
    'panorama_zabezpieczenia_antykorozyjne': 'PANORAMA [Przemysł i energetyka]: Zabezpieczenia antykorozyjne',
    'panorama_zapalniczki_i_zapa%C5%82ki': 'PANORAMA [Przemysł i energetyka]: Zapalniczki i zapałki',
    'panorama_zawiesia_linowe_%C5%82a%C5%84cuchowe_i_pasowe': 'PANORAMA [Przemysł i energetyka]: Zawiesia linowe, łańcuchowe i pasowe',
    'panorama_zbiorniki_i_pojemniki': 'PANORAMA [Przemysł i energetyka]: Zbiorniki i pojemniki',
    'panorama_z%C5%82om_i_surowce_wt%C3%B3rne': 'PANORAMA [Przemysł i energetyka]: Złom i surowce wtórne',
    'panorama_%C5%82a%C5%84cuchy': 'PANORAMA [Przemysł i energetyka]: Łańcuchy',
    'panorama_%C5%82o%C5%BCyska': 'PANORAMA [Przemysł i energetyka]: Łożyska',
    'panorama_%C5%9Bwiece_i_znicze': 'PANORAMA [Przemysł i energetyka]: Świece i znicze',
    'panorama_artyku%C5%82y_rolnicze': 'PANORAMA [Rolnictwo i leśnictwo]: Artykuły rolnicze',
    'panorama_gie%C5%82dy': 'PANORAMA [Rolnictwo i leśnictwo]: Giełdy',
    'panorama_grzyby_i_runo_le%C5%9Bne': 'PANORAMA [Rolnictwo i leśnictwo]: Grzyby i runo leśne',
    'panorama_hodowla_i_hurtownie_ryb': 'PANORAMA [Rolnictwo i leśnictwo]: Hodowla i hurtownie ryb',
    'panorama_hurtownie_rolnicze': 'PANORAMA [Rolnictwo i leśnictwo]: Hurtownie rolnicze',
    'panorama_hurtownie_ro%C5%9Blin_nasion_i_cebulek': 'PANORAMA [Rolnictwo i leśnictwo]: Hurtownie roślin, nasion i cebulek',
    'panorama_jaja': 'PANORAMA [Rolnictwo i leśnictwo]: Jaja',
    'panorama_korek_naturalny': 'PANORAMA [Rolnictwo i leśnictwo]: Korek naturalny',
    'panorama_le%C5%9Bnictwo': 'PANORAMA [Rolnictwo i leśnictwo]: Leśnictwo',
    'panorama_nawozy': 'PANORAMA [Rolnictwo i leśnictwo]: Nawozy',
    'panorama_ochrona_%C5%9Brodowiska': 'PANORAMA [Rolnictwo i leśnictwo]: Ochrona środowiska',
    'panorama_parki_narodowe_krajobrazowe_i_rezerwaty': 'PANORAMA [Rolnictwo i leśnictwo]: Parki narodowe, krajobrazowe i rezerwaty',
    'panorama_pasze': 'PANORAMA [Rolnictwo i leśnictwo]: Pasze',
    'panorama_pieczarkarnie': 'PANORAMA [Rolnictwo i leśnictwo]: Pieczarkarnie',
    'panorama_produkcja_artyku%C5%82%C3%B3w_rolniczych': 'PANORAMA [Rolnictwo i leśnictwo]: Produkcja artykułów rolniczych',
    'panorama_produkcja_ro%C5%9Blin_i_nasion': 'PANORAMA [Rolnictwo i leśnictwo]: Produkcja roślin i nasion',
    'panorama_ro%C5%9Bliny_nasiona_i_cebulki': 'PANORAMA [Rolnictwo i leśnictwo]: Rośliny, nasiona i cebulki',
    'panorama_serwis_sprz%C4%99tu_rolniczego': 'PANORAMA [Rolnictwo i leśnictwo]: Serwis sprzętu rolniczego',
    'panorama_us%C5%82ugi_rolnicze': 'PANORAMA [Rolnictwo i leśnictwo]: Usługi rolnicze',
    'panorama_wynajem_magazyn%C3%B3w': 'PANORAMA [Rolnictwo i leśnictwo]: Wynajem magazynów',
    'panorama_wynajem_powierzchni_ch%C5%82odniczych': 'PANORAMA [Rolnictwo i leśnictwo]: Wynajem powierzchni chłodniczych',
    'panorama_wyroby_wiklinowe_i_bambusowe': 'PANORAMA [Rolnictwo i leśnictwo]: Wyroby wiklinowe i bambusowe',
    'panorama_zbo%C5%BCa': 'PANORAMA [Rolnictwo i leśnictwo]: Zboża',
    'panorama_zwierz%C4%99ta_hodowlane': 'PANORAMA [Rolnictwo i leśnictwo]: Zwierzęta hodowlane',
    'panorama_%C5%9Brodki_ochrony_ro%C5%9Blin': 'PANORAMA [Rolnictwo i leśnictwo]: Środki ochrony roślin',
    'panorama_agencje_artystyczne': 'PANORAMA [Rozrywka i rekreacja]: Agencje artystyczne',
    'panorama_akcesoria_dla_artyst%C3%B3w_i_plastyk%C3%B3w': 'PANORAMA [Rozrywka i rekreacja]: Akcesoria dla artystów i plastyków',
    'panorama_antyki_i_dzie%C5%82a_sztuki': 'PANORAMA [Rozrywka i rekreacja]: Antyki i dzieła sztuki',
    'panorama_antykwariaty': 'PANORAMA [Rozrywka i rekreacja]: Antykwariaty',
    'panorama_artyku%C5%82y_zoologiczne': 'PANORAMA [Rozrywka i rekreacja]: Artykuły zoologiczne',
    'panorama_astrologia': 'PANORAMA [Rozrywka i rekreacja]: Astrologia',
    'panorama_automaty_do_gier': 'PANORAMA [Rozrywka i rekreacja]: Automaty do gier',
    'panorama_balony': 'PANORAMA [Rozrywka i rekreacja]: Balony',
    'panorama_bary': 'PANORAMA [Rozrywka i rekreacja]: Bary',
    'panorama_baseny_i_parki_wodne': 'PANORAMA [Rozrywka i rekreacja]: Baseny i parki wodne',
    'panorama_bro%C5%84_i_amunicja': 'PANORAMA [Rozrywka i rekreacja]: Broń i amunicja',
    'panorama_centra_handlowe': 'PANORAMA [Rozrywka i rekreacja]: Centra handlowe',
    'panorama_cyrki_i_weso%C5%82e_miasteczka': 'PANORAMA [Rozrywka i rekreacja]: Cyrki i wesołe miasteczka',
    'panorama_domy_kultury_i_kluby_osiedlowe': 'PANORAMA [Rozrywka i rekreacja]: Domy kultury i kluby osiedlowe',
    'panorama_dyskoteki': 'PANORAMA [Rozrywka i rekreacja]: Dyskoteki',
    'panorama_escape_rooms': 'PANORAMA [Rozrywka i rekreacja]: Escape rooms',
    'panorama_filatelistyka': 'PANORAMA [Rozrywka i rekreacja]: Filatelistyka',
    'panorama_filatelistyka_i_numizmatyka': 'PANORAMA [Rozrywka i rekreacja]: Filatelistyka i numizmatyka',
    'panorama_galerie_sztuki': 'PANORAMA [Rozrywka i rekreacja]: Galerie sztuki',
    'panorama_genealogia_i_heraldyka': 'PANORAMA [Rozrywka i rekreacja]: Genealogia i heraldyka',
    'panorama_gry_komputerowe': 'PANORAMA [Rozrywka i rekreacja]: Gry komputerowe',
    'panorama_hale_widowiskowo_sportowe': 'PANORAMA [Rozrywka i rekreacja]: Hale widowiskowo-sportowe',
    'panorama_hurtownie_ksi%C4%85%C5%BCek': 'PANORAMA [Rozrywka i rekreacja]: Hurtownie książek',
    'panorama_hurtownie_sprz%C4%99tu_sportowego_i_turystycznego': 'PANORAMA [Rozrywka i rekreacja]: Hurtownie sprzętu sportowego i turystycznego',
    'panorama_hurtownie_zabawek': 'PANORAMA [Rozrywka i rekreacja]: Hurtownie zabawek',
    'panorama_instrumenty_i_sklepy_muzyczne': 'PANORAMA [Rozrywka i rekreacja]: Instrumenty i sklepy muzyczne',
    'panorama_jachty': 'PANORAMA [Rozrywka i rekreacja]: Jachty',
    'panorama_je%C5%BAdziectwo': 'PANORAMA [Rozrywka i rekreacja]: Jeździectwo',
    'panorama_kasyna_i_bukmacherzy': 'PANORAMA [Rozrywka i rekreacja]: Kasyna i bukmacherzy',
    'panorama_kawiarnie': 'PANORAMA [Rozrywka i rekreacja]: Kawiarnie',
    'panorama_kina': 'PANORAMA [Rozrywka i rekreacja]: Kina',
    'panorama_kluby_muzyczne': 'PANORAMA [Rozrywka i rekreacja]: Kluby muzyczne',
    'panorama_kluby_nocne': 'PANORAMA [Rozrywka i rekreacja]: Kluby nocne',
    'panorama_ksi%C4%99garnie': 'PANORAMA [Rozrywka i rekreacja]: Księgarnie',
    'panorama_lecznice_weterynaryjne': 'PANORAMA [Rozrywka i rekreacja]: Lecznice weterynaryjne',
    'panorama_metaloplastyka': 'PANORAMA [Rozrywka i rekreacja]: Metaloplastyka',
    'panorama_militaria': 'PANORAMA [Rozrywka i rekreacja]: Militaria',
    'panorama_modelarstwo': 'PANORAMA [Rozrywka i rekreacja]: Modelarstwo',
    'panorama_muzea': 'PANORAMA [Rozrywka i rekreacja]: Muzea',
    'panorama_my%C5%9Blistwo': 'PANORAMA [Rozrywka i rekreacja]: Myślistwo',
    'panorama_nauka_muzyki': 'PANORAMA [Rozrywka i rekreacja]: Nauka muzyki',
    'panorama_no%C5%9Bniki_danych_i_p%C5%82yty_cd_i_dvd': 'PANORAMA [Rozrywka i rekreacja]: Nośniki danych i płyty CD i DVD',
    'panorama_numizmatyka': 'PANORAMA [Rozrywka i rekreacja]: Numizmatyka',
    'panorama_odzie%C5%BC_sportowa': 'PANORAMA [Rozrywka i rekreacja]: Odzież sportowa',
    'panorama_ogrody_zoologiczne_i_botaniczne': 'PANORAMA [Rozrywka i rekreacja]: Ogrody zoologiczne i botaniczne',
    'panorama_o%C5%9Brodki_i_kluby_sportowo_rekreacyjne': 'PANORAMA [Rozrywka i rekreacja]: Ośrodki i kluby sportowo-rekreacyjne',
    'panorama_parki_rozrywki': 'PANORAMA [Rozrywka i rekreacja]: Parki rozrywki',
    'panorama_pirotechnika': 'PANORAMA [Rozrywka i rekreacja]: Pirotechnika',
    'panorama_pizzerie': 'PANORAMA [Rozrywka i rekreacja]: Pizzerie',
    'panorama_pojazdy_zabytkowe_i_doro%C5%BCki': 'PANORAMA [Rozrywka i rekreacja]: Pojazdy zabytkowe i dorożki',
    'panorama_producenci_sprz%C4%99tu_sportowego_i_turystycznego': 'PANORAMA [Rozrywka i rekreacja]: Producenci sprzętu sportowego i turystycznego',
    'panorama_produkcja_zabawek': 'PANORAMA [Rozrywka i rekreacja]: Produkcja zabawek',
    'panorama_projektowanie_i_monta%C5%BC_plac%C3%B3w_zabaw': 'PANORAMA [Rozrywka i rekreacja]: Projektowanie i montaż placów zabaw',
    'panorama_puby': 'PANORAMA [Rozrywka i rekreacja]: Puby',
    'panorama_ramy_i_oprawy_obraz%C3%B3w': 'PANORAMA [Rozrywka i rekreacja]: Ramy i oprawy obrazów',
    'panorama_restauracje': 'PANORAMA [Rozrywka i rekreacja]: Restauracje',
    'panorama_rowery': 'PANORAMA [Rozrywka i rekreacja]: Rowery',
    'panorama_r%C4%99kodzie%C5%82o_artystyczne': 'PANORAMA [Rozrywka i rekreacja]: Rękodzieło artystyczne',
    'panorama_sale_weselne_i_organizacja_wesel': 'PANORAMA [Rozrywka i rekreacja]: Sale weselne i organizacja wesel',
    'panorama_sale_zabaw': 'PANORAMA [Rozrywka i rekreacja]: Sale zabaw',
    'panorama_salony_bilardowe': 'PANORAMA [Rozrywka i rekreacja]: Salony bilardowe',
    'panorama_schroniska_dla_zwierz%C4%85t': 'PANORAMA [Rozrywka i rekreacja]: Schroniska dla zwierząt',
    'panorama_sex_shopy': 'PANORAMA [Rozrywka i rekreacja]: Sex shopy',
    'panorama_si%C5%82ownie_i_fitness': 'PANORAMA [Rozrywka i rekreacja]: Siłownie i fitness',
    'panorama_sklepy_z_zabawkami': 'PANORAMA [Rozrywka i rekreacja]: Sklepy z zabawkami',
    'panorama_sprz%C4%99t_i_wyposa%C5%BCenie_kr%C4%99gielni': 'PANORAMA [Rozrywka i rekreacja]: Sprzęt i wyposażenie kręgielni',
    'panorama_sprz%C4%99t_i_wyposa%C5%BCenie_weterynaryjne': 'PANORAMA [Rozrywka i rekreacja]: Sprzęt i wyposażenie weterynaryjne',
    'panorama_sprz%C4%99t_sportowy_i_turystyczny': 'PANORAMA [Rozrywka i rekreacja]: Sprzęt sportowy i turystyczny',
    'panorama_stadiony_sportowe': 'PANORAMA [Rozrywka i rekreacja]: Stadiony sportowe',
    'panorama_systemy_d%C5%BAwi%C4%99kowe_i_audio': 'PANORAMA [Rozrywka i rekreacja]: Systemy dźwiękowe i audio',
    'panorama_szko%C5%82y_ta%C5%84ca': 'PANORAMA [Rozrywka i rekreacja]: Szkoły tańca',
    'panorama_teatry_i_filharmonie': 'PANORAMA [Rozrywka i rekreacja]: Teatry i filharmonie',
    'panorama_wynajem_i_serwis_sprz%C4%99tu_sportowego_i_turystycznego': 'PANORAMA [Rozrywka i rekreacja]: Wynajem i serwis sprzętu sportowego i turystycznego',
    'panorama_wyposa%C5%BCenie_obiekt%C3%B3w_sportowych': 'PANORAMA [Rozrywka i rekreacja]: Wyposażenie obiektów sportowych',
    'panorama_wypo%C5%BCyczalnie_film%C3%B3w_wideo_i_dvd': 'PANORAMA [Rozrywka i rekreacja]: Wypożyczalnie filmów wideo i DVD',
    'panorama_w%C4%99dkarstwo': 'PANORAMA [Rozrywka i rekreacja]: Wędkarstwo',
    'panorama_zespo%C5%82y_muzyczne': 'PANORAMA [Rozrywka i rekreacja]: Zespoły muzyczne',
    'panorama_zwierz%C4%99ta_domowe': 'PANORAMA [Rozrywka i rekreacja]: Zwierzęta domowe',
    'panorama_%C5%9Bwietlice_%C5%9Brodowiskowe': 'PANORAMA [Rozrywka i rekreacja]: Świetlice środowiskowe',
    'panorama_%C5%BCegluga': 'PANORAMA [Rozrywka i rekreacja]: Żegluga',
    'panorama_anteny': 'PANORAMA [Telekomunikacja, Internet, technologie]: Anteny',
    'panorama_audyty_oprogramowania_i_sprz%C4%99tu_komputerowego': 'PANORAMA [Telekomunikacja, Internet, technologie]: Audyty oprogramowania i sprzętu komputerowego',
    'panorama_informatyka': 'PANORAMA [Telekomunikacja, Internet, technologie]: Informatyka',
    'panorama_internet': 'PANORAMA [Telekomunikacja, Internet, technologie]: Internet',
    'panorama_odzyskiwanie_i_ochrona_danych_komputerowych': 'PANORAMA [Telekomunikacja, Internet, technologie]: Odzyskiwanie i ochrona danych komputerowych',
    'panorama_operatorzy_telekomunikacyjni': 'PANORAMA [Telekomunikacja, Internet, technologie]: Operatorzy telekomunikacyjni',
    'panorama_oprogramowanie_komputerowe': 'PANORAMA [Telekomunikacja, Internet, technologie]: Oprogramowanie komputerowe',
    'panorama_serwis_komputer%C3%B3w': 'PANORAMA [Telekomunikacja, Internet, technologie]: Serwis komputerów',
    'panorama_serwisy_informacyjne': 'PANORAMA [Telekomunikacja, Internet, technologie]: Serwisy informacyjne',
    'panorama_sieci_komputerowe_i_integracja_system%C3%B3w': 'PANORAMA [Telekomunikacja, Internet, technologie]: Sieci komputerowe i integracja systemów',
    'panorama_sprz%C4%99t_i_centrale_telefoniczne': 'PANORAMA [Telekomunikacja, Internet, technologie]: Sprzęt i centrale telefoniczne',
    'panorama_sprz%C4%99t_radiokomunikacyjny': 'PANORAMA [Telekomunikacja, Internet, technologie]: Sprzęt radiokomunikacyjny',
    'panorama_stacje_radiowe_i_telewizyjne': 'PANORAMA [Telekomunikacja, Internet, technologie]: Stacje radiowe i telewizyjne',
    'panorama_systemy_i_technologie_multimedialne': 'PANORAMA [Telekomunikacja, Internet, technologie]: Systemy i technologie multimedialne',
    'panorama_systemy_i_us%C5%82ugi_telekomunikacyjne': 'PANORAMA [Telekomunikacja, Internet, technologie]: Systemy i usługi telekomunikacyjne',
    'panorama_agroturystyka': 'PANORAMA [Turystyka]: Agroturystyka',
    'panorama_biura_podr%C3%B3%C5%BCy_i_agencje_turystyczne': 'PANORAMA [Turystyka]: Biura podróży i agencje turystyczne',
    'panorama_hotele': 'PANORAMA [Turystyka]: Hotele',
    'panorama_informacja_turystyczna': 'PANORAMA [Turystyka]: Informacja turystyczna',
    'panorama_kempingi': 'PANORAMA [Turystyka]: Kempingi',
    'panorama_komunikacja_i_przewozy_pasa%C5%BCerskie': 'PANORAMA [Turystyka]: Komunikacja i przewozy pasażerskie',
    'panorama_linie_lotnicze': 'PANORAMA [Turystyka]: Linie lotnicze',
    'panorama_lotniska': 'PANORAMA [Turystyka]: Lotniska',
    'panorama_namioty_i_hale_namiotowe': 'PANORAMA [Turystyka]: Namioty i hale namiotowe',
    'panorama_noclegi_i_kwatery_prywatne': 'PANORAMA [Turystyka]: Noclegi i kwatery prywatne',
    'panorama_noclegownie': 'PANORAMA [Turystyka]: Noclegownie',
    'panorama_pensjonaty_hostele_i_o%C5%9Brodki_wypoczynkowe': 'PANORAMA [Turystyka]: Pensjonaty, hostele i ośrodki wypoczynkowe',
    'panorama_sprzeda%C5%BC_i_rezerwacja_bilet%C3%B3w': 'PANORAMA [Turystyka]: Sprzedaż i rezerwacja biletów',
    'panorama_wyposa%C5%BCenie_hoteli': 'PANORAMA [Turystyka]: Wyposażenie hoteli',
    'panorama_adwokaci': 'PANORAMA [Usługi dla firm]: Adwokaci',
    'panorama_agenci_okr%C4%99towi_i_morscy': 'PANORAMA [Usługi dla firm]: Agenci okrętowi i morscy',
    'panorama_agencje_fotograficzne': 'PANORAMA [Usługi dla firm]: Agencje fotograficzne',
    'panorama_agencje_i_doradztwo_reklamowe': 'PANORAMA [Usługi dla firm]: Agencje i doradztwo reklamowe',
    'panorama_agencje_i_sk%C5%82ady_celne': 'PANORAMA [Usługi dla firm]: Agencje i składy celne',
    'panorama_agencje_marketingowe': 'PANORAMA [Usługi dla firm]: Agencje marketingowe',
    'panorama_agencje_modelek': 'PANORAMA [Usługi dla firm]: Agencje modelek',
    'panorama_agencje_ochrony': 'PANORAMA [Usługi dla firm]: Agencje ochrony',
    'panorama_agencje_po%C5%9Brednictwa_pracy': 'PANORAMA [Usługi dla firm]: Agencje pośrednictwa pracy',
    'panorama_agencje_pracy_tymczasowej': 'PANORAMA [Usługi dla firm]: Agencje pracy tymczasowej',
    'panorama_agencje_prasowe': 'PANORAMA [Usługi dla firm]: Agencje prasowe',
    'panorama_agencje_public_relations': 'PANORAMA [Usługi dla firm]: Agencje public relations',
    'panorama_agencje_t%C5%82umaczy': 'PANORAMA [Usługi dla firm]: Agencje tłumaczy',
    'panorama_akcesoria_i_gad%C5%BCety_reklamowe': 'PANORAMA [Usługi dla firm]: Akcesoria i gadżety reklamowe',
    'panorama_akcesoria_szewskie_i_kaletnicze': 'PANORAMA [Usługi dla firm]: Akcesoria szewskie i kaletnicze',
    'panorama_archiwa_i_archiwizacja_danych': 'PANORAMA [Usługi dla firm]: Archiwa i archiwizacja danych',
    'panorama_artyku%C5%82y_i_sprz%C4%99t_bhp': 'PANORAMA [Usługi dla firm]: Artykuły i sprzęt BHP',
    'panorama_artyku%C5%82y_i_wyposa%C5%BCenie_salon%C3%B3w_fryzjerskich': 'PANORAMA [Usługi dla firm]: Artykuły i wyposażenie salonów fryzjerskich',
    'panorama_automaty_do_sprzeda%C5%BCy': 'PANORAMA [Usługi dla firm]: Automaty do sprzedaży',
    'panorama_badania_i_monitoring_rynku': 'PANORAMA [Usługi dla firm]: Badania i monitoring rynku',
    'panorama_badania_i_us%C5%82ugi_archeologiczne': 'PANORAMA [Usługi dla firm]: Badania i usługi archeologiczne',
    'panorama_badania_i_uzdatnianie_wody': 'PANORAMA [Usługi dla firm]: Badania i uzdatnianie wody',
    'panorama_banki': 'PANORAMA [Usługi dla firm]: Banki',
    'panorama_bazy_danych': 'PANORAMA [Usługi dla firm]: Bazy danych',
    'panorama_biura_og%C5%82osze%C5%84': 'PANORAMA [Usługi dla firm]: Biura ogłoszeń',
    'panorama_biura_rachunkowe': 'PANORAMA [Usługi dla firm]: Biura rachunkowe',
    'panorama_biura_reklamy': 'PANORAMA [Usługi dla firm]: Biura reklamy',
    'panorama_bony_i_kupony': 'PANORAMA [Usługi dla firm]: Bony i kupony',
    'panorama_budowa_i_wynajem_hal_przemys%C5%82owych': 'PANORAMA [Usługi dla firm]: Budowa i wynajem hal przemysłowych',
    'panorama_catering': 'PANORAMA [Usługi dla firm]: Catering',
    'panorama_czyszczenie_strumieniowo_%C5%9Bcierne': 'PANORAMA [Usługi dla firm]: Czyszczenie strumieniowo-ścierne',
    'panorama_czytniki_i_karty_identyfikacyjne': 'PANORAMA [Usługi dla firm]: Czytniki i karty identyfikacyjne',
    'panorama_dezynfekcja_dezynsekcja_i_deratyzacja': 'PANORAMA [Usługi dla firm]: Dezynfekcja dezynsekcja i deratyzacja',
    'panorama_doradztwo_finansowe_i_kredytowe': 'PANORAMA [Usługi dla firm]: Doradztwo finansowe i kredytowe',
    'panorama_doradztwo_gospodarcze': 'PANORAMA [Usługi dla firm]: Doradztwo gospodarcze',
    'panorama_doradztwo_personalne': 'PANORAMA [Usługi dla firm]: Doradztwo personalne',
    'panorama_doradztwo_podatkowe': 'PANORAMA [Usługi dla firm]: Doradztwo podatkowe',
    'panorama_doradztwo_prawne': 'PANORAMA [Usługi dla firm]: Doradztwo prawne',
    'panorama_druk_cyfrowy': 'PANORAMA [Usługi dla firm]: Druk cyfrowy',
    'panorama_druk_na_odzie%C5%BCy': 'PANORAMA [Usługi dla firm]: Druk na odzieży',
    'panorama_druk_offsetowy': 'PANORAMA [Usługi dla firm]: Druk offsetowy',
    'panorama_druk_plakat%C3%B3w_wielkoformatowych': 'PANORAMA [Usługi dla firm]: Druk plakatów wielkoformatowych',
    'panorama_drukarnie_i_poligrafia': 'PANORAMA [Usługi dla firm]: Drukarnie i poligrafia',
    'panorama_druki_akcydensowe': 'PANORAMA [Usługi dla firm]: Druki akcydensowe',
    'panorama_elektroinstalatorstwo': 'PANORAMA [Usługi dla firm]: Elektroinstalatorstwo',
    'panorama_etykiety_i_naklejki': 'PANORAMA [Usługi dla firm]: Etykiety i naklejki',
    'panorama_firmy_konsultingowe': 'PANORAMA [Usługi dla firm]: Firmy konsultingowe',
    'panorama_flagi_i_artyku%C5%82y_propagandowe': 'PANORAMA [Usługi dla firm]: Flagi i artykuły propagandowe',
    'panorama_geodezja': 'PANORAMA [Usługi dla firm]: Geodezja',
    'panorama_grafika_komputerowa': 'PANORAMA [Usługi dla firm]: Grafika komputerowa',
    'panorama_grawerowanie': 'PANORAMA [Usługi dla firm]: Grawerowanie',
    'panorama_hale_targ%C3%B3w_i_wystaw': 'PANORAMA [Usługi dla firm]: Hale targów i wystaw',
    'panorama_hurt_i_produkcja_zegar%C3%B3w_i_zegark%C3%B3w': 'PANORAMA [Usługi dla firm]: Hurt i produkcja zegarów i zegarków',
    'panorama_hurtownie_sprz%C4%99tu_fotograficznego': 'PANORAMA [Usługi dla firm]: Hurtownie sprzętu fotograficznego',
    'panorama_import_i_eksport': 'PANORAMA [Usługi dla firm]: Import i eksport',
    'panorama_informatyka': 'PANORAMA [Usługi dla firm]: Informatyka',
    'panorama_inkubatory_przedsi%C4%99biorczo%C5%9Bci': 'PANORAMA [Usługi dla firm]: Inkubatory przedsiębiorczości',
    'panorama_instalacja_system%C3%B3w_alarmowych': 'PANORAMA [Usługi dla firm]: Instalacja systemów alarmowych',
    'panorama_instytuty_i_o%C5%9Brodki_badawcze': 'PANORAMA [Usługi dla firm]: Instytuty i ośrodki badawcze',
    'panorama_internet': 'PANORAMA [Usługi dla firm]: Internet',
    'panorama_introligatornie': 'PANORAMA [Usługi dla firm]: Introligatornie',
    'panorama_kadry_i_p%C5%82ace': 'PANORAMA [Usługi dla firm]: Kadry i płace',
    'panorama_kalendarze_katalogi_i_foldery_reklamowe': 'PANORAMA [Usługi dla firm]: Kalendarze, katalogi i foldery reklamowe',
    'panorama_karty_kredytowe_p%C5%82atnicze_i_programy_lojalno%C5%9Bciowe': 'PANORAMA [Usługi dla firm]: Karty kredytowe, płatnicze i programy lojalnościowe',
    'panorama_kasy_fiskalne_i_sklepowe': 'PANORAMA [Usługi dla firm]: Kasy fiskalne i sklepowe',
    'panorama_kolporta%C5%BC_gazet_i_czasopism': 'PANORAMA [Usługi dla firm]: Kolportaż gazet i czasopism',
    'panorama_konserwacja_zabytk%C3%B3w': 'PANORAMA [Usługi dla firm]: Konserwacja zabytków',
    'panorama_kredyty_i_finansowanie': 'PANORAMA [Usługi dla firm]: Kredyty i finansowanie',
    'panorama_ksero': 'PANORAMA [Usługi dla firm]: Ksero',
    'panorama_kurierzy': 'PANORAMA [Usługi dla firm]: Kurierzy',
    'panorama_kursy_i_szkolenia': 'PANORAMA [Usługi dla firm]: Kursy i szkolenia',
    'panorama_leasing': 'PANORAMA [Usługi dla firm]: Leasing',
    'panorama_lombardy': 'PANORAMA [Usługi dla firm]: Lombardy',
    'panorama_mapy_i_plany': 'PANORAMA [Usługi dla firm]: Mapy i plany',
    'panorama_maszyny_do_szycia': 'PANORAMA [Usługi dla firm]: Maszyny do szycia',
    'panorama_maszyny_i_materia%C5%82y_drukarskie': 'PANORAMA [Usługi dla firm]: Maszyny i materiały drukarskie',
    'panorama_nawigacja_i_lokalizacja_satelitarna': 'PANORAMA [Usługi dla firm]: Nawigacja i lokalizacja satelitarna',
    'panorama_na%C5%9Bwietlanie_i_skanowanie_druku': 'PANORAMA [Usługi dla firm]: Naświetlanie i skanowanie druku',
    'panorama_nieruchomo%C5%9Bci': 'PANORAMA [Usługi dla firm]: Nieruchomości',
    'panorama_nietypowe_us%C5%82ugi_reklamowe': 'PANORAMA [Usługi dla firm]: Nietypowe usługi reklamowe',
    'panorama_niszczenie_dokument%C3%B3w': 'PANORAMA [Usługi dla firm]: Niszczenie dokumentów',
    'panorama_obiekty_konferencyjne': 'PANORAMA [Usługi dla firm]: Obiekty konferencyjne',
    'panorama_obs%C5%82uga_cudzoziemc%C3%B3w': 'PANORAMA [Usługi dla firm]: Obsługa cudzoziemców',
    'panorama_oczyszczanie_%C5%9Bciek%C3%B3w': 'PANORAMA [Usługi dla firm]: Oczyszczanie ścieków',
    'panorama_odszkodowania': 'PANORAMA [Usługi dla firm]: Odszkodowania',
    'panorama_odzie%C5%BC_robocza': 'PANORAMA [Usługi dla firm]: Odzież robocza',
    'panorama_odzyskiwanie_i_ochrona_danych_komputerowych': 'PANORAMA [Usługi dla firm]: Odzyskiwanie i ochrona danych komputerowych',
    'panorama_oklejanie_samochod%C3%B3w': 'PANORAMA [Usługi dla firm]: Oklejanie samochodów',
    'panorama_opakowania_papierowe_i_tekturowe': 'PANORAMA [Usługi dla firm]: Opakowania papierowe i tekturowe',
    'panorama_operatorzy_logistyczni': 'PANORAMA [Usługi dla firm]: Operatorzy logistyczni',
    'panorama_operatorzy_pocztowi': 'PANORAMA [Usługi dla firm]: Operatorzy pocztowi',
    'panorama_operatorzy_telekomunikacyjni': 'PANORAMA [Usługi dla firm]: Operatorzy telekomunikacyjni',
    'panorama_organizacja_i_sprz%C4%99t_dla_targ%C3%B3w_i_wystaw': 'PANORAMA [Usługi dla firm]: Organizacja i sprzęt dla targów i wystaw',
    'panorama_organizacja_imprez_i_konferencji': 'PANORAMA [Usługi dla firm]: Organizacja imprez i konferencji',
    'panorama_ostrzenie': 'PANORAMA [Usługi dla firm]: Ostrzenie',
    'panorama_osuszanie_budynk%C3%B3w': 'PANORAMA [Usługi dla firm]: Osuszanie budynków',
    'panorama_papier': 'PANORAMA [Usługi dla firm]: Papier',
    'panorama_plakatowanie': 'PANORAMA [Usługi dla firm]: Plakatowanie',
    'panorama_pomiary_konsultacje_i_badania_bhp': 'PANORAMA [Usługi dla firm]: Pomiary, konsultacje i badania BHP',
    'panorama_po%C5%9Brednictwo_handlu': 'PANORAMA [Usługi dla firm]: Pośrednictwo handlu',
    'panorama_po%C5%9Brednicy_ubezpieczeniowi': 'PANORAMA [Usługi dla firm]: Pośrednicy ubezpieczeniowi',
    'panorama_prace_podwodne': 'PANORAMA [Usługi dla firm]: Prace podwodne',
    'panorama_prace_wysoko%C5%9Bciowe': 'PANORAMA [Usługi dla firm]: Prace wysokościowe',
    'panorama_pralnie_i_us%C5%82ugi_czyszczenia': 'PANORAMA [Usługi dla firm]: Pralnie i usługi czyszczenia',
    'panorama_produkcja_i_dystrybucja_film%C3%B3w': 'PANORAMA [Usługi dla firm]: Produkcja i dystrybucja filmów',
    'panorama_przedstawicielstwa_firm_zagranicznych': 'PANORAMA [Usługi dla firm]: Przedstawicielstwa firm zagranicznych',
    'panorama_radcy_prawni': 'PANORAMA [Usługi dla firm]: Radcy prawni',
    'panorama_recykling': 'PANORAMA [Usługi dla firm]: Recykling',
    'panorama_redakcje_i_wydawcy_gazet_i_czasopism': 'PANORAMA [Usługi dla firm]: Redakcje i wydawcy gazet i czasopism',
    'panorama_reklama_zewn%C4%99trzna': 'PANORAMA [Usługi dla firm]: Reklama zewnętrzna',
    'panorama_rewidenci_i_us%C5%82ugi_audytorskie': 'PANORAMA [Usługi dla firm]: Rewidenci i usługi audytorskie',
    'panorama_rzecznicy_patentowi': 'PANORAMA [Usługi dla firm]: Rzecznicy patentowi',
    'panorama_rzeczoznawcy': 'PANORAMA [Usługi dla firm]: Rzeczoznawcy',
    'panorama_serwis_i_instalacja_klimatyzacji': 'PANORAMA [Usługi dla firm]: Serwis i instalacja klimatyzacji',
    'panorama_serwis_kserokopiarek': 'PANORAMA [Usługi dla firm]: Serwis kserokopiarek',
    'panorama_sitodruk': 'PANORAMA [Usługi dla firm]: Sitodruk',
    'panorama_sk%C5%82ad_tekstu_do_druku': 'PANORAMA [Usługi dla firm]: Skład tekstu do druku',
    'panorama_specjalne_strefy_ekonomiczne': 'PANORAMA [Usługi dla firm]: Specjalne strefy ekonomiczne',
    'panorama_spedycja': 'PANORAMA [Usługi dla firm]: Spedycja',
    'panorama_spedycja_mi%C4%99dzynarodowa': 'PANORAMA [Usługi dla firm]: Spedycja międzynarodowa',
    'panorama_sprzeda%C5%BC_wysy%C5%82kowa': 'PANORAMA [Usługi dla firm]: Sprzedaż wysyłkowa',
    'panorama_sprz%C4%85tanie_terenu': 'PANORAMA [Usługi dla firm]: Sprzątanie terenu',
    'panorama_sprz%C4%85tanie_wn%C4%99trz_i_mycie_okien': 'PANORAMA [Usługi dla firm]: Sprzątanie wnętrz i mycie okien',
    'panorama_sprz%C4%99t_i_centrale_telefoniczne': 'PANORAMA [Usługi dla firm]: Sprzęt i centrale telefoniczne',
    'panorama_sprz%C4%99t_i_wyposa%C5%BCenie_kr%C4%99gielni': 'PANORAMA [Usługi dla firm]: Sprzęt i wyposażenie kręgielni',
    'panorama_stacje_radiowe_i_telewizyjne': 'PANORAMA [Usługi dla firm]: Stacje radiowe i telewizyjne',
    'panorama_studia_nagra%C5%84': 'PANORAMA [Usługi dla firm]: Studia nagrań',
    'panorama_syndycy_i_likwidatorzy': 'PANORAMA [Usługi dla firm]: Syndycy i likwidatorzy',
    'panorama_systemy_audiowizualne': 'PANORAMA [Usługi dla firm]: Systemy audiowizualne',
    'panorama_systemy_i_us%C5%82ugi_telekomunikacyjne': 'PANORAMA [Usługi dla firm]: Systemy i usługi telekomunikacyjne',
    'panorama_systemy_kontroli_dost%C4%99pu_i_czasu_pracy': 'PANORAMA [Usługi dla firm]: Systemy kontroli dostępu i czasu pracy',
    'panorama_szyldy_i_banery': 'PANORAMA [Usługi dla firm]: Szyldy i banery',
    'panorama_telebimy_diodowe_led': 'PANORAMA [Usługi dla firm]: Telebimy diodowe LED',
    'panorama_telefony_kom%C3%B3rkowe': 'PANORAMA [Usługi dla firm]: Telefony komórkowe',
    'panorama_telemarketing': 'PANORAMA [Usługi dla firm]: Telemarketing',
    'panorama_telewizja_przemys%C5%82owa': 'PANORAMA [Usługi dla firm]: Telewizja przemysłowa',
    'panorama_telewizja_satelitarna': 'PANORAMA [Usługi dla firm]: Telewizja satelitarna',
    'panorama_torby_walizki_i_teczki': 'PANORAMA [Usługi dla firm]: Torby, walizki i teczki',
    'panorama_transport_kolejowy': 'PANORAMA [Usługi dla firm]: Transport kolejowy',
    'panorama_transport_lotniczy': 'PANORAMA [Usługi dla firm]: Transport lotniczy',
    'panorama_transport_mi%C4%99dzynarodowy': 'PANORAMA [Usługi dla firm]: Transport międzynarodowy',
    'panorama_transport_morski_i_%C5%9Br%C3%B3dl%C4%85dowy': 'PANORAMA [Usługi dla firm]: Transport morski i śródlądowy',
    'panorama_transport_samochodowy': 'PANORAMA [Usługi dla firm]: Transport samochodowy',
    'panorama_transport_%C5%82adunk%C3%B3w_niebezpiecznych': 'PANORAMA [Usługi dla firm]: Transport ładunków niebezpiecznych',
    'panorama_t%C5%82umacze': 'PANORAMA [Usługi dla firm]: Tłumacze',
    'panorama_t%C5%82umacze_przysi%C4%99gli': 'PANORAMA [Usługi dla firm]: Tłumacze przysięgli',
    'panorama_ubezpieczenia': 'PANORAMA [Usługi dla firm]: Ubezpieczenia',
    'panorama_usuwanie_i_neutralizacja_azbestu': 'PANORAMA [Usługi dla firm]: Usuwanie i neutralizacja azbestu',
    'panorama_us%C5%82ugi_dystrybucyjne': 'PANORAMA [Usługi dla firm]: Usługi dystrybucyjne',
    'panorama_us%C5%82ugi_gazownicze': 'PANORAMA [Usługi dla firm]: Usługi gazownicze',
    'panorama_us%C5%82ugi_pakowania': 'PANORAMA [Usługi dla firm]: Usługi pakowania',
    'panorama_us%C5%82ugi_portowe_i_prze%C5%82adunkowe': 'PANORAMA [Usługi dla firm]: Usługi portowe i przeładunkowe',
    'panorama_us%C5%82ugi_sekretarskie': 'PANORAMA [Usługi dla firm]: Usługi sekretarskie',
    'panorama_us%C5%82ugi_wysy%C5%82kowe': 'PANORAMA [Usługi dla firm]: Usługi wysyłkowe',
    'panorama_utylizacja_odpad%C3%B3w': 'PANORAMA [Usługi dla firm]: Utylizacja odpadów',
    'panorama_wa%C5%BCne_telefony': 'PANORAMA [Usługi dla firm]: Ważne telefony',
    'panorama_windykacja_d%C5%82ug%C3%B3w_i_nale%C5%BCno%C5%9Bci': 'PANORAMA [Usługi dla firm]: Windykacja długów i należności',
    'panorama_wirtualne_biura': 'PANORAMA [Usługi dla firm]: Wirtualne biura',
    'panorama_wycena_nieruchomo%C5%9Bci': 'PANORAMA [Usługi dla firm]: Wycena nieruchomości',
    'panorama_wydawnictwa': 'PANORAMA [Usługi dla firm]: Wydawnictwa',
    'panorama_wynajem_i_sprzeda%C5%BC_kserokopiarek': 'PANORAMA [Usługi dla firm]: Wynajem i sprzedaż kserokopiarek',
    'panorama_wynajem_magazyn%C3%B3w': 'PANORAMA [Usługi dla firm]: Wynajem magazynów',
    'panorama_wynajem_powierzchni_ch%C5%82odniczych': 'PANORAMA [Usługi dla firm]: Wynajem powierzchni chłodniczych',
    'panorama_wyposa%C5%BCenie_biur_projektowych': 'PANORAMA [Usługi dla firm]: Wyposażenie biur projektowych',
    'panorama_wyposa%C5%BCenie_hoteli': 'PANORAMA [Usługi dla firm]: Wyposażenie hoteli',
    'panorama_wyposa%C5%BCenie_i_narz%C4%99dzia_jubilerskie': 'PANORAMA [Usługi dla firm]: Wyposażenie i narzędzia jubilerskie',
    'panorama_wyposa%C5%BCenie_i_sprz%C4%99t_dla_kin_i_teatr%C3%B3w': 'PANORAMA [Usługi dla firm]: Wyposażenie i sprzęt dla kin i teatrów',
    'panorama_wyposa%C5%BCenie_i_sprz%C4%99t_introligatorski': 'PANORAMA [Usługi dla firm]: Wyposażenie i sprzęt introligatorski',
    'panorama_wyposa%C5%BCenie_i_zaopatrzenie_piekarni': 'PANORAMA [Usługi dla firm]: Wyposażenie i zaopatrzenie piekarni',
    'panorama_wyposa%C5%BCenie_klub%C3%B3w_bilardowych': 'PANORAMA [Usługi dla firm]: Wyposażenie klubów bilardowych',
    'panorama_wyposa%C5%BCenie_kwiaciarni': 'PANORAMA [Usługi dla firm]: Wyposażenie kwiaciarni',
    'panorama_wyposa%C5%BCenie_magazyn%C3%B3w': 'PANORAMA [Usługi dla firm]: Wyposażenie magazynów',
    'panorama_wyposa%C5%BCenie_pralni_i_farbiarni': 'PANORAMA [Usługi dla firm]: Wyposażenie pralni i farbiarni',
    'panorama_wyposa%C5%BCenie_salon%C3%B3w_kosmetycznych': 'PANORAMA [Usługi dla firm]: Wyposażenie salonów kosmetycznych',
    'panorama_wyposa%C5%BCenie_sklep%C3%B3w': 'PANORAMA [Usługi dla firm]: Wyposażenie sklepów',
    'panorama_wyposa%C5%BCenie_stacji_radiowo_telewizyjnych': 'PANORAMA [Usługi dla firm]: Wyposażenie stacji radiowo-telewizyjnych',
    'panorama_wypo%C5%BCyczalnie_stroj%C3%B3w': 'PANORAMA [Usługi dla firm]: Wypożyczalnie strojów',
    'panorama_wywiadownie_gospodarcze': 'PANORAMA [Usługi dla firm]: Wywiadownie gospodarcze',
    'panorama_wyw%C3%B3z_%C5%9Bmieci_i_odpad%C3%B3w': 'PANORAMA [Usługi dla firm]: Wywóz śmieci i odpadów',
    'panorama_zaopatrzenie_biur': 'PANORAMA [Usługi dla firm]: Zaopatrzenie biur',
    'panorama_zarz%C4%85dzanie_nieruchomo%C5%9Bciami': 'PANORAMA [Usługi dla firm]: Zarządzanie nieruchomościami',
    'panorama_znakowanie_i_monitorowanie_samochod%C3%B3w': 'PANORAMA [Usługi dla firm]: Znakowanie i monitorowanie samochodów',
    'panorama_znakowanie_kodowanie_i_hologramy': 'PANORAMA [Usługi dla firm]: Znakowanie, kodowanie i hologramy',
    'panorama_adwokaci': 'PANORAMA [Usługi dla każdego]: Adwokaci',
    'panorama_agencje_detektywistyczne': 'PANORAMA [Usługi dla każdego]: Agencje detektywistyczne',
    'panorama_agencje_fotograficzne': 'PANORAMA [Usługi dla każdego]: Agencje fotograficzne',
    'panorama_agencje_ochrony': 'PANORAMA [Usługi dla każdego]: Agencje ochrony',
    'panorama_agencje_po%C5%9Brednictwa_pracy': 'PANORAMA [Usługi dla każdego]: Agencje pośrednictwa pracy',
    'panorama_agencje_pracy_tymczasowej': 'PANORAMA [Usługi dla każdego]: Agencje pracy tymczasowej',
    'panorama_agencje_t%C5%82umaczy': 'PANORAMA [Usługi dla każdego]: Agencje tłumaczy',
    'panorama_astrologia': 'PANORAMA [Usługi dla każdego]: Astrologia',
    'panorama_badania_i_uzdatnianie_wody': 'PANORAMA [Usługi dla każdego]: Badania i uzdatnianie wody',
    'panorama_bankomaty': 'PANORAMA [Usługi dla każdego]: Bankomaty',
    'panorama_baseny_i_parki_wodne': 'PANORAMA [Usługi dla każdego]: Baseny i parki wodne',
    'panorama_bazy_danych': 'PANORAMA [Usługi dla każdego]: Bazy danych',
    'panorama_biura_matrymonialne': 'PANORAMA [Usługi dla każdego]: Biura matrymonialne',
    'panorama_bony_i_kupony': 'PANORAMA [Usługi dla każdego]: Bony i kupony',
    'panorama_budowa_i_wyposa%C5%BCenie_saun': 'PANORAMA [Usługi dla każdego]: Budowa i wyposażenie saun',
    'panorama_centra_handlowe': 'PANORAMA [Usługi dla każdego]: Centra handlowe',
    'panorama_czyszczenie_i_renowacja_dywan%C3%B3w_i_wyk%C5%82adzin': 'PANORAMA [Usługi dla każdego]: Czyszczenie i renowacja dywanów i wykładzin',
    'panorama_czyszczenie_strumieniowo_%C5%9Bcierne': 'PANORAMA [Usługi dla każdego]: Czyszczenie strumieniowo-ścierne',
    'panorama_deweloperzy': 'PANORAMA [Usługi dla każdego]: Deweloperzy',
    'panorama_dewocjonalia': 'PANORAMA [Usługi dla każdego]: Dewocjonalia',
    'panorama_dezynfekcja_dezynsekcja_i_deratyzacja': 'PANORAMA [Usługi dla każdego]: Dezynfekcja dezynsekcja i deratyzacja',
    'panorama_doradztwo_podatkowe': 'PANORAMA [Usługi dla każdego]: Doradztwo podatkowe',
    'panorama_doradztwo_prawne': 'PANORAMA [Usługi dla każdego]: Doradztwo prawne',
    'panorama_elektroakustyka': 'PANORAMA [Usługi dla każdego]: Elektroakustyka',
    'panorama_elektroinstalatorstwo': 'PANORAMA [Usługi dla każdego]: Elektroinstalatorstwo',
    'panorama_fryzjerzy_i_salony_fryzjerskie': 'PANORAMA [Usługi dla każdego]: Fryzjerzy i salony fryzjerskie',
    'panorama_fundusze_emerytalne': 'PANORAMA [Usługi dla każdego]: Fundusze emerytalne',
    'panorama_genealogia_i_heraldyka': 'PANORAMA [Usługi dla każdego]: Genealogia i heraldyka',
    'panorama_grafika_komputerowa': 'PANORAMA [Usługi dla każdego]: Grafika komputerowa',
    'panorama_grawerowanie': 'PANORAMA [Usługi dla każdego]: Grawerowanie',
    'panorama_handel_obwo%C5%BAny': 'PANORAMA [Usługi dla każdego]: Handel obwoźny',
    'panorama_handel_z%C5%82otem_i_srebrem': 'PANORAMA [Usługi dla każdego]: Handel złotem i srebrem',
    'panorama_hotele_dla_zwierz%C4%85t': 'PANORAMA [Usługi dla każdego]: Hotele dla zwierząt',
    'panorama_hurt_i_produkcja_zegar%C3%B3w_i_zegark%C3%B3w': 'PANORAMA [Usługi dla każdego]: Hurt i produkcja zegarów i zegarków',
    'panorama_hurtownie_sprz%C4%99tu_fotograficznego': 'PANORAMA [Usługi dla każdego]: Hurtownie sprzętu fotograficznego',
    'panorama_hydraulicy': 'PANORAMA [Usługi dla każdego]: Hydraulicy',
    'panorama_internet': 'PANORAMA [Usługi dla każdego]: Internet',
    'panorama_kaletnictwo_i_rymarstwo': 'PANORAMA [Usługi dla każdego]: Kaletnictwo i rymarstwo',
    'panorama_kantory': 'PANORAMA [Usługi dla każdego]: Kantory',
    'panorama_kawiarenki_internetowe': 'PANORAMA [Usługi dla każdego]: Kawiarenki internetowe',
    'panorama_kominiarze': 'PANORAMA [Usługi dla każdego]: Kominiarze',
    'panorama_komisy': 'PANORAMA [Usługi dla każdego]: Komisy',
    'panorama_korepetycje': 'PANORAMA [Usługi dla każdego]: Korepetycje',
    'panorama_krawiectwo': 'PANORAMA [Usługi dla każdego]: Krawiectwo',
    'panorama_ksero': 'PANORAMA [Usługi dla każdego]: Ksero',
    'panorama_kurierzy': 'PANORAMA [Usługi dla każdego]: Kurierzy',
    'panorama_kursy_i_nauka_jazdy': 'PANORAMA [Usługi dla każdego]: Kursy i nauka jazdy',
    'panorama_kwiaciarnie': 'PANORAMA [Usługi dla każdego]: Kwiaciarnie',
    'panorama_leczenie_uzale%C5%BCnie%C5%84': 'PANORAMA [Usługi dla każdego]: Leczenie uzależnień',
    'panorama_lombardy': 'PANORAMA [Usługi dla każdego]: Lombardy',
    'panorama_lornetki_i_lunety': 'PANORAMA [Usługi dla każdego]: Lornetki i lunety',
    'panorama_magiel': 'PANORAMA [Usługi dla każdego]: Magiel',
    'panorama_malowanie_i_tapetowanie': 'PANORAMA [Usługi dla każdego]: Malowanie i tapetowanie',
    'panorama_mapy_i_plany': 'PANORAMA [Usługi dla każdego]: Mapy i plany',
    'panorama_maszyny_do_szycia': 'PANORAMA [Usługi dla każdego]: Maszyny do szycia',
    'panorama_nieruchomo%C5%9Bci': 'PANORAMA [Usługi dla każdego]: Nieruchomości',
    'panorama_notariusze': 'PANORAMA [Usługi dla każdego]: Notariusze',
    'panorama_obs%C5%82uga_cudzoziemc%C3%B3w': 'PANORAMA [Usługi dla każdego]: Obsługa cudzoziemców',
    'panorama_oczyszczanie_%C5%9Bciek%C3%B3w': 'PANORAMA [Usługi dla każdego]: Oczyszczanie ścieków',
    'panorama_odszkodowania': 'PANORAMA [Usługi dla każdego]: Odszkodowania',
    'panorama_odzyskiwanie_i_ochrona_danych_komputerowych': 'PANORAMA [Usługi dla każdego]: Odzyskiwanie i ochrona danych komputerowych',
    'panorama_operatorzy_pocztowi': 'PANORAMA [Usługi dla każdego]: Operatorzy pocztowi',
    'panorama_operatorzy_telekomunikacyjni': 'PANORAMA [Usługi dla każdego]: Operatorzy telekomunikacyjni',
    'panorama_organizacja_imprez_i_konferencji': 'PANORAMA [Usługi dla każdego]: Organizacja imprez i konferencji',
    'panorama_ostrzenie': 'PANORAMA [Usługi dla każdego]: Ostrzenie',
    'panorama_osuszanie_budynk%C3%B3w': 'PANORAMA [Usługi dla każdego]: Osuszanie budynków',
    'panorama_pami%C4%85tki_i_upominki': 'PANORAMA [Usługi dla każdego]: Pamiątki i upominki',
    'panorama_papierosy_elektroniczne': 'PANORAMA [Usługi dla każdego]: Papierosy elektroniczne',
    'panorama_place_i_hale_targowe': 'PANORAMA [Usługi dla każdego]: Place i hale targowe',
    'panorama_poczt%C3%B3wki_i_widok%C3%B3wki': 'PANORAMA [Usługi dla każdego]: Pocztówki i widokówki',
    'panorama_pomoc_domowa': 'PANORAMA [Usługi dla każdego]: Pomoc domowa',
    'panorama_po%C5%9Brednicy_ubezpieczeniowi': 'PANORAMA [Usługi dla każdego]: Pośrednicy ubezpieczeniowi',
    'panorama_produkcja_kosmetyk%C3%B3w': 'PANORAMA [Usługi dla każdego]: Produkcja kosmetyków',
    'panorama_przeprowadzki': 'PANORAMA [Usługi dla każdego]: Przeprowadzki',
    'panorama_radcy_prawni': 'PANORAMA [Usługi dla każdego]: Radcy prawni',
    'panorama_rzeczoznawcy': 'PANORAMA [Usługi dla każdego]: Rzeczoznawcy',
    'panorama_salony_spa_i_odnowa_biologiczna': 'PANORAMA [Usługi dla każdego]: Salony SPA i odnowa biologiczna',
    'panorama_sejfy_i_kasy_pancerne': 'PANORAMA [Usługi dla każdego]: Sejfy i kasy pancerne',
    'panorama_serwis_i_instalacja_klimatyzacji': 'PANORAMA [Usługi dla każdego]: Serwis i instalacja klimatyzacji',
    'panorama_sex_shopy': 'PANORAMA [Usługi dla każdego]: Sex shopy',
    'panorama_si%C5%82ownie_i_fitness': 'PANORAMA [Usługi dla każdego]: Siłownie i fitness',
    'panorama_sklepy_wielobran%C5%BCowe': 'PANORAMA [Usługi dla każdego]: Sklepy wielobranżowe',
    'panorama_solaria': 'PANORAMA [Usługi dla każdego]: Solaria',
    'panorama_sprzeda%C5%BC_wysy%C5%82kowa': 'PANORAMA [Usługi dla każdego]: Sprzedaż wysyłkowa',
    'panorama_sprz%C4%85tanie_wn%C4%99trz_i_mycie_okien': 'PANORAMA [Usługi dla każdego]: Sprzątanie wnętrz i mycie okien',
    'panorama_sprz%C4%99t_fotograficzny': 'PANORAMA [Usługi dla każdego]: Sprzęt fotograficzny',
    'panorama_styli%C5%9Bci_wiza%C5%BCy%C5%9Bci_i_projektanci_mody': 'PANORAMA [Usługi dla każdego]: Styliści, wizażyści i projektanci mody',
    'panorama_supermarkety_i_hipermarkety': 'PANORAMA [Usługi dla każdego]: Supermarkety i hipermarkety',
    'panorama_systemy_i_us%C5%82ugi_telekomunikacyjne': 'PANORAMA [Usługi dla każdego]: Systemy i usługi telekomunikacyjne',
    'panorama_szewc': 'PANORAMA [Usługi dla każdego]: Szewc',
    'panorama_tatua%C5%BCe': 'PANORAMA [Usługi dla każdego]: Tatuaże',
    'panorama_taxi': 'PANORAMA [Usługi dla każdego]: Taxi',
    'panorama_telefony_alarmowe': 'PANORAMA [Usługi dla każdego]: Telefony alarmowe',
    'panorama_telefony_kom%C3%B3rkowe': 'PANORAMA [Usługi dla każdego]: Telefony komórkowe',
    'panorama_telefony_zaufania': 'PANORAMA [Usługi dla każdego]: Telefony zaufania',
    'panorama_telewizja_kablowa': 'PANORAMA [Usługi dla każdego]: Telewizja kablowa',
    'panorama_telewizja_przemys%C5%82owa': 'PANORAMA [Usługi dla każdego]: Telewizja przemysłowa',
    'panorama_telewizja_satelitarna': 'PANORAMA [Usługi dla każdego]: Telewizja satelitarna',
    'panorama_torby_walizki_i_teczki': 'PANORAMA [Usługi dla każdego]: Torby, walizki i teczki',
    'panorama_t%C5%82umacze': 'PANORAMA [Usługi dla każdego]: Tłumacze',
    'panorama_t%C5%82umacze_przysi%C4%99gli': 'PANORAMA [Usługi dla każdego]: Tłumacze przysięgli',
    'panorama_ubezpieczenia': 'PANORAMA [Usługi dla każdego]: Ubezpieczenia',
    'panorama_uk%C5%82adanie_gresu_i_p%C5%82ytek_ceramicznych': 'PANORAMA [Usługi dla każdego]: Układanie gresu i płytek ceramicznych',
    'panorama_uk%C5%82adanie_wyk%C5%82adzin_pod%C5%82ogowych': 'PANORAMA [Usługi dla każdego]: Układanie wykładzin podłogowych',
    'panorama_us%C5%82ugi_fotograficzne': 'PANORAMA [Usługi dla każdego]: Usługi fotograficzne',
    'panorama_us%C5%82ugi_gazownicze': 'PANORAMA [Usługi dla każdego]: Usługi gazownicze',
    'panorama_us%C5%82ugi_kamieniarskie': 'PANORAMA [Usługi dla każdego]: Usługi kamieniarskie',
    'panorama_us%C5%82ugi_pogrzebowe': 'PANORAMA [Usługi dla każdego]: Usługi pogrzebowe',
    'panorama_us%C5%82ugi_tapicerskie': 'PANORAMA [Usługi dla każdego]: Usługi tapicerskie',
    'panorama_wa%C5%BCne_telefony': 'PANORAMA [Usługi dla każdego]: Ważne telefony',
    'panorama_wideofilmowanie': 'PANORAMA [Usługi dla każdego]: Wideofilmowanie',
    'panorama_wycena_nieruchomo%C5%9Bci': 'PANORAMA [Usługi dla każdego]: Wycena nieruchomości',
    'panorama_wypo%C5%BCyczalnie_film%C3%B3w_wideo_i_dvd': 'PANORAMA [Usługi dla każdego]: Wypożyczalnie filmów wideo i DVD',
    'panorama_wypo%C5%BCyczalnie_stroj%C3%B3w': 'PANORAMA [Usługi dla każdego]: Wypożyczalnie strojów',
    'panorama_wyw%C3%B3z_%C5%9Bmieci_i_odpad%C3%B3w': 'PANORAMA [Usługi dla każdego]: Wywóz śmieci i odpadów',
    'panorama_zamki_i_zabezpieczenia_antyw%C5%82amaniowe': 'PANORAMA [Usługi dla każdego]: Zamki i zabezpieczenia antywłamaniowe',
    'panorama_zegarmistrzowie': 'PANORAMA [Usługi dla każdego]: Zegarmistrzowie',
    'panorama_%C5%9Blusarstwo_i_dorabianie_kluczy': 'PANORAMA [Usługi dla każdego]: Ślusarstwo i dorabianie kluczy',
    'panorama_%C5%9Blusarze': 'PANORAMA [Usługi dla każdego]: Ślusarze',
    'panorama_alergolodzy': 'PANORAMA [Zdrowie i uroda]: Alergolodzy',
    'panorama_androlodzy': 'PANORAMA [Zdrowie i uroda]: Androlodzy',
    'panorama_anestezjolodzy': 'PANORAMA [Zdrowie i uroda]: Anestezjolodzy',
    'panorama_aparaty_s%C5%82uchowe': 'PANORAMA [Zdrowie i uroda]: Aparaty słuchowe',
    'panorama_apteki': 'PANORAMA [Zdrowie i uroda]: Apteki',
    'panorama_artyku%C5%82y_i_sprz%C4%99t_pszczelarski': 'PANORAMA [Zdrowie i uroda]: Artykuły i sprzęt pszczelarski',
    'panorama_artyku%C5%82y_ortopedyczne': 'PANORAMA [Zdrowie i uroda]: Artykuły ortopedyczne',
    'panorama_baseny_i_parki_wodne': 'PANORAMA [Zdrowie i uroda]: Baseny i parki wodne',
    'panorama_bi%C5%BCuteria_sztuczna': 'PANORAMA [Zdrowie i uroda]: Biżuteria sztuczna',
    'panorama_bi%C5%BCuteria_z%C5%82ota_i_srebrna': 'PANORAMA [Zdrowie i uroda]: Biżuteria złota i srebrna',
    'panorama_budowa_i_wyposa%C5%BCenie_saun': 'PANORAMA [Zdrowie i uroda]: Budowa i wyposażenie saun',
    'panorama_chirurdzy': 'PANORAMA [Zdrowie i uroda]: Chirurdzy',
    'panorama_chirurgia_plastyczna': 'PANORAMA [Zdrowie i uroda]: Chirurgia plastyczna',
    'panorama_dermatolodzy': 'PANORAMA [Zdrowie i uroda]: Dermatolodzy',
    'panorama_diabetolodzy': 'PANORAMA [Zdrowie i uroda]: Diabetolodzy',
    'panorama_dietetycy': 'PANORAMA [Zdrowie i uroda]: Dietetycy',
    'panorama_domy_i_o%C5%9Brodki_pomocy_spo%C5%82ecznej': 'PANORAMA [Zdrowie i uroda]: Domy i ośrodki pomocy społecznej',
    'panorama_dozowniki_myd%C5%82a': 'PANORAMA [Zdrowie i uroda]: Dozowniki mydła',
    'panorama_endokrynolodzy': 'PANORAMA [Zdrowie i uroda]: Endokrynolodzy',
    'panorama_fryzjerzy_dla_zwierz%C4%85t': 'PANORAMA [Zdrowie i uroda]: Fryzjerzy dla zwierząt',
    'panorama_fryzjerzy_i_salony_fryzjerskie': 'PANORAMA [Zdrowie i uroda]: Fryzjerzy i salony fryzjerskie',
    'panorama_gabinety_podologiczne': 'PANORAMA [Zdrowie i uroda]: Gabinety podologiczne',
    'panorama_gastrolodzy': 'PANORAMA [Zdrowie i uroda]: Gastrolodzy',
    'panorama_genetycy': 'PANORAMA [Zdrowie i uroda]: Genetycy',
    'panorama_geriatrzy': 'PANORAMA [Zdrowie i uroda]: Geriatrzy',
    'panorama_ginekolodzy_i_po%C5%82o%C5%BCnicy': 'PANORAMA [Zdrowie i uroda]: Ginekolodzy i położnicy',
    'panorama_hematolodzy': 'PANORAMA [Zdrowie i uroda]: Hematolodzy',
    'panorama_homeopaci': 'PANORAMA [Zdrowie i uroda]: Homeopaci',
    'panorama_hospicja': 'PANORAMA [Zdrowie i uroda]: Hospicja',
    'panorama_hurtownie_artyku%C5%82%C3%B3w_higienicznych': 'PANORAMA [Zdrowie i uroda]: Hurtownie artykułów higienicznych',
    'panorama_hurtownie_bi%C5%BCuterii': 'PANORAMA [Zdrowie i uroda]: Hurtownie biżuterii',
    'panorama_hurtownie_farmaceutyczne': 'PANORAMA [Zdrowie i uroda]: Hurtownie farmaceutyczne',
    'panorama_hurtownie_kosmetyczne': 'PANORAMA [Zdrowie i uroda]: Hurtownie kosmetyczne',
    'panorama_instrumenty_optyczne': 'PANORAMA [Zdrowie i uroda]: Instrumenty optyczne',
    'panorama_interni%C5%9Bci': 'PANORAMA [Zdrowie i uroda]: Interniści',
    'panorama_jubilerstwo': 'PANORAMA [Zdrowie i uroda]: Jubilerstwo',
    'panorama_kardiolodzy': 'PANORAMA [Zdrowie i uroda]: Kardiolodzy',
    'panorama_laboratoria_medyczne': 'PANORAMA [Zdrowie i uroda]: Laboratoria medyczne',
    'panorama_laryngolodzy': 'PANORAMA [Zdrowie i uroda]: Laryngolodzy',
    'panorama_leczenie_chor%C3%B3b_zaka%C5%BAnych': 'PANORAMA [Zdrowie i uroda]: Leczenie chorób zakaźnych',
    'panorama_leczenie_uzale%C5%BCnie%C5%84': 'PANORAMA [Zdrowie i uroda]: Leczenie uzależnień',
    'panorama_lekarskie_wizyty_domowe': 'PANORAMA [Zdrowie i uroda]: Lekarskie wizyty domowe',
    'panorama_lekarze_analitycy': 'PANORAMA [Zdrowie i uroda]: Lekarze analitycy',
    'panorama_lekarze_medycyny_estetycznej': 'PANORAMA [Zdrowie i uroda]: Lekarze medycyny estetycznej',
    'panorama_lekarze_medycyny_paliatywnej': 'PANORAMA [Zdrowie i uroda]: Lekarze medycyny paliatywnej',
    'panorama_lekarze_medycyny_pracy': 'PANORAMA [Zdrowie i uroda]: Lekarze medycyny pracy',
    'panorama_lekarze_rodzinni': 'PANORAMA [Zdrowie i uroda]: Lekarze rodzinni',
    'panorama_lekarze_uzale%C5%BCnie%C5%84_alkoholowych': 'PANORAMA [Zdrowie i uroda]: Lekarze uzależnień alkoholowych',
    'panorama_logopedzi': 'PANORAMA [Zdrowie i uroda]: Logopedzi',
    'panorama_masa%C5%BC': 'PANORAMA [Zdrowie i uroda]: Masaż',
    'panorama_medycyna_naturalna': 'PANORAMA [Zdrowie i uroda]: Medycyna naturalna',
    'panorama_mobilne_us%C5%82ugi_fryzjerskie': 'PANORAMA [Zdrowie i uroda]: Mobilne usługi fryzjerskie',
    'panorama_mobilne_us%C5%82ugi_kosmetyczne': 'PANORAMA [Zdrowie i uroda]: Mobilne usługi kosmetyczne',
    'panorama_narodowy_fundusz_zdrowia': 'PANORAMA [Zdrowie i uroda]: Narodowy Fundusz Zdrowia',
    'panorama_nefrolodzy': 'PANORAMA [Zdrowie i uroda]: Nefrolodzy',
    'panorama_neurochirurdzy': 'PANORAMA [Zdrowie i uroda]: Neurochirurdzy',
    'panorama_neurolodzy': 'PANORAMA [Zdrowie i uroda]: Neurolodzy',
    'panorama_odchudzanie': 'PANORAMA [Zdrowie i uroda]: Odchudzanie',
    'panorama_od%C5%BCywki_i_suplementy_diety': 'PANORAMA [Zdrowie i uroda]: Odżywki i suplementy diety',
    'panorama_okulary': 'PANORAMA [Zdrowie i uroda]: Okulary',
    'panorama_okuli%C5%9Bci': 'PANORAMA [Zdrowie i uroda]: Okuliści',
    'panorama_onkolodzy': 'PANORAMA [Zdrowie i uroda]: Onkolodzy',
    'panorama_opieka_prywatna_nad_osobami_starszymi': 'PANORAMA [Zdrowie i uroda]: Opieka prywatna nad osobami starszymi',
    'panorama_optycy': 'PANORAMA [Zdrowie i uroda]: Optycy',
    'panorama_ortodonci': 'PANORAMA [Zdrowie i uroda]: Ortodonci',
    'panorama_ortopedzi': 'PANORAMA [Zdrowie i uroda]: Ortopedzi',
    'panorama_patomorfolodzy': 'PANORAMA [Zdrowie i uroda]: Patomorfolodzy',
    'panorama_pediatrzy': 'PANORAMA [Zdrowie i uroda]: Pediatrzy',
    'panorama_peruki_i_treski': 'PANORAMA [Zdrowie i uroda]: Peruki i treski',
    'panorama_piel%C4%99gniarki': 'PANORAMA [Zdrowie i uroda]: Pielęgniarki',
    'panorama_pogotowie_ratunkowe': 'PANORAMA [Zdrowie i uroda]: Pogotowie ratunkowe',
    'panorama_praktyka_lekarska': 'PANORAMA [Zdrowie i uroda]: Praktyka lekarska',
    'panorama_prezerwatywy': 'PANORAMA [Zdrowie i uroda]: Prezerwatywy',
    'panorama_producenci_farmaceutyk%C3%B3w': 'PANORAMA [Zdrowie i uroda]: Producenci farmaceutyków',
    'panorama_produkcja_artyku%C5%82%C3%B3w_higienicznych': 'PANORAMA [Zdrowie i uroda]: Produkcja artykułów higienicznych',
    'panorama_produkcja_kosmetyk%C3%B3w': 'PANORAMA [Zdrowie i uroda]: Produkcja kosmetyków',
    'panorama_proktolodzy': 'PANORAMA [Zdrowie i uroda]: Proktolodzy',
    'panorama_przed%C5%82u%C5%BCanie_i_zag%C4%99szczanie_w%C5%82os%C3%B3w': 'PANORAMA [Zdrowie i uroda]: Przedłużanie i zagęszczanie włosów',
    'panorama_przewozy_os%C3%B3b_niepe%C5%82nosprawnych': 'PANORAMA [Zdrowie i uroda]: Przewozy osób niepełnosprawnych',
    'panorama_przychodnie_prywatne': 'PANORAMA [Zdrowie i uroda]: Przychodnie prywatne',
    'panorama_psychiatrzy_psycholodzy_i_psychoterapeuci': 'PANORAMA [Zdrowie i uroda]: Psychiatrzy psycholodzy i psychoterapeuci',
    'panorama_publiczne_przychodnie_i_o%C5%9Brodki_zdrowia': 'PANORAMA [Zdrowie i uroda]: Publiczne przychodnie i ośrodki zdrowia',
    'panorama_pulmonolodzy': 'PANORAMA [Zdrowie i uroda]: Pulmonolodzy',
    'panorama_radiolodzy': 'PANORAMA [Zdrowie i uroda]: Radiolodzy',
    'panorama_rehabilitacja': 'PANORAMA [Zdrowie i uroda]: Rehabilitacja',
    'panorama_rehabilitacja_medyczna': 'PANORAMA [Zdrowie i uroda]: Rehabilitacja medyczna',
    'panorama_reumatolodzy': 'PANORAMA [Zdrowie i uroda]: Reumatolodzy',
    'panorama_salony_spa_i_odnowa_biologiczna': 'PANORAMA [Zdrowie i uroda]: Salony SPA i odnowa biologiczna',
    'panorama_salony_i_gabinety_kosmetyczne': 'PANORAMA [Zdrowie i uroda]: Salony i gabinety kosmetyczne',
    'panorama_sanatoria': 'PANORAMA [Zdrowie i uroda]: Sanatoria',
    'panorama_seksuolodzy': 'PANORAMA [Zdrowie i uroda]: Seksuolodzy',
    'panorama_si%C5%82ownie_i_fitness': 'PANORAMA [Zdrowie i uroda]: Siłownie i fitness',
    'panorama_sklepy_z_artyku%C5%82ami_kosmetycznymi': 'PANORAMA [Zdrowie i uroda]: Sklepy z artykułami kosmetycznymi',
    'panorama_solaria': 'PANORAMA [Zdrowie i uroda]: Solaria',
    'panorama_sprz%C4%99t_i_materia%C5%82y_stomatologiczne': 'PANORAMA [Zdrowie i uroda]: Sprzęt i materiały stomatologiczne',
    'panorama_sprz%C4%99t_i_wyposa%C5%BCenie_salon%C3%B3w_spa': 'PANORAMA [Zdrowie i uroda]: Sprzęt i wyposażenie salonów SPA',
    'panorama_sprz%C4%99t_i_wyposa%C5%BCenie_solari%C3%B3w': 'PANORAMA [Zdrowie i uroda]: Sprzęt i wyposażenie solariów',
    'panorama_sprz%C4%99t_rehabilitacyjny': 'PANORAMA [Zdrowie i uroda]: Sprzęt rehabilitacyjny',
    'panorama_stomatolodzy_i_protetycy': 'PANORAMA [Zdrowie i uroda]: Stomatolodzy i protetycy',
    'panorama_styli%C5%9Bci_wiza%C5%BCy%C5%9Bci_i_projektanci_mody': 'PANORAMA [Zdrowie i uroda]: Styliści, wizażyści i projektanci mody',
    'panorama_szko%C5%82y_rodzenia': 'PANORAMA [Zdrowie i uroda]: Szkoły rodzenia',
    'panorama_szpitale_i_kliniki_prywatne': 'PANORAMA [Zdrowie i uroda]: Szpitale i kliniki prywatne',
    'panorama_szpitale_i_kliniki_publiczne': 'PANORAMA [Zdrowie i uroda]: Szpitale i kliniki publiczne',
    'panorama_tatua%C5%BCe': 'PANORAMA [Zdrowie i uroda]: Tatuaże',
    'panorama_ubezpieczenia_spo%C5%82eczne': 'PANORAMA [Zdrowie i uroda]: Ubezpieczenia społeczne',
    'panorama_urolodzy': 'PANORAMA [Zdrowie i uroda]: Urolodzy',
    'panorama_wyposa%C5%BCenie_i_sprz%C4%99t_medyczny': 'PANORAMA [Zdrowie i uroda]: Wyposażenie i sprzęt medyczny',
    'panorama_zak%C5%82ady_opieku%C5%84czo_lecznicze': 'PANORAMA [Zdrowie i uroda]: Zakłady opiekuńczo-lecznicze',
    'panorama_%C5%BCywno%C5%9B%C4%87_ekologiczna': 'PANORAMA [Zdrowie i uroda]: Żywność ekologiczna',
    'panorama_aromaty_i_dodatki_do_%C5%BCywno%C5%9Bci': 'PANORAMA [Żywność i używki]: Aromaty i dodatki do żywności',
    'panorama_bary': 'PANORAMA [Żywność i używki]: Bary',
    'panorama_catering': 'PANORAMA [Żywność i używki]: Catering',
    'panorama_cukiernie_i_sklepy_cukiernicze': 'PANORAMA [Żywność i używki]: Cukiernie i sklepy cukiernicze',
    'panorama_cukrownie': 'PANORAMA [Żywność i używki]: Cukrownie',
    'panorama_grzyby_i_runo_le%C5%9Bne': 'PANORAMA [Żywność i używki]: Grzyby i runo leśne',
    'panorama_herbata': 'PANORAMA [Żywność i używki]: Herbata',
    'panorama_hodowla_i_hurtownie_ryb': 'PANORAMA [Żywność i używki]: Hodowla i hurtownie ryb',
    'panorama_hurtownie_alkoholi': 'PANORAMA [Żywność i używki]: Hurtownie alkoholi',
    'panorama_hurtownie_cukiernicze': 'PANORAMA [Żywność i używki]: Hurtownie cukiernicze',
    'panorama_hurtownie_mi%C4%99sa_w%C4%99dlin_i_drobiu': 'PANORAMA [Żywność i używki]: Hurtownie mięsa, wędlin i drobiu',
    'panorama_hurtownie_nabia%C5%82u': 'PANORAMA [Żywność i używki]: Hurtownie nabiału',
    'panorama_hurtownie_spo%C5%BCywcze': 'PANORAMA [Żywność i używki]: Hurtownie spożywcze',
    'panorama_hurtownie_warzyw_i_owoc%C3%B3w': 'PANORAMA [Żywność i używki]: Hurtownie warzyw i owoców',
    'panorama_jaja': 'PANORAMA [Żywność i używki]: Jaja',
    'panorama_kawa': 'PANORAMA [Żywność i używki]: Kawa',
    'panorama_kawiarnie': 'PANORAMA [Żywność i używki]: Kawiarnie',
    'panorama_mi%C3%B3d_i_produkty_pszczelarskie': 'PANORAMA [Żywność i używki]: Miód i produkty pszczelarskie',
    'panorama_mi%C4%99so_i_w%C4%99dliny': 'PANORAMA [Żywność i używki]: Mięso i wędliny',
    'panorama_mro%C5%BConki': 'PANORAMA [Żywność i używki]: Mrożonki',
    'panorama_m%C4%85ka': 'PANORAMA [Żywność i używki]: Mąka',
    'panorama_napoje_orze%C5%BAwiaj%C4%85ce_i_wody': 'PANORAMA [Żywność i używki]: Napoje orzeźwiające i wody',
    'panorama_oleje_i_t%C5%82uszcze_spo%C5%BCywcze': 'PANORAMA [Żywność i używki]: Oleje i tłuszcze spożywcze',
    'panorama_papierosy_elektroniczne': 'PANORAMA [Żywność i używki]: Papierosy elektroniczne',
    'panorama_papierosy_i_tyto%C5%84': 'PANORAMA [Żywność i używki]: Papierosy i tytoń',
    'panorama_piekarnie': 'PANORAMA [Żywność i używki]: Piekarnie',
    'panorama_pizzerie': 'PANORAMA [Żywność i używki]: Pizzerie',
    'panorama_producenci_alkoholi': 'PANORAMA [Żywność i używki]: Producenci alkoholi',
    'panorama_producenci_i_hurtownie_lod%C3%B3w': 'PANORAMA [Żywność i używki]: Producenci i hurtownie lodów',
    'panorama_producenci_i_hurtownie_piwa': 'PANORAMA [Żywność i używki]: Producenci i hurtownie piwa',
    'panorama_producenci_i_hurtownie_%C5%BCywno%C5%9Bci_ekologicznej': 'PANORAMA [Żywność i używki]: Producenci i hurtownie żywności ekologicznej',
    'panorama_producenci_mi%C4%99sa_w%C4%99dlin_i_drobiu': 'PANORAMA [Żywność i używki]: Producenci mięsa, wędlin i drobiu',
    'panorama_producenci_%C5%BCywno%C5%9Bci': 'PANORAMA [Żywność i używki]: Producenci żywności',
    'panorama_produkcja_nabia%C5%82u': 'PANORAMA [Żywność i używki]: Produkcja nabiału',
    'panorama_produkcja_wyrob%C3%B3w_cukierniczych': 'PANORAMA [Żywność i używki]: Produkcja wyrobów cukierniczych',
    'panorama_przetw%C3%B3rstwo_rybne': 'PANORAMA [Żywność i używki]: Przetwórstwo rybne',
    'panorama_przetw%C3%B3rstwo_warzyw_i_owoc%C3%B3w': 'PANORAMA [Żywność i używki]: Przetwórstwo warzyw i owoców',
    'panorama_puby': 'PANORAMA [Żywność i używki]: Puby',
    'panorama_rybo%C5%82%C3%B3wstwo': 'PANORAMA [Żywność i używki]: Rybołówstwo',
    'panorama_ryby_i_owoce_morza': 'PANORAMA [Żywność i używki]: Ryby i owoce morza',
    'panorama_sklepy_monopolowe': 'PANORAMA [Żywność i używki]: Sklepy monopolowe',
    'panorama_sklepy_owocowo_warzywne': 'PANORAMA [Żywność i używki]: Sklepy owocowo-warzywne',
    'panorama_sklepy_spo%C5%BCywcze': 'PANORAMA [Żywność i używki]: Sklepy spożywcze',
    'panorama_urz%C4%85dzenia_do_produkcji_%C5%BCywno%C5%9Bci': 'PANORAMA [Żywność i używki]: Urządzenia do produkcji żywności',
    'panorama_wyposa%C5%BCenie_i_zaopatrzenie_piekarni': 'PANORAMA [Żywność i używki]: Wyposażenie i zaopatrzenie piekarni',
    'panorama_zaopatrzenie_i_wyposa%C5%BCenie_gastronomiczne': 'PANORAMA [Żywność i używki]: Zaopatrzenie i wyposażenie gastronomiczne',
    'panorama_zio%C5%82a_i_przyprawy': 'PANORAMA [Żywność i używki]: Zioła i przyprawy',
    'panorama_%C5%BCywno%C5%9B%C4%87_ekologiczna': 'PANORAMA [Żywność i używki]: Żywność ekologiczna',
    # Speciální sekce bez podkategorií (přímé seznamy firem)
    'panorama_biuro_z': 'PANORAMA [Biuro]: Wszystkie firmy',
    'panorama_kancelaria_o': 'PANORAMA [Kancelaria]: Wszystkie firmy',
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

@app.route('/start_all', methods=['POST'])
def start_all_scraping():
    """Spustí scraping pro všechny kategorie v sekci"""
    if scraping_status['running']:
        logger.warning("Scraping již běží - odmítám nový požadavek")
        return jsonify({'error': 'Scraping již běží'}), 400
    
    try:
        data = request.json
        categories = data.get('categories', [])
        max_companies = int(data.get('max_companies', 10))
        
        logger.info(f"Přijat požadavek na scraping VŠECH kategorií: počet={len(categories)}, max_companies={max_companies}")
        
        # Validace
        invalid_cats = [c for c in categories if c not in CATEGORIES]
        if invalid_cats:
            logger.error(f"Neplatné kategorie: {invalid_cats[:5]}")
            return jsonify({'error': 'Některé kategorie jsou neplatné'}), 400
        
        # Spustit v threadu
        thread = threading.Thread(target=scrape_all_categories_thread, args=(categories, max_companies))
        thread.start()
        logger.info(f"Thread pro {len(categories)} kategorií spuštěn")
        
        return jsonify({'status': 'started'})
    except Exception as e:
        logger.error(f"Chyba při startu all scrapingu: {str(e)}", exc_info=True)
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

@app.route('/api/sections')
def get_sections():
    """Vrátí seznam všech hlavních sekcí"""
    sections = set()
    for name in CATEGORIES.values():
        if name.startswith('PANORAMA ['):
            # Extrahovat název sekce z formátu "PANORAMA [Section]: Category"
            section = name.split('[')[1].split(']')[0]
            sections.add(section)
    return jsonify(sorted(list(sections)))

@app.route('/api/subcategories/<section>')
def get_subcategories(section):
    """Vrátí všechny podkategorie pro danou sekci"""
    subcategories = {}
    for slug, name in CATEGORIES.items():
        if name.startswith(f'PANORAMA [{section}]:'):
            subcategories[slug] = name
    return jsonify(subcategories)

if __name__ == '__main__':
    logger.info("=== APLIKACE STARTUJE ===")
    logger.info(f"Počet kategorií: {len(CATEGORIES)}")
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Spouštím Flask na portu {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
