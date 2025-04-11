import joblib
import pandas as pd
import numpy as np
from imdb import IMDb
from utils import serializar, enriquecer_datos

# Cargar datos de imdb
imdb_top = pd.read_csv("imdb_top1000.csv")

# Cargar modelo y binarizadores
model = joblib.load('modelo/modelo_recomendador.pkl')
mlb_genres = joblib.load('modelo/mlb_genres.pkl')
mlb_directors = joblib.load('modelo/mlb_directors.pkl')
mlb_actors = joblib.load('modelo/mlb_actors.pkl')

ia = IMDb()

def recomendar(letterboxd_ratings):
    """
    letterboxd_ratings: DataFrame con 'title', 'year', 'rating'
    Retorna un DataFrame con las recomendaciones
    """

    # Enriquecer datos
    imdb_enriched = serializar(imdb_top)

    print("\n Dependiendo de la red, esto puede tardar más o menos")
    print("\nEnriqueciendo los ratings de Letterboxd...")
    letterboxd_enriched = enriquecer_datos(letterboxd_ratings, imdb_enriched)

    # Mostrar resultados
    print(f"\nPelículas enriquecidas: {len(letterboxd_enriched)}/{len(letterboxd_ratings)}")

    # Filtrar las películas del top 1000 que ya estén en el historial de Letterboxd
    unwatched_movies = imdb_enriched[~imdb_enriched['title'].isin(letterboxd_enriched['title'])]

    letterboxd_enriched = letterboxd_enriched.copy()

    letterboxd_enriched['genres'] = letterboxd_enriched['genres'].apply(lambda x: x if isinstance(x, list) else eval(x))
    letterboxd_enriched['directors'] = letterboxd_enriched['directors'].apply(lambda x: x if isinstance(x, list) else eval(x))
    letterboxd_enriched['actors'] = letterboxd_enriched['actors'].apply(lambda x: x if isinstance(x, list) else eval(x))

    imdb_enriched['genres'] = imdb_enriched['genres'].apply(lambda x: x if isinstance(x, list) else eval(x))
    imdb_enriched['directors'] = imdb_enriched['directors'].apply(lambda x: x if isinstance(x, list) else eval(x))
    imdb_enriched['actors'] = imdb_enriched['actors'].apply(lambda x: x if isinstance(x, list) else eval(x))

    # Preparar las características (features) y la variable objetivo (target) para las películas no vistas
    X_train = np.hstack([
        mlb_genres.fit_transform(letterboxd_enriched['genres']),
        mlb_directors.fit_transform(letterboxd_enriched['directors']),
        mlb_actors.fit_transform(letterboxd_enriched['actors']),
        letterboxd_enriched[['year', 'imdb_rating', 'runtime']].values
    ])
    y_train = letterboxd_enriched['user_rating'].values

    # Entrenar el modelo
    model.fit(X_train, y_train)

    # Predecir en películas no vistas del Top 250 IMDb
    X_test = np.hstack([
        mlb_genres.transform(unwatched_movies['genres']),
        mlb_directors.transform(unwatched_movies['directors']),
        mlb_actors.transform(unwatched_movies['actors']),
        unwatched_movies[['year', 'imdb_rating', 'runtime']].values
    ])
    
    y_pred = model.predict(X_test)
    unwatched_movies['predicted_rating'] = y_pred
    recommendations = unwatched_movies.sort_values(by='predicted_rating', ascending=False).head(100)

    return recommendations

