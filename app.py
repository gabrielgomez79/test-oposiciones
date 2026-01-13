import streamlit as st
import pandas as pd
import random

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

# ================= FUNCIONES DE CARGA =================
def obtener_datos_completos(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        df = pd.read_csv(csv_url)
        df.columns = df.columns.astype(str).str.strip() 
        return df
    except:
        return pd.DataFrame()

def procesar_bloques(df):
    preguntas_finales = []
    if df.empty or 'Pregunta' not in df.columns: 
        return []
    
    # Recorremos el Excel en bloques de 5 filas
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # Fila 0 del bloque: Enunciado y Justificación explicativa
        enunciado = str(bloque.iloc[0]['Pregunta']).strip()
        justificacion_texto = str(bloque.iloc[0]['Justificación']).strip()
        
        opciones_bloque = []
        texto_correcta = ""
        
        # Filas 1 a 4 del bloque: Las 4 opciones
        for j in range(1, 5):
            opcion_actual = str(bloque.iloc[j]['Pregunta']).strip()
            marcador = str(bloque.iloc[j]['Justificación']).lower()
            
            opciones_bloque.append(opcion_actual)
            
            # Identificamos la correcta por el marcador en la segunda columna
            if "correcta" in marcador:
                texto_correcta = opcion_actual
        
        if enunciado and enunciado.lower() != "nan" and texto_correcta:
            preguntas_finales.append({
                "pregunta": enunciado,
                "opciones": opciones_bloque,
                "correcta": texto_correcta,
                "explicacion": justificacion_texto
            })
    return preguntas_finales

# ================= INTERFAZ =================
st.set_page_config(page_title="App Oposiciones", layout="centered")

if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 'tema_id': '', 'titulo_largo': '', 
        'idx': 0, 'puntos': 0, 'preguntas': [], 'modo': ''
    })

# --- PANTALLA 1: SELECCIÓN ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia")
    
    if st.button("🔄 Actualizar Temario"):
        st.cache_data.clear()
        st.rerun()

    df_idx = obtener_datos_completos(URL_SHEET, "Indice")
    
    if not df_idx.empty:
        opciones_validas = []
        for _, fila in df_idx.iterrows():
            id_tema = str(fila['Tema']).strip()
            df_temp = obtener_datos_completos(URL_SHEET, id_tema)
            if len(procesar_bloques(df_temp)) > 0:
                opciones_validas.append(f"{id_tema} - {fila['Nombre Largo']}")
        
        if opciones_validas:
            seleccion = st.selectbox("Selecciona un tema:", opciones_validas)
            if st.button("Continuar"):
                partes = seleccion.split(" - ", 1)
                st.session_state.tema_id = partes[0].strip()
                st.session_state.titulo_largo = partes[1].strip()
                
                df_qs = obtener_datos_completos(URL_SHEET, st.session_state.tema_id)
                lista_qs = procesar_bloques(df_qs)
                random.shuffle(lista_qs) # Aleatoriedad
                
                st.session_state.preguntas = lista_qs
                st.session_state.idx = 0
                st.session_state.puntos = 0
                st.session_state.paso = 'modo'
                st.rerun()

# --- PANTALLA 2: MODO ---
elif st.session_state.paso == 'modo':
    st.info(f"🎯 **{st.session_state.tema_id}: {st.session_state.titulo_largo}**")
    c1, c2 = st.columns(2)
    if c1.button("🛠️ Entrenamiento", use_container_width=True):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if c2.button("⏱️ Examen", use_container_width=True):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

# --- PANTALLA 3: TEST ---
elif st.session_state.paso == 'test':
    st.markdown(f"### {st.session_state.tema_id}: {st.session_state.titulo_largo}")
    st.caption(f"Pregunta {st.session_state.idx + 1} de {len(st.session_state.preguntas)}")
    st.divider()

    item = st.session_state.preguntas[st.session_state.idx]
    st.write(f"**{item['pregunta']}**")
    
    # IMPORTANTE: index=None para que no haya nada marcado
    seleccion = st.radio("Elige una opción:", item['opciones'], index=None, key=f"rad_{st.session_state.idx}")

    col_val, col_sig = st.columns(2)

    # Lógica de validación de texto
    es_correcta = False
    if seleccion:
        # Limpiamos ambos textos para comparar sin errores de espacios o mayúsculas
        es_correcta = seleccion.strip().lower() == item['correcta'].strip().lower()

    if st.session_state.modo == 'Entrenamiento':
        if col_val.button("Validar ✅", use_container_width=True):
            if seleccion is None:
                st.warning("⚠️ Selecciona una respuesta.")
            elif es_correcta:
                st.success("¡Correcto! ✨")
            else:
                st.error(f"Incorrecto. La correcta era: {item['correcta']}")
                st.info(f"💡 {item['explicacion']}")

    btn_txt = "Siguiente ➡️" if seleccion else "Saltar ⏭️"
    if col_sig.button(btn_txt, use_container_width=True):
        if es_correcta:
            st.session_state.puntos += 1
        st.session_state.idx += 1
        st.rerun()

# --- RESULTADOS ---
if st.session_state.paso == 'test' and st.session_state.idx >= len(st.session_state.preguntas):
    st.balloons()
    st.title("🏁 Fin del Test")
    st.metric("Puntuación", f"{st.session_state.puntos} / {len(st.session_state.preguntas)}")
    if st.button("Volver al Inicio"):
        st.session_state.clear()
        st.rerun()