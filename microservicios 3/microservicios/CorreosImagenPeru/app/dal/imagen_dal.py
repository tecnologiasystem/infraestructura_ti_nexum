import os
import json

class ImagenDAL:
    IMAGE_NAME = "clickable_mi_image.png"
    AREAS_NAME = "clickable_areas.json"

    async def guardar_imagen_y_areas(self, upload_file, areas: list, images_folder: str):
        image_path = os.path.join(images_folder, self.IMAGE_NAME)

        content = await upload_file.read()
        with open(image_path, "wb") as f:
            f.write(content)

        areas_path = os.path.join(images_folder, self.AREAS_NAME)
        with open(areas_path, "w", encoding="utf-8") as f:
            json.dump(areas, f, ensure_ascii=False)

    def leer_areas(self, images_folder: str):
        areas_path = os.path.join(images_folder, self.AREAS_NAME)
        if not os.path.exists(areas_path):
            return []
        with open(areas_path, "r", encoding="utf-8") as f:
            return json.load(f)
