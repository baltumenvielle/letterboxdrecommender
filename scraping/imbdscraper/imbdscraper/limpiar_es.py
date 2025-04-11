with open("urls_peliculas.txt", "r") as f:
    urls = f.readlines()

urls_limpias = [url.replace("/es/", "/") for url in urls]

with open("urls_peliculas.txt", "w") as f:
    f.writelines(urls_limpias)
