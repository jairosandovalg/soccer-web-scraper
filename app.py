import streamlit as st
import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@st.cache_resource
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # 🌟 EVITAR DETECCIÓN: Ocultar automatización de Selenium
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User-Agent real y moderno para evitar bloqueos
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        service = Service("/usr/bin/chromedriver")
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    # Cambiar propiedades del navegador por script para simular que es un usuario real
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    return driver

def escanear_en_directo():
    driver = get_driver()
    # Usamos la URL que va directamente a la pestaña en vivo para evitar fallas al hacer clic
    driver.get("https://www.flashscore.cl/?s=2") 
    
    st.info("Conectando con Flashscore y cargando eventos en directo...")
    time.sleep(5)  # Damos un margen seguro para que cargue el JavaScript dinámico de los partidos

    # Forzar scroll hacia abajo para asegurar el renderizado de la lista
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Flashscore agrupa partidos usando selectores de eventos vivos que contienen identificadores "g_1_"
    match_events = soup.find_all("div", id=lambda x: x and x.startswith("g_1_"))
    
    lista_partidos = []
    
    for event in match_events:
        try:
            match_id = event.get('id').split('_')[-1]
            url_partido = f"https://www.flashscore.cl/partido/{match_id}/#/resumen/estadisticas"
            
            # Buscar nombres de equipos usando clases comunes de Flashscore
            home_team = event.find("div", class_=lambda c: c and "home" in c.lower() and "participant" in c.lower())
            away_team = event.find("div", class_=lambda c: c and "away" in c.lower() and "participant" in c.lower())
            
            score_home = event.find("div", class_=lambda c: c and "score" in c.lower() and "home" in c.lower())
            score_away = event.find("div", class_=lambda c: c and "score" in c.lower() and "away" in c.lower())
            
            # Formatear nombres válidos
            name_home = home_team.get_text(strip=True) if home_team else "Local"
            name_away = away_team.get_text(strip=True) if away_team else "Visitante"
            val_score_h = score_home.get_text(strip=True) if score_home else "0"
            val_score_a = score_away.get_text(strip=True) if score_away else "0"
            
            lista_partidos.append({
                "id": match_id,
                "Partido": f"{name_home} vs {name_away}",
                "Marcador": f"{val_score_h} - {val_score_a}",
                "url": url_partido
            })
        except Exception:
            continue
            
    return lista_partidos
