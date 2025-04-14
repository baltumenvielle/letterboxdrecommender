import pandas as pd
import streamlit as st
import zipfile
import io
from imdb_model import utils, model
import warnings

warnings.filterwarnings('ignore')

@st.cache_resource
def entrenar_modelo(enriched_user_data):
    return model.preparar_y_entrenar_modelo(enriched_user_data)

# Configuración de la página
st.set_page_config(page_title="Movie Night?", page_icon="🍿")

st.title("🍿 Movie night?")
st.markdown("""
    ¿Te recomendamos una película para esta noche?
    Subí dos archivos ZIP exportados desde Letterboxd (uno por persona).  
    La app buscará películas que ambos quieran ver, basadas en las predicciones personalizadas.
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("🎬 ZIP de la primera persona", type=["zip"], key="user1")
with col2:
    file2 = st.file_uploader("🎬 ZIP de la segunda persona", type=["zip"], key="user2")

def cargar_ratings_desde_zip(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zf:
        archivo_csv = [f for f in zf.namelist() if 'ratings' in f.lower() and f.endswith('.csv')]
        if archivo_csv:
            with zf.open(archivo_csv[0]) as f:
                data = utils.cargar_letterboxd(f)
            return data
        else:
            return None

if file1 and file2:
    user1 = cargar_ratings_desde_zip(file1)
    user2 = cargar_ratings_desde_zip(file2)

    if user1 is None or user2 is None:
        st.error("❌ Uno de los archivos ZIP no contiene un archivo válido llamado `ratings.csv`.")
    else:   
        # Crear columnas vacías a los costados y una al centro para el botón
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.empty()
        with col2:
            ejecutar = st.button("✨ ¡Recomendanos algo!", type="primary")
        with col3:
            st.empty()

        if ejecutar:
            progress = st.progress(0, text="⏳ Iniciando análisis...")

            # Paso 1: Limpieza
            user1 = user1.drop(['Date', 'Letterboxd URI'], axis=1)
            user2 = user2.drop(['Date', 'Letterboxd URI'], axis=1)
            progress.progress(10, text="🧹 Limpiando datos...")

            # Paso 2: Unir ratings
            merged = pd.merge(user1, user2, on=['title', 'year'], suffixes=('_u1', '_u2'))
            merged['rating'] = (merged['rating_u1'] + merged['rating_u2']) / 2
            progress.progress(30, text="🔗 Combinando gustos...")

            # Paso 3: Enriquecer con datos de IMDb
            imdb_data = utils.cargar_top_imdb()
            enriched_user_data = utils.enriquecer_datos(merged, imdb_data)
            progress.progress(50, text="🎞️ Enriqueciendo con IMDb...")

            # Paso 4: Entrenamiento del modelo
            with st.spinner("⚙️ Entrenando el modelo..."):
                model_trained, mlb_g, mlb_d, mlb_a = entrenar_modelo(enriched_user_data)
            progress.progress(75, text="📈 Modelo entrenado...")

            # Paso 5: Predicción
            with st.spinner("🎯 Generando recomendaciones..."):
                recomendaciones = model.predecir_recomendaciones(
                    model_trained,
                    imdb_data,
                    enriched_user_data['title'],
                    mlb_g, mlb_d, mlb_a
                )
            progress.progress(100, text="✅ ¡Listo!")

            # Mostrar resultados
            st.markdown("## 🎬 ¡A disfrutar!")

            recomendaciones_top20 = (
                recomendaciones
                .sort_values(by='predicted_rating', ascending=False)
                .head(20)
            )

            st.dataframe(recomendaciones_top20, use_container_width=True, hide_index=True)

            # Descarga de recomendaciones como Excel y CSV
            st.markdown("### 💾 Descargar recomendaciones")

            # Excel
            output_excel = io.BytesIO()
            recomendaciones_top20.to_excel(output_excel, index=False, engine='openpyxl')
            output_excel.seek(0)

            st.download_button(
                label="⬇️ Descargar como Excel",
                data=output_excel,
                file_name='recomendaciones.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            # CSV
            csv_data = recomendaciones_top20.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="⬇️ Descargar como CSV",
                data=csv_data,
                file_name='recomendaciones.csv',
                mime='text/csv'
            )
