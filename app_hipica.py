import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Hípica Chile", page_icon="🏇")

def conectar_db():
    return sqlite3.connect('hipica_chile.db')

def obtener_datos():
    conn = conectar_db()
    try:
        # Cargamos todos los datos disponibles
        df = pd.read_sql("SELECT * FROM resultados", conn)
        
        # Normalizamos nombres de columnas (de 'Ejemplar' a 'caballo')
        renombrar = {
            'Ejemplar': 'caballo', 'Nombre': 'caballo', 'Caballo': 'caballo',
            'Orden': 'posicion', 'Llegada': 'posicion', 'Pos.': 'posicion'
        }
        df = df.rename(columns=renombrar)
        
        if 'caballo' in df.columns:
            # Limpieza de datos
            df['posicion'] = pd.to_numeric(df['posicion'], errors='coerce').fillna(10)
            
            # Cálculo de rendimiento
            stats = df.groupby('caballo').agg(
                prom_pos=('posicion', 'mean'),
                carreras=('posicion', 'count')
            ).reset_index()
            
            # Puntaje: A menor posición, más puntos
            stats['Score'] = (100 / (stats['prom_pos'] + 0.5)).round(1)
            return stats.sort_values(by='Score', ascending=False)
        return pd.DataFrame()
    except:
        return pd.DataFrame()
    finally:
        conn.close()

st.title("🏇 Predictor Hípico Chile")

# Interfaz simplificada para móvil
tab1, tab2 = st.tabs(["🏆 Ranking", "🔍 Buscador"])

with tab1:
    res = obtener_datos()
    if not res.empty:
        st.subheader("Mejores según historial")
        for _, row in res.head(20).iterrows():
            with st.expander(f"⭐ {row['caballo']}"):
                st.write(f"**Puntaje:** {row['Score']} pts")
                st.write(f"**Carreras registradas:** {int(row['carreras'])}")
    else:
        st.info("Aún no hay datos suficientes. Sube tu archivo .db actualizado.")

with tab2:
    nombre = st.text_input("Buscar caballo por nombre")
    if nombre:
        conn = conectar_db()
        # Busca en cualquier columna de nombre posible
        query = f"SELECT * FROM resultados WHERE Ejemplar LIKE '%{nombre}%' OR Caballo LIKE '%{nombre}%' LIMIT 10"
        busqueda = pd.read_sql(query, conn)
        st.dataframe(busqueda)
        conn.close()
