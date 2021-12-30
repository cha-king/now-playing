import logging
import os

from fastapi import FastAPI, Response, WebSocket
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from . import sentry
from . import schema
from .spotify.client import Client as SpotifyClient


LIST_LENGTH = 5


LOG_LEVEL = os.environ.get("LOG_LEVEL", logging.INFO)
logging.basicConfig(level=LOG_LEVEL)

logger = logging.getLogger(__name__)

# Removes duplicate uvicorn logging
logging.getLogger("uvicorn").propagate = False


app = FastAPI()
api = FastAPI()
app.mount('/api', api)
app.mount("/", StaticFiles(directory="now-playing/static", html=True), name="static")


@app.on_event("startup")
async def on_startup():
    sentry.init()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    refresh_token = os.getenv("REFRESH_TOKEN")

    spotify = SpotifyClient(client_id, client_secret, refresh_token)
    spotify.start()
    api.state.spotify = spotify


@app.on_event("shutdown")
async def on_shutdown():
    await api.state.spotify.stop()


@api.get("/recently-played", response_model=list[schema.Song])
async def get_recently_played():
    recently_played = await api.state.spotify.get_recently_played()

    songs = [
        schema.Song(
            name=song["track"]["name"],
            artist=song["track"]["artists"][0]["name"],
            album=song["track"]["album"]["name"],
            song_href=song['item']['external_urls']['spotify'],
            album_href=song['track']['album']['external_urls']['spotify'],
            artist_href=song['track']['artists'][0]['external_urls']['spotify'],
            image_href=song['track']['album']['images'][0]['url']
        )
        for song in recently_played["items"]
    ]

    return songs


@api.get("/now-playing", response_model=schema.NowPlaying)
async def get_now_playing():
    currently_playing = api.state.spotify.now_playing

    if currently_playing is None:
        return Response(status_code=204)

    return currently_playing


@api.websocket("/ws/now-playing")
async def websocket_now_playing(websocket: WebSocket):
    await websocket.accept()
    api.state.spotify.subscribe(websocket)
    logger.debug("Subscribed websocket")
    try:
        await websocket.receive_text()
    except WebSocketDisconnect:
        api.state.spotify.unsubscribe(websocket)
        logger.debug("Unsubscribed websocket")
