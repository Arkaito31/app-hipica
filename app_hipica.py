import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Hípica Chile Multi-Sede", page_icon="🏇")

# --- BARRA LATERAL (CONFIGURACIÓN) ---
st.sidebar.title("Configuración")
hipodromo = st.sidebar.selectbox(
    "Selecciona el Hipódromo:",
    ["Club Hípico de Santiago", "Valparaíso Sporting", "Hipódromo Chile"]
)

# Diccionario para mapear selección con nombre de archivo
archivos_db = {
    "Club Hípico de Santiago": "chs_resultados.db",
    "Valparaíso Sporting": "vsc_resultados.db",
    "Hipódromo Chile": "hipodromo_resultados.db"
}

db_actual = archivos_db[hipodromo]

def conectar_db():
    return sqlite3.connect(db_actual)

def obtener_datos():
    if not os.path.exists(db_actual):
        return None
    
    conn = conectar_db()
    try:
        df = pd.read_sql("SELECT * FROM resultados", conn)
        
        # Normalizar columnas (los sitios web usan nombres distintos)
        renombrar = {
            'Ejemplar': 'caballo', 'Nombre': 'caballo', 'Caballo': 'caballo',
            'Orden': 'posicion', 'Llegada': 'posicion', 'Pos.': 'posicion', 'Lleg.': 'posicion'
        }
        df = df.rename(columns=renombrar)
        
        if 'caballo' in df.columns and 'posicion' in df.columns:
            # Limpiar datos de posición (quitar letras o vacíos)
            df['posicion'] = pd.to_numeric(df['posicion'], errors='coerce').fillna(10)
            
            stats = df.groupby('caballo').agg(
                prom_pos=('posicion', 'mean'),
                carreras=('posicion', 'count')
            ).reset_index()
            
            # Algoritmo de Score
            stats['Score'] = (100 / (stats['prom_pos'] + 0.5)).round(1)
            return stats.sort_values(by='Score', ascending=False)
        return pd.DataFrame()
    except:
        return pd.DataFrame()
    finally:
        conn.close()

# --- CUERPO DE LA APP ---
st.title(f"🏇 {hipodromo}")
st.write(f"Leyendo datos de: `{db_actual}`")

tab1, tab2 = st.tabs(["🏆 Ranking Favoritos", "🔍 Buscador"])

with tab1:
    res = obtener_datos()
    if res is None:
        st.error(f"⚠️ El archivo `{db_actual}` no se encuentra en GitHub. ¡Súbelo para ver los datos!")
    elif not res.empty:
        st.subheader("Mejores rendimientos (Historial)")
        for _, row in res.head(20).iterrows():
            with st.expander(f"⭐ {row['caballo']}"):
                st.metric("Puntaje", f"{row['Score']} pts")
                st.write(f"Carreras analizadas: {int(row['carreras'])}")
                st.write(f"Posición promedio: {row['prom_pos']:.1f}")
    else:
        st.info("No hay datos suficientes en esta base de datos.")

with tab2:
    nombre = st.text_input("Buscar ejemplar:")
    if nombre and os.path.exists(db_actual):
        conn = conectar_db()
        # Buscamos por nombre en las columnas comunes
        query = f"SELECT * FROM resultados WHERE Ejemplar LIKE '%{nombre}%' OR Caballo LIKE '%{nombre}%' OR Nombre LIKE '%{nombre}%' LIMIT 15"
        busqueda = pd.read_sql(query, conn)
        st.dataframe(busqueda)
        conn.close()
