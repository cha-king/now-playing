import time

import requests


REFRESH_TOKEN_URL = 'https://accounts.spotify.com/api/token'
CLIENT_ID = '848f238a0495449c9e848625965d28a7'
CLIENT_SECRET = '9f49919b40af446391f180043e0cd7fb'

REFRESH_TOKEN = 'AQCamaJkgDEgKZQX36XuEb-Km-k3z8szccYs_dGfddfh1TShmybICLOIHGJI53uoD8U3fGWQxiC8Wjj4IserWs5jcMFVj_vJdo0v2Hrs75uN0BGowZFWBGTOTiBIyc3rjqw'


def get_access_token(refresh_token: str) -> dict:
    response = requests.post(
        REFRESH_TOKEN_URL,
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
    )
    response.raise_for_status()
    return response.json()


class AuthToken:
    def __init__(self, refresh_token: str):
        self._refresh_token = refresh_token
        self._access_token = None
        self._expires_at = None
        self._session = requests.session()

    def get(self) -> str:
        if not (self._access_token and self._expires_at) or self._expires_at >= time.time():
            self._refresh_access_token()

        return self._access_token

    def _refresh_access_token(self):
        response = self._session.post(
            REFRESH_TOKEN_URL,
            auth=(CLIENT_ID, CLIENT_SECRET),
            data={
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token,
            }
        )
        response.raise_for_status()
        response_json = response.json()

        self._access_token = response_json['access_token']
        self._expires_at = time.time() + response_json['expires_in'] - 30


if __name__ == '__main__':
    token = AuthToken(REFRESH_TOKEN)
    print(token.get())
