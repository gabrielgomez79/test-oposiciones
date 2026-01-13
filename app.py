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
    """
    Esta función crea el 'paquete' indivisible:
    Pregunta + 4 Opciones + Respuesta Correcta + Justificación
    """
    preguntas_finales = []
    if df.empty or 'Pregunta' not in df.columns: 
        return []
    
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # 1. Extraemos el enunciado y la justificación (Fila 1 del bloque)
        enunciado = str(bloque.iloc[0]['Pregunta']).strip()
        explicacion_txt = str(bloque.iloc[0]['Justificación']).strip()
        
        # 2. Extraemos las 4 opciones y localizamos la correcta (Filas 2-5)
        opciones_bloque = []
        respuesta_correcta = ""
        
        for j in range(1, 5):
            texto_opcion = str(bloque.iloc[j]['Pregunta']).strip()
            marcador_justif = str(bloque.iloc[j]['Justificación']).lower()
            opciones_bloque.append(texto_opcion)
            
            # Buscamos la marca de 'correcta' en la columna de Justificación
            if "correcta" in marcador_justif:
                respuesta_correcta = texto_opcion
        
        # 3. EMPAQUETAMOS: Si el bloque está completo, lo añadimos como unidad
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
                
                # CARGAMOS LOS PAQUETES
                df_qs = obtener_datos_completos(URL_SHEET, st.session_state.tema_id)
                lista_desordenada = procesar_bloques(df_qs)
                
                # MEZCLAMOS LOS PAQUETES (No se mezclan filas sueltas, sino preguntas completas)
                random.shuffle(lista_desordenada)
                
                st.session_state.preguntas = lista_desordenada
                st.session_state.paso = 'modo'
                st.rerun()

# --- PANTALLA 2: MODO ---
elif st.session_state.paso == 'modo':
    st.info(f"🎯 **{st.session_state.tema_id}: {st.session_state.titulo_largo}**")
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
        # Extraemos el 'paquete' de la posición actual
        item = qs[st.session_state.idx]
        st.write(f"**{item['pregunta']}**")
        
        # Las opciones se muestran en el orden que tengan dentro de su paquete
        seleccion = st.radio("Opciones:", item['opciones'], index=None, key=f"p_{st.session_state.idx}")

        col_val, col_sig = st.columns(2)

        if st.session_state.modo == 'Entrenamiento':
            if col_val.button("Validar ✅", use_container_width=True):
                if seleccion is None:
                    st.warning("⚠️ Selecciona una respuesta.")
                else:
                    es_ok = seleccion.strip().lower() == item['correcta'].strip().lower()
                    if es_ok: st.success("¡Correcto!")
                    else: st.error(f"Incorrecto. La correcta era: {item['correcta']}")
                    st.info(f"💡 {item['explicacion']}")

        # Botón Siguiente / Saltar
        btn_txt = "Siguiente ➡️" if seleccion is not None else "Saltar ⏭️"
        if col_sig.button(btn_txt, use_container_width=True):
            if seleccion is not None:
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