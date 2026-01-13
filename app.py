import streamlit as st
import pandas as pd
import random

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

# ================= MOTOR DE CARGA (NUEVO) =================
def obtener_datos(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        df = pd.read_csv(csv_url)
        return df
    except:
        return pd.DataFrame()

def procesar_temario(df):
    lista_final = []
    if df.empty: return []
    
    # Recorremos saltando de 5 en 5 (bloques atómicos)
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        
        # Datos del enunciado
        pregunta_txt = str(bloque.iloc[0, 0]).strip()
        justificacion_txt = str(bloque.iloc[0, 1]).strip()
        
        opciones = []
        correcta_index = -1
        
        # Leemos las 4 opciones siguientes
        for n in range(1, 5):
            texto_opc = str(bloque.iloc[n, 0]).strip()
            es_correcta = "correcta" in str(bloque.iloc[n, 1]).lower()
            
            opciones.append(texto_opc)
            if es_correcta:
                correcta_index = n - 1 # Guardamos la posición original 0,1,2 o 3
        
        # Solo guardamos si hay una pregunta válida y una respuesta marcada como correcta
        if pregunta_txt and correcta_index != -1:
            lista_final.append({
                "pregunta": pregunta_txt,
                "opciones": opciones,
                "correcta_txt": opciones[correcta_index], # Guardamos el TEXTO exacto
                "explicacion": justificacion_txt
            })
    return lista_final

# ================= CONFIGURACIÓN DE PÁGINA =================
st.set_page_config(page_title="Oposiciones Pro", layout="centered")

# Inicialización de estados
if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 'tema_id': '', 'titulo_largo': '',
        'preguntas': [], 'idx': 0, 'puntos': 0, 'modo': ''
    })

# --- PANTALLA 1: SELECCIÓN ---
if st.session_state.paso == 'inicio':
    st.title("📚 Selector de Temas")
    
    df_idx = obtener_datos(URL_SHEET, "Indice")
    if not df_idx.empty:
        # Filtrar solo temas que existen y tienen contenido
        temas_disponibles = []
        for _, fila in df_idx.iterrows():
            t_id = str(fila['Tema']).strip()
            t_nom = str(fila['Nombre Largo']).strip()
            # Verificación rápida
            df_t = obtener_datos(URL_SHEET, t_id)
            if not df_t.empty and len(df_t) >= 5:
                temas_disponibles.append(f"{t_id} - {t_nom}")
        
        seleccion = st.selectbox("Elige tu tema:", temas_disponibles)
        
        if st.button("Empezar Estudio"):
            t_id_clean = seleccion.split(" - ")[0].strip()
            t_nom_clean = seleccion.split(" - ")[1].strip()
            
            # Cargar y Barajar
            raw_data = obtener_datos(URL_SHEET, t_id_clean)
            lista_preguntas = procesar_temario(raw_data)
            random.shuffle(lista_preguntas) # Mezcla total
            
            st.session_state.update({
                'tema_id': t_id_clean,
                'titulo_largo': t_nom_clean,
                'preguntas': lista_preguntas,
                'paso': 'modo',
                'idx': 0, 'puntos': 0
            })
            st.rerun()

# --- PANTALLA 2: MODO ---
elif st.session_state.paso == 'modo':
    st.subheader(f"Tema: {st.session_state.titulo_largo}")
    c1, c2 = st.columns(2)
    if c1.button("🛠️ Entrenamiento", use_container_width=True):
        st.session_state.modo = 'Entrenamiento'; st.session_state.paso = 'test'; st.rerun()
    if c2.button("⏱️ Examen", use_container_width=True):
        st.session_state.modo = 'Examen'; st.session_state.paso = 'test'; st.rerun()

# --- PANTALLA 3: TEST ---
elif st.session_state.paso == 'test':
    preguntas = st.session_state.preguntas
    actual = st.session_state.idx
    
    if actual < len(preguntas):
        item = preguntas[actual]
        
        st.write(f"**Pregunta {actual + 1} / {len(preguntas)}**")
        st.markdown(f"### {item['pregunta']}")
        
        # Usamos un formulario para evitar que Streamlit recargue antes de tiempo
        with st.form(key=f"form_{actual}"):
            # Mostramos las opciones
            opcion_elegida = st.radio("Selecciona una respuesta:", item['opciones'], index=None)
            
            col_btn1, col_btn2 = st.columns(2)
            validar = col_btn1.form_submit_button("✅ Validar")
            siguiente = col_btn2.form_submit_button("➡️ Siguiente / Saltar")
            
            if validar:
                if opcion_elegida is None:
                    st.warning("Selecciona algo primero.")
                else:
                    # COMPARACIÓN DIRECTA DE TEXTO
                    if opcion_elegida == item['correcta_txt']:
                        st.success("¡CORRECTO!")
                    else:
                        st.error(f"INCORRECTO. La buena era: {item['correcta_txt']}")
                    
                    if st.session_state.modo == 'Entrenamiento':
                        st.info(f"💡 {item['explicacion']}")
            
            if siguiente:
                if opcion_elegida == item['correcta_txt']:
                    st.session_state.puntos += 1
                st.session_state.idx += 1
                st.rerun()
    else:
        st.title("🏁 Resultados Finales")
        st.metric("Aciertos", f"{st.session_state.puntos} de {len(preguntas)}")
        if st.button("Volver al Inicio"):
            st.session_state.clear()
            st.rerun()