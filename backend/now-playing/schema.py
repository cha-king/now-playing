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


class NowPlaying(BaseModel):
    song: Song
    theme: List[Color]
