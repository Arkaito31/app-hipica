import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Hípica Chile Predictor", page_icon="🏇")

# --- CONFIGURACIÓN DE BASE DE DATOS ---
archivos_db = {
    "Club Hípico de Santiago": "chs_resultados.db",
    "Valparaíso Sporting": "vsc_resultados.db",
    "Hipódromo Chile": "hipodromo_resultados.db"
}

hipodromo = st.sidebar.selectbox("Selecciona Hipódromo:", list(archivos_db.keys()))
db_actual = archivos_db[hipodromo]

def obtener_datos_caballo(nombres_caballos):
    if not os.path.exists(db_actual): return pd.DataFrame()
    
    conn = sqlite3.connect(db_actual)
    # Convertimos la lista de nombres para la consulta SQL
    nombres_format = "','".join([n.upper().strip() for n in nombres_caballos])
    query = f"""
        SELECT * FROM resultados 
        WHERE UPPER(Ejemplar) IN ('{nombres_format}') 
           OR UPPER(Caballo) IN ('{nombres_format}') 
           OR UPPER(Nombre) IN ('{nombres_format}')
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Normalizar y Calcular
    renombrar = {'Ejemplar': 'caballo', 'Nombre': 'caballo', 'Caballo': 'caballo', 'Orden': 'posicion', 'Llegada': 'posicion'}
    df = df.rename(columns=renombrar)
    if not df.empty and 'posicion' in df.columns:
        df['posicion'] = pd.to_numeric(df['posicion'], errors='coerce').fillna(10)
        stats = df.groupby('caballo').agg(
            prom_pos=('posicion', 'mean'),
            carreras=('posicion', 'count'),
            mejor_llegada=('posicion', 'min')
        ).reset_index()
        stats['Score'] = (100 / (stats['prom_pos'] + 0.5)).round(1)
        return stats.sort_values(by='Score', ascending=False)
    return pd.DataFrame()

# --- INTERFAZ ---
st.title(f"🏇 {hipodromo}")

tab1, tab2, tab3 = st.tabs(["🏆 Ranking General", "🔍 Buscador", "🔥 Simular Carrera"])

with tab3:
    st.header("Comparador de Carrera")
    st.write("Ingresa los nombres de los caballos que corren (separados por coma):")
    entrada = st.text_area("Ejemplo: Mufasa, El Egipcio, Fast Rock", help="Copia los nombres del programa oficial")
    
    if st.button("Analizar Carrera"):
        lista_caballos = [n.strip() for n in entrada.split(",") if n.strip()]
        if lista_caballos:
            resultados = obtener_datos_caballo(lista_caballos)
            if not resultados.empty:
                st.subheader("📊 Ranking de Probabilidades")
                
                # Resaltar al mejor
                mejor = resultados.iloc[0]
                st.success(f"🥇 El mejor candidato según datos es: **{mejor['caballo']}**")
                
                # Tabla comparativa
                st.table(resultados[['caballo', 'Score', 'prom_pos', 'carreras']])
                
                # Advertencia de datos
                faltantes = set([n.upper() for n in lista_caballos]) - set(resultados['caballo'].str.upper())
                if faltantes:
                    st.warning(f"No tengo datos de: {', '.join(faltantes)}. (Probablemente son debutantes)")
            else:
                st.error("No encontré datos de ninguno de esos caballos en este hipódromo.")

# (Las pestañas tab1 y tab2 mantienen el código anterior de Ranking y Buscador)
