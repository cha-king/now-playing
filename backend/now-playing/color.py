import httpx
from PIL import Image

from io import BytesIO
from typing import List, Tuple


QUANTIZATION_FACTOR = 64


def get_colors_from_url(client: httpx.Client, url: str, n: int = 4) -> List[Tuple]:
    img = load_image(client, url)
    colors = get_colors(img, n)
    return colors


def load_image(client: httpx.Client, url: str) -> Image:
    response = client.get(url)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content))

    return img


def get_colors(img: Image, n: int = 4) -> List[Tuple]:
    q_img = img.quantize(QUANTIZATION_FACTOR)

    pallete = q_img.getpalette()
    colors = [tuple(pallete[i:i+3]) for i in range(0, 64*3, 3)]

    dom_colors_p = sorted(q_img.getcolors(), key=lambda x: x[0], reverse=True)[:n]
    dom_colors = list(map(lambda x: colors[x[1]], dom_colors_p))
    return dom_colors
