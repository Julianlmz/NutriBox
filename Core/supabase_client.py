import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

_supabase_client: Optional[Client] = None


def get_supabase_client():
    """
    Obtiene el cliente de Supabase (Singleton).
    """
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Credenciales de Supabase no encontradas en .env")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


async def upload_to_bucket(file: UploadFile):
    """
    Sube un archivo a Supabase Storage y devuelve la URL pública.
    """
    client = get_supabase_client()

    if not file or not file.filename:
        # El archivo es opcional, si no viene, devolvemos None
        return None

    try:
        # Leer el contenido del archivo
        file_content = await file.read()

        # Crear un nombre de archivo único
        file_extension = file.filename.split(".")[-1]
        file_name = f"public/alimentos/{uuid.uuid4()}.{file_extension}"

        # Subir el archivo
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": file.content_type}
        )

        # Obtener la URL pública
        public_url = client.storage.from_(
            SUPABASE_BUCKET
        ).get_public_url(file_name)

        return public_url

    except Exception as e:
        print(f"Error en Supabase: {e}")
        # Lanza una excepción 500 para informar al frontend
        raise HTTPException(status_code=500, detail=f"Error al subir la imagen: {e}")