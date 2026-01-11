import streamlit as st
import pandas as pd

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

# ================= FUNCIONES DE CARGA =================
@st.cache_data
def obtener_datos_completos(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip() 
        return df
    except:
        return pd.DataFrame()

def procesar_bloques(df):
    preguntas_finales = []
    # Recorremos el dataframe en saltos de 5 filas exactas
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # FILA 1 del bloque (Índice 0): Enunciado
        enunciado = str(bloque.iloc[0]['Pregunta']).strip()
        explicacion_txt = str(bloque.iloc[0]['Justificación']).strip()
        
        # FILAS 2 a 5 del bloque (Índices 1, 2, 3, 4): Opciones y Marcador de Correcta
        opciones_bloque = []
        respuesta_correcta = ""
        
        # Analizamos las 4 filas de respuestas dentro del bloque
        for j in range(1, 5):
            texto_opcion = str(bloque.iloc[j]['Pregunta']).strip()
            marcador_justif = str(bloque.iloc[j]['Justificación']).lower()
            
            opciones_bloque.append(texto_opcion)
            
            # Buscamos la palabra "correcta" en la segunda columna (Justificación)
            if "correcta" in marcador_justif:
                respuesta_correcta = texto_opcion
        
        if enunciado and respuesta_correcta:
            preguntas_finales.append({
                "pregunta": enunciado,
                "opciones": opciones_bloque,
                "correcta": respuesta_correcta,
                "explicacion": explicacion_txt
            })
    return preguntas_finales

# ================= INTERFAZ =================
st.set_page_config(page_title="App Oposiciones", layout="centered")

if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 'tema_id': '', 'titulo_largo': '', 
        'idx': 0, 'puntos': 0, 'preguntas': [], 'modo': ''
    })

# --- PANTALLA 1: INICIO ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia")
    tema = st.selectbox("Selecciona Tema:", ["Tema 01", "Tema 02"])
    
    if st.button("Comenzar"):
        # 1. Cargar Título Largo desde pestaña 'Indice'
        df_idx = obtener_datos_completos(URL_SHEET, "Indice")
        if not df_idx.empty:
            df_idx['Tema_clean'] = df_idx['Tema'].astype(str).str.strip()
            res = df_idx[df_idx['Tema_clean'] == tema]
            st.session_state.titulo_largo = res.iloc[0]['Nombre Largo'] if not res.empty else tema
        
        # 2. Cargar y Procesar Preguntas
        df_qs = obtener_datos_completos(URL_SHEET, tema)
        if not df_qs.empty:
            st.session_state.preguntas = procesar_bloques(df_qs)
            st.session_state.tema_id = tema
            st.session_state.paso = 'modo'
            st.rerun()

# --- PANTALLA 2: MODO ---
elif st.session_state.paso == 'modo':
    st.info(f"🎯 **{st.session_state.titulo_largo}**")
    col1, col2 = st.columns(2)
    if col1.button("🛠️ Entrenamiento"):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if col2.button("⏱️ Examen"):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# --- PANTALLA 3: TEST ---
elif st.session_state.paso == 'test':
    st.markdown(f"### {st.session_state.titulo_largo}")
    st.divider()

    qs = st.session_state.preguntas
    if st.session_state.idx < len(qs):
        item = qs[st.session_state.idx]
        st.write(f"**Pregunta {st.session_state.idx + 1}:**")
        st.write(item['pregunta'])
        
        seleccion = st.radio("Elige una opción:", item['opciones'], key=f"p_{st.session_state.idx}")

        # Comparación robusta para evitar fallos por espacios o tildes
        es_ok = seleccion.strip().lower() == item['correcta'].strip().lower()

        if st.session_state.modo == 'Entrenamiento':
            if st.button("Validar ✅"):
                if es_ok: st.success("¡Correcto!")
                else: st.error(f"Incorrecto. La correcta es: {item['correcta']}")
                st.info(f"💡 {item['explicacion']}")

        if st.button("Siguiente ➡️"):
            if es_ok: st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.title("🏁 Fin del Test")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(qs)}")
        if st.button("Reiniciar"):
            st.session_state.clear()
            st.rerun()