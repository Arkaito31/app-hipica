import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Hípica Chile", page_icon="🏇")

def conectar_db():
    return sqlite3.connect('hipica_chile.db')

def obtener_datos():
    conn = conectar_db()
    try:
        # Cargamos los datos crudos para ver qué columnas existen
        df = pd.read_sql("SELECT * FROM resultados", conn)
        
        # Diccionario para normalizar nombres de columnas
        # Si el hipódromo puso 'Ejemplar', lo cambiamos a 'caballo'
        columnas_clip = {
            'Ejemplar': 'caballo', 'Nombre': 'caballo', 'Caballo': 'caballo',
            'Orden': 'posicion', 'Llegada': 'posicion', 'Pos.': 'posicion'
        }
        df = df.rename(columns=columnas_clip)
        
        # Si después de renombrar tenemos lo necesario, calculamos
        if 'caballo' in df.columns and 'posicion' in df.columns:
            # Limpiamos la columna posicion por si tiene letras
            df['posicion'] = pd.to_numeric(df['posicion'], errors='coerce').fillna(10)
            
            stats = df.groupby('caballo').agg(
                promedio_pos=('posicion', 'mean'),
                carreras_total=('posicion', 'count')
            ).reset_index()
            
            stats['Score'] = (100 / (stats['promedio_pos'] + 0.5)).round(1)
            return stats.sort_values(by='Score', ascending=False)
        return pd.DataFrame()
    except:
        return pd.DataFrame()
    finally:
        conn.close()

st.title("🏇 Predictor Hípico Chile")

menu = st.sidebar.radio("Navegación", ["🏆 Top Ranking", "🔍 Buscador"])

if menu == "🏆 Top Ranking":
    res = obtener_datos()
    if not res.empty:
        st.subheader("Favoritos por Historial")
        for _, row in res.head(15).iterrows():
            with st.expander(f"⭐ {row['caballo']}"):
                st.metric("Puntaje", f"{row['Score']} pts")
                st.write(f"Carreras analizadas: {int(row['carreras_total'])}")
    else:
        st.warning("Base de datos conectada, pero las columnas no coinciden. Ejecuta la aspiradora de nuevo para refrescar.")

elif menu == "🔍 Buscador":
    nombre = st.text_input("Nombre del caballo")
    if nombre:
        conn = conectar_db()
        df = pd.read_sql(f"SELECT * FROM resultados WHERE Ejemplar LIKE '%{nombre}%' OR Caballo LIKE '%{nombre}%'", conn)
        st.dataframe(df)
        conn.close()
    
    resumen = pd.read_sql("SELECT hipodromo, COUNT(*) as cantidad FROM resultados GROUP BY hipodromo", conn)
    st.bar_chart(resumen.set_index('hipodromo'))

    conn.close()
