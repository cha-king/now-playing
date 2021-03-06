import time
import logging
from typing import Optional

from httpx import AsyncClient


TOKEN_URL = "https://accounts.spotify.com/api/token"


logger = logging.getLogger(__name__)


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
