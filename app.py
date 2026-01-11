import streamlit as st
import pandas as pd

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

# ================= FUNCIONES DE CARGA =================
def obtener_datos_completos(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        df = pd.read_csv(csv_url)
        # Limpiamos nombres de columnas de espacios laterales
        df.columns = df.columns.astype(str).str.strip() 
        return df
    except:
        return pd.DataFrame()

def procesar_bloques(df):
    preguntas_finales = []
    if df.empty: 
        return []
    
    # Verificación de seguridad: ¿Existen las columnas necesarias?
    if 'Pregunta' not in df.columns or 'Justificación' not in df.columns:
        return []

    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # Leemos con get() o verificando nulos para evitar errores de celda vacía
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
        
        # Solo añadimos si hay contenido real
        if enunciado and enunciado.lower() != "nan" and respuesta_correcta:
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

# --- PANTALLA 1: SELECCIÓN DE TEMA ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia")
    
    if st.button("🔄 Actualizar Temario"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Verificando temas disponibles..."):
        df_idx = obtener_datos_completos(URL_SHEET, "Indice")
    
    if not df_idx.empty and 'Tema' in df_idx.columns:
        opciones_validas = []
        
        for _, fila in df_idx.iterrows():
            id_tema = str(fila['Tema']).strip()
            nombre_largo = str(fila.get('Nombre Largo', 'Sin título')).strip()
            
            # Verificación en tiempo real de la hoja
            df_temp = obtener_datos_completos(URL_SHEET, id_tema)
            preguntas_test = procesar_bloques(df_temp)
            
            # SOLO si tiene preguntas procesables se añade a la lista
            if len(preguntas_test) > 0:
                opciones_validas.append(f"{id_tema} - {nombre_largo}")
        
        if opciones_validas:
            seleccion_completa = st.selectbox("Selecciona un tema:", opciones_validas)
            
            if st.button("Continuar"):
                partes = seleccion_completa.split(" - ", 1)
                st.session_state.tema_id = partes[0].strip()
                st.session_state.titulo_largo = partes[1].strip()
                
                # Cargamos definitivamente
                df_qs = obtener_datos_completos(URL_SHEET, st.session_state.tema_id)
                st.session_state.preguntas = procesar_bloques(df_qs)
                st.session_state.paso = 'modo'
                st.rerun()
        else:
            st.warning("⚠️ No se encontraron temas con contenido válido. Revisa que las pestañas tengan las columnas 'Pregunta' y 'Justificación'.")
    else:
        st.error("❌ No se pudo leer la hoja 'Indice' o no tiene la columna 'Tema'.")

# --- PANTALLA 2: MODO ---
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
    st.caption(f"Pregunta {st.session_state.idx + 1} de {len(st.session_state.preguntas)}")
    st.divider()

    qs = st.session_state.preguntas
    if st.session_state.idx < len(qs):
        item = qs[st.session_state.idx]
        st.write(f"**{item['pregunta']}**")
        
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