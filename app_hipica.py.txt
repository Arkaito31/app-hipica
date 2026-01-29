import streamlit as st
import pandas as pd
import sqlite3

# Configuración visual para móvil
st.set_page_config(
    page_title="Hípica Chile Predictor",
    page_icon="🏇",
    layout="centered"
)

# Función para conectar con tu base de datos
def conectar_db():
    return sqlite3.connect('hipica_chile.db')

# Lógica del Algoritmo de Predicción
def obtener_ranking():
    conn = conectar_db()
    try:
        # Analizamos caballos con al menos 3 carreras para mayor precisión
        query = """
            SELECT caballo, 
                   AVG(posicion) as promedio_pos, 
                   COUNT(*) as carreras_total,
                   hipodromo
            FROM resultados 
            GROUP BY caballo 
            HAVING carreras_total >= 3
        """
        df = pd.read_sql(query, conn)
        
        # Algoritmo de Scoring (Base 100)
        # A menor posición promedio, mayor puntaje
        df['Score'] = (100 / (df['promedio_pos'] + 0.5)).round(1)
        
        # Bonus por experiencia (más carreras = más confiable)
        df['Score'] = df['Score'] + (df['carreras_total'] * 0.5)
        
        return df.sort_values(by='Score', ascending=False)
    except Exception as e:
        st.error(f"Error al leer la base de datos: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# --- INTERFAZ DE LA APP ---
st.title("🏇 Predictor Hípico Chile")
st.markdown("---")

# Menú inferior tipo App
menu = st.sidebar.radio("Navegación", ["🏆 Top Ranking", "🔍 Buscador de Caballos", "📊 Mi Base de Datos"])

if menu == "🏆 Top Ranking":
    st.header("Mejores Rendimientos")
    st.write("Caballos con mayor probabilidad según su historial:")
    
    ranking = obtener_ranking()
    
    if not ranking.empty:
        for i, row in ranking.head(20).iterrows():
            # Formato de tarjeta para móvil
            with st.expander(f"⭐ {row['caballo']}"):
                col1, col2 = st.columns(2)
                col1.metric("Puntaje", f"{row['Score']} pts")
                col2.metric("Pos. Promedio", f"{row['promedio_pos']:.1f}")
                st.write(f"📍 Hipódromo principal: {row['hipodromo']}")
                st.write(f"📋 Carreras analizadas: {row['carreras_total']}")
    else:
        st.info("No hay suficientes datos. Asegúrate de que 'hipica_chile.db' esté en la misma carpeta.")

elif menu == "🔍 Buscador de Caballos":
    st.header("Buscador de Ejemplares")
    nombre = st.text_input("Escribe el nombre del caballo:")
    
    if nombre:
        conn = conectar_db()
        query = f"SELECT fecha, hipodromo, posicion, dividendo FROM resultados WHERE caballo LIKE '%{nombre}%' ORDER BY fecha DESC"
        historial = pd.read_sql(query, conn)
        conn.close()
        
        if not historial.empty:
            st.success(f"Historial para {nombre.upper()}")
            st.dataframe(historial, use_container_width=True)
        else:
            st.warning("No se encontró historial para ese nombre.")

elif menu == "📊 Mi Base de Datos":
    st.header("Estado del Sistema")
    conn = conectar_db()
    total_registros = pd.read_sql("SELECT COUNT(*) as total FROM resultados", conn).iloc[0]['total']
    st.metric("Total de Carreras Guardadas", total_registros)
    
    resumen = pd.read_sql("SELECT hipodromo, COUNT(*) as cantidad FROM resultados GROUP BY hipodromo", conn)
    st.bar_chart(resumen.set_index('hipodromo'))
    conn.close()