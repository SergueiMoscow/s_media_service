"""
Получение отдельных png файлов с картинками папок из одного colored_folders.png
"""
import os
from pathlib import Path

from PIL import Image


def rotate_and_crop_image(input_filename, left, top, right, bottom, output_filename, angle=90):
    """
    Функция для поворота и обрезки изображения с сохранением всех частей изображения после поворота.

    :param input_filename: имя входного файла изображения.
    :param left: левая координата для начала обрезки.
    :param top: верхняя координата для начала обрезки.
    :param right: правая координата для конца обрезки.
    :param bottom: нижняя координата для конца обрезки.
    :param output_filename: имя файла для сохранения обрезанного и повернутого изображения.
    :param angle: угол поворота изображения в градусах.
    """
    with Image.open(input_filename) as img:
        # Обрезаем изображение по заданным координатам
        cropped_image = img.crop((left, top, right, bottom))
        rotated_image = cropped_image.rotate(angle, Image.Resampling.NEAREST, expand=True)

        # Создаем новый холст с нейтральным фоном (например, белым)
        canvas = Image.new('RGBA', (rotated_image.width, rotated_image.height), (0, 0, 0, 0))
        # Помещаем обрезанное изображение в центр холста

        canvas.paste(rotated_image, (0, 0))

        rotated_image.save(output_filename, 'PNG')


def main():
    root_dir = Path(__file__).parent.parent.parent
    images_dir = os.path.join(root_dir, 'images')

    input_file_name = os.path.join(images_dir, 'colored_folders.png')
    rotate_and_crop_image(
        input_file_name, 82, 19, 164, 139, os.path.join(images_dir, 'folder1.png')
    )
    rotate_and_crop_image(
        input_file_name, 230, 19, 312, 139, os.path.join(images_dir, 'folder2.png')
    )
    rotate_and_crop_image(
        input_file_name, 378, 19, 460, 139, os.path.join(images_dir, 'folder3.png')
    )

    rotate_and_crop_image(
        input_file_name, 82, 167, 164, 281, os.path.join(images_dir, 'folder4.png')
    )
    rotate_and_crop_image(
        input_file_name, 230, 167, 312, 281, os.path.join(images_dir, 'folder5.png')
    )
    rotate_and_crop_image(
        input_file_name, 378, 167, 460, 281, os.path.join(images_dir, 'folder6.png')
    )

    rotate_and_crop_image(
        input_file_name, 82, 315, 164, 434, os.path.join(images_dir, 'folder7.png')
    )
    rotate_and_crop_image(
        input_file_name, 230, 315, 312, 434, os.path.join(images_dir, 'folder8.png')
    )
    rotate_and_crop_image(
        input_file_name, 378, 315, 460, 434, os.path.join(images_dir, 'folder9.png')
    )

    rotate_and_crop_image(
        input_file_name, 82, 463, 164, 577, os.path.join(images_dir, 'folder10.png')
    )
    rotate_and_crop_image(
        input_file_name, 230, 463, 312, 577, os.path.join(images_dir, 'folder11.png')
    )
    rotate_and_crop_image(
        input_file_name, 378, 463, 460, 577, os.path.join(images_dir, 'folder12.png')
    )


if __name__ == '__main__':
    main()
