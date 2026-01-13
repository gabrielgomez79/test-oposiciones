import streamlit as st
import pandas as pd
import random

# ================= CONFIGURACIÓN =================
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=sharing"

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
    for i in range(0, len(df), 5):
        bloque = df.iloc[i:i+5]
        if len(bloque) < 5: break
        enunciado = str(bloque.iloc[0, 0]).strip()
        justificacion_txt = str(bloque.iloc[0, 1]).strip()
        opciones_del_bloque = []
        texto_de_la_correcta = None
        for j in range(1, 5):
            texto_opcion = str(bloque.iloc[j, 0]).strip()
            marca_fb = str(bloque.iloc[j, 1]).lower().strip()
            opciones_del_bloque.append(texto_opcion)
            if "correcta" in marca_fb:
                texto_de_la_correcta = texto_opcion
        if enunciado and enunciado.lower() != "nan" and texto_de_la_correcta:
            lista_final.append({
                "pregunta": enunciado,
                "opciones": opciones_del_bloque,
                "correcta": texto_de_la_correcta,
                "explicacion": justificacion_txt
            })
    return lista_final

# ================= INTERFAZ =================
st.set_page_config(page_title="App Oposiciones", layout="centered")

if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 'idx': 0, 'puntos': 0, 
        'preguntas': [], 'modo': '', 'total_examen': 0
    })

# --- PANTALLA 1: SELECCIÓN DE TEMA ---
if st.session_state.paso == 'inicio':
    st.title("📚 Mi Academia de Oposiciones")
    df_idx = obtener_datos(URL_SHEET, "Indice")
    
    if not df_idx.empty:
        temas = [f"{str(r['Tema']).strip()} - {str(r.get('Nombre Largo', 'Sin título')).strip()}" for _, r in df_idx.iterrows()]
        seleccion = st.selectbox("Selecciona un tema:", temas)
        
        if st.button("Comenzar"):
            t_id = seleccion.split(" - ")[0].strip()
            raw = obtener_datos(URL_SHEET, t_id)
            preguntas_cargadas = procesar_temario(raw)
            
            if preguntas_cargadas:
                random.shuffle(preguntas_cargadas)
                st.session_state.preguntas = preguntas_cargadas
                st.session_state.paso = 'modo'
                st.rerun()
            else:
                st.error("No hay preguntas válidas en este tema.")

# --- PANTALLA 2: SELECCIÓN DE MODO Y CANTIDAD ---
elif st.session_state.paso == 'modo':
    total_disponible = len(st.session_state.preguntas)
    st.info(f"Tema cargado con **{total_disponible}** preguntas.")
    
    tab1, tab2 = st.tabs(["🛠️ Modo Entrenamiento", "⏱️ Modo Examen"])
    
    with tab1:
        st.write("En este modo verás la solución al instante.")
        if st.button("Iniciar Entrenamiento", use_container_width=True):
            st.session_state.modo = 'Entrenamiento'
            st.session_state.paso = 'test'
            st.rerun()
            
    with tab2:
        st.write("Selecciona cuántas preguntas quieres:")
        # Slider para elegir cantidad
        cantidad = st.slider("Número de preguntas:", 1, total_disponible, total_disponible)
        
        col_ex1, col_ex2 = st.columns(2)
        if col_ex1.button(f"Hacer {cantidad} preguntas", use_container_width=True):
            st.session_state.preguntas = st.session_state.preguntas[:cantidad]
            st.session_state.modo = 'Examen'
            st.session_state.paso = 'test'
            st.rerun()
        
        if col_ex2.button("Todas las preguntas", use_container_width=True):
            st.session_state.modo = 'Examen'
            st.session_state.paso = 'test'
            st.rerun()

# --- PANTALLA 3: TEST ---
elif st.session_state.paso == 'test':
    qs = st.session_state.preguntas
    idx = st.session_state.idx
    
    if idx < len(qs):
        item = qs[idx]
        st.write(f"**Pregunta {idx + 1} de {len(qs)}**")
        st.subheader(item['pregunta'])
        
        seleccion = st.radio("Selecciona tu respuesta:", item['opciones'], index=None, key=f"r_{idx}")
        col1, col2 = st.columns(2)
        
        # Lógica Entrenamiento: Permite validar antes de pasar
        if st.session_state.modo == 'Entrenamiento':
            if col1.button("Validar ✅"):
                if seleccion:
                    if seleccion.strip() == item['correcta'].strip():
                        st.success("¡Respuesta Correcta!")
                    else:
                        st.error(f"Incorrecto. La correcta es: {item['correcta']}")
                    st.info(f"Justificación: {item['explicacion']}")
                else:
                    st.warning("Selecciona una opción.")

        # Botón para avanzar
        texto_btn = "Siguiente ➡️" if seleccion else "Saltar ⏭️"
        if col2.button(texto_btn):
            if seleccion and seleccion.strip() == item['correcta'].strip():
                st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.balloons()
        st.title("🏁 Resultados Finales")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(qs)}")
        if st.button("Volver al Inicio"):
            # Limpiamos todo para empezar de cero
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()