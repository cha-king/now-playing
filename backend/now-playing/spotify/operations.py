from typing import Optional

from httpx import AsyncClient


URL_RECENTLY_PLAYED = 'https://api.spotify.com/v1/me/player/recently-played'
URL_CURRENTLY_PLAYING = 'https://api.spotify.com/v1/me/player/currently-playing'


async def get_recently_played(client: AsyncClient, access_token: str, limit: int = 5) -> dict:
    response = await client.get(
        URL_RECENTLY_PLAYED,
        headers={'Authorization': f'Bearer {access_token}'},
        params={'limit': limit},
    )
    response.raise_for_status()
    return response.json()


async def get_currently_playing(client: AsyncClient, access_token: str) -> Optional[dict]:
    response = await client.get(
        URL_CURRENTLY_PLAYING,
        headers={'Authorization': f'Bearer {access_token}'},
    )
    response.raise_for_status()

    if response.status_code == 204:
        return None
    else:
        return response.json()
