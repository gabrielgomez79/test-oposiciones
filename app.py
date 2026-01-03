import streamlit as st
import pandas as pd

# CONFIGURACIÓN
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=drive_link"

def obtener_titulo_largo(url, tema_id):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Indice"
        df_idx = pd.read_csv(csv_url)
        df_idx.columns = [c.strip() for c in df_idx.columns]
        # Buscamos la fila que coincide
        fila = df_idx[df_idx['Tema'].astype(str).str.strip() == tema_id.strip()]
        if not fila.empty:
            return fila.iloc[0]['Nombre Largo']
        return f"Título no definido para {tema_id}"
    except:
        return f"Repaso: {tema_id}"

def cargar_preguntas(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        df = pd.read_csv(csv_url)
        df.columns = [c.strip() for c in df.columns]
        
        datos = []
        for i in range(0, len(df), 5):
            bloque = df.iloc[i:i+5]
            if len(bloque) < 5: break
            opciones = bloque.iloc[1:5]['Pregunta'].astype(str).tolist()
            estados = bloque.iloc[1:5]['Justificación'].astype(str).tolist()
            
            correcta = ""
            for idx, est in enumerate(estados):
                if "correcta" in est.lower():
                    correcta = opciones[idx]
                    break
            
            datos.append({
                "q": bloque.iloc[0]['Pregunta'],
                "tips": bloque.iloc[0]['Justificación'],
                "ops": opciones,
                "ans": correcta
            })
        return datos
    except:
        return []

# --- APP ---
st.set_page_config(page_title="Test Oposiciones", layout="centered")

if 'paso' not in st.session_state:
    st.session_state.update({'paso': 'inicio', 'tema_id': '', 'titulo_largo': '', 'modo': '', 'idx': 0, 'puntos': 0})

# 1. INICIO
if st.session_state.paso == 'inicio':
    st.title("📚 Selector de Tema")
    tema = st.selectbox("Elige:", ["Tema 01", "Tema 02"])
    if st.button("Continuar"):
        st.session_state.tema_id = tema
        # BUSCAMOS EL TÍTULO AQUÍ Y LO GUARDAMOS
        st.session_state.titulo_largo = obtener_titulo_largo(URL_SHEET, tema)
        st.session_state.paso = 'modo'
        st.rerun()

# 2. MODO
elif st.session_state.paso == 'modo':
    # MOSTRAMOS EL TÍTULO LARGO
    st.info(f"📍 {st.session_state.titulo_largo}")
    st.write("---")
    c1, c2 = st.columns(2)
    if c1.button("🛠️ Entrenamiento"):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if c2.button("⏱️ Examen"):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# 3. TEST
elif st.session_state.paso == 'test':
    # TÍTULO SIEMPRE ARRIBA
    st.markdown(f"### {st.session_state.titulo_largo}")
    st.caption(f"Pregunta {st.session_state.idx + 1} | Modo {st.session_state.modo}")
    st.divider()

    preguntas = cargar_preguntas(URL_SHEET, st.session_state.tema_id)
    if st.session_state.idx < len(preguntas):
        p = preguntas[st.session_state.idx]
        st.write(p['q'])
        res = st.radio("Opciones:", p['ops'], key=f"v_{st.session_state.idx}")
        
        if st.session_state.modo == 'Entrenamiento':
            if st.button("Comprobar ✅"):
                if res == p['ans']: st.success("¡Correcto!")
                else: st.error(f"Fallo. Es: {p['ans']}")
                st.info(f"Explicación: {p['tips']}")

        if st.button("Siguiente ➡️"):
            if res == p['ans']: st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.title("🏁 Resultados")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(preguntas)}")
        if st.button("Reiniciar"):
            st.session_state.clear()
            st.rerun()