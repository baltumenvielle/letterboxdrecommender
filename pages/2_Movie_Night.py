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
        user1 = user1.drop(['Letterbod URI', 'Date'])
        user2 = user2.drop(['Letterbod URI', 'Date'])
        merged = pd.merge(user1, user2, on=['title', 'year'], suffixes=('_u1', '_u2'))
        merged['rating'] = (merged['user_rating_u1'] + merged['user_rating_u2']) / 2

        imdb_data = utils.cargar_top_imdb()
        user1_enriched = utils.enriquecer_datos(user1, imdb_data)
        user2_enriched = utils.enriquecer_datos(user2, imdb_data)
        # Unir gustos y promediar ratings
        
        # Mantener solo las columnas necesarias para entrenar
        columnas_entrenamiento = ['title', 'year', 'genres_u1', 'directors_u1', 'actors_u1', 'joint_rating']
        merged = merged[columnas_entrenamiento].rename(columns={
            'genres_u1': 'genres',
            'directors_u1': 'directors',
            'actors_u1': 'actors',
            'joint_rating': 'rating'
        })

        st.write(merged.columns)

        # Entrenar modelo conjunto
        with st.spinner("🎷 Buscando armonía cinéfila..."):
            model_joint, mlb_g, mlb_d, mlb_a = model.preparar_y_entrenar_modelo(merged)
            recomendaciones = model.predecir_recomendaciones(model_joint, imdb_data, merged['title'], mlb_g, mlb_d, mlb_a)

        st.markdown("### ✨ Películas que ambos podrían disfrutar:")
        st.dataframe(recomendaciones[['title']], use_container_width=True)

        st.download_button(
            label="⬇️ Descargar lista recomendada (CSV)",
            data=recomendaciones[['title']].to_csv(index=False).encode('utf-8'),
            file_name='peliculas_recomendadas.csv',
            mime='text/csv'
        )