import streamlit as st
import pandas as pd

# SUSTITUYE ESTO POR TU LINK DE GOOGLE SHEETS
# El link debe ser "Cualquier persona con el enlace" -> "Lector"
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=drive_link"

# Función para obtener el nombre largo del tema desde la pestaña 'Indice'
def obtener_titulo_largo(url, tema_corto):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Indice"
        df_indice = pd.read_csv(csv_url)
        # Buscamos la fila donde la columna 'Tema' coincide con nuestro tema seleccionado
        titulo = df_indice[df_indice['Tema'] == tema_corto]['Nombre Largo'].values[0]
        return titulo
    except:
        return tema_corto # Si falla o no existe, devuelve el nombre corto

def obtener_datos(url, hoja):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={hoja.replace(' ', '%20')}"
        df_raw = pd.read_csv(csv_url)
        df_raw.columns = [c.strip() for c in df_raw.columns]
        
        preguntas = []
        for i in range(0, len(df_raw), 5):
            bloque = df_raw.iloc[i:i+5]
            if len(bloque) < 5: break
            item = {
                "enunciado": bloque.iloc[0]['Pregunta'],
                "explicacion": bloque.iloc[0]['Justificación'],
                "opciones": bloque.iloc[1:5]['Pregunta'].tolist(),
                "correcta": ""
            }
            estados = bloque.iloc[1:5]['Justificación'].tolist()
            for idx, estado in enumerate(estados):
                if str(estado).strip().lower() == "correcta":
                    item["correcta"] = item["opciones"][idx]
                    break
            preguntas.append(item)
        return preguntas
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return []

# --- INTERFAZ ---
st.set_page_config(page_title="Mi Academia Móvil", page_icon="📱")

if 'paso' not in st.session_state:
    st.session_state.update({'paso': 'inicio', 'tema': '', 'modo': '', 'idx': 0, 'puntos': 0, 'logs': []})

if st.session_state.paso == 'inicio':
    st.title("📚 Repaso de Oposiciones")
    # Asegúrate de que estos nombres de temas coincidan con los de la columna 'Tema' en tu hoja 'Indice'
    tema_elegido = st.selectbox("Selecciona el Tema:", ["Tema 01", "Tema 02"]) 
    if st.button("Continuar"):
        st.session_state.tema = tema_elegido
        st.session_state.paso = 'modo'
        st.rerun()

elif st.session_state.paso == 'modo':
    # Obtener el título largo para mostrarlo
    titulo_completo = obtener_titulo_largo(URL_SHEET, st.session_state.tema)
    st.info(f"📍 **{titulo_completo}**")
    
    st.write("¿Cómo quieres estudiar hoy?")
    c1, c2 = st.columns(2)
    if c1.button("🛠️ Entrenamiento"):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if c2.button("⏱️ Examen"):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

elif st.session_state.paso == 'test':
    # Título largo siempre visible arriba en el test
    titulo_completo = obtener_titulo_largo(URL_SHEET, st.session_state.tema)
    st.markdown(f"### {titulo_completo}")
    st.divider()

    datos = obtener_datos(URL_SHEET, st.session_state.tema)
    if st.session_state.idx < len(datos):
        p = datos[st.session_state.idx]
        st.caption(f"Pregunta {st.session_state.idx + 1} de {len(datos)} | Modo: {st.session_state.modo}")
        st.write(f"#### {p['enunciado']}")
        
        eleccion = st.radio("Opciones:", p['opciones'], key=f"r_{st.session_state.idx}")
        
        if st.session_state.modo == 'Entrenamiento':
            if st.button("Comprobar ✅"):
                if eleccion == p['correcta']:
                    st.success("¡Correcto!")
                else:
                    st.error(f"Incorrecto. Es: {p['correcta']}")
                st.info(f"💡 {p['explicacion']}")

        if st.button("Siguiente ➡️"):
            if eleccion == p['correcta']: st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.title("🏁 Fin del Test")
        st.metric("Aciertos", f"{st.session_state.puntos} / {len(datos)}")
        if st.button("Volver al Inicio"):
            st.session_state.clear()
            st.rerun()