from pydantic import BaseModel, HttpUrl


class Song(BaseModel):
    name: str
    album: str
    artist: str
    href: HttpUrl
