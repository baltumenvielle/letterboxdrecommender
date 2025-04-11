import pandas as pd
from recomendador_v1 import recomendar

# Cargar el CSV de Letterboxd
ratings_usuario = pd.read_csv('letterboxd_ratings.csv')

ratings_usuario.rename(columns={
    'Name': 'title',
    'Year': 'year',
    'Rating': 'rating'
}, inplace=True)

# Obtener 100 recomendaciones
recomendaciones = recomendar(ratings_usuario)
print(recomendaciones)
