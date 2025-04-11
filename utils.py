import pandas as pd
import numpy as np
from imdb import IMDb
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import warnings

ia = IMDb()
warnings.filterwarnings('ignore')

def serializar(df):
  
  df = df.copy()
  df = df[['title', 'year', 'imdb_rating', 'genres', 'directors', 'actors', 'runtime']]
  
  df['genres'] = df['genres'].apply(lambda x: [item.strip() for item in x.split(',')])
  df['directors'] = df['directors'].apply(lambda x: [item.strip() for item in x.split(',')])
  df['actors'] = df['actors'].apply(lambda x: [item.strip() for item in x.split(',')])

  # Convertir tiempo de ejecución a minutos
  def convert_runtime(runtime):
    try:
        parts = runtime.split("h ")
        hours = int(parts[0]) * 60 if parts[0].isdigit() else 0
        minutes = int(parts[1].replace("m", "")) if len(parts) > 1 and parts[1].replace("m", "").isdigit() else 0
        return int(hours + minutes)
    except:
        return None

  df["runtime"] = df["runtime"].apply(convert_runtime)

  return df

df_top_global = None

def obtener_info_local(title, year, df_top):
    """Busca los datos en el CSV local"""
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
    """Busca los datos usando la API de IMDb"""
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
    except Exception:
        return None
    
def enriquecer_fila(fila):
    """Enriquece una fila con datos de IMDb, primero local, luego API"""
    title = str(fila['title'])
    year = fila['year']
    
    # Buscar primero en el CSV local
    info = obtener_info_local(title, year, df_top_global)
    
    # Si no está, buscar con la API
    if not info:
        info = obtener_info_imdb(title, year)
    
    if info:
        info['user_rating'] = fila['rating']
    return info

def enriquecer_datos(df, df_top, max_workers=10):
    """Añade datos de IMDB a un DataFrame usando concurrencia"""
    global df_top_global
    df_top_global = df_top  # guardar el dataframe para uso dentro de los threads

    datos_enriquecidos = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(enriquecer_fila, fila): fila for _, fila in df.iterrows()}
        for futuro in tqdm(as_completed(futuros), total=len(futuros)):
            resultado = futuro.result()
            if resultado:
                datos_enriquecidos.append(resultado)
                
    df_top_global = None  # limpiar después
    return pd.DataFrame(datos_enriquecidos)

