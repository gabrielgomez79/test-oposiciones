import streamlit as st
import pandas as pd

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

# ================= FUNCIONES MEJORADAS =================
@st.cache_data
def obtener_datos_limpios(url, nombre_hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja.replace(' ', '%20')}"
        df = pd.read_csv(csv_url)
        # Limpiamos nombres de columnas (quita espacios invisibles)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

def procesar_preguntas(df):
    preguntas_list = []
    # Recorremos en bloques de 5
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # Opciones: filas 2 a 5 del bloque
        opciones = bloque.iloc[1:5]['Pregunta'].astype(str).str.strip().tolist()
        # Estados: buscamos la palabra "correcta" sin importar puntos o mayúsculas
        estados = bloque.iloc[1:5]['Justificación'].astype(str).str.lower().tolist()
        
        correcta = ""
        for idx, est in enumerate(estados):
            if "correcta" in est: # Busca el texto "correcta" dentro de la celda
                correcta = opciones[idx]
                break
        
        preguntas_list.append({
            "enunciado": str(bloque.iloc[0]['Pregunta']).strip(),
            "explicacion": str(bloque.iloc[0]['Justificación']).strip(),
            "opciones": opciones,
            "correcta": correcta
        })
    return preguntas_list

# ================= INTERFAZ STREAMLIT =================
st.set_page_config(page_title="App Oposiciones", layout="centered")

if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 'tema_id': '', 'titulo_largo': '', 
        'modo': '', 'idx': 0, 'puntos': 0, 'preguntas': []
    })

# --- PASO 1: SELECCIÓN ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia Móvil")
    tema = st.selectbox("Elige tu tema:", ["Tema 01", "Tema 02"])
    
    if st.button("Empezar Estudio"):
        # 1. Buscar Título Largo
        df_idx = obtener_datos_limpios(URL_SHEET, "Indice")
        if not df_idx.empty:
            df_idx['Tema_match'] = df_idx['Tema'].astype(str).str.strip().str.lower()
            match = df_idx[df_idx['Tema_match'] == tema.lower().strip()]
            st.session_state.titulo_largo = str(match.iloc[0]['Nombre Largo']) if not match.empty else tema
        
        # 2. Cargar Preguntas
        df_qs = obtener_datos_limpios(URL_SHEET, tema)
        if not df_qs.empty:
            st.session_state.preguntas = procesar_preguntas(df_qs)
            st.session_state.tema_id = tema
            st.session_state.paso = 'modo'
            st.rerun()

# --- PASO 2: MODO ---
elif st.session_state.paso == 'modo':
    st.info(f"🎯 **{st.session_state.titulo_largo}**")
    c1, c2 = st.columns(2)
    if c1.button("🛠️ Entrenamiento"):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if c2.button("⏱️ Examen"):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# --- PASO 3: TEST ---
elif st.session_state.paso == 'test':
    # EL TÍTULO SIEMPRE VISIBLE ARRIBA
    st.markdown(f"### {st.session_state.titulo_largo}")
    st.divider()

    p = st.session_state.preguntas[st.session_state.idx]
    st.write(f"**{p['enunciado']}**")
    
    respuesta = st.radio("Opciones:", p['opciones'], key=f"q_{st.session_state.idx}")

    # Comparación blindada (quita espacios y tildes si las hubiera)
    es_correcta = respuesta.strip().lower() == p['correcta'].strip().lower()

    if st.session_state.modo == 'Entrenamiento':
        if st.button("Comprobar ✅"):
            if es_correcta: st.success("¡Muy bien! Es correcto.")
            else: st.error(f"Incorrecto. La buena era: {p['correcta']}")
            st.info(f"💡 {p['explicacion']}")

    if st.button("Siguiente ➡️"):
        if es_correcta: st.session_state.puntos += 1
        st.session_state.idx += 1
        st.rerun()

# --- RESULTADOS ---
if st.session_state.paso == 'test' and st.session_state.idx >= len(st.session_state.preguntas):
    st.balloons()
    st.title("🏁 ¡Test Terminado!")
    st.metric("Tu Nota", f"{st.session_state.puntos} / {len(st.session_state.preguntas)}")
    if st.button("Volver al Inicio"):
        st.session_state.clear()
        st.rerun()