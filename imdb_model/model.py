# imdb_model/model.py
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MultiLabelBinarizer

def preparar_y_entrenar_modelo(df):
    mlb_genres = MultiLabelBinarizer()
    mlb_directors = MultiLabelBinarizer()
    mlb_actors = MultiLabelBinarizer()

    df['genres'] = df['genres'].apply(lambda x: x if isinstance(x, list) else eval(x))
    df['directors'] = df['directors'].apply(lambda x: x if isinstance(x, list) else eval(x))
    df['actors'] = df['actors'].apply(lambda x: x if isinstance(x, list) else eval(x))

    X = np.hstack([
        mlb_genres.fit_transform(df['genres']),
        mlb_directors.fit_transform(df['directors']),
        mlb_actors.fit_transform(df['actors']),
        df[['year', 'imdb_rating', 'runtime']].values
    ])
    y = df['user_rating'].values

    model = RandomForestRegressor(n_estimators=200, max_depth=20, min_samples_leaf=5, random_state=42)
    model.fit(X, y)

    return model, mlb_genres, mlb_directors, mlb_actors

def predecir_recomendaciones(model, imdb_data, watched_titles, mlb_genres, mlb_directors, mlb_actors):
    unseen = imdb_data[~imdb_data['title'].isin(watched_titles)]

    X_test = np.hstack([
        mlb_genres.transform(unseen['genres']),
        mlb_directors.transform(unseen['directors']),
        mlb_actors.transform(unseen['actors']),
        unseen[['year', 'imdb_rating', 'runtime']].values
    ])

    y_pred = model.predict(X_test)
    unseen['predicted_rating'] = y_pred

    return unseen.sort_values(by='predicted_rating', ascending=False).head(50)
