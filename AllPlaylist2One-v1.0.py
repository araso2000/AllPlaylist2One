import spotipy
import os
import smtplib
import pickle

from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

scope = 'playlist-modify-public'

#Variables del entorno que recogen las claves publico/privadas de la API de Spotify
os.environ["SPOTIPY_CLIENT_ID"] = "xxxxxxxxxx"
os.environ["SPOTIPY_CLIENT_SECRET"] = "xxxxxxxx"
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:8080"

#Interfaces de Spotipy
try:
    with open("./gestor1.pkl",'rb') as file:
        gestor1 = pickle.load(file)
except:
    gestor1 = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    with open('./gestor1.pkl', 'wb') as file:
        pickle.dump(gestor1, file)

try:
    with open("./gestor2.pkl", 'rb') as file:
        gestor2 = pickle.load(file)
except:
    gestor2 = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    with open('./gestor2.pkl','wb') as file:
        pickle.dump(gestor2,file)

#Playlist a unir
fav1URI = "spotify:playlist:4JuNe7niLd3TTfGyDS4qJA"
fav2URI = "spotify:playlist:2XQv6iZnJxhaUTAQq7V2ay"
fav3URI = "spotify:playlist:0LyFgMaQJynqmLqPG6iCKv"
fav4URI = "spotify:playlist:268m9hPmNcFflE7EesoWTH"
fav5URI = "spotify:playlist:6y9mSr78gkaqWHpxhyaVvT"
fav6URI = "spotify:playlist:3IbjEaz8lV0OBSCdhU1PtX"
fav7URI = "spotify:playlist:66iy1muuNIXNU0I7z0MID7"

playlists = [fav1URI, fav2URI, fav3URI, fav4URI, fav5URI, fav6URI, fav7URI]

#Playlist donde se unen
todoURI = "spotify:playlist:31m0z9XdTmamdjBunmhDif"

def calcularNumeroVueltasSuperior(numero):
    guardarTexto("Calculando numero de vueltas superior")
    if (int(numero / 100) < (numero / 100)):
        numVueltas = int(numero / 100) + 1
    elif (int(numero / 100) == (numero / 100)):
        numVueltas = int(numero / 100)

    return numVueltas

def calcularNumeroVueltasInferior(numero):
    guardarTexto("Calculando numero de vueltas inferior")
    if (int(numero / 100) < (numero / 100)):
        numVueltas = int(numero / 100)
    elif (int(numero / 100) == (numero / 100)):
        numVueltas = int(numero / 100)

    return numVueltas

def extraerCanciones(playlist):
    guardarTexto(f"Comenzando a extraer canciones de la playlist: {playlist}")

    listaCanciones = []
    offset = 0

    tamPlaylist = gestor1.playlist_items(playlist)['total']
    numVueltas = calcularNumeroVueltasSuperior(tamPlaylist)

    for x in range(0,numVueltas):
        response = gestor1.playlist_items(playlist, offset=offset)
        limiteSuperior = 100

        if (x == numVueltas - 1):
            limiteSuperior = response['total'] - response['offset']

        for y in range(0, limiteSuperior):
            listaCanciones.append(response['items'][y]['track']['id'])

        guardarTexto(f"Extraido {x+1} de {numVueltas} vueltas")
        offset += 100


    guardarTexto(f"Extraccion de las canciones de la playlist {playlist} realizada correctamente")
    return listaCanciones

def extraerVariasPlaylist(listaPlaylists):
    lista = []
    contador = 1
    guardarTexto(f"Extraccion masiva de canciones. Volumen de trabajo: {len(listaPlaylists)} playlists en total")
    for x in listaPlaylists:
        guardarTexto(f"\nExtrayendo playlist {contador} de {len(listaPlaylists)}")
        for y in extraerCanciones(x):
            lista.append(y)
        guardarTexto(f"Extraida correctamente")
        contador += 1

    guardarTexto(f"\nExtraidas todas las canciones de la playlist\n")
    return lista

def borrarCanciones(canciones,playlistTodo):
    guardarTexto(f"\nBorrando {len(canciones)} canciones de TODO...")
    if len(canciones) <= 100:
        gestor2.playlist_remove_all_occurrences_of_items(playlistTodo, canciones)
    else:
        vueltas = calcularNumeroVueltasInferior(len(canciones))
        offset = 0

        for x in range(0, vueltas):
            gestor2.playlist_remove_all_occurrences_of_items(playlistTodo, canciones[offset:offset + 100])
            offset += 100
        gestor2.playlist_remove_all_occurrences_of_items(playlistTodo, canciones[offset:len(canciones):1])

    guardarTexto(f"Borrado\n")

def sincronizar(listaPlaylists,playlistTodo):
    guardarTexto(f"Sincronizando las playlist...")
    listaVariada = extraerVariasPlaylist(listaPlaylists)

    guardarTexto(f"Extraer canciones de TODO")
    listaTodo = extraerCanciones(playlistTodo)

    listaBorrar = []
    guardarTexto(f"\nBuscando canciones que sobran de la playlist TODO")
    try:
        for x in listaTodo:
            if x not in listaVariada:
                listaBorrar.append(x)
    except:
        guardarTexto(f"No hay canciones en la playlist TODO\n")

    if len(listaBorrar) == 0:
        guardarTexto(f"No hay canciones para borrar\n")
    else:
        borrarCanciones(listaBorrar,playlistTodo)

    listaTodo = extraerCanciones(playlistTodo)

    listaAdd = []
    guardarTexto(f"\nBuscando canciones que faltan en la playlist TODO")
    try:
        for x in listaVariada:
            if x not in listaTodo:
                listaAdd.append(x)
    except:
        guardarTexto(f"No hay canciones para añadir")

    if len(listaAdd) == 0 :
        guardarTexto(f"No hay canciones nuevas para añadir\n")
    else:
        guardarTexto("\nAñadiendo nuevas canciones a TODO...")
        addCanciones(playlistTodo,listaAdd)

    guardarTexto(f"\nSincronizado!")

def addCanciones(playlistDestino,listaCanciones):
    vueltas = calcularNumeroVueltasInferior(len(listaCanciones))
    offset = 0
    contador = 1

    guardarTexto(f"Añadiendo {len(listaCanciones)} canciones a TODO")

    for x in range(0,vueltas):
        gestor2.playlist_add_items(playlistDestino,listaCanciones[offset:offset+100],position=offset)
        guardarTexto(f"Vuelta {contador} de {vueltas}")
        offset += 100
        contador += 1

    guardarTexto(f"Añadiendo ultima vuelta")
    gestor2.playlist_add_items(playlistDestino,listaCanciones[offset:len(listaCanciones):1],position=offset)

    guardarTexto(f"Todas las canciones a añadir han sido añadidas")

def guardarTexto(texto):
    f = open("./resSincroSpotify.txt", "a")
    f.write(texto + "\n")
    f.close()

def sendEmail():
    msg = MIMEMultipart()
    msg['Subject'] = "Resultado Sincronización Spotify " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")


    archivo = open("./resSincroSpotify.txt")
    msg.attach(MIMEText(archivo.read(), 'plain'))

    server = smtplib.SMTP('smtp.office365.com:587')
    server.starttls()
    server.login("email", "password")

    server.sendmail("originEmail", "destEmail", msg.as_string())

    server.quit()

def inicializarTexto():
    f = open("./resSincroSpotify.txt", "w")
    f.write("")
    f.close()

print("Sincronizando playlists de Spotify...")
inicializarTexto()
text = "Hora de inicio: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n"
guardarTexto(text)
sincronizar(playlists,todoURI)
print("Sincronizado!")
text = "Hora de fin: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n"
guardarTexto(text)
print("Enviando email...")
sendEmail()
print("Terminado!")
