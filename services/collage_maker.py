import io
import random

from PIL import Image, ImageOps


class CollageMaker:

    max_count_images = 10
    min_percent_out = 20
    border_width = 0
    border_color = (255, 255, 255)
    can_repeat = False
    _used_images = []  # Для избежания повторения
    _max_rotate_degree = 50

    def __init__(
        self,
        width: int,
        height: int,
        image_files: list,
        count_images: int | None = None,
        can_repeat: bool = False,
    ):
        self.width = width
        self.height = height
        self._used_images = []
        self.image_files = image_files
        if count_images:
            if can_repeat:
                # Если могут повторяться, то ограничиваем до self.max_count_images
                self.count_images = min(count_images, self.max_count_images)
            else:
                # Если НЕ могут повторяться - ограничиваем количество
                self.count_images = min(len(image_files), self.max_count_images)
        else:
            # Если количество не задано - берём фактическое, ограничиваем self.max_count_images.
            self.count_images = min(len(image_files), self.max_count_images)

    def set_additional_parameters(
        self,
        min_percent_out: int | None = None,
        border_width: int | None = None,
        border_color: tuple[int, int, int] | None = None,
    ):
        if min_percent_out is not None:
            self.min_percent_out = min_percent_out
        if border_width is not None:
            self.border_width = border_width
        if border_color is not None:
            self.border_color = border_color

    def get_image_position(
        self,
        image_width: int,
        image_height: int,
    ) -> (int, int):
        # Вычисление минимального и максимального значения для left
        left_min = 0 - (self.min_percent_out / 2) / 100 * image_width
        left_max = self.width - ((100 - self.min_percent_out) / 2) / 100 * image_width

        # Вычисление минимального и максимального значения для top
        top_min = 0 - (self.min_percent_out / 2) / 100 * image_height
        top_max = self.height - ((100 - self.min_percent_out) / 2) / 100 * image_height

        # Генерация случайных значений для left и top в заданных диапазонах
        left = random.uniform(left_min, left_max)
        top = random.uniform(top_min, top_max)

        # Возвращение результата
        return int(left), int(top)

    def get_image_size(
        self,
        image_width: int,
        image_height: int,
        min_percent: int,
    ) -> (int, int):
        """
        Возвращает новые размеры изображения,
        чтобы они были не более min_percent % от размера холста.
        """
        max_width = (self.width * min_percent) // 100
        max_height = (self.height * min_percent) // 100

        # Пропорционально уменьшаем изображение, если оно превышает максимально допустимые размеры
        if image_width > max_width or image_height > max_height:
            width_ratio = max_width / image_width
            height_ratio = max_height / image_height

            # Используем наименьшее из отношений, чтобы изображение умещалось по обеим осям
            scale_factor = min(width_ratio, height_ratio)

            # Получаем новые размеры, округляем их до целого числа
            new_width = int(image_width * scale_factor)
            new_height = int(image_height * scale_factor)
        else:
            # Размеры изображения уже удовлетворяют ограничениям, оставляем их без изменений
            new_width, new_height = image_width, image_height

        return round(new_width), round(new_height)

    def get_random_image(self):
        if len(self._used_images) == len(self.image_files):
            self._used_images = []
        available_images = [img for img in self.image_files if img not in self._used_images]
        if not available_images:
            raise ValueError('No available images to use.')
        random_image = random.choice(available_images)
        self._used_images.append(random_image)
        return random_image

    def generate_image(self) -> bytes:
        # Создаём пустую канву для результирующего изображения
        result_img = Image.new('RGB', (self.width, self.height), color=(255, 255, 255))

        for _ in range(self.count_images):
            # Открытие исходного изображения
            src_img_path = self.get_random_image()
            with Image.open(src_img_path) as src_img:
                # Меняем размеры (если нужно)
                src_img = src_img.resize(
                    (self.get_image_size(src_img.width, src_img.height, 50)),
                    resample=Image.Resampling.HAMMING,
                )
                # Добавляем рамку (если нужно)
                if self.border_width > 0:
                    src_img = ImageOps.expand(
                        src_img, border=self.border_width, fill=self.border_color
                    )

                # Поворот случайным образом
                angle = random.uniform(-self._max_rotate_degree, self._max_rotate_degree)
                rotated = src_img.convert('RGBA').rotate(angle, expand=True)

                # Создаем маску для повернутого изображения
                mask = rotated.convert('RGBA')
                # Случайное положение
                x_pos, y_pos = self.get_image_position(
                    image_width=rotated.width,
                    image_height=rotated.height,
                )
                result_img.paste(rotated, (x_pos, y_pos), mask)

        # Сохранение результата в байты
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        return img_byte_arr


# # Для использования в FastAPI
# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
#
# app = FastAPI()
#
#
# @app.get("/generate_image")
# def get_image(folders: int):
#     # Замените 'path_to_image.webp' на путь к вашему файлу .webp
#     img_bytes = generate_image('path_to_image.webp', folders, 800, 600, 10)
#     return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
#

# class FoldersImageGenerator(APIView):
#     def get(self):
#         return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
