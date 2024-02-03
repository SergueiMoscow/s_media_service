import os
import unittest
from unittest.mock import patch

from common.settings import ROOT_DIR
from services.collage_maker import CollageMaker


class TestCollageMaker(unittest.TestCase):
    image1 = os.path.join(ROOT_DIR, 'images/folder1.png')
    image2 = os.path.join(ROOT_DIR, 'images/folder2.png')

    def setUp(self):
        self.image_file_paths = [self.image1, self.image2]
        self.width = 800
        self.height = 600
        self.collagemaker = CollageMaker(self.width, self.height, self.image_file_paths)

    def test_initialization(self):
        self.assertEqual(self.collagemaker.width, self.width)
        self.assertEqual(self.collagemaker.height, self.height)
        self.assertEqual(self.collagemaker.image_files, self.image_file_paths)
        self.assertEqual(self.collagemaker.count_images, len(self.image_file_paths))

    def test_set_additional_parameters(self):
        self.collagemaker.set_additional_parameters(
            min_percent_out=30, border_width=5, border_color=(0, 0, 0)
        )
        self.assertEqual(self.collagemaker.min_percent_out, 30)
        self.assertEqual(self.collagemaker.border_width, 5)
        self.assertEqual(self.collagemaker.border_color, (0, 0, 0))

    @patch('random.randrange')
    def test_get_image_position(self, mock_uniform):
        mock_uniform.return_value = 50
        expected_position = (50, 50)
        image_position = self.collagemaker.get_image_position(100, 100)
        self.assertEqual(expected_position, image_position)

    @patch('random.randrange')
    def test_get_image_size(self, mock_uniform):  # pylint: disable=unused-argument
        size = self.collagemaker.get_image_size(500, 400, 50)
        self.assertTrue(size[0] <= self.width * 0.5)
        self.assertTrue(size[1] <= self.height * 0.5)

    @patch('random.choice')
    @patch('random.uniform')
    def test_get_random_image(self, mock_uniform, mock_choice):  # pylint: disable=unused-argument
        mock_choice.return_value = self.image1
        self.image_file_paths = [self.image1, self.image2]
        collagemaker_no_repeat = CollageMaker(
            self.width, self.height, self.image_file_paths, can_repeat=False
        )
        self.assertEqual(collagemaker_no_repeat.get_random_image(), self.image1)

    def test_generate_image(self):
        # В этом тесте мы хотели бы проверить, что генерация изображения
        # завершается без исключений и возвращает байты
        generated_image = self.collagemaker.generate_image()
        self.assertIsInstance(generated_image, bytes)

    # В этом методе мы убедимся, что после вызова `generate_image`, количество
    # изображений соответствует ожидаемому
    def test_generate_image_count(self):
        self.collagemaker.generate_image()
        self.assertEqual(
            len(self.collagemaker._used_images),  # pylint: disable=protected-access
            self.collagemaker.count_images,
        )


if __name__ == '__main__':
    unittest.main()
