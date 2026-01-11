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
        
        # FILA 1 del bloque (Índice 0): Enunciado y Justificación general
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

# Inicialización de estados de sesión
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

# --- PANTALLA 1: SELECCIÓN DE TEMA ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia")
    tema = st.selectbox("Selecciona Tema de estudio:", ["Tema 01", "Tema 02"])
    
    if st.button("Continuar"):
        # 1. Cargar Título Largo desde pestaña 'Indice'
        df_idx = obtener_datos_completos(URL_SHEET, "Indice")
        if not df_idx.empty:
            df_idx['Tema_clean'] = df_idx['Tema'].astype(str).str.strip()
            res = df_idx[df_idx['Tema_clean'] == tema]
            st.session_state.titulo_largo = res.iloc[0]['Nombre Largo'] if not res.empty else "Tema sin título"
        
        # 2. Cargar y Procesar Preguntas
        df_qs = obtener_datos_completos(URL_SHEET, tema)
        if not df_qs.empty:
            st.session_state.preguntas = procesar_bloques(df_qs)
            st.session_state.tema_id = tema
            st.session_state.paso = 'modo'
            st.rerun()
        else:
            st.error(f"No se pudieron cargar preguntas para el {tema}. Revisa el nombre de la hoja.")

# --- PANTALLA 2: SELECCIÓN DE MODO ---
elif st.session_state.paso == 'modo':
    st.info(f"🎯 **{st.session_state.tema_id}: {st.session_state.titulo_largo}**")
    st.write("---")
    st.write("### Elige tu metodología:")
    col1, col2 = st.columns(2)
    if col1.button("🛠️ Entrenamiento", use_container_width=True):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if col2.button("⏱️ Examen", use_container_width=True):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# --- PANTALLA 3: TEST (ENTRENAMIENTO O EXAMEN) ---
elif st.session_state.paso == 'test':
    # Encabezado combinado solicitado
    st.markdown(f"### {st.session_state.tema_id}: {st.session_state.titulo_largo}")
    st.caption(f"Modo actual: {st.session_state.modo}")
    st.divider()

    qs = st.session_state.preguntas
    if st.session_state.idx < len(qs):
        item = qs[st.session_state.idx]
        st.write(f"**Pregunta {st.session_state.idx + 1} de {len(qs)}**")
        st.write(item['pregunta'])
        
        # index=None asegura que no haya selección previa
        seleccion = st.radio(
            "Selecciona tu respuesta:", 
            item['opciones'], 
            index=None, 
            key=f"p_{st.session_state.idx}"
        )

        col_val, col_sig = st.columns(2)

        # Botón Validar (Solo disponible en modo Entrenamiento)
        if st.session_state.modo == 'Entrenamiento':
            if col_val.button("Validar ✅", use_container_width=True):
                if seleccion is None:
                    st.warning("⚠️ Selecciona una respuesta para validar.")
                else:
                    es_ok = seleccion.strip().lower() == item['correcta'].strip().lower()
                    if es_ok: 
                        st.success("¡Correcto! ✨")
                    else: 
                        st.error(f"Incorrecto. La respuesta correcta era: {item['correcta']}")
                    st.info(f"💡 **Justificación:** {item['explicacion']}")

        # Botón Siguiente (Aplica a ambos modos con validación de selección)
        if col_sig.button("Siguiente ➡️", use_container_width=True):
            if seleccion is None:
                st.warning("⚠️ Debes marcar una opción para continuar.")
            else:
                es_ok = seleccion.strip().lower() == item['correcta'].strip().lower()
                if es_ok: 
                    st.session_state.puntos += 1
                st.session_state.idx += 1
                st.rerun()
    else:
        # PANTALLA FINAL DE RESULTADOS
        st.balloons()
        st.title("🏁 Resultados Finales")
        st.metric("Puntuación Obtenida", f"{st.session_state.puntos} / {len(qs)}")
        
        # Calcular porcentaje si quieres añadirlo
        porcentaje = (st.session_state.puntos / len(qs)) * 100
        st.progress(porcentaje / 100)
        st.write(f"Has acertado el {porcentaje:.1f}% de las preguntas.")

        if st.button("Volver al Inicio"):
            st.session_state.clear()
            st.rerun()