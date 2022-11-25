from functools import lru_cache
from io import BytesIO
from typing import List, Tuple

import httpx
from PIL import Image


CACHE_SIZE = 64
QUANTIZATION_FACTOR = 4


@lru_cache(CACHE_SIZE)
async def get_colors_from_url(client: httpx.AsyncClient, url: str, n: int = 4) -> List[Tuple]:
    img = await load_image(client, url)
    colors = get_colors(img, n)
    return colors


async def load_image(client: httpx.AsyncClient, url: str) -> Image:
    response = await client.get(url)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content))

    return img


def get_colors(img: Image, n: int = 4) -> List[Tuple]:
    q_img = img.quantize(QUANTIZATION_FACTOR, kmeans=QUANTIZATION_FACTOR)

    pallete = q_img.getpalette()
    colors = [tuple(pallete[i:i+3]) for i in range(0, 64*3, 3)]

    dom_colors_p = sorted(q_img.getcolors(), key=lambda x: x[0], reverse=True)[:n]
    dom_colors = list(map(lambda x: colors[x[1]], dom_colors_p))

    luxs = [get_luminance(color) for color in dom_colors]

    base_lux = luxs[0]
    ratios = [get_contrast_ratio(base_lux, lux) for lux in luxs[1:]]
    max_ratio = max(ratios)
    max_i = ratios.index(max_ratio) + 1
    primary_color = dom_colors[0]
    secondary_color = dom_colors[max_i]

    return [primary_color, secondary_color]


def get_luminance(color: Tuple[int, int, int]) -> float:
    n_color = [None, None, None]
    for i, channel in enumerate(color):
        c = channel / 255
        if c <= 0.03928:
            n_color[i] = c / 12.92
        else:
            n_color[i] = ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * n_color[0] + 0.7152 * n_color[1] + 0.0722 * n_color[2]


def get_contrast_ratio(base_l: int, ref_l: int) -> float:
    if base_l > ref_l:
        l1 = base_l
        l2 = ref_l
    else:
        l1 = ref_l
        l2 = base_l

    return (l1 + 0.05) / (l2 + 0.05)
