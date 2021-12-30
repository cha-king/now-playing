import asyncio
import datetime
import logging
from asyncio import Task, Future
from typing import Optional, List

from fastapi import WebSocket
from httpx import AsyncClient, RequestError, HTTPStatusError

from .auth import AccessToken
from .exception import ApiError
from ..schema import Song, Color
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
        self._task: Task = Optional[None]
        self._websockets: set[WebSocket] = set()
        self._current_song: Optional[Song] = None
        self._current_song_id: Optional[str] = None
        self._current_theme: Optional[List[Color]] = None

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
                current_song = await self._get_currently_playing_safe()
            except ApiError:
                logger.exception("Unable to get currently playing")
                continue
            logger.debug("Acquired song")

            song_id = current_song["item"]["id"] if current_song else None
            if song_id == self._current_song_id:
                continue
            logger.debug("Song has changed")

            song = Song.from_spotify_response(current_song) if current_song else None

            await self._publish_song_to_websockets(song)
            logger.debug("Published song to websockets")

            self._current_song = song
            self._current_song_id = song_id

    async def _get_currently_playing_safe(self) -> Optional[dict]:
        try:
            currently_playing = await self.get_currently_playing()
        except RequestError:
            raise ApiError("Unable to get currently playing")
        except HTTPStatusError as e:
            if 500 <= e.response.status_code <= 599:
                raise ApiError("Unable to get currently playing")
            else:
                raise

        # Weird Spotify response handling
        if currently_playing and not currently_playing["item"]:
            raise ApiError("'Item' field missing from Spotify response")

        return currently_playing

    async def _publish_song_to_websockets(self, song: Optional[Song]):
        song_dict = song.dict() if song else {}
        aws = [websocket.send_json(song_dict) for websocket in self._websockets]
        await asyncio.gather(*aws)
