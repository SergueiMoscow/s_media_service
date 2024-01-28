import os
import random
import shutil
import tempfile
import uuid

MIN_FOLDERS = 1
MAX_FOLDERS = 5
MIN_DEPTH = 1
MAX_DEPTH = 5
MIN_FILES = 1
MAX_FILES = 5
MIN_SIZE = 1
MAX_SIZE = 1


class RandomTempFolder:
    def __init__(self):
        self.root_dir = tempfile.mkdtemp()
        self.files_count = 0
        self.folders_count = 0
        self.size = 0
        self.temp_directory_fixture()

    def temp_directory_fixture(self):
        root = self.root_dir
        return self.create_random_folder(parent=root, depth=random.randint(MIN_DEPTH, MAX_DEPTH))

    def create_random_folder(self, parent, depth):
        folders = random.randint(MIN_FOLDERS, MAX_FOLDERS)
        files = random.randint(MIN_FILES, MAX_FILES)
        for _ in range(files):
            self.create_random_file(parent)
        if depth > 0:
            for _ in range(folders):
                unique_id = uuid.uuid4()
                folder_name = os.path.join(parent, f'folder_{unique_id}')
                os.mkdir(folder_name)
                self.folders_count += 1
                self.create_random_folder(parent=folder_name, depth=depth - 1)

    def create_random_file(self, folder):
        file_name = os.path.join(folder, f'file_{random.randint(1, 1000)}.txt')
        file_size = random.randint(MIN_SIZE, MAX_SIZE)
        if not os.path.isfile(file_name):
            with open(file_name, 'wb') as file_out:
                file_out.write(os.urandom(file_size))
            if os.path.isfile(file_name):
                self.files_count += 1
                self.size += file_size

    def destroy(self):
        shutil.rmtree(self.root_dir)
