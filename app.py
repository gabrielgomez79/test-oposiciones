import streamlit as st
import pandas as pd

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

# ================= FUNCIONES =================
@st.cache_data
def obtener_titulo_largo(url, tema_id):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        # Forzamos la lectura de la hoja "Indice"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Indice"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        # Normalizamos para comparar
        df['Tema_match'] = df['Tema'].astype(str).str.lower().str.replace(" ", "")
        tema_buscado = tema_id.lower().replace(" ", "")
        
        fila = df[df['Tema_match'] == tema_buscado]
        if not fila.empty:
            return str(fila.iloc[0]['Nombre Largo']).strip()
        return f"Título no encontrado en Indice para {tema_id}"
    except Exception as e:
        return f"Error cargando Indice: {str(e)}"

@st.cache_data
def cargar_preguntas(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        
        datos = []
        for i in range(0, len(df), 5):
            bloque = df.iloc[i:i+5]
            if len(bloque) < 5: break
            
            # Limpiamos opciones
            opciones = bloque.iloc[1:5]['Pregunta'].astype(str).str.strip().tolist()
            # Leemos la columna Justificación para encontrar la correcta
            estados = bloque.iloc[1:5]['Justificación'].astype(str).str.lower().tolist()
            
            correcta = ""
            for idx, est in enumerate(estados):
                # BUSQUEDA FLEXIBLE: Si contiene "correcta", esa es la buena (aunque tenga puntos o negritas)
                if "correcta" in est:
                    correcta = opciones[idx]
                    break
            
            datos.append({
                "q": str(bloque.iloc[0]['Pregunta']).strip(),
                "tips": str(bloque.iloc[0]['Justificación']).strip(),
                "ops": opciones,
                "ans": correcta 
            })
        return datos
    except:
        return []

# ================= INTERFAZ =================
st.set_page_config(page_title="App Test Oposiciones", layout="centered")

# Inicializamos todas las variables necesarias en el estado de la sesión
if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 
        'tema_id': '', 
        'titulo_largo': '', 
        'modo': '', 
        'idx': 0, 
        'puntos': 0, 
        'preguntas': []
    })

# --- 1. SELECCIÓN TEMA ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia")
    tema = st.selectbox("Selecciona el tema de estudio:", ["Tema 01", "Tema 02"])
    
    if st.button("Empezar"):
        st.session_state.tema_id = tema
        # Guardamos el título largo AQUÍ para que persista
        st.session_state.titulo_largo = obtener_titulo_largo(URL_SHEET, tema)
        with st.spinner("Preparando preguntas..."):
            st.session_state.preguntas = cargar_preguntas(URL_SHEET, tema)
        st.session_state.paso = 'modo'
        st.rerun()

# --- 2. SELECCIÓN MODO ---
elif st.session_state.paso == 'modo':
    # Mostramos el título que guardamos antes
    st.info(f"📍 {st.session_state.titulo_largo}")
    st.write("---")
    c1, c2 = st.columns(2)
    if c1.button("🛠️ Entrenamiento"):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if c2.button("⏱️ Examen"):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# --- 3. TEST ---
elif st.session_state.paso == 'test':
    # EL TÍTULO LARGO SIEMPRE ARRIBA
    st.markdown(f"### {st.session_state.titulo_largo}")
    st.caption(f"Pregunta {st.session_state.idx + 1} de {len(st.session_state.preguntas)} | Modo {st.session_state.modo}")
    st.divider()

    if st.session_state.idx < len(st.session_state.preguntas):
        p = st.session_state.preguntas[st.session_state.idx]
        st.write(f"**{p['q']}**")
        
        # Widget de respuesta
        res = st.radio("Selecciona tu respuesta:", p['ops'], key=f"r_{st.session_state.idx}")

        # COMPARACIÓN BLINDADA: quitamos espacios y pasamos a minúsculas
        es_correcta = res.strip().lower() == p['ans'].strip().lower()

        if st.session_state.modo == 'Entrenamiento':
            if st.button("Comprobar ✅"):
                if es_correcta:
                    st.success("¡Correcto! ✨")
                else:
                    st.error(f"Incorrecto. La respuesta era: {p['ans']}")
                st.info(f"**Justificación:** {p['tips']}")

        if st.button("Siguiente Pregunta ➡️"):
            if es_correcta:
                st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.title("🏁 Resultados")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(st.session_state.preguntas)}")
        if st.button("Volver al Inicio"):
            # Limpiamos todo para empezar de cero
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()