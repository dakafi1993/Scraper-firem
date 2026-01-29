"""
NÁVOD: Ruční stažení kategorií ze všech sekcí Panorama Firm
=============================================================

PROČ RUČNÍ STAŽENÍ?
- Panorama Firm blokuje automatické stahování (Connection Reset, Timeout)
- Kategorie jsou rozdělené podle písmen v HTML struktuře
- Nejrychlejší a nejspolehlivější je stáhnout HTML ručně

JAK NA TO (5-10 minut práce):
==============================

KROK 1: Otevři prohlížeč (Chrome/Firefox)
------------------------------------------

KROK 2: Pro každou sekci:
--------------------------
Otevři URL a ulož HTML (Ctrl+S):

1. Biuro:
   https://panoramafirm.pl/biuro,z/branze.html
   Ulož jako: biuro_branze.html

2. Budownictwo:
   https://panoramafirm.pl/budownictwo,b/branze.html
   Ulož jako: budownictwo_branze.html

3. Dom i ogród:
   https://panoramafirm.pl/dom_i_ogród,c/branze.html
   Ulož jako: dom_i_ogrod_branze.html

4. Dzieci:
   https://panoramafirm.pl/dzieci,u/branze.html
   Ulož jako: dzieci_branze.html

5. Finanse i ubezpieczenia:
   https://panoramafirm.pl/finanse_i_ubezpieczenia,r/branze.html
   Ulož jako: finanse_branze.html

6. Instytucje, urzędy:
   https://panoramafirm.pl/instytucje_urzędy,f/branze.html
   Ulož jako: instytucje_branze.html

7. Kancelaria:
   https://panoramafirm.pl/kancelaria,y/branze.html
   Ulož jako: kancelaria_branze.html

8. Motoryzacja i transport:
   https://panoramafirm.pl/motoryzacja_i_transport,h/branze.html
   Ulož jako: motoryzacja_branze.html

9. Nauka:
   https://panoramafirm.pl/nauka,i/branze.html
   Ulož jako: nauka_branze.html

10. Odzież i tekstylia:
    https://panoramafirm.pl/odzież_i_tekstylia,g/branze.html
    Ulož jako: odziez_branze.html

11. Porady:
    https://panoramafirm.pl/porady,w/branze.html
    Ulož jako: porady_branze.html

12. Przemysł i energetyka:
    https://panoramafirm.pl/przemysł_i_energetyka,k/branze.html
    Ulož jako: przemysl_branze.html

13. Rolnictwo i leśnictwo:
    https://panoramafirm.pl/rolnictwo_i_leśnictwo,j/branze.html
    Ulož jako: rolnictwo_branze.html

14. Rozrywka i rekreacja:
    https://panoramafirm.pl/rozrywka_i_rekreacja,l/branze.html
    Ulož jako: rozrywka_branze.html

15. Telekomunikacja, Internet, technologie:
    https://panoramafirm.pl/telekomunikacja_internet_technologie,t/branze.html
    Ulož jako: telekomunikacja_branze.html

16. Turystyka:
    https://panoramafirm.pl/turystyka,m/branze.html
    Ulož jako: turystyka_branze.html

17. Usługi dla firm:
    https://panoramafirm.pl/usługi_dla_firm,n/branze.html
    Ulož jako: uslugi_dla_firm_branze.html

18. Usługi dla każdego:
    https://panoramafirm.pl/usługi_dla_każdego,p/branze.html
    Ulož jako: uslugi_dla_kazdego_branze.html

19. Zdrowie i uroda:
    https://panoramafirm.pl/zdrowie_i_uroda,s/branze.html
    Ulož jako: zdrowie_branze.html

20. Żywność i używki:
    https://panoramafirm.pl/żywność_i_używki,a/branze.html
    Ulož jako: zywnosc_branze.html


KROK 3: Spusť skript pro zpracování
------------------------------------
python process_manual_html.py


DŮLEŽITÉ TIPY:
--------------
✓ Ulož soubory do složky d:\skript\
✓ Ulož jako "Webová stránka, pouze HTML" (ne kompletní)
✓ Můžeš začít jen s několika sekcemi a dopracovat později
✓ Už máš: branze_page_structure.html (Dom i ogród) - 155 kategorií!


ODHAD KATEGORIÍ:
----------------
Dom i ogród: 155 kategorií (už máš!)
Ostatní sekce: ~100-200 kategorií každá
CELKEM: odhadem 2000-3000 kategorií (vs. současných 983)
"""

print(__doc__)
