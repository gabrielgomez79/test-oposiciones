import streamlit as st
import pandas as pd

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=drive_link"

# ================= FUNCIONES =================
@st.cache_data
def obtener_titulo_largo(url, tema_id):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Indice"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        df['Tema_norm'] = df['Tema'].astype(str).str.lower().str.replace(" ", "").str.strip()
        tema_norm = tema_id.lower().replace(" ", "").strip()
        fila = df[df['Tema_norm'] == tema_norm]
        if not fila.empty:
            return str(fila.iloc[0]['Nombre Largo']).strip()
        return f"Repaso: {tema_id}"
    except:
        return f"Repaso: {tema_id}"

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
            
            # Opciones y estados
            opciones = bloque.iloc[1:5]['Pregunta'].astype(str).str.strip().tolist()
            estados = bloque.iloc[1:5]['Justificación'].astype(str).str.strip().tolist()
            
            correcta = ""
            for idx, est in enumerate(estados):
                # MEJORA: Buscamos si la palabra "correcta" aparece dentro del texto (ignora puntos y negritas)
                if "correcta" in est.lower():
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

if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 'tema_id': '', 'titulo_largo': '', 
        'modo': '', 'idx': 0, 'puntos': 0, 'preguntas': []
    })

# --- 1. SELECCIÓN TEMA ---
if st.session_state.paso == 'inicio':
    st.title("📚 Selector de Tema")
    tema = st.selectbox("Elige el tema:", ["Tema 01", "Tema 02"])
    if st.button("Continuar"):
        st.session_state.tema_id = tema
        st.session_state.titulo_largo = obtener_titulo_largo(URL_SHEET, tema)
        with st.spinner("Cargando preguntas..."):
            st.session_state.preguntas = cargar_preguntas(URL_SHEET, tema)
        st.session_state.paso = 'modo'
        st.rerun()

# --- 2. SELECCIÓN MODO ---
elif st.session_state.paso == 'modo':
    st.subheader(st.session_state.titulo_largo)
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
    st.markdown(f"### {st.session_state.titulo_largo}")
    st.caption(f"Pregunta {st.session_state.idx + 1} de {len(st.session_state.preguntas)} | Modo {st.session_state.modo}")
    st.divider()

    p = st.session_state.preguntas[st.session_state.idx]
    st.write(p['q'])
    res = st.radio("Opciones:", p['ops'], key=f"r_{st.session_state.idx}")

    # Comparación robusta: limpia espacios y minúsculas
    es_correcta = res.strip().lower() == p['ans'].strip().lower()

    if st.session_state.modo == 'Entrenamiento':
        if st.button("Comprobar ✅"):
            if es_correcta:
                st.success("¡Correcto! ✨")
            else:
                st.error(f"Incorrecto.")
                st.write(f"✅ La respuesta correcta es: **{p['ans']}**")
            st.info(f"**Justificación:** {p['tips']}")

    if st.button("Siguiente ➡️"):
        if es_correcta:
            st.session_state.puntos += 1
        st.session_state.idx += 1
        st.rerun()

# --- RESULTADOS ---
elif st.session_state.idx >= len(st.session_state.preguntas):
    st.title("🏁 Resultados Finales")
    st.metric("Aciertos", f"{st.session_state.puntos} / {len(st.session_state.preguntas)}")
    if st.button("Volver al Inicio"):
        st.session_state.clear()
        st.rerun()