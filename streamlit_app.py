import pandas as pd
import streamlit as st
import zipfile
import io
from imbd_model import utils, model

@st.cache_data
def cargar_top_imdb():
    return utils.cargar_top_imdb()

@st.cache_resource
def entrenar_modelo(enriched_user_data):
    return model.preparar_y_entrenar_modelo(enriched_user_data)

# Configuración de la página
st.set_page_config(page_title="Letterboxd Recommender", layout="wide")
st.title("🎬 Letterboxd Recommender")
st.markdown("""
    Subí tu archivo ZIP exportado desde Letterboxd (debe contener un archivo llamado `ratings.csv`).
    Las recomendaciones se basan en tus películas vistas y datos enriquecidos desde IMDb.  
""", unsafe_allow_html=True)

# Subida de archivo ZIP
uploaded_file = st.file_uploader("📂 Subí el archivo ZIP", type=["zip"])

if uploaded_file:
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_files = zip_ref.namelist()
        ratings_file = [f for f in zip_files if 'ratings' in f.lower() and f.endswith('.csv')]

        if ratings_file:
            with zip_ref.open(ratings_file[0]) as ratings_csv:
                user_data = utils.cargar_letterboxd(ratings_csv)

            st.success(f"✅ Archivo `{ratings_file[0]}` cargado exitosamente.")

            # Mostrar un solo GIF mientras se cargan los datos
            gif_url = "https://media.giphy.com/media/3o7rc0qU6m5hneMsuc/giphy.gif"
            gif_placeholder = st.empty()
            gif_placeholder.image(gif_url, width=300)

            # Cargar y enriquecer datos
            imdb_data = cargar_top_imdb()
            enriched_user_data = utils.enriquecer_datos(user_data, imdb_data)

            # Entrenamiento del modelo
            with st.spinner("⚙️ Entrenando el modelo..."):
                model_trained, mlb_g, mlb_d, mlb_a = entrenar_modelo(enriched_user_data)

            st.success("📈 ¡Modelo entrenado con éxito!")

            # Generar recomendaciones
            with st.spinner("🎯 Generando recomendaciones..."):
                recomendaciones = model.predecir_recomendaciones(
                    model_trained,
                    imdb_data,
                    enriched_user_data['title'],
                    mlb_g, mlb_d, mlb_a
                )

            # Mostrar top 10
            st.markdown("## 🎬 Top 10 Recomendaciones Personalizadas")
            st.markdown("Basadas en tu historial de películas vistas:")

            columnas_a_mostrar = ['title', 'year', 'genres', 'directors', 'predicted_rating']
            recomendaciones_top10 = recomendaciones[columnas_a_mostrar].head(10)
            st.dataframe(recomendaciones_top10, use_container_width=True)

            # Recomendación destacada
            top_reco = recomendaciones_top10.iloc[0]
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("## 🌟 Recomendación destacada:")
            with col2:
                st.markdown(f"**{top_reco['title']}** ({top_reco['year']}) - 🎯 Predicción: `{top_reco['predicted_rating']:.2f}`")

            # Descarga de recomendaciones como Excel y CSV
            st.markdown("### 💾 Descargar recomendaciones")

            # Excel
            output_excel = io.BytesIO()
            recomendaciones_top10.to_excel(output_excel, index=False, engine='openpyxl')
            output_excel.seek(0)

            st.download_button(
                label="⬇️ Descargar como Excel",
                data=output_excel,
                file_name='recomendaciones.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            # CSV
            csv_data = recomendaciones_top10.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="⬇️ Descargar como CSV",
                data=csv_data,
                file_name='recomendaciones.csv',
                mime='text/csv'
            )

        else:
            st.error("❌ No se encontró un archivo llamado `ratings.csv` en el ZIP. Asegurate de exportarlo correctamente desde Letterboxd.")
