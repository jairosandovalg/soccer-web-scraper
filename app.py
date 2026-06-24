import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Configuración básica de Streamlit
st.set_page_config(page_title="Paso 1: Conexión Flashscore", layout="wide")
st.title("🕵️ Bot de Estadísticas - Paso 1")
st.subheader("Verificación de ingreso a la plataforma")

@st.cache_resource
def iniciar_navegador():
    """Configura e inicia el navegador en modo oculto (headless)."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Ejecución en segundo plano
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Simulación de usuario real para evitar bloqueos de pantalla
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    try:
        # Intento de inicio estándar (Streamlit Cloud con packages.txt)
        service = Service()
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Ruta alternativa por si se ejecuta localmente en Linux configurado
        service = Service("/usr/bin/chromedriver")
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        return webdriver.Chrome(service=service, options=chrome_options)

# --- INTERFAZ DE STREAMLIT ---

if st.button("🚀 Conectar con la Página"):
    with st.spinner("Abriendo el enlace externo..."):
        try:
            driver = iniciar_navegador()
            
            # Dirección URL solicitada
            url = "https://www.flashscore.pe/"
            driver.get(url)
            
            # Extraemos el título oficial de la página cargada para validar
            titulo_pagina = driver.title
            
            if "Flashscore" in titulo_pagina or "Marcadores" in titulo_pagina:
                # 🟢 MENSAJE DE ÉXITO
                st.success(f"¡Estamos en Flashscore! (Validado exitosamente: '{titulo_pagina}')")
                st.balloons()
            else:
                st.warning(f"Se ingresó a la URL pero el título no coincide de forma esperada: {titulo_pagina}")
                
        except Exception as e:
            st.error(f"Error al intentar ingresar a la página: {str(e)}")

    st.info("➡️ Reemplaza tu archivo en GitHub con este bloque limpio. Una vez que este Paso 1 te arroje el recuadro verde con globos, avísame para integrar de inmediato el Paso 2 (Listar partidos en vivo) sin errores.")
