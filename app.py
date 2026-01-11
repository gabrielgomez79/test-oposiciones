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
        df.columns = df.columns.str.strip() # Limpiar espacios en nombres de columnas
        return df
    except:
        return pd.DataFrame()

def procesar_bloques(df):
    preguntas_finales = []
    # Procesamos de 5 en 5 filas
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # 1. El enunciado está siempre en la primera fila del bloque
        pregunta_texto = str(bloque.iloc[0]['Pregunta']).strip()
        justificacion_texto = str(bloque.iloc[0]['Justificación']).strip()
        
        # 2. Extraer opciones (Filas 1 a 4 del bloque)
        opciones_bloque = bloque.iloc[1:5]['Pregunta'].astype(str).str.strip().tolist()
        estados_bloque = bloque.iloc[1:5]['Justificación'].astype(str).str.lower().tolist()
        
        # 3. BUSCADOR INTELIGENTE DE LA CORRECTA
        # Buscamos en las 4 filas de opciones cuál tiene la palabra "correcta"
        respuesta_correcta = ""
        for idx, texto_justif in enumerate(estados_bloque):
            if "correcta" in texto_justif:
                respuesta_correcta = opciones_bloque[idx]
                break
        
        # Solo añadimos si encontramos una pregunta y una respuesta
        if pregunta_texto and respuesta_correcta:
            preguntas_finales.append({
                "pregunta": pregunta_texto,
                "opciones": opciones_bloque,
                "correcta": respuesta_correcta,
                "explicacion": justificacion_texto
            })
    return preguntas_finales

# ================= INTERFAZ =================
st.set_page_config(page_title="Test Oposiciones", layout="centered")

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
        # Cargar Título
        df_idx = obtener_datos_completos(URL_SHEET, "Indice")
        if not df_idx.empty:
            df_idx['Tema_clean'] = df_idx['Tema'].astype(str).str.strip()
            res = df_idx[df_idx['Tema_clean'] == tema]
            st.session_state.titulo_largo = res.iloc[0]['Nombre Largo'] if not res.empty else tema
        
        # Cargar Preguntas
        df_qs = obtener_datos_completos(URL_SHEET, tema)
        if not df_qs.empty:
            st.session_state.preguntas = procesar_bloques(df_qs)
            st.session_state.tema_id = tema
            st.session_state.paso = 'modo'
            st.rerun()

# --- PANTALLA 2: MODO ---
elif st.session_state.paso == 'modo':
    st.subheader(f"📍 {st.session_state.titulo_largo}")
    col1, col2 = st.columns(2)
    if col1.button("🛠️ Entrenamiento"):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if col2.button("⏱️ Examen"):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# --- PANTALLA 3: TEST ---
elif st.session_state.paso == 'test':
    # Título persistente
    st.markdown(f"### {st.session_state.titulo_largo}")
    st.divider()

    qs = st.session_state.preguntas
    if st.session_state.idx < len(qs):
        item = qs[st.session_state.idx]
        
        st.write(f"**Pregunta {st.session_state.idx + 1}:**")
        st.write(item['pregunta'])
        
        seleccion = st.radio("Elige una opción:", item['opciones'], key=f"p_{st.session_state.idx}")

        # COMPARACIÓN ABSOLUTA (Sin espacios, sin mayúsculas)
        es_ok = seleccion.strip().lower() == item['correcta'].strip().lower()

        if st.session_state.modo == 'Entrenamiento':
            if st.button("Validar"):
                if es_ok: st.success("¡Correcto!")
                else: st.error(f"Fallo. La correcta es: {item['correcta']}")
                st.info(f"Justificación: {item['explicacion']}")

        if st.button("Siguiente ➡️"):
            if es_ok: st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.title("🏁 Resultados")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(qs)}")
        if st.button("Reiniciar"):
            st.session_state.clear()
            st.rerun()