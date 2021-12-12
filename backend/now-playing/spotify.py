import asyncio
import datetime
import logging
import time
from asyncio import Task, Future
from typing import Optional

from fastapi import WebSocket
from httpx import AsyncClient

from .schema import Song


TOKEN_URL = "https://accounts.spotify.com/api/token"

POLL_TIME = datetime.timedelta(seconds=1)


logger = logging.getLogger(__name__)


class Spotify:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self._client = AsyncClient(http2=True)
        self._token = AccessToken(self._client, client_id, client_secret, refresh_token)
        self.currently_playing: Optional[dict] = None
        self._task: Task = Optional[None]
        self._websockets: set[WebSocket] = set()

    async def get_recently_played(self, limit: int = 5) -> dict:
        access_token = await self._token.get()

        response = await self._client.get(
            'https://api.spotify.com/v1/me/player/recently-played',
            headers={'Authorization': f'Bearer {access_token}'},
            params={'limit': limit},
        )
        response.raise_for_status()
        return response.json()

    async def get_currently_playing(self) -> Optional[dict]:
        access_token = await self._token.get()

        response = await self._client.get(
            'https://api.spotify.com/v1/me/player/currently-playing',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        response.raise_for_status()

        if response.status_code == 204:
            return None
        else:
            return response.json()

    def start(self):
        self._task = asyncio.create_task(self._loop())

        # TODO: Figure out how to kill main event loop when exception is raised
        def handle_exception(future: Future):
            if future.cancelled():
                return
            if exception := future.exception():
                raise exception

        self._task.add_done_callback(handle_exception)

    def stop(self):
        self._task.cancel()
        logger.info("get_currently_playing task canceled")

    def subscribe(self, websocket: WebSocket):
        self._websockets.add(websocket)

    async def _loop(self):
        logger.info("Starting get_currently_playing task..")
        while True:
            await asyncio.sleep(POLL_TIME.total_seconds())
            currently_playing = await self.get_currently_playing()
            logger.debug("Acquired song")

            if currently_playing:
                new_id = currently_playing["item"]["id"]
            else:
                new_id = None

            if self.currently_playing:
                current_id = self.currently_playing["item"]["id"]
            else:
                current_id = None

            if new_id == current_id:
                continue

            logger.debug("Song has changed")

            if currently_playing:
                song = Song(
                    name=currently_playing['item']['name'],
                    artist=currently_playing['item']['artists'][0]['name'],
                    album=currently_playing['item']['album']['name'],
                    href=currently_playing['context']['external_urls']['spotify'],
                    image_url=currently_playing['item']['album']['images'][0]['url']
                )
                song_json = dict(song)
            else:
                song_json = {}

            aws = [websocket.send_json(song_json) for websocket in self._websockets]
            await asyncio.gather(*aws)
            logger.debug("Published song to websockets")

            self.currently_playing = currently_playing


class AccessToken:
    def __init__(self, client: AsyncClient, client_id: str, client_secret: str, refresh_token: str):
        self._client = client
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token

        self._access_token: Optional[str] = None
        self._expires_at: Optional[int] = None

    async def get(self):
        if not self._access_token or time.time() >= self._expires_at:
            await self._get_access_token()
        return self._access_token

    async def _get_access_token(self):
        response = await self._client.post(
            TOKEN_URL,
            auth=(self._client_id, self._client_secret),
            data={"grant_type": "refresh_token", "refresh_token": self._refresh_token},
        )
        response.raise_for_status()
        response_json = response.json()

        self._access_token = response_json['access_token']
        self._expires_at = response_json['expires_in'] + time.time() - 30
        logger.debug("Acquired access token")
