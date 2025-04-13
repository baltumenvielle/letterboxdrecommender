import pandas as pd
import streamlit as st
import zipfile
import io
from imdb_model import utils, model
import warnings

warnings.filterwarnings('ignore')

@st.cache_data
def cargar_top_imdb():
    return utils.cargar_top_imdb()

@st.cache_resource
def entrenar_modelo(enriched_user_data):
    return model.preparar_y_entrenar_modelo(enriched_user_data)

st.set_page_config(page_title="Recomendame!", page_icon="🎬")
st.title("🎬 Letterboxd Recommender")
st.markdown("""
    Subí tu archivo ZIP exportado desde Letterboxd (debe contener un archivo llamado `ratings.csv`).
    Las recomendaciones se basan en tus películas vistas y datos enriquecidos desde IMDb.  
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📂 Subí el archivo ZIP", type=["zip"])

if uploaded_file:
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_files = zip_ref.namelist()
        ratings_file = [f for f in zip_files if 'ratings' in f.lower() and f.endswith('.csv')]

        if ratings_file:
            with zip_ref.open(ratings_file[0]) as ratings_csv:
                user_data = utils.cargar_letterboxd(ratings_csv)

            st.success(f"✅ Archivo `{ratings_file[0]}` cargado exitosamente.")

            # Botón para generar recomendaciones
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            procesar = st.button("🔍 Generar Recomendaciones", type="primary")
            st.markdown("</div>", unsafe_allow_html=True)

            if procesar:
                # Barra de progreso
                progreso = st.progress(0, text="Inicializando...")

                # Paso 1: Cargar IMDb
                progreso.progress(20, text="🔄 Cargando base de datos IMDb...")
                imdb_data = cargar_top_imdb()

                # Paso 2: Enriquecer datos
                progreso.progress(50, text="🔧 Enriqueciendo tus datos...")
                enriched_user_data = utils.enriquecer_datos(user_data, imdb_data)

                # Paso 3: Entrenar modelo
                progreso.progress(75, text="⚙️ Entrenando modelo personalizado...")
                model_trained, mlb_g, mlb_d, mlb_a = entrenar_modelo(enriched_user_data)

                # Paso 4: Generar recomendaciones
                progreso.progress(90, text="🎯 Generando recomendaciones...")
                recomendaciones = model.predecir_recomendaciones(
                    model_trained,
                    imdb_data,
                    enriched_user_data['title'],
                    mlb_g, mlb_d, mlb_a
                )

                progreso.progress(100, text="✅ ¡Listo!")

                # Mostrar top 100
                st.markdown("## 🎬 Top 100 Recomendaciones Personalizadas")
                recomendaciones_top100 = (
                    recomendaciones.sort_values(by='predicted_rating', ascending=False).head(100)
                )
                st.dataframe(recomendaciones_top100, use_container_width=True, hide_index=True)

                # Botones de descarga
                st.markdown("### 💾 Descargar recomendaciones")

                # Excel
                output_excel = io.BytesIO()
                recomendaciones_top100.to_excel(output_excel, index=False, engine='openpyxl')
                output_excel.seek(0)
                st.download_button(
                    label="⬇️ Descargar como Excel",
                    data=output_excel,
                    file_name='recomendaciones.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

                # CSV
                csv_data = recomendaciones_top100.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Descargar como CSV",
                    data=csv_data,
                    file_name='recomendaciones.csv',
                    mime='text/csv'
                )
        else:
            st.error("❌ No se encontró un archivo llamado `ratings.csv` en el ZIP. Asegurate de exportarlo correctamente desde Letterboxd.")
