import streamlit as st
import pandas as pd

# CONFIGURACIÓN
URL_SHEET = "https://docs.google.com/spreadsheets/d/1WbF-G8EDJKFp0oNqdbCbAYbGsMXtPKe7HuylUcjY3sQ/edit?usp=drive_link"

def obtener_titulo_largo(url, tema_corto):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        # Forzamos la lectura de la hoja "Indice"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Indice"
        df_indice = pd.read_csv(csv_url)
        
        # Limpiamos espacios en blanco en los nombres de las columnas y datos
        df_indice.columns = [c.strip() for c in df_indice.columns]
        df_indice['Tema'] = df_indice['Tema'].astype(str).str.strip()
        
        # Buscamos el título
        resultado = df_indice[df_indice['Tema'] == tema_corto]
        
        if not resultado.empty:
            return resultado.iloc[0]['Nombre Largo']
        else:
            return f"⚠️ No se encontró el título para '{tema_corto}' en la hoja Indice"
    except Exception as e:
        return f"❌ Error al leer la hoja Indice: {e}"

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
        st.error(f"Error al conectar con la hoja de preguntas: {e}")
        return []

# --- INTERFAZ ---
st.set_page_config(page_title="App Test Oposiciones", layout="wide")

if 'paso' not in st.session_state:
    st.session_state.update({'paso': 'inicio', 'tema': '', 'modo': '', 'idx': 0, 'puntos': 0})

if st.session_state.paso == 'inicio':
    st.title("📚 Selector de Tema")
    # Asegúrate de que estos nombres coincidan con la columna 'Tema' de tu hoja 'Indice'
    tema_elegido = st.selectbox("Elige tema:", ["Tema 01", "Tema 02"])
    if st.button("Comenzar"):
        st.session_state.tema = tema_elegido
        st.session_state.paso = 'modo'
        st.rerun()

elif st.session_state.paso == 'modo':
    titulo = obtener_titulo_largo(URL_SHEET, st.session_state.tema)
    st.header(titulo) # Esto mostrará el título largo o el mensaje de error
    
    st.write("---")
    c1, c2 = st.columns(2)
    if c1.button("🛠️ Entrenamiento"):
        st.session_state.modo, st.session_state.paso = 'Entrenamiento', 'test'
        st.rerun()
    if c2.button("⏱️ Examen"):
        st.session_state.modo, st.session_state.paso = 'Examen', 'test'
        st.rerun()

elif st.session_state.paso == 'test':
    titulo = obtener_titulo_largo(URL_SHEET, st.session_state.tema)
    st.subheader(titulo)
    st.write(f"Modo: {st.session_state.modo}")
    st.divider()

    datos = obtener_datos(URL_SHEET, st.session_state.tema)
    if st.session_state.idx < len(datos):
        p = datos[st.session_state.idx]
        st.write(f"**Pregunta {st.session_state.idx + 1}:**")
        st.info(p['enunciado'])
        
        eleccion = st.radio("Respuesta:", p['opciones'], key=f"q_{st.session_state.idx}")
        
        if st.session_state.modo == 'Entrenamiento':
            if st.button("Comprobar"):
                if eleccion == p['correcta']: st.success("¡Correcto!")
                else: st.error(f"Fallo. Era: {p['correcta']}")
                st.write(f"**Justificación:** {p['explicacion']}")

        if st.button("Siguiente"):
            if eleccion == p['correcta']: st.session_state.puntos += 1
            st.session_state.idx += 1
            st.rerun()
    else:
        st.title("🏁 Resultados")
        st.metric("Puntuación", f"{st.session_state.puntos} / {len(datos)}")
        if st.button("Inicio"):
            st.session_state.clear()
            st.rerun()