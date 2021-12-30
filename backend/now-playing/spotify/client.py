import asyncio
import datetime
import logging
from asyncio import Task, Future
from typing import Optional

from fastapi import WebSocket
from httpx import AsyncClient, RequestError, HTTPStatusError

from .auth import AccessToken
from ..schema import Song
from .operations import (
    get_currently_playing,
    get_recently_played,
)


POLL_TIME = datetime.timedelta(seconds=1)
HTTP_TIMEOUT = 10


logger = logging.getLogger(__name__)


class Client:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self._client = AsyncClient(timeout=HTTP_TIMEOUT)
        self._token = AccessToken(self._client, client_id, client_secret, refresh_token)
        self.currently_playing: Optional[dict] = None
        self._task: Task = Optional[None]
        self._websockets: set[WebSocket] = set()

    async def get_recently_played(self, limit: int = 5) -> dict:
        access_token = await self._token.get()
        return await get_recently_played(self._client, access_token, limit)

    async def get_currently_playing(self) -> Optional[dict]:
        access_token = await self._token.get()
        return await get_currently_playing(self._client, access_token)

    def start(self):
        self._task = asyncio.create_task(self._loop())

        # TODO: Figure out how to kill main event loop when exception is raised
        def handle_exception(future: Future):
            if future.cancelled():
                return
            if exception := future.exception():
                raise exception

        self._task.add_done_callback(handle_exception)

    async def stop(self):
        self._task.cancel()
        logger.info("get_currently_playing task canceled")
        await self._client.aclose()

    def subscribe(self, websocket: WebSocket):
        self._websockets.add(websocket)

    def unsubscribe(self, websocket: WebSocket):
        self._websockets.remove(websocket)

    async def _loop(self):
        logger.info("Starting get_currently_playing task..")
        while True:
            await asyncio.sleep(POLL_TIME.total_seconds())
            try:
                currently_playing = await self.get_currently_playing()
            except RequestError:
                logger.exception("Unable to get currently playing")
                continue
            except HTTPStatusError as e:
                if 500 <= e.response.status_code <= 599:
                    logger.exception("Unable to get currently playing")
                    continue
                else:
                    raise

            logger.debug("Acquired song")

            # Weird Spotify response handling
            if currently_playing and not currently_playing["item"]:
                continue

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
                    song_href=currently_playing['context']['external_urls']['spotify'],
                    album_href=currently_playing['item']['album']['external_urls']['spotify'],
                    artist_href=currently_playing['item']['artists'][0]['external_urls']['spotify'],
                    image_href=currently_playing['item']['album']['images'][0]['url'],
                )
                song_json = dict(song)
            else:
                song_json = {}

            aws = [websocket.send_json(song_json) for websocket in self._websockets]
            await asyncio.gather(*aws)
            logger.debug("Published song to websockets")

            self.currently_playing = currently_playing
