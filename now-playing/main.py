import os

from fastapi import FastAPI

from . import schema
from .spotify import Spotify


LIST_LENGTH = 5


app = FastAPI()


@app.on_event("startup")
async def on_startup():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    refresh_token = os.getenv("REFRESH_TOKEN")

    spotify = Spotify(client_id, client_secret, refresh_token)
    app.state.spotify = spotify


@app.get("/recently-played", response_model=list[schema.Song])
async def get_recently_played():
    recently_played = await app.state.spotify.get_recently_played()

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


@app.get("/now-playing", response_model=schema.Song)
async def get_now_playing():
    currently_playing = await app.state.spotify.get_currently_playing()

    if currently_playing is None:
        return {}

    song = schema.Song(
        name=currently_playing['item']['name'],
        artist=currently_playing['item']['artists'][0]['name'],
        album=currently_playing['item']['album']['name'],
        href=currently_playing['context']['external_urls']['spotify']
    )

    return song
