import asyncio
import datetime
import time
from asyncio import Task
from typing import Optional

from httpx import AsyncClient


TOKEN_URL = "https://accounts.spotify.com/api/token"

POLL_TIME = datetime.timedelta(seconds=1)


class Spotify:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self._client = AsyncClient(http2=True)
        self._token = AccessToken(self._client, client_id, client_secret, refresh_token)
        self.currently_playing: Optional[dict] = None
        self._task: Task = Optional[None]

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

        def handle_exception(future: Future):
            if future.cancelled():
                return
            if exception := future.exception():
                raise exception

        self._task.add_done_callback(handle_exception)

    def stop(self):
        self._task.cancel()

    async def _loop(self):
        while True:
            self.currently_playing = await self.get_currently_playing()
            await asyncio.sleep(POLL_TIME.total_seconds())


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
