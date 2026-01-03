import streamlit as st
import pandas as pd

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=drive_link"

# ================= FUNCIONES =================
@st.cache_data
def obtener_titulo_largo(url, tema_id):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{sheet_id}/gviz/tq?tqx=out:csv&sheet=Indice"
        )

        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()

        # Normalización fuerte (CLAVE)
        df['Tema_norm'] = (
            df['Tema']
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "")
        )

        tema_norm = (
            tema_id
            .strip()
            .lower()
            .replace(" ", "")
        )

        fila = df[df['Tema_norm'] == tema_norm]

        if not fila.empty:
            return str(fila.iloc[0]['Nombre Largo']).strip()

        return f"Repaso: {tema_id}"

    except Exception:
        return f"Repaso: {tema_id}"


@st.cache_data
def cargar_preguntas(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        )

        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()

        datos = []

        for i in range(0, len(df), 5):
            bloque = df.iloc[i:i + 5]
            if len(bloque) < 5:
                break

            opciones = bloque.iloc[1:5]['Pregunta'].astype(str).tolist()
            estados = bloque.iloc[1:5]['Justificación'].astype(str).tolist()

            correcta = ""
            for idx, est in enumerate(estados):
                if "correcta" in est.lower():
                    correcta = opciones[idx]
                    break

            datos.append({
                "q": str(bloque.iloc[0]['Pregunta']),
                "tips": str(bloque.iloc[0]['Justificación']),
                "ops": opciones,
                "ans": correcta
            })

        return datos

    except Exception:
        return []


# ================= APP =================
st.set_page_config(page_title="Test Oposiciones", layout="centered")

# ================= SESSION STATE =================
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

# ================= 1. INICIO =================
if st.session_state.paso == 'inicio':
    st.title("📚 Selector de Tema")

    tema = st.selectbox("Elige:", ["Tema 01", "Tema 02"])

    if st.button("Continuar"):
        st.session_state.tema_id = tema
        st.session_state.titulo_largo = obtener_titulo_largo(URL_SHEET, tema)
        st.session_state.preguntas = cargar_preguntas(URL_SHEET, tema)
        st.session_state.idx = 0
        st.session_state.puntos = 0
        st.session_state.paso = 'modo'
        st.rerun()

# ================= 2. MODO =================
elif st.session_state.paso == 'modo':
    titulo = st.session_state.get("titulo_largo", "").strip()
    st.header(titulo if titulo else f"Repaso: {st.session_state.tema_id}")
    st.write("---")

    c1, c2 = st.columns(2)

    if c1.button("🛠️ Entrenamiento"):
        st.session_state.modo = 'Entrenamiento'
        st.session_state.paso = 'test'
        st.rerun()

    if c2.button("⏱️ Examen"):
        st.session_state.modo = 'Examen'
        st.session_state.paso = 'test'
        st.rerun()

# ================= 3. TEST =================
elif st.session_state.paso == 'test':
    titulo = st.session_state.get("titulo_largo", "").strip()
    st.header(titulo if titulo else f"Repaso: {st.session_state.tema_id}")
    st.caption(f"Pregunta {st.session_state.idx + 1} | Modo {st.session_state.modo}")
    st.divider()

    preguntas = st.session_state.preguntas

    if st.session_state.idx < len(preguntas):
        p = preguntas[st.session_state.idx]

        st.write(p['q'])
        res = st.radio("Opciones:", p['ops'], key=f"v_{st.session_state.idx}")

        if st.session_state.modo == 'Entrenamiento':
            if st.button("Comprobar ✅"):
                if res == p['ans']:
                    st.success("¡Correcto!")
                else:
                    st.error(f"Incorrecto. La respuesta correcta es: {p['ans']}")
                st.info(f"Explicación: {p['tips']}")

        if st.button("Siguiente ➡️"):
            if res == p['ans']:
                st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()

    else:
        st.title("🏁 Resultados")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(preguntas)}")

        if st.button("Reiniciar"):
            st.session_state.clear()
            st.rerun()
