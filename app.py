import streamlit as st
import pandas as pd
import random

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

def obtener_datos(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        return pd.read_csv(csv_url)
    except:
        return pd.DataFrame()

def procesar_temario(df):
    lista_final = []
    if df.empty: return []
    
    # Recorremos el Excel estrictamente de 5 en 5
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # Fila 0: Pregunta y Justificación
        pregunta_txt = str(bloque.iloc[0, 0]).strip()
        justificacion_txt = str(bloque.iloc[0, 1]).strip()
        
        # Extraemos las 4 opciones de las filas 1, 2, 3 y 4 del bloque
        opt_a = str(bloque.iloc[1, 0]).strip()
        opt_b = str(bloque.iloc[2, 0]).strip()
        opt_c = str(bloque.iloc[3, 0]).strip()
        opt_d = str(bloque.iloc[4, 0]).strip()
        
        opciones = [opt_a, opt_b, opt_c, opt_d]
        
        # BUSQUEDA MANUAL DE LA CORRECTA (Sin bucles que sobreescriban)
        # Solo miramos la columna 1 (Justificación) de las filas de respuesta
        texto_correcta = None
        if "correcta" in str(bloque.iloc[1, 1]).lower(): texto_correcta = opt_a
        elif "correcta" in str(bloque.iloc[2, 1]).lower(): texto_correcta = opt_b
        elif "correcta" in str(bloque.iloc[3, 1]).lower(): texto_correcta = opt_c
        elif "correcta" in str(bloque.iloc[4, 1]).lower(): texto_correcta = opt_d
        
        # Solo si encontramos una respuesta marcada como correcta, añadimos la pregunta
        if pregunta_txt and texto_correcta:
            lista_final.append({
                "pregunta": pregunta_txt,
                "opciones": opciones,
                "correcta": texto_correcta,
                "explicacion": justificacion_txt
            })
    return lista_final

# ================= INTERFAZ STREAMLIT =================
st.set_page_config(page_title="App Oposiciones", layout="centered")

if 'paso' not in st.session_state:
    st.session_state.update({'paso': 'inicio', 'idx': 0, 'puntos': 0, 'preguntas': []})

if st.session_state.paso == 'inicio':
    st.title("📚 Selector de Temas")
    df_idx = obtener_datos(URL_SHEET, "Indice")
    
    if not df_idx.empty:
        # Filtrado de temas con contenido
        opciones_menu = []
        for _, fila in df_idx.iterrows():
            t_id = str(fila['Tema']).strip()
            df_t = obtener_datos(URL_SHEET, t_id)
            if not df_t.empty and len(df_t) >= 5:
                opciones_menu.append(f"{t_id} - {fila['Nombre Largo']}")
        
        seleccion = st.selectbox("Elige tema:", opciones_menu)
        
        if st.button("Empezar"):
            tema_id = seleccion.split(" - ")[0].strip()
            raw_data = obtener_datos(URL_SHEET, tema_id)
            st.session_state.preguntas = procesar_temario(raw_data)
            random.shuffle(st.session_state.preguntas) # Aleatoriedad
            st.session_state.paso = 'test'
            st.rerun()

elif st.session_state.paso == 'test':
    preguntas = st.session_state.preguntas
    idx = st.session_state.idx
    
    if idx < len(preguntas):
        item = preguntas[idx]
        st.write(f"**Pregunta {idx + 1} de {len(preguntas)}**")
        st.subheader(item['pregunta'])
        
        # Importante: El KEY debe ser único para que no herede la respuesta anterior
        # El radio button NO tiene nada seleccionado por defecto (index=None)
        elegida = st.radio("Opciones:", item['opciones'], index=None, key=f"q_{idx}")
        
        col1, col2 = st.columns(2)
        
        # VALIDACIÓN: Comparación de texto exacta
        if col1.button("Validar ✅"):
            if elegida:
                if elegida.strip() == item['correcta'].strip():
                    st.success("¡Correcto!")
                else:
                    st.error(f"Incorrecto. La correcta era: {item['correcta']}")
                st.info(f"💡 {item['explicacion']}")
            else:
                st.warning("Elige una opción.")

        if col2.button("Siguiente ➡️"):
            if elegida and elegida.strip() == item['correcta'].strip():
                st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.balloons()
        st.title("🏁 Resultados")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(preguntas)}")
        if st.button("Volver al inicio"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()