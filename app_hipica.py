import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Hípica Chile Predictor", page_icon="🏇", layout="wide")

archivos_db = {
    "Club Hípico de Santiago": "chs_resultados.db",
    "Valparaíso Sporting": "vsc_resultados.db",
    "Hipódromo Chile": "hipodromo_resultados.db"
}

hipodromo = st.sidebar.selectbox("Selecciona Hipódromo:", list(archivos_db.keys()))
db_actual = archivos_db[hipodromo]

def obtener_datos_seguros(nombres_usuario=None):
    if not os.path.exists(db_actual):
        return pd.DataFrame()
    
    conn = sqlite3.connect(db_actual)
    try:
        df = pd.read_sql("SELECT * FROM resultados", conn)
        
        # 1. Normalizar nombres de columnas automáticamente
        renombrar = {
            'Ejemplar': 'caballo', 'Nombre': 'caballo', 'Caballo': 'caballo',
            'Orden': 'posicion', 'Llegada': 'posicion', 'Pos.': 'posicion', 'Lleg.': 'posicion'
        }
        df = df.rename(columns=renombrar)
        
        if 'caballo' not in df.columns or 'posicion' not in df.columns:
            return pd.DataFrame()

        # 2. Limpieza de datos: todo a Mayúsculas y posiciones a números
        df['caballo'] = df['caballo'].astype(str).str.upper().str.strip()
        df['posicion'] = pd.to_numeric(df['posicion'], errors='coerce').fillna(10)

        # 3. Si el usuario ingresó caballos para simular
        if nombres_usuario:
            busqueda = [n.upper().strip() for n in nombres_usuario]
            df = df[df['caballo'].isin(busqueda)]

        # 4. Agrupar resultados
        stats = df.groupby('caballo').agg(
            prom_pos=('posicion', 'mean'),
            carreras=('posicion', 'count'),
            mejor=('posicion', 'min')
        ).reset_index()
        
        stats['Score'] = (100 / (stats['prom_pos'] + 0.5)).round(1)
        return stats.sort_values(by='Score', ascending=False)
            
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# --- INTERFAZ ---
st.title(f"🏇 {hipodromo}")

tab1, tab2 = st.tabs(["🏆 Ranking del Hipódromo", "🔥 Analizar Carrera Específica"])

with tab1:
    res_gen = obtener_datos_seguros()
    if not res_gen.empty:
        st.write(f"Mostrando los mejores de {len(res_gen)} caballos registrados.")
        st.dataframe(res_gen.head(50), use_container_width=True)
    else:
        st.warning(f"La base de datos `{db_actual}` parece estar vacía o no existe en GitHub.")

with tab2:
    st.subheader("Simulador de Carrera")
    st.info("Pega los nombres tal como aparecen en el programa.")
    entrada = st.text_area("Nombres (ej: Oppa, Pazzelle, Merengon):")
    
    if st.button("Calcular Favoritos"):
        if entrada:
            lista = [n.strip() for n in entrada.split(",") if n.strip()]
            res_carrera = obtener_datos_seguros(lista)
            
            if not res_carrera.empty:
                st.success(f"🥇 Favorito por historial: **{res_carrera.iloc[0]['caballo']}**")
                st.table(res_carrera)
                
                # Reporte de los que no tienen historial
                encontrados = res_carrera['caballo'].tolist()
                faltan = [n.upper() for n in lista if n.upper() not in encontrados]
                if faltan:
                    st.warning(f"Sin datos de (posibles debutantes): {', '.join(faltan)}")
            else:
                st.error("No se encontró historial de estos ejemplares. Prueba subir una base de datos con más días de historia.")
