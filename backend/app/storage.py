"""Almacenamiento privado de medios (MinIO/S3).

Claves: ``org/{organizacion_id}/inmuebles/{inmueble_id}/originales/{uuid}.{ext}``.
El prefijo NO sustituye la autorización: las URLs temporales solo se emiten después de verificar
membresía + pertenencia del inmueble y del asset a la organización del request, y
``presign_get`` comprueba además que la clave esté bajo el prefijo de esa organización.
"""
from functools import lru_cache
from uuid import UUID, uuid4

import boto3
from botocore.config import Config

from .config import settings

PREFIJO_ORG = 'org'


def prefijo_organizacion(organizacion_id: UUID) -> str:
    return f'{PREFIJO_ORG}/{organizacion_id}/'


def clave_original(organizacion_id: UUID, inmueble_id: UUID, extension: str) -> str:
    return f'{prefijo_organizacion(organizacion_id)}inmuebles/{inmueble_id}/originales/{uuid4().hex}{extension}'


class ClaveFueraDeOrganizacion(Exception):
    pass


def _s3_client(endpoint_url: str):
    return boto3.client(
        's3', endpoint_url=endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name='us-east-1',
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    )


class Storage:
    def __init__(self, bucket: str, internal_endpoint: str, public_endpoint: str, expira: int):
        self.bucket = bucket
        self.expira = expira
        self._internal = _s3_client(internal_endpoint)
        # La firma usa el endpoint público porque es el navegador quien abre la URL.
        self._public = _s3_client(public_endpoint)

    def put(self, key: str, body: bytes, content_type: str) -> None:
        self._internal.put_object(
            Bucket=self.bucket, Key=key, Body=body, ContentType=content_type, Metadata={'origen': 'original'},
        )

    def delete(self, key: str) -> None:
        self._internal.delete_object(Bucket=self.bucket, Key=key)

    def presign_get(self, organizacion_id: UUID, key: str) -> str:
        if not key.startswith(prefijo_organizacion(organizacion_id)):
            raise ClaveFueraDeOrganizacion(key)
        return self._public.generate_presigned_url(
            'get_object', Params={'Bucket': self.bucket, 'Key': key}, ExpiresIn=self.expira,
        )

    def presign_get_legacy(self, key: str) -> str:
        """Solo API v1 DEMO (claves antiguas sin prefijo de organización)."""
        return self._public.generate_presigned_url(
            'get_object', Params={'Bucket': self.bucket, 'Key': key}, ExpiresIn=self.expira,
        )


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    """Dependencia sustituible en tests."""
    return Storage(settings.s3_bucket, settings.s3_endpoint, settings.s3_public_endpoint,
                   settings.s3_url_expira_segundos)
