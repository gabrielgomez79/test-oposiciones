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
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        enunciado = str(bloque.iloc[0]['Pregunta']).strip()
        explicacion_txt = str(bloque.iloc[0]['Justificación']).strip()
        
        opciones_bloque = []
        respuesta_correcta = ""
        
        for j in range(1, 5):
            texto_opcion = str(bloque.iloc[j]['Pregunta']).strip()
            marcador_justif = str(bloque.iloc[j]['Justificación']).lower()
            opciones_bloque.append(texto_opcion)
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
        'paso': 'inicio', 
        'tema_id': '', 
        'titulo_largo': '', 
        'idx': 0, 
        'puntos': 0, 
        'preguntas': [], 
        'modo': ''
    })

# --- PANTALLA 1: SELECCIÓN DE TEMA (MODIFICADA) ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia")
    
    # 1. Cargamos el índice primero para llenar el selector
    with st.spinner("Cargando catálogo de temas..."):
        df_idx = obtener_datos_completos(URL_SHEET, "Indice")
    
    if not df_idx.empty:
        # Creamos una lista de strings tipo "Tema 01 - Título Largo"
        opciones_selector = []
        for _, fila in df_idx.iterrows():
            texto_combinado = f"{fila['Tema']} - {fila['Nombre Largo']}"
            opciones_selector.append(texto_combinado)
        
        seleccion_completa = st.selectbox("Selecciona el tema a estudiar:", opciones_selector)
        
        if st.button("Continuar"):
            # Separamos la selección (asumimos que el separador es " - ")
            partes = seleccion_completa.split(" - ", 1)
            st.session_state.tema_id = partes[0].strip()
            st.session_state.titulo_largo = partes[1].strip()
            
            # 2. Cargar las preguntas del tema seleccionado
            with st.spinner(f"Cargando preguntas de {st.session_state.tema_id}..."):
                df_qs = obtener_datos_completos(URL_SHEET, st.session_state.tema_id)
                if not df_qs.empty:
                    st.session_state.preguntas = procesar_bloques(df_qs)
                    st.session_state.paso = 'modo'
                    st.rerun()
                else:
                    st.error(f"Error: No se encontró la hoja '{st.session_state.tema_id}' o está vacía.")
    else:
        st.error("No se pudo cargar la hoja 'Indice'. Verifica el nombre de la pestaña en Google Sheets.")

# --- PANTALLA 2: SELECCIÓN DE MODO ---
elif st.session_state.paso == 'modo':
    st.info(f"🎯 **{st.session_state.tema_id}: {st.session_state.titulo_largo}**")
    st.write("---")
    col1, col2 = st.columns(2)
    if col1.button("🛠️ Entrenamiento", use_container_width=True):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if col2.button("⏱️ Examen", use_container_width=True):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# --- PANTALLA 3: TEST ---
elif st.session_state.paso == 'test':
    st.markdown(f"### {st.session_state.tema_id}: {st.session_state.titulo_largo}")
    st.caption(f"Modo: {st.session_state.modo}")
    st.divider()

    qs = st.session_state.preguntas
    if st.session_state.idx < len(qs):
        item = qs[st.session_state.idx]
        st.write(f"**Pregunta {st.session_state.idx + 1} de {len(qs)}**")
        st.write(item['pregunta'])
        
        seleccion = st.radio("Opciones:", item['opciones'], index=None, key=f"p_{st.session_state.idx}")

        col_val, col_sig = st.columns(2)

        if st.session_state.modo == 'Entrenamiento':
            if col_val.button("Validar ✅", use_container_width=True):
                if seleccion is None:
                    st.warning("⚠️ Selecciona una respuesta.")
                else:
                    es_ok = seleccion.strip().lower() == item['correcta'].strip().lower()
                    if es_ok: st.success("¡Correcto!")
                    else: st.error(f"Incorrecto. Era: {item['correcta']}")
                    st.info(f"💡 {item['explicacion']}")

        if col_sig.button("Siguiente ➡️", use_container_width=True):
            if seleccion is None:
                st.warning("⚠️ Debes marcar una opción.")
            else:
                if seleccion.strip().lower() == item['correcta'].strip().lower():
                    st.session_state.puntos += 1
                st.session_state.idx += 1
                st.rerun()
    else:
        st.balloons()
        st.title("🏁 Resultados")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(qs)}")
        if st.button("Volver al Inicio"):
            st.session_state.clear()
            st.rerun()