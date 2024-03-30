from itertools import batched
from typing import Any
from urllib.parse import urljoin, urlencode


class Utils:
    @staticmethod
    def split_list_into_fixed_chunks(data_list: list, chunks: int) -> list[list[Any]]:
        return [list(chunk) for chunk in batched(data_list, chunks)]

    @staticmethod
    def url_generator(base_url: str, path: str) -> str:
        return urljoin(base_url, path)

    @staticmethod
    def get_max_divider_by_list_length(items: list) -> int | None:
        max_devider = None

        for i in range(2, len(items)):
            if len(items) % i == 0:
                max_devider = i

        return max_devider
