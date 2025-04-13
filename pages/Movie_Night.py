import pandas as pd
import streamlit as st
import zipfile
import io
from imdb_model import utils, model


# Configuración de la página
st.set_page_config(page_title="Movie Night?", page_icon="🍿")

st.title("🍿 Movie night?")
st.markdown("""
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
        imdb_data = utils.cargar_top_imdb()
        user1_enriched = utils.enriquecer_datos(user1, imdb_data)
        user2_enriched = utils.enriquecer_datos(user2, imdb_data)

        # Entrenar modelos
        with st.spinner("🎷 Analizando gustos..."):
            model1, mlb_g1, mlb_d1, mlb_a1 = model.preparar_y_entrenar_modelo(user1_enriched)
            model2, mlb_g2, mlb_d2, mlb_a2 = model.preparar_y_entrenar_modelo(user2_enriched)

            rec1 = model.predecir_recomendaciones(model1, imdb_data, user1_enriched['title'], mlb_g1, mlb_d1, mlb_a1)
            rec2 = model.predecir_recomendaciones(model2, imdb_data, user2_enriched['title'], mlb_g2, mlb_d2, mlb_a2)

        # Eliminar columnas de puntuación
        rec1 = rec1.drop(columns=["predicted_rating"])
        rec2 = rec2.drop(columns=["predicted_rating"])

        en_comun = pd.merge(rec1, rec2, on="title", how="inner")

        st.markdown("### ✨ Películas que ambos podrían disfrutar:")
        st.dataframe(en_comun[['title']], use_container_width=True)

        # Descarga
        st.download_button(
            label="⬇️ Descargar lista en común (CSV)",
            data=en_comun[['title']].to_csv(index=False).encode('utf-8'),
            file_name='peliculas_en_comun.csv',
            mime='text/csv'
        )
