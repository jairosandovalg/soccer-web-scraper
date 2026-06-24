@st.cache_resource
def get_driver():
    chrome_options = Options()
    # Argumentos críticos para entornos Linux en la nube (Docker/Streamlit Cloud)
    chrome_options.add_argument("--headless=new")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # En Linux/Streamlit Cloud con packages.txt, el binario suele mapearse directo
        service = Service()
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Alternativa por si las rutas locales de Streamlit Cloud requieren asignación explícita
        service = Service("/usr/bin/chromedriver")
        chrome_options.binary_location = "/usr/bin/chromium-browser"
        return webdriver.Chrome(service=service, options=chrome_options)

def extraer_datos_partido(driver, url_partido):
    """Navega al partido, hace clic en estadísticas y extrae los datos."""
    stats_data = {}
    try:
        driver.get(url_partido)
        
        # Esperar a que la pestaña de Estadísticas aparezca y hacer clic
        tab_estadisticas = WebDriverWait(driver, 7).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@data-testid, 'wcl-tab') and .//text()='Estadísticas']"))
        )
        driver.execute_script("arguments[0].click();", tab_estadisticas)
        time.sleep(1.5) # Esperar a que carguen las barras de estadísticas
        
        # Parsear con BeautifulSoup la sección cargada
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.find_all("div", {"data-testid": "wcl-statistics"})
        
        for row in rows:
            # Buscar categoría (nombre de la estadística)
            cat_div = row.find("div", {"data-testid": "wcl-statistics-category"})
            if cat_div:
                categoria = cat_div.get_text(strip=True)
                
                # Valores local y visitante
                home_val = row.find("div", class_=lambda x: x and 'wcl-homeValue' in x).get_text(strip=True)
                away_val = row.find("div", class_=lambda x: x and 'wcl-awayValue' in x).get_text(strip=True)
                
                stats_data[f"{categoria} (L)"] = home_val
                stats_data[f"{categoria} (V)"] = away_val
    except Exception as e:
        st.sidebar.warning(f"No se pudieron extraer estadísticas completas de un partido.")
    
    return stats_data

def escanear_en_directo():
    driver = get_driver()
    # Flashscore versión global/latam suele usar directo o en vivo
    driver.get("https://www.flashscore.cl/") 
    
    st.info("Buscando partidos 'EN DIRECTO'...")
    try:
        # Clic en el filtro de "EN DIRECTO"
        btn_directo = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filters__text') and text()='EN DIRECTO']"))
        )
        driver.execute_script("arguments[0].click();", btn_directo)
        time.sleep(2)
    except Exception as e:
        st.error("No se encontró el botón 'EN DIRECTO' o no hay partidos live en este momento.")
        return []

    # Obtener los enlaces de todos los partidos en vivo actuales
    soup = BeautifulSoup(driver.page_source, "html.parser")
    # Los contenedores de los partidos suelen tener ids que inician con 'g_1_'
    match_events = soup.find_all("div", id=lambda x: x and x.startswith("g_1_"))
    
    lista_partidos = []
    
    for event in match_events:
        match_id = event.get('id').split('_')[-1]
        url_partido = f"https://www.flashscore.cl/partido/{match_id}/#/resumen/estadisticas"
        
        # Extraer nombres de equipos preliminares
        home_team = event.find("div", class_="event__participant--home")
        away_team = event.find("div", class_="event__participant--away")
        score_home = event.find("div", class_="event__score--home")
        score_away = event.find("div", class_="event__score--away")
        
        if home_team and away_team:
            lista_partidos.append({
                "id": match_id,
                "Partido": f"{home_team.get_text(strip=True)} vs {away_team.get_text(strip=True)}",
                "Marcador": f"{score_home.get_text(strip=True) if score_home else 0} - {score_away.get_text(strip=True) if score_away else 0}",
                "url": url_partido
            })
            
    return lista_partidos

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

if st.button("🔄 Escanear Partidos en Vivo"):
    partidos_live = escanear_en_directo()
    
    if not partidos_live:
        st.warning("No se detectaron partidos activos en la sección En Directo.")
    else:
        st.success(f"Se encontraron {len(partidos_live)} partidos en vivo. Extrayendo métricas...")
        
        resultados_totales = []
        progress_bar = st.progress(0)
        
        driver = get_driver()
        for idx, partido in enumerate(partidos_live):
            # Actualizar barra de progreso
            progress_bar.progress((idx + 1) / len(partidos_live))
            
            # Extraer las estadísticas internas de cada partido
            estadisticas = extraer_datos_partido(driver, partido["url"])
            
            # Unir datos básicos con estadísticas
            datos_completos = {
                "Partido": partido["Partido"],
                "Marcador": partido["Marcador"]
            }
            datos_completos.update(estadisticas)
            resultados_totales.append(datos_completos)
            
        # Convertir a Dataframe de Pandas
        df = pd.DataFrame(resultados_totales)
        
        # Reordenar y limpiar columnas faltantes si el partido no posee métricas aún
        df = df.fillna("-")
        
        # Mostrar tabla interactiva en Streamlit
        st.write("### 📊 Tabla Comparativa de Estadísticas")
        st.dataframe(df, use_container_width=True)
        
        # Alertas de apuestas automáticas (Ejemplo de valor)
        st.markdown("### 🚨 Alertas de Oportunidades (Basadas en tus métricas)");
        for index, row in df.iterrows():
            # Validación simple por si existe la métrica de remates en el dataframe
            if "Remates totales (L)" in row and row["Remates totales (L)"] != "-":
                remates_l = int(row["Remates totales (L)"])
                if remates_l > 12:
                    st.warning(f"🔥 **Oportunidad de Over/Esquinas**: El local en `{row['Partido']}` tiene alta presión ({remates_l} remates).")
