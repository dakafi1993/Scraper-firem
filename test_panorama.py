#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test scraper pro panoramafirm.pl - zjistit strukturu
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_panorama():
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://panoramafirm.pl/przemys%C5%82_i_energetyka,k/branze.html"
        print(f"Otevírám: {url}")
        
        driver.get(url)
        time.sleep(5)
        
        # Uložit HTML
        with open('panorama_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        print("✅ HTML uloženo do panorama_page.html")
        print("\nHledám možné prvky s názvy firem...")
        
        # Zkusit najít firmy
        possible_classes = [
            'company-name',
            'company_name', 
            'firma-nazwa',
            'name',
            'title'
        ]
        
        for cls in possible_classes:
            elements = driver.find_elements(By.CLASS_NAME, cls)
            if elements:
                print(f"\n✅ Našel jsem {len(elements)} prvků s class='{cls}'")
                for i, el in enumerate(elements[:3]):
                    print(f"  [{i+1}] {el.text[:100]}")
        
        input("\nStiskněte Enter pro ukončení...")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    test_panorama()
