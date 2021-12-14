from pydantic import BaseModel, HttpUrl


class Song(BaseModel):
    name: str
    album: str
    artist: str
    song_href: HttpUrl
    album_href: HttpUrl
    artist_href: HttpUrl
    image_href: HttpUrl
