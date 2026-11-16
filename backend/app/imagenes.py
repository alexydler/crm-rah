from io import BytesIO

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

MAX_FILE_BYTES = 12 * 1024 * 1024
ALLOWED_FORMATS = {'JPEG': ('image/jpeg', '.jpg'), 'PNG': ('image/png', '.png'), 'WEBP': ('image/webp', '.webp')}


async def leer_imagen_validada(archivo: UploadFile) -> tuple[bytes, str, str]:
    """Devuelve (contenido, content_type, extensión). El tipo se deduce del contenido, no del cliente."""
    contenido = await archivo.read(MAX_FILE_BYTES + 1)
    if len(contenido) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail='Máximo 12 MiB por fotografía')
    try:
        with Image.open(BytesIO(contenido)) as im:
            image_format = im.format
            im.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=422, detail='Archivo de imagen no válido') from None
    if image_format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=422, detail='Solo JPEG, PNG o WEBP')
    content_type, extension = ALLOWED_FORMATS[image_format]
    return contenido, content_type, extension
