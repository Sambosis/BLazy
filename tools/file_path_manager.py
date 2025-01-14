from pathlib import Path
from load_constants import get_logs_dir

class FilePathManager:
    def __init__(self):
        self.image_dir = get_logs_dir() / 'computer_tool_images'
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, image_data, image_name):
        image_path = self.image_dir / image_name
        with open(image_path, 'wb') as f:
            f.write(image_data)
        return image_path

    def get_image_path(self, image_name):
        return self.image_dir / image_name
