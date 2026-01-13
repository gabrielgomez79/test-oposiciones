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

# ================= INICIALIZACIÓN DE ESTADOS =================
if 'paso' not in st.session_state:
    st.session_state.update({
        'paso': 'inicio', 'idx': 0, 'aciertos': 0, 'fallos': 0, 'blancos': 0,
        'preguntas': [], 'modo': '', 'historial': []
    })

st.set_page_config(page_title="App Oposiciones", layout="wide")

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
        if st.button("Iniciar Entrenamiento", use_container_width=True):
            st.session_state.modo = 'Entrenamiento'
            st.session_state.paso = 'test'
            st.rerun()
            
    with tab2:
        cantidad = st.slider("Número de preguntas para el examen:", 1, total_disponible, total_disponible)
        if st.button(f"Iniciar Examen con {cantidad} preguntas", use_container_width=True):
            st.session_state.preguntas = st.session_state.preguntas[:cantidad]
            st.session_state.modo = 'Examen'
            st.session_state.paso = 'test'
            st.session_state.historial = [] 
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
        
        if st.session_state.modo == 'Entrenamiento':
            if col1.button("Validar ✅"):
                if seleccion:
                    if seleccion.strip() == item['correcta'].strip():
                        st.success("¡Respuesta Correcta!")
                    else:
                        st.error(f"Incorrecto. La correcta es: {item['correcta']}")
                    st.info(f"💡 {item['explicacion']}")
                else:
                    st.warning("Selecciona una opción.")

        if col2.button("Siguiente ➡️"):
            # Lógica de corrección
            resultado_marca = "❌"
            es_blanco = False
            
            if not seleccion:
                resultado_marca = "⚪" # Blanco
                st.session_state.blancos += 1
                es_blanco = True
            elif seleccion.strip() == item['correcta'].strip():
                resultado_marca = "✅" # Acierto
                st.session_state.aciertos += 1
            else:
                resultado_marca = "❌" # Fallo
                st.session_state.fallos += 1

            # Guardamos en el historial
            st.session_state.historial.append({
                'Pregunta': item['pregunta'],
                'Tu Respuesta': seleccion if seleccion else "No contestada",
                'Correcta': item['correcta'],
                'Resultado': resultado_marca,
                'Justificación': item['explicacion']
            })
            
            st.session_state.idx += 1
            st.rerun()
    else:
        # PANTALLA DE RESULTADOS
        st.balloons()
        st.title("🏁 Resultados Finales")
        
        # CÁLCULOS DE NOTA
        n_preguntas = len(qs)
        a = st.session_state.aciertos
        f = st.session_state.fallos
        b = st.session_state.blancos
        
        # Fórmula: (Aciertos - (Fallos * 0.3333333)) / Total
        puntos_totales = a - (f * 0.3333333)
        nota_final = (puntos_totales / n_preguntas) * 10
        nota_final = max(0, nota_final) # Evitar notas negativas

        # Mostrar métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Aciertos ✅", a)
        m2.metric("Fallos ❌", f)
        m3.metric("Blancos ⚪", b)
        m4.metric("NOTA FINAL", f"{nota_final:.2f} / 10")

        st.subheader("📊 Desglose Detallado")
        df_resumen = pd.DataFrame(st.session_state.historial)
        st.table(df_resumen)
        
        if st.button("Volver al Inicio"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()