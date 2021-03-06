from typing import List

from pydantic import BaseModel, HttpUrl
from pydantic.color import Color


class Artist(BaseModel):
    name: str
    href: HttpUrl


class Album(BaseModel):
    name: str
    href: HttpUrl
    artwork_href: HttpUrl


class Song(BaseModel):
    name: str
    href: HttpUrl
    album: Album
    artist: Artist

    @classmethod
    def from_spotify_response(cls, response):
        return cls(
            name=response['item']['name'],
            href=response['item']['external_urls']['spotify'],
            album=Album(
                name=response['item']['album']['name'],
                href=response['item']['album']['external_urls']['spotify'],
                artwork_href=response['item']['album']['images'][0]['url'],
            ),
            artist=Artist(
                name=response['item']['artists'][0]['name'],
                href=response['item']['artists'][0]['external_urls']['spotify'],
            ),
        )


class Theme(BaseModel):
    primary: Color
    secondary: Color


class NowPlaying(BaseModel):
    song: Song
    theme: Theme
