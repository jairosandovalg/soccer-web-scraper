import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Configuración básica de Streamlit
st.set_page_config(page_title="Paso 2: Clic En Directo", layout="wide")
st.title("⚽ Bot de Estadísticas - Paso 2")
st.subheader("Ingreso a la sección EN DIRECTO y conteo de partidos")

@st.cache_resource
def iniciar_navegador():
    """Configura e inicia el navegador en modo oculto (headless)."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Ejecución en segundo plano
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Simulación de usuario real para evitar bloqueos
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    try:
        service = Service()
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        service = Service("/usr/bin/chromedriver")
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        return webdriver.Chrome(service=service, options=chrome_options)

# --- INTERFAZ DE STREAMLIT ---

if st.button("🚀 Ir a En Directo y Contar Partidos"):
    with st.spinner("Conectando a Flashscore Perú..."):
        try:
            driver = iniciar_navegador()
            
            # 1. Entrar a la página principal
            url = "https://www.flashscore.pe/"
            driver.get(url)
            
            # 2. Buscar el botón "EN DIRECTO" solicitado mediante su clase y texto
            st.text("Buscando el botón 'EN DIRECTO'...")
            
            # Esperamos un máximo de 10 segundos a que el elemento sea visible y cliqueable
            boton_directo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filters__text') and text()='EN DIRECTO']"))
            )
            
            # Hacer clic usando JavaScript para asegurar la acción en entornos en la nube
            driver.execute_script("arguments[0].click();", boton_directo)
            
            st.text("¡Clic realizado con éxito! Esperando que cargue la lista de partidos en vivo...")
            time.sleep(4)  # Espera de cortesía para que cargue el contenido dinámico
            
            # 3. Analizar el HTML obtenido tras el clic
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # En Flashscore, los partidos en vivo usan filas con IDs que comienzan con "g_1_"
            partidos_en_vivo = soup.find_all("div", id=lambda x: x and x.startswith("g_1_"))
            
            # 4. Mostrar el resultado del análisis solicitado
            cantidad_partidos = len(partidos_en_vivo)
            
            if cantidad_partidos == 0:
                st.warning("Se ingresó a la sección 'EN DIRECTO' pero no se detectaron partidos activos en este momento.")
            else:
                st.success(f"📊 ¡Análisis completado! Actualmente hay **{cantidad_partidos}** partidos en vivo.")
                
                # Opcional: Mostrar una lista rápida de los partidos contados para corroborar visualmente
                st.write("### ⏱️ Partidos detectados en el conteo:")
                for idx, fila in enumerate(partidos_en_vivo):
                    local = fila.find("div", class_=lambda c: c and "home" in c.lower() and "participant" in c.lower())
                    visitante = fila.find("div", class_=lambda c: c and "away" in c.lower() and "participant" in c.lower())
                    
                    nom_local = local.get_text(strip=True) if local else "Local"
                    nom_visitante = visitante.get_text(strip=True) if visitante else "Visitante"
                    
                    st.write(f"- {nom_local} vs {nom_visitante}")
                    
        except Exception as e:
            st.error(f"Error durante el proceso: {str(e)}")

    st.info("➡️ Sube este código a tu repositorio. Cuando lo pruebes y te confirme el recuadro verde con la cantidad exacta de partidos en vivo, me avisas para pasar al **Paso 3** (extraer los enlaces de esos partidos e ingresar a la pestaña interna de estadísticas).")
