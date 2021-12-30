from typing import List

from pydantic import BaseModel, HttpUrl


class Artist(BaseModel):
    name: str
    href: HttpUrl


class Color(BaseModel):
    red: int
    green: int
    blue: int


class Album(BaseModel):
    name: str
    href: HttpUrl
    artwork_href: HttpUrl


class Song(BaseModel):
    name: str
    album: Album
    artist: Artist

    @classmethod
    def from_spotify_response(cls, response):
        return cls(
            name=response['item']['name'],
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


class NowPlaying(BaseModel):
    song: Song
    theme: List[Color]
