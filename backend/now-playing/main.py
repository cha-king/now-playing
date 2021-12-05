import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import schema
from .spotify import Spotify


LIST_LENGTH = 5


app = FastAPI()
api = FastAPI()
app.mount('/api', api)
app.mount("/", StaticFiles(directory="now-playing/static", html=True), name="static")


@app.on_event("startup")
async def on_startup():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    refresh_token = os.getenv("REFRESH_TOKEN")

    spotify = Spotify(client_id, client_secret, refresh_token)
    api.state.spotify = spotify


@api.get("/recently-played", response_model=list[schema.Song])
async def get_recently_played():
    recently_played = await api.state.spotify.get_recently_played()

    songs = [
        schema.Song(
            name=song["track"]["name"],
            artist=song["track"]["artists"][0]["name"],
            album=song["track"]["album"]["name"],
            href=song['context']['external_urls']['spotify']
        )
        for song in recently_played["items"]
    ]

    return songs


@api.get("/now-playing", response_model=schema.Song)
async def get_now_playing():
    currently_playing = await api.state.spotify.get_currently_playing()

    if currently_playing is None:
        return {}

    song = schema.Song(
        name=currently_playing['item']['name'],
        artist=currently_playing['item']['artists'][0]['name'],
        album=currently_playing['item']['album']['name'],
        href=currently_playing['context']['external_urls']['spotify']
    )

    return song
