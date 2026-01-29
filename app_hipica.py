import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Hípica Chile Predictor", page_icon="🏇")

# --- CONFIGURACIÓN DE BASES DE DATOS ---
archivos_db = {
    "Club Hípico de Santiago": "chs_resultados.db",
    "Valparaíso Sporting": "vsc_resultados.db",
    "Hipódromo Chile": "hipodromo_resultados.db"
}

hipodromo = st.sidebar.selectbox("Selecciona Hipódromo:", list(archivos_db.keys()))
db_actual = archivos_db[hipodromo]

def obtener_datos_seguros(nombres_caballos=None):
    if not os.path.exists(db_actual):
        return pd.DataFrame()
    
    conn = sqlite3.connect(db_actual)
    try:
        # Cargamos una muestra para detectar nombres de columnas reales
        df_muestra = pd.read_sql("SELECT * FROM resultados LIMIT 1", conn)
        cols = df_muestra.columns.tolist()
        
        # Identificar cuál es la columna del nombre y de la posición
        col_nombre = next((c for c in cols if c.lower() in ['ejemplar', 'caballo', 'nombre']), None)
        col_pos = next((c for c in cols if c.lower() in ['posicion', 'llegada', 'orden', 'pos.', 'lleg.']), None)
        
        if not col_nombre or not col_pos:
            return pd.DataFrame()

        # Construir consulta filtrada o total
        if nombres_caballos:
            nombres_format = "','".join([n.upper().strip() for n in nombres_caballos])
            query = f"SELECT [{col_nombre}] as caballo, [{col_pos}] as posicion FROM resultados WHERE UPPER([{col_nombre}]) IN ('{nombres_format}')"
        else:
            query = f"SELECT [{col_nombre}] as caballo, [{col_pos}] as posicion FROM resultados"
            
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            df['posicion'] = pd.to_numeric(df['posicion'], errors='coerce').fillna(10)
            stats = df.groupby('caballo').agg(
                prom_pos=('posicion', 'mean'),
                carreras=('posicion', 'count')
            ).reset_index()
            stats['Score'] = (100 / (stats['prom_pos'] + 0.5)).round(1)
            return stats.sort_values(by='Score', ascending=False)
            
    except Exception as e:
        st.error(f"Error técnico: {e}")
    finally:
        conn.close()
    return pd.DataFrame()

# --- INTERFAZ ---
st.title(f"🏇 {hipodromo}")

tab1, tab2 = st.tabs(["🏆 Ranking General", "🔥 Analizar Carrera"])

with tab1:
    res_gen = obtener_datos_seguros()
    if not res_gen.empty:
        st.dataframe(res_gen.head(20), use_container_width=True)
    else:
        st.warning(f"No hay datos en {db_actual}. ¿Ya subiste el archivo a GitHub?")

with tab2:
    st.subheader("Simulador de Carrera")
    entrada = st.text_area("Pega los nombres de los caballos separados por coma:")
    
    if st.button("Calcular Favoritos"):
        lista = [n.strip() for n in entrada.split(",") if n.strip()]
        if lista:
            res_carrera = obtener_datos_seguros(lista)
            if not res_carrera.empty:
                st.success(f"🥇 Favorito sugerido: **{res_carrera.iloc[0]['caballo']}**")
                st.table(res_carrera)
                
                # Reporte de debutantes o sin datos
                encontrados = res_carrera['caballo'].str.upper().tolist()
                faltan = [n for n in lista if n.upper() not in encontrados]
                if faltan:
                    st.info(f"Sin historial de: {', '.join(faltan)} (Debutantes)")
            else:
                st.error("No hay registros de estos caballos en este hipódromo.")
