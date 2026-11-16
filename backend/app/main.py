from io import BytesIO
from uuid import UUID, uuid4

import boto3
from botocore.config import Config
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import Inmueble, InmuebleMedia
from .schemas import Estado, InmuebleCreate, InmuebleOut, MediaOut, Tipo

app = FastAPI(title='CRM RAH VZLA Local API', version='0.2.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()],
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['Content-Type'],
)


def s3_client(endpoint_url: str):
    return boto3.client(
        's3', endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name='us-east-1',
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    )


def media_response(media: InmuebleMedia) -> MediaOut:
    # Solo se firma una URL temporal: la firma pública utiliza localhost porque el navegador la abre.
    url = s3_client(settings.s3_public_endpoint).generate_presigned_url(
        'get_object', Params={'Bucket': settings.s3_bucket, 'Key': media.object_key}, ExpiresIn=900
    )
    return MediaOut(
        id=media.id, inmueble_id=media.inmueble_id, tipo=media.tipo,
        etiqueta_estancia=media.etiqueta_estancia, orden=media.orden,
        content_type=media.content_type, url_temporal=url,
    )


def get_inmueble_or_404(inmueble_id: UUID, db: Session) -> Inmueble:
    inmueble = db.get(Inmueble, inmueble_id)
    if inmueble is None:
        raise HTTPException(status_code=404, detail='Inmueble no encontrado')
    return inmueble


@app.get('/health')
def health(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'status': 'ok'}


@app.get('/api/v1/inmuebles', response_model=list[InmuebleOut])
def listar_inmuebles(
    tipo: Tipo | None = None,
    estado: Estado | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Inmueble)
    if tipo:
        stmt = stmt.where(Inmueble.tipo == tipo)
    if estado:
        stmt = stmt.where(Inmueble.estado == estado)
    return db.scalars(stmt.order_by(Inmueble.creado_en.desc(), Inmueble.titulo.asc()).limit(100)).all()


@app.post('/api/v1/inmuebles', response_model=InmuebleOut, status_code=201)
def crear_inmueble(payload: InmuebleCreate, db: Session = Depends(get_db)):
    inmueble = Inmueble(**payload.model_dump())
    db.add(inmueble)
    db.commit()
    db.refresh(inmueble)
    return inmueble


@app.get('/api/v1/inmuebles/{inmueble_id}', response_model=InmuebleOut)
def leer_inmueble(inmueble_id: UUID, db: Session = Depends(get_db)):
    return get_inmueble_or_404(inmueble_id, db)


@app.get('/api/v1/inmuebles/{inmueble_id}/media', response_model=list[MediaOut])
def listar_media(inmueble_id: UUID, db: Session = Depends(get_db)):
    get_inmueble_or_404(inmueble_id, db)
    media_items = db.scalars(
        select(InmuebleMedia).where(InmuebleMedia.inmueble_id == inmueble_id)
        .order_by(InmuebleMedia.orden.asc(), InmuebleMedia.creado_en.asc())
    ).all()
    return [media_response(media) for media in media_items]


MAX_FILE_BYTES = 12 * 1024 * 1024
ALLOWED_FORMATS = {'JPEG': ('image/jpeg', '.jpg'), 'PNG': ('image/png', '.png'), 'WEBP': ('image/webp', '.webp')}


@app.post('/api/v1/inmuebles/{inmueble_id}/media', response_model=MediaOut, status_code=201)
async def subir_foto(
    inmueble_id: UUID,
    archivo: UploadFile = File(...),
    etiqueta_estancia: str | None = Form(default=None, max_length=60),
    db: Session = Depends(get_db),
):
    get_inmueble_or_404(inmueble_id, db)
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
    key = f'inmuebles/{inmueble_id}/originales/{uuid4().hex}{extension}'
    s3_client(settings.s3_endpoint).put_object(
        Bucket=settings.s3_bucket, Key=key, Body=contenido,
        ContentType=content_type, Metadata={'origen': 'original'},
    )
    media = InmuebleMedia(
        inmueble_id=inmueble_id, object_key=key, tipo='foto',
        etiqueta_estancia=etiqueta_estancia, content_type=content_type, orden=0,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media_response(media)
