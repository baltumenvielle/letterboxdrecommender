# imdb_model/utils.py
import pandas as pd
import numpy as np
from imdb import IMDb
from concurrent.futures import ThreadPoolExecutor, as_completed

ia = IMDb()
df_top_global = None

def cargar_letterboxd(file):
    df = pd.read_csv(file)
    df = df.rename(columns={
        'Name': 'title',
        'Year': 'year',
        'Rating': 'rating'
    })
    return df

def cargar_top_imdb():
    df = pd.read_csv('imdb_top1000.csv')
    return serializar(df)

def serializar(df):
    df = df[['title', 'year', 'imdb_rating', 'genres', 'directors', 'actors', 'runtime']]
    df.loc[:, 'genres'] = df['genres'].apply(lambda x: [item.strip() for item in x.split(',')])
    df.loc[:, 'directors'] = df['directors'].apply(lambda x: [item.strip() for item in x.split(',')])
    df.loc[:, 'actors'] = df['actors'].apply(lambda x: [item.strip() for item in str(x).split(',')] if pd.notnull(x) else [])
    df.loc[:, 'runtime'] = df['runtime'].apply(convert_runtime)

    return df

def convert_runtime(runtime):
    try:
        parts = runtime.split("h ")
        hours = int(parts[0]) * 60 if parts[0].isdigit() else 0
        minutes = int(parts[1].replace("m", "")) if len(parts) > 1 and parts[1].replace("m", "").isdigit() else 0
        return int(hours + minutes)
    except:
        return None

def obtener_info_local(title, year, df_top):
    filtered_df = df_top[df_top['title'] == title]
    if not filtered_df.empty:
        movie = filtered_df.iloc[0]
        return {
            'title': movie['title'],
            'year': movie.get('year', year),
            'imdb_rating': movie.get('imdb_rating', np.nan),
            'genres': movie.get('genres', []),
            'directors': movie.get('directors', []),
            'actors': movie.get('actors', [])[:10],
            'runtime': movie.get('runtime', 0)
        }
    return None

def obtener_info_imdb(title, year):
    try:
        resultados = ia.search_movie(f"{title} {year}")
        if not resultados:
            return None

        pelicula = ia.get_movie(resultados[0].movieID)
        return {
            'title': pelicula.get('title', title),
            'year': pelicula.get('year', year),
            'imdb_rating': pelicula.get('rating', np.nan),
            'genres': pelicula.get('genres', []),
            'directors': [d['name'] for d in pelicula.get('directors', [])],
            'actors': [a['name'] for a in pelicula.get('actors', [])][:10],
            'runtime': pelicula.get('runtime', [0])[0] if pelicula.get('runtime') else 0
        }
    except:
        return None

def enriquecer_fila(fila):
    title = str(fila['title'])
    year = fila['year']
    info = obtener_info_local(title, year, df_top_global)
    if not info:
        info = obtener_info_imdb(title, year)
    if info:
        info['user_rating'] = fila['rating']
    return info

def enriquecer_datos(df, df_top, max_workers=20):
    global df_top_global
    df_top_global = df_top
    datos_enriquecidos = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(enriquecer_fila, fila): fila for _, fila in df.iterrows()}
        for futuro in as_completed(futuros):
            resultado = futuro.result()
            if resultado:
                datos_enriquecidos.append(resultado)

    df_top_global = None
    return pd.DataFrame(datos_enriquecidos)
