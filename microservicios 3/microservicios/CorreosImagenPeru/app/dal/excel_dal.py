import os
import pandas as pd

class ExcelDAL:
    async def guardar_excel(self, upload_file, upload_folder: str) -> str:
        path = os.path.join(upload_folder, upload_file.filename)

        content = await upload_file.read()
        with open(path, "wb") as f:
            f.write(content)

        return path

    def obtener_clientes(self, excel_path: str):
        if not os.path.exists(excel_path):
            return []
        df = pd.read_excel(excel_path)
        return df.to_dict("records")
