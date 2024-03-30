from typing import Any
from io import BytesIO
import asyncio

import aiohttp
from PIL import Image

from utils import Utils
from logger.logger import logger

import config


class YandexDiskParserService:
    base_url = config.YANDEX_BASE_API_URL
    resources_path = config.YANDEX_API_RESOURCES_PATH

    @classmethod
    def _get_file_download_url_list_by_yandex_disk_items(cls, items: list) -> list[str]:
        try:
            return [list(filter(lambda s: s['name'] == config.DOWNLOAD_IMAGE_SIZE, item['sizes']))[0]['url'] for item in items]
        except Exception as e:
            logger.critical(e, exc_info=True)

    @classmethod
    async def _get_public_resources_by_dir(cls, public_key: str, dir: str) -> dict[Any]:
        try:
            async with aiohttp.ClientSession() as session:
                request_url = Utils.url_generator(
                    base_url=cls.base_url, path=cls.resources_path)
                async with session.get(request_url, params={'public_key': public_key, 'path': f'/{dir}'}) as resp:
                    return {'data': await resp.json(), 'status': resp.status}
        except Exception as e:
            logger.critical(e, exc_info=True)

    @classmethod
    async def _get_image_by_download_url(cls, url: str) -> dict[Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url,) as resp:
                    return await resp.read()
        except Exception as e:
            logger.critical(e, exc_info=True)


class ImageGenerator:
    internal_field_size = config.IMAGE_INTERNAL_FIELD_SIZE
    external_field_size = config.IMAGE_EXTERNAL_FIELD_SIZE
    background_color = '#ffffff'

    @classmethod
    def _concat_images_h(cls, images_list: list[Image.Image]) -> Image.Image:
        width = sum(image.width for image in images_list) + \
            cls.internal_field_size * (len(images_list)-1)
        height = max(image.height for image in images_list)
        composite = Image.new('RGB', (width, height), cls.background_color)
        y = 0

        for image in images_list:
            composite.paste(image, (y, 0))
            y += cls.internal_field_size + image.width
        return composite

    @classmethod
    def _concat_images_v(cls, images_list: list[Image.Image]) -> Image.Image:
        width = max(image.width for image in images_list)
        height = sum(image.height for image in images_list) + \
            cls.internal_field_size * (len(images_list)-1)
        composite = Image.new('RGB', (width + cls.external_field_size,
                                      height + cls.external_field_size),
                              cls.background_color)
        y = cls.external_field_size // 2

        for image in images_list:
            composite.paste(image, (50, y))
            y += cls.internal_field_size + image.height
        return composite

    @classmethod
    def generate_result_image(cls, images_list: list[Image.Image], path='results') -> None:
        try:
            max_devider = Utils.get_max_divider_by_list_length(images_list)
            
            if max_devider == None and len(images_list) > 7:
                raise Exception(
                    'Изображение будет не эстетичным, добавьте пожалуйста еще изображений')

            chunked_list_images = Utils.split_list_into_fixed_chunks(
                images_list, max_devider)
            cls._concat_images_v([cls._concat_images_h(images)
                                 for images in chunked_list_images]).save('results/Result.tif')
        except Exception as e:
            logger.critical(e, exc_info=True)


class MainService:
    @classmethod
    async def run(cls, dirs_name_list: list[str]):
        try:
            image_download_urls = []
            all_images = []

            all_public_resources = await cls.get_public_resources_by_dirs_name_list(dirs_name_list)

            for index, dir_public_resources in enumerate(all_public_resources):
                if dir_public_resources['status'] != 200:
                    logger.info(f'Ошибка при получении данных по папке {dirs_name_list[index]}')
                    continue
                dir_items = dir_public_resources['data']['_embedded']['items']
                image_download_urls += YandexDiskParserService._get_file_download_url_list_by_yandex_disk_items(dir_items)

            all_images = await cls.get_images_by_download_url_list(image_download_urls)

            ImageGenerator.generate_result_image(all_images)
        except Exception as e:
            logger.critical(e, exc_info=True)

    @classmethod
    async def get_public_resources_by_dirs_name_list(cls, dirs_name_list: list[str]) -> dict[Any]:
        try:
            get_dirs_data_tasks = [YandexDiskParserService._get_public_resources_by_dir(
                config.YANDEX_DATA_FOLDER, dir_name) for dir_name in dirs_name_list]

            dirs_pubic_data = await asyncio.gather(*get_dirs_data_tasks)

            return dirs_pubic_data
        except Exception as e:
            logger.critical(e, exc_info=True)

    
    @classmethod
    async def get_images_by_download_url_list(cls, image_download_urls: list[str]) -> list[Image.Image]:
        try:
            get_images_data_tasks = [YandexDiskParserService._get_image_by_download_url(
                download_url) for download_url in image_download_urls]

            images_data = await asyncio.gather(*get_images_data_tasks)

            pil_images_list = [Image.open(BytesIO(image_data)) for image_data in images_data]

            return pil_images_list
        except Exception as e:
            logger.critical(e, exc_info=True)
