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
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Nastavit logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
    # DEMO VERZE - Pouze 2 kategorie (po zaplacení odkomentujte zbytek)
    'panorama_https://panoramafirm.pl/aerozole': 'PANORAMA: Aerozole',
    'panorama_https://panoramafirm.pl/agregaty_pr%C4%85dotw%C3%B3rcze': 'PANORAMA: Agregaty prądotwórcze',
}

# Po zaplacení odkomentujte všechny kategorie níže a smažte řádek výše s }
"""
CATEGORIES = {
    'panorama_https://panoramafirm.pl/aerozole': 'PANORAMA: Aerozole',
    'panorama_https://panoramafirm.pl/agregaty_pr%C4%85dotw%C3%B3rcze': 'PANORAMA: Agregaty prądotwórcze',
    'panorama_https://panoramafirm.pl/agregaty_komory_i_meble_ch%C5%82odnicze': 'PANORAMA: Agregaty, komory i meble chłodnicze',
    'panorama_https://panoramafirm.pl/akumulatory_i_baterie': 'PANORAMA: Akumulatory i baterie',
    'panorama_https://panoramafirm.pl/armatura_hydrauliczna': 'PANORAMA: Armatura hydrauliczna',
    'panorama_https://panoramafirm.pl/armatura_przemys%C5%82owa': 'PANORAMA: Armatura przemysłowa',
    'panorama_https://panoramafirm.pl/artyku%C5%82y_elektrotechniczne': 'PANORAMA: Artykuły elektrotechniczne',
    'panorama_https://panoramafirm.pl/artyku%C5%82y_metalowe': 'PANORAMA: Artykuły metalowe',
    'panorama_https://panoramafirm.pl/automatyka': 'PANORAMA: Automatyka',
    'panorama_https://panoramafirm.pl/autoz%C5%82om': 'PANORAMA: Autozłom',
    'panorama_https://panoramafirm.pl/badania_nieniszcz%C4%85ce': 'PANORAMA: Badania nieniszczące',
    'panorama_https://panoramafirm.pl/biopaliwa': 'PANORAMA: Biopaliwa',
    'panorama_https://panoramafirm.pl/bro%C5%84_i_amunicja': 'PANORAMA: Broń i amunicja',
    'panorama_https://panoramafirm.pl/brykiety_i_w%C4%99giel_drzewny': 'PANORAMA: Brykiety i węgiel drzewny',
    'panorama_https://panoramafirm.pl/budowa_i_sprz%C4%99t_drogowy': 'PANORAMA: Budowa i sprzęt drogowy',
    'panorama_https://panoramafirm.pl/budowa_i_wyposa%C5%BCenie_stacji_paliw': 'PANORAMA: Budowa i wyposażenie stacji paliw',
    'panorama_https://panoramafirm.pl/budowa_wyposa%C5%BCenie_i_remont_statk%C3%B3w': 'PANORAMA: Budowa, wyposażenie i remont statków',
    'panorama_https://panoramafirm.pl/budownictwo_kolejowe': 'PANORAMA: Budownictwo kolejowe',
    'panorama_https://panoramafirm.pl/budownictwo_przemys%C5%82owe': 'PANORAMA: Budownictwo przemysłowe',
    'panorama_https://panoramafirm.pl/chemia_gospodarcza': 'PANORAMA: Chemia gospodarcza',
    'panorama_https://panoramafirm.pl/czyszcz%C4%85ce_urz%C4%85dzenia_przemys%C5%82owe': 'PANORAMA: Czyszczące urządzenia przemysłowe',
    'panorama_https://panoramafirm.pl/czy%C5%9Bciwa_przemys%C5%82owe': 'PANORAMA: Czyściwa przemysłowe',
    'panorama_https://panoramafirm.pl/drabiny': 'PANORAMA: Drabiny',
    'panorama_https://panoramafirm.pl/drewno': 'PANORAMA: Drewno',
    'panorama_https://panoramafirm.pl/drewno_budowlane': 'PANORAMA: Drewno budowlane',
    'panorama_https://panoramafirm.pl/drewno_opa%C5%82owe': 'PANORAMA: Drewno opałowe',
    'panorama_https://panoramafirm.pl/drut_i_liny_stalowe': 'PANORAMA: Drut i liny stalowe',
    'panorama_https://panoramafirm.pl/dystrybucja_energii_elektrycznej': 'PANORAMA: Dystrybucja energii elektrycznej',
    'panorama_https://panoramafirm.pl/d%C5%BAwigi_i_%C5%BCurawie': 'PANORAMA: Dźwigi i żurawie',
    'panorama_https://panoramafirm.pl/elektrociep%C5%82ownie': 'PANORAMA: Elektrociepłownie',
    'panorama_https://panoramafirm.pl/elektronarz%C4%99dzia': 'PANORAMA: Elektronarzędzia',
    'panorama_https://panoramafirm.pl/energia_odnawialna': 'PANORAMA: Energia odnawialna',
    'panorama_https://panoramafirm.pl/farby_i_lakiery': 'PANORAMA: Farby i lakiery',
    'panorama_https://panoramafirm.pl/filtry': 'PANORAMA: Filtry',
    'panorama_https://panoramafirm.pl/formy_wtryskowe': 'PANORAMA: Formy wtryskowe',
    'panorama_https://panoramafirm.pl/galwanizacja': 'PANORAMA: Galwanizacja',
    'panorama_https://panoramafirm.pl/gaz_ziemny': 'PANORAMA: Gaz ziemny',
    'panorama_https://panoramafirm.pl/gazy_techniczne': 'PANORAMA: Gazy techniczne',
    'panorama_https://panoramafirm.pl/g%C3%B3rnicze_materia%C5%82y_wybuchowe': 'PANORAMA: Górnicze materiały wybuchowe',
    'panorama_https://panoramafirm.pl/grzejnictwo_elektryczne': 'PANORAMA: Grzejnictwo elektryczne',
    'panorama_https://panoramafirm.pl/hurtownie_artyku%C5%82%C3%B3w_elektrotechnicznych': 'PANORAMA: Hurtownie artykułów elektrotechnicznych',
    'panorama_https://panoramafirm.pl/hurtownie_artyku%C5%82%C3%B3w_metalowych': 'PANORAMA: Hurtownie artykułów metalowych',
    'panorama_https://panoramafirm.pl/hurtownie_chemii_gospodarczej': 'PANORAMA: Hurtownie chemii gospodarczej',
    'panorama_https://panoramafirm.pl/hurtownie_cz%C4%99%C5%9Bci_elektronicznych': 'PANORAMA: Hurtownie części elektronicznych',
    'panorama_https://panoramafirm.pl/hurtownie_farb_lakier%C3%B3w_i_emalii': 'PANORAMA: Hurtownie farb, lakierów i emalii',
    'panorama_https://panoramafirm.pl/hurtownie_%C5%9Brodk%C3%B3w_chemicznych': 'PANORAMA: Hurtownie środków chemicznych',
    'panorama_https://panoramafirm.pl/hurtownie_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA: Hurtownie urządzeń elektrycznych',
    'panorama_https://panoramafirm.pl/hydraulika_si%C5%82owa': 'PANORAMA: Hydraulika siłowa',
    'panorama_https://panoramafirm.pl/hydrotechnika': 'PANORAMA: Hydrotechnika',
    'panorama_https://panoramafirm.pl/instalacja_i_serwis_ogrzewania': 'PANORAMA: Instalacja i serwis ogrzewania',
    'panorama_https://panoramafirm.pl/instalacje_i_urz%C4%85dzenia_energetyczne': 'PANORAMA: Instalacje i urządzenia energetyczne',
    'panorama_https://panoramafirm.pl/instalacje_przemys%C5%82owe': 'PANORAMA: Instalacje przemysłowe',
    'panorama_https://panoramafirm.pl/inwestycje_budowlane': 'PANORAMA: Inwestycje budowlane',
    'panorama_https://panoramafirm.pl/kleje_i_%C5%BCywice': 'PANORAMA: Kleje i żywice',
    'panorama_https://panoramafirm.pl/kompresory': 'PANORAMA: Kompresory',
    'panorama_https://panoramafirm.pl/konstrukcje_aluminiowe': 'PANORAMA: Konstrukcje aluminiowe',
    'panorama_https://panoramafirm.pl/konstrukcje_stalowe': 'PANORAMA: Konstrukcje stalowe',
    'panorama_https://panoramafirm.pl/kontenery': 'PANORAMA: Kontenery',
    'panorama_https://panoramafirm.pl/kraty_pomostowe': 'PANORAMA: Kraty pomostowe',
    'panorama_https://panoramafirm.pl/laminaty': 'PANORAMA: Laminaty',
    'panorama_https://panoramafirm.pl/lasery': 'PANORAMA: Lasery',
    'panorama_https://panoramafirm.pl/liczniki_energii_elektrycznej': 'PANORAMA: Liczniki energii elektrycznej',
    'panorama_https://panoramafirm.pl/%C5%82a%C5%84cuchy': 'PANORAMA: Łańcuchy',
    'panorama_https://panoramafirm.pl/%C5%82o%C5%BCyska': 'PANORAMA: Łożyska',
    'panorama_https://panoramafirm.pl/magnesy_i_elektromagnesy': 'PANORAMA: Magnesy i elektromagnesy',
    'panorama_https://panoramafirm.pl/malowanie_i_lakierowanie_przemys%C5%82owe': 'PANORAMA: Malowanie i lakierowanie przemysłowe',
    'panorama_https://panoramafirm.pl/maszty_i_s%C5%82upy': 'PANORAMA: Maszty i słupy',
    'panorama_https://panoramafirm.pl/maszyny_do_obr%C3%B3bki_drewna': 'PANORAMA: Maszyny do obróbki drewna',
    'panorama_https://panoramafirm.pl/maszyny_do_obr%C3%B3bki_metali': 'PANORAMA: Maszyny do obróbki metali',
    'panorama_https://panoramafirm.pl/maszyny_dziewiarskie': 'PANORAMA: Maszyny dziewiarskie',
    'panorama_https://panoramafirm.pl/maszyny_i_sprz%C4%99t_g%C3%B3rniczy': 'PANORAMA: Maszyny i sprzęt górniczy',
    'panorama_https://panoramafirm.pl/maszyny_pakuj%C4%85ce': 'PANORAMA: Maszyny pakujące',
    'panorama_https://panoramafirm.pl/materia%C5%82y_do_spawania_i_zgrzewania': 'PANORAMA: Materiały do spawania i zgrzewania',
    'panorama_https://panoramafirm.pl/materia%C5%82y_drewnopochodne': 'PANORAMA: Materiały drewnopochodne',
    'panorama_https://panoramafirm.pl/materia%C5%82y_elektryczne': 'PANORAMA: Materiały elektryczne',
    'panorama_https://panoramafirm.pl/materia%C5%82y_ognioodporne': 'PANORAMA: Materiały ognioodporne',
    'panorama_https://panoramafirm.pl/materia%C5%82y_%C5%9Bcierne_i_polerskie': 'PANORAMA: Materiały ścierne i polerskie',
    'panorama_https://panoramafirm.pl/metale_nie%C5%BCelazne_i_kolorowe': 'PANORAMA: Metale nieżelazne i kolorowe',
    'panorama_https://panoramafirm.pl/metale_%C5%BCelazne': 'PANORAMA: Metale żelazne',
    'panorama_https://panoramafirm.pl/metalizowanie_i_powlekanie_tworzyw': 'PANORAMA: Metalizowanie i powlekanie tworzyw',
    'panorama_https://panoramafirm.pl/nape%C5%82nianie_butli_gazowych': 'PANORAMA: Napełnianie butli gazowych',
    'panorama_https://panoramafirm.pl/narz%C4%99dzia': 'PANORAMA: Narzędzia',
    'panorama_https://panoramafirm.pl/narz%C4%99dzia_pneumatyczne': 'PANORAMA: Narzędzia pneumatyczne',
    'panorama_https://panoramafirm.pl/obr%C3%B3bka_metali': 'PANORAMA: Obróbka metali',
    'panorama_https://panoramafirm.pl/obr%C3%B3bka_tworzyw_sztucznych': 'PANORAMA: Obróbka tworzyw sztucznych',
    'panorama_https://panoramafirm.pl/odlewnie': 'PANORAMA: Odlewnie',
    'panorama_https://panoramafirm.pl/ogrzewanie_elektryczne': 'PANORAMA: Ogrzewanie elektryczne',
    'panorama_https://panoramafirm.pl/okucia': 'PANORAMA: Okucia',
    'panorama_https://panoramafirm.pl/olej_opa%C5%82owy': 'PANORAMA: Olej opałowy',
    'panorama_https://panoramafirm.pl/oleje_techniczne_i_smary': 'PANORAMA: Oleje techniczne i smary',
    'panorama_https://panoramafirm.pl/opakowania': 'PANORAMA: Opakowania',
    'panorama_https://panoramafirm.pl/opakowania_foliowe': 'PANORAMA: Opakowania foliowe',
    'panorama_https://panoramafirm.pl/opakowania_jednorazowe': 'PANORAMA: Opakowania jednorazowe',
    'panorama_https://panoramafirm.pl/opakowania_z_tworzyw_sztucznych': 'PANORAMA: Opakowania z tworzyw sztucznych',
    'panorama_https://panoramafirm.pl/palety': 'PANORAMA: Palety',
    'panorama_https://panoramafirm.pl/paliwa_i_opa%C5%82_ekologiczny': 'PANORAMA: Paliwa i opał ekologiczny',
    'panorama_https://panoramafirm.pl/pasy_nap%C4%99dowe_i_transportuj%C4%85ce': 'PANORAMA: Pasy napędowe i transportujące',
    'panorama_https://panoramafirm.pl/p%C4%99dzle_i_szczotki': 'PANORAMA: Pędzle i szczotki',
    'panorama_https://panoramafirm.pl/piece': 'PANORAMA: Piece',
    'panorama_https://panoramafirm.pl/pirotechnika': 'PANORAMA: Pirotechnika',
    'panorama_https://panoramafirm.pl/pneumatyka_si%C5%82owa': 'PANORAMA: Pneumatyka siłowa',
    'panorama_https://panoramafirm.pl/podno%C5%9Bniki': 'PANORAMA: Podnośniki',
    'panorama_https://panoramafirm.pl/podzespo%C5%82y_elektroniczne': 'PANORAMA: Podzespoły elektroniczne',
    'panorama_https://panoramafirm.pl/pompy': 'PANORAMA: Pompy',
    'panorama_https://panoramafirm.pl/posadzki_przemys%C5%82owe': 'PANORAMA: Posadzki przemysłowe',
    'panorama_https://panoramafirm.pl/prace_podwodne': 'PANORAMA: Prace podwodne',
    'panorama_https://panoramafirm.pl/producenci_farb_i_lakier%C3%B3w': 'PANORAMA: Producenci farb i lakierów',
    'panorama_https://panoramafirm.pl/produkcja_artyku%C5%82%C3%B3w_elektrotechnicznych': 'PANORAMA: Produkcja artykułów elektrotechnicznych',
    'panorama_https://panoramafirm.pl/produkcja_artyku%C5%82%C3%B3w_higienicznych': 'PANORAMA: Produkcja artykułów higienicznych',
    'panorama_https://panoramafirm.pl/produkcja_artyku%C5%82%C3%B3w_metalowych': 'PANORAMA: Produkcja artykułów metalowych',
    'panorama_https://panoramafirm.pl/produkcja_chemii_gospodarczej': 'PANORAMA: Produkcja chemii gospodarczej',
    'panorama_https://panoramafirm.pl/produkcja_cz%C4%99%C5%9Bci_elektronicznych': 'PANORAMA: Produkcja części elektronicznych',
    'panorama_https://panoramafirm.pl/produkcja_kosmetyk%C3%B3w': 'PANORAMA: Produkcja kosmetyków',
    'panorama_https://panoramafirm.pl/produkcja_spr%C4%99%C5%BCyn': 'PANORAMA: Produkcja sprężyn',
    'panorama_https://panoramafirm.pl/produkcja_%C5%9Brodk%C3%B3w_chemicznych': 'PANORAMA: Produkcja środków chemicznych',
    'panorama_https://panoramafirm.pl/produkcja_urz%C4%85dze%C5%84_elektronicznych': 'PANORAMA: Produkcja urządzeń elektronicznych',
    'panorama_https://panoramafirm.pl/produkcja_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA: Produkcja urządzeń elektrycznych',
    'panorama_https://panoramafirm.pl/produkcja_zas%C5%82on_firanek_i_karniszy': 'PANORAMA: Produkcja zasłon, firanek i karniszy',
    'panorama_https://panoramafirm.pl/przemys%C5%82owe_urz%C4%85dzenia_elektryczne': 'PANORAMA: Przemysłowe urządzenia elektryczne',
    'panorama_https://panoramafirm.pl/przeno%C5%9Bniki': 'PANORAMA: Przenośniki',
    'panorama_https://panoramafirm.pl/przewody_kable_i_%C5%9Bwiat%C5%82owody': 'PANORAMA: Przewody, kable i światłowody',
    'panorama_https://panoramafirm.pl/recykling': 'PANORAMA: Recykling',
    'panorama_https://panoramafirm.pl/rury': 'PANORAMA: Rury',
    'panorama_https://panoramafirm.pl/sejfy_i_kasy_pancerne': 'PANORAMA: Sejfy i kasy pancerne',
    'panorama_https://panoramafirm.pl/serwis_urz%C4%85dze%C5%84_ch%C5%82odniczych': 'PANORAMA: Serwis urządzeń chłodniczych',
    'panorama_https://panoramafirm.pl/serwis_urz%C4%85dze%C5%84_elektrycznych': 'PANORAMA: Serwis urządzeń elektrycznych',
    'panorama_https://panoramafirm.pl/silikon': 'PANORAMA: Silikon',
    'panorama_https://panoramafirm.pl/silniki_i_pr%C4%85dnice': 'PANORAMA: Silniki i prądnice',
    'panorama_https://panoramafirm.pl/sklepy_z_cz%C4%99%C5%9Bciami_elektronicznymi': 'PANORAMA: Sklepy z częściami elektronicznymi',
    'panorama_https://panoramafirm.pl/s%C3%B3l_przemys%C5%82owa': 'PANORAMA: Sól przemysłowa',
    'panorama_https://panoramafirm.pl/sprz%C4%99t_do_produkcji_opakowa%C5%84': 'PANORAMA: Sprzęt do produkcji opakowań',
    'panorama_https://panoramafirm.pl/sprz%C4%99t_do_utylizacji_odpad%C3%B3w': 'PANORAMA: Sprzęt do utylizacji odpadów',
    'panorama_https://panoramafirm.pl/sprz%C4%99t_i_materia%C5%82y_hydrauliczne': 'PANORAMA: Sprzęt i materiały hydrauliczne',
    'panorama_https://panoramafirm.pl/sprz%C4%99t_i_zabezpieczenia_przeciwpo%C5%BCarowe': 'PANORAMA: Sprzęt i zabezpieczenia przeciwpożarowe',
    'panorama_https://panoramafirm.pl/sprz%C4%99t_lotniczy': 'PANORAMA: Sprzęt lotniczy',
    'panorama_https://panoramafirm.pl/sprz%C4%99t_radiokomunikacyjny': 'PANORAMA: Sprzęt radiokomunikacyjny',
    'panorama_https://panoramafirm.pl/sprz%C4%99t_torowy_i_kolejowy': 'PANORAMA: Sprzęt torowy i kolejowy',
    'panorama_https://panoramafirm.pl/stacje_paliw': 'PANORAMA: Stacje paliw',
    'panorama_https://panoramafirm.pl/stal_i_wyroby_stalowe': 'PANORAMA: Stal i wyroby stalowe',
    'panorama_https://panoramafirm.pl/studnie': 'PANORAMA: Studnie',
    'panorama_https://panoramafirm.pl/surowce_mineralne': 'PANORAMA: Surowce mineralne',
    'panorama_https://panoramafirm.pl/suwnice': 'PANORAMA: Suwnice',
    'panorama_https://panoramafirm.pl/systemy_zamocowa%C5%84': 'PANORAMA: Systemy zamocowań',
    'panorama_https://panoramafirm.pl/szk%C5%82o_budowlane': 'PANORAMA: Szkło budowlane',
    'panorama_https://panoramafirm.pl/szk%C5%82o_przemys%C5%82owe': 'PANORAMA: Szkło przemysłowe',
    'panorama_https://panoramafirm.pl/sznury_liny_i_nici': 'PANORAMA: Sznury, liny i nici',
    'panorama_https://panoramafirm.pl/%C5%9Bwiece_i_znicze': 'PANORAMA: Świece i znicze',
    'panorama_https://panoramafirm.pl/tartaki': 'PANORAMA: Tartaki',
    'panorama_https://panoramafirm.pl/technika_liniowa': 'PANORAMA: Technika liniowa',
    'panorama_https://panoramafirm.pl/techniki_bezwykopowe': 'PANORAMA: Techniki bezwykopowe',
    'panorama_https://panoramafirm.pl/toalety_przeno%C5%9Bne': 'PANORAMA: Toalety przenośne',
    'panorama_https://panoramafirm.pl/tworzywa_sztuczne': 'PANORAMA: Tworzywa sztuczne',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_do_produkcji_obuwia': 'PANORAMA: Urządzenia do produkcji obuwia',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_elektroniczne': 'PANORAMA: Urządzenia elektroniczne',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_elektryczne': 'PANORAMA: Urządzenia elektryczne',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_grzewcze': 'PANORAMA: Urządzenia grzewcze',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_i_maszyny_przemys%C5%82owe': 'PANORAMA: Urządzenia i maszyny przemysłowe',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_lakiernicze': 'PANORAMA: Urządzenia lakiernicze',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_pneumatyczne': 'PANORAMA: Urządzenia pneumatyczne',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_pomiarowe': 'PANORAMA: Urządzenia pomiarowe',
    'panorama_https://panoramafirm.pl/urz%C4%85dzenia_spawalnicze_i_zgrzewaj%C4%85ce': 'PANORAMA: Urządzenia spawalnicze i zgrzewające',
    'panorama_https://panoramafirm.pl/us%C5%82ugi_i_projekty_g%C3%B3rnicze': 'PANORAMA: Usługi i projekty górnicze',
    'panorama_https://panoramafirm.pl/us%C5%82ugi_kamieniarskie': 'PANORAMA: Usługi kamieniarskie',
    'panorama_https://panoramafirm.pl/us%C5%82ugi_spawania_i_zgrzewania': 'PANORAMA: Usługi spawania i zgrzewania',
    'panorama_https://panoramafirm.pl/uszczelki_i_uszczelnienia': 'PANORAMA: Uszczelki i uszczelnienia',
    'panorama_https://panoramafirm.pl/utylizacja_odpad%C3%B3w': 'PANORAMA: Utylizacja odpadów',
    'panorama_https://panoramafirm.pl/wagi': 'PANORAMA: Wagi',
    'panorama_https://panoramafirm.pl/w%C4%99%C5%BCe_przemys%C5%82owe': 'PANORAMA: Węże przemysłowe',
    'panorama_https://panoramafirm.pl/wodoci%C4%85gi_i_kanalizacja': 'PANORAMA: Wodociągi i kanalizacja',
    'panorama_https://panoramafirm.pl/w%C3%B3zki_wid%C5%82owe': 'PANORAMA: Wózki widłowe',
    'panorama_https://panoramafirm.pl/wyci%C4%85gi_i_koleje_linowe': 'PANORAMA: Wyciągi i koleje linowe',
    'panorama_https://panoramafirm.pl/wydobycie_i_sprzeda%C5%BC_w%C4%99gla': 'PANORAMA: Wydobycie i sprzedaż węgla',
    'panorama_https://panoramafirm.pl/wynajem_maszyn_i_narz%C4%99dzi': 'PANORAMA: Wynajem maszyn i narzędzi',
    'panorama_https://panoramafirm.pl/wyposa%C5%BCenie_sprz%C4%99t_i_instalacje_ch%C5%82odnicze': 'PANORAMA: Wyposażenie, sprzęt i instalacje chłodnicze',
    'panorama_https://panoramafirm.pl/wyroby_hutnicze': 'PANORAMA: Wyroby hutnicze',
    'panorama_https://panoramafirm.pl/wytwarzanie_energii_odnawialnej': 'PANORAMA: Wytwarzanie energii odnawialnej',
    'panorama_https://panoramafirm.pl/wzornictwo_przemys%C5%82owe': 'PANORAMA: Wzornictwo przemysłowe',
    'panorama_https://panoramafirm.pl/zabezpieczenia_antykorozyjne': 'PANORAMA: Zabezpieczenia antykorozyjne',
    'panorama_https://panoramafirm.pl/zapalniczki_i_zapa%C5%82ki': 'PANORAMA: Zapalniczki i zapałki',
    'panorama_https://panoramafirm.pl/zawiesia_linowe_%C5%82a%C5%84cuchowe_i_pasowe': 'PANORAMA: Zawiesia linowe, łańcuchowe i pasowe',
    'panorama_https://panoramafirm.pl/zbiorniki_i_pojemniki': 'PANORAMA: Zbiorniki i pojemniki',
    'panorama_https://panoramafirm.pl/z%C5%82om_i_surowce_wt%C3%B3rne': 'PANORAMA: Złom i surowce wtórne',
}
"""

def setup_driver():
    """Nastavení Chrome driveru"""
    chrome_options = Options()
    
    # Docker/Server nastavení - OPTIMALIZACE PRO NÍZKOU PAMĚŤ
    chrome_options.add_argument('--headless=new')  # Nový headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')
    
    # Snížení paměťové náročnosti
    chrome_options.add_argument('--disable-dev-tools')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--metrics-recording-only')
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--disable-permissions-api')
    chrome_options.add_argument('--single-process')  # KRITICKÉ - jeden proces místo více
    
    # Anti-detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Window size
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extract_company_names(driver, category_url, max_companies, source='aleo'):
    """Extrahuje názvy firem z aleo.com nebo panoramafirm.pl
    
    Returns:
        - ALEO: list of strings (názvy firem)
        - PANORAMA: list of dicts {'name': str, 'website': str, 'email': str}
    """
    try:
        driver.get(category_url)
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
            scroll_attempts = max_companies // 25 + 2
            
            for i in range(scroll_attempts):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # DEBUG - První scroll vypsat HTML strukturu
                if i == 0:
                    logger.info("=== DEBUG: HTML STRUKTURA ===")
                    all_h2 = soup.find_all('h2')
                    logger.info(f"Celkem H2 tagů na stránce: {len(all_h2)}")
                    for idx, h2 in enumerate(all_h2[:5], 1):  # První 5 H2
                        logger.info(f"H2 #{idx}: Text='{h2.get_text(strip=True)[:50]}', Class={h2.get('class')}")
                    
                    # Zkusit najít karty firem jinak
                    article_tags = soup.find_all('article')
                    logger.info(f"Celkem article tagů: {len(article_tags)}")
                    
                    divs_with_firma = soup.find_all('div', class_=lambda c: c and any('firma' in str(x).lower() for x in c) if c else False)
                    logger.info(f"Divů s 'firma' v třídě: {len(divs_with_firma)}")
                    
                    # Hledat linky na /firma/
                    firma_links = soup.find_all('a', href=lambda h: h and '/firma/' in h)
                    logger.info(f"Linků na /firma/: {len(firma_links)}")
                    if firma_links:
                        logger.info(f"První link: {firma_links[0].get('href')}")
                    logger.info("=== KONEC DEBUG ===")
                
                h2_elements = soup.find_all('h2', class_=lambda c: c and 'text-h1' in c if c else False)
                
                for h2 in h2_elements:
                    name = h2.get_text(strip=True)
                    
                    # Filtrovat nerelevantní názvy
                    if not name or name in seen_names or name.startswith('Wyniki') or name.startswith('Jakie') or len(name) < 3:
                        continue
                    
                    # Najít odkaz na detail firmy
                    detail_link = None
                    parent = h2.parent
                    for _ in range(10):
                        if parent:
                            a_tag = parent.find('a', href=lambda h: h and '/firma/' in h)
                            if a_tag:
                                detail_link = a_tag.get('href')
                                if not detail_link.startswith('http'):
                                    detail_link = f"https://panoramafirm.pl{detail_link}"
                                break
                            parent = parent.parent
                        else:
                            break
                    
                    if detail_link and name not in seen_names:
                        company_details.append({'name': name, 'url': detail_link})
                        seen_names.add(name)
                
                scraping_status['message'] = f'📂 Načteno {len(company_details)} firem ze seznamu... (scroll {i+1}/{scroll_attempts})'
                logger.info(f"Po scrollu {i+1}: Celkem {len(company_details)} firem")
                
                if len(company_details) >= max_companies:
                    break
            
            logger.info(f"Fáze 1 dokončena: Našel jsem {len(company_details)} firem")
            logger.info(f"Zahajuji Fázi 2: Procházení detailů {min(len(company_details), max_companies)} firem")
            
            # KROK 2: Projít detail každé firmy
            for idx, company in enumerate(company_details[:max_companies], 1):
                scraping_status['message'] = f'🔍 Zpracovávám {idx}/{min(len(company_details), max_companies)}: {company["name"]}'
                logger.info(f"[{idx}/{min(len(company_details), max_companies)}] Otevírám detail: {company['name']}")
                
                website = None
                email = None
                
                try:
                    # Otevřít detail firmy
                    driver.get(company['url'])
                    time.sleep(2)
                    logger.info(f"  Detail načten: {company['url']}")
                    
                    detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    # Hledat web - všechny externí linky
                    for link in detail_soup.find_all('a', href=True):
                        href = link.get('href', '')
                        
                        # Najít web link (mimo Panorama a social media)
                        if (href.startswith('http') and 
                            'panoramafirm.pl' not in href and
                            '/firma/' not in href and
                            'facebook.com' not in href and
                            'linkedin.com' not in href and
                            'instagram.com' not in href and
                            'twitter.com' not in href and
                            'youtube.com' not in href):
                            website = href
                            logger.info(f"  Nalezen web: {website}")
                            break
                    
                    # Hledat email na celé stránce
                    all_emails = EMAIL_PATTERN.findall(driver.page_source)
                    for potential_email in all_emails:
                        # Filtrovat nerelevantní emaily
                        if not any(skip in potential_email.lower() for skip in ['example', 'test@', 'noreply', '@panorama', '@google', '@facebook']):
                            email = potential_email
                            logger.info(f"  Nalezen email: {email}")
                            break
                    
                    if not website:
                        logger.info(f"  Web nenalezen")
                    if not email:
                        logger.info(f"  Email nenalezen")
                    
                except Exception as e:
                    logger.error(f"  Chyba při zpracování {company['name']}: {str(e)}")
                    scraping_status['message'] = f'⚠️ Chyba u {company["name"]}: {str(e)}'
                    time.sleep(1)
                
                all_data.append({
                    'name': company['name'],
                    'website': website or '',
                    'email': email or ''
                })
            
            return all_data
        
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
        driver.get(url)
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
        driver.get(url)
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
    scraping_status['message'] = '🚀 Spouštím Chrome...'
    
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
            source = 'panorama'
            # Panorama má celý URL ve slugu
            category_url = category_slug.replace('panorama_', '')
        else:
            logger.error(f"Neznámý zdroj kategorie: {category_slug}")
            scraping_status['message'] = '❌ Neznámý zdroj'
            scraping_status['running'] = False
            return
        
        # KROK 1: Otevřít stránku
        logger.info(f"Otevírám URL: {category_url}")
        scraping_status['message'] = f'🔓 Otevírám {source.upper()}...'
        
        driver.get(category_url)
        time.sleep(5)  # Počkat na načtení stránky
        logger.info("Stránka načtena")
        
        # KROK 2: Načíst firmy
        scraping_status['message'] = f'📂 Načítám firmy z kategorie...'
        logger.info(f"Volám extract_company_names() pro zdroj: {source}")
        
        company_names = extract_company_names(driver, category_url, max_companies, source)
        
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
                scraping_status['progress'] = idx
                logger.info(f"[{idx}/{len(company_names)}] {company_data['name']} - Web: {company_data['website']}, Email: {company_data['email']}")
                
                # Použít přímo data z Panorama
                scraping_status['results'].append({
                    'category': category_title,
                    'name': company_data['name'],
                    'website': company_data['website'] or '',
                    'email': company_data['email'] or ''
                })
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
        output_file = f'output/{source}_{safe_filename}_{timestamp}.csv'
        
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
        
    except Exception as e:
        scraping_status['message'] = f'❌ Chyba: {str(e)}'
    
    finally:
        if driver:
            driver.quit()
        scraping_status['running'] = False

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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
