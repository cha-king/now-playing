import asyncio
import datetime
import logging
from asyncio import Task, Future
from typing import Optional

from fastapi import WebSocket
from httpx import AsyncClient, RequestError, HTTPStatusError

from .auth import AccessToken
from .exception import ApiError, RateLimitError
from ..schema import Song, NowPlaying, Color, Theme
from .operations import (
    get_currently_playing,
    get_recently_played,
)
from ..color import get_colors_from_url


POLL_TIME = datetime.timedelta(seconds=1)
HTTP_TIMEOUT = 10


logger = logging.getLogger(__name__)


class Client:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self._client = AsyncClient(timeout=HTTP_TIMEOUT)
        self._token = AccessToken(self._client, client_id, client_secret, refresh_token)
        self._task: Optional[Task] = None
        self._websockets: set[WebSocket] = set()
        self._current_song_id: Optional[str] = None
        self.now_playing: Optional[NowPlaying] = None

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
            except RateLimitError as e:
                logger.exception("Rate limited. Waiting..")
                await asyncio.sleep(e.retry_time)
                continue
            logger.debug("Acquired song")

            song_id = current_song["item"]["id"] if current_song else None
            if song_id == self._current_song_id:
                continue
            logger.debug("Song has changed")

            if current_song:
                song = Song.from_spotify_response(current_song)
                try:
                colors = await get_colors_from_url(self._client, song.album.artwork_href)
                except ApiError:
                    logger.exception("Unable to download image artwork")
                    continue
                primary_color, secondary_color = colors
                theme = Theme(
                    primary=Color(f'rgb{primary_color}'),
                    secondary=Color(f'rgb{secondary_color}'),
                )
                now_playing = NowPlaying(song=song, theme=theme)
            else:
                song = None
                theme = None
                now_playing = None

            await self._publish_to_websockets(now_playing)
            logger.debug("Published to websockets")

            self._current_song_id = song_id
            self.now_playing = now_playing

    async def _get_currently_playing_safe(self) -> Optional[dict]:
        try:
            currently_playing = await self.get_currently_playing()
        except RequestError:
            raise ApiError("Unable to get currently playing")
        except HTTPStatusError as e:
            if 500 <= e.response.status_code <= 599:
                raise ApiError("Unable to get currently playing")
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers['Retry-After'])
                raise RateLimitError(f"Rate limited. Retry in {retry_after} seconds", retry_after)
            else:
                raise

        # Weird Spotify response handling
        if currently_playing and not currently_playing["item"]:
            raise ApiError("'Item' field missing from Spotify response")

        return currently_playing

    async def _publish_to_websockets(self, now_playing: Optional[NowPlaying]):
        now_playing_json = now_playing.json() if now_playing else ""
        aws = [websocket.send_text(now_playing_json) for websocket in self._websockets]
        await asyncio.gather(*aws)
