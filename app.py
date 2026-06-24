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
st.set_page_config(page_title="Paso 3: Enlaces de Partidos", layout="wide")
st.title("⚽ Bot de Estadísticas - Paso 3")
st.subheader("Extracción de partidos en vivo y sus enlaces de estadísticas")

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

if st.button("🔗 Listar Partidos y Enlaces en Vivo"):
    with st.spinner("Conectando a Flashscore Perú..."):
        try:
            driver = iniciar_navegador()
            
            # 1. Entrar a la página principal
            url = "https://www.flashscore.pe/"
            driver.get(url)
            
            # 2. Hacer clic en "EN DIRECTO"
            boton_directo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filters__text') and text()='EN DIRECTO']"))
            )
            driver.execute_script("arguments[0].click();", boton_directo)
            
            st.text("Ingresando a la sección 'EN DIRECTO'...")
            time.sleep(4)  # Espera para carga total del contenido dinámico
            
            # 3. Analizar el HTML con BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Buscamos las filas de partidos en vivo (que contienen id que inicia con "g_1_")
            partidos_en_vivo = soup.find_all("div", id=lambda x: x and x.startswith("g_1_"))
            
            if not partidos_en_vivo:
                st.warning("No se detectaron partidos activos en este instante.")
            else:
                st.success(f"📊 ¡Análisis completado! Se encontraron {len(partidos_en_vivo)} partidos en vivo.")
                st.write("### 📂 Directorio de Partidos en Directo y Enlaces:")
                
                # Recorremos cada partido para extraer nombres y armar URLs
                for idx, fila in enumerate(partidos_en_vivo):
                    # Extraer el ID único del partido (ejemplo: K0YnEaMq)
                    id_partido = fila.get('id').split('_')[-1]
                    
                    # Extraer nombres de los equipos utilizando las clases del contenedor
                    local = fila.find("div", class_=lambda c: c and "home" in c.lower() and "participant" in c.lower())
                    visitante = fila.find("div", class_=lambda c: c and "away" in c.lower() and "participant" in c.lower())
                    
                    nom_local = local.get_text(strip=True) if local else "Local"
                    nom_visitante = visitante.get_text(strip=True) if visitante else "Visitante"
                    
                    nombre_partido = f"{nom_local} vs {nom_visitante}"
                    
                    # Armamos la URL exacta y directa a la pestaña de estadísticas usando el ID
                    url_estadisticas = f"https://www.flashscore.pe/partido/{id_partido}/#/resumen/estadisticas"
                    
                    # 🟢 MOSTRAR EN PANTALLA EL PARTIDO CON SU ENLACE SOLICITADO
                    st.markdown(f"**{idx + 1}. Partido:** {nombre_partido}")
                    st.code(url_estadisticas, language="text")  # Formato fácil de copiar
                    st.markdown(f"[🔗 Abrir pestaña de estadísticas en el navegador]({url_estadisticas})")
                    st.write("---")  # Línea divisoria entre partidos
                    
        except Exception as e:
            st.error(f"Error durante el proceso de extracción: {str(e)}")

    st.info("➡️ Sube este código a GitHub. Cuando ejecutes el botón y veas en tu pantalla la lista de partidos con sus respectivas URLs estructuradas en las cajas de texto, confirmamos el éxito y pasamos al **Paso 4** (el paso final: entrar a cada uno de esos links, hacer clic en el botón 'Estadísticas' y plasmar las métricas en la tabla).")
