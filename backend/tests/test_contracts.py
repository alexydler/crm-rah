from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.schemas import InmuebleCreate


BASE = {
    'titulo': 'Apartamento ficticio', 'tipo': 'apartamento', 'operacion': 'venta',
    'precio': '125000.00', 'zona': 'Zona ficticia',
}


def test_moneda_normalizada():
    obj = InmuebleCreate(**(BASE | {'moneda': 'usd'}))
    assert obj.moneda == 'USD'
    assert obj.precio == Decimal('125000.00')


def test_precio_negativo_rechazado():
    with pytest.raises(ValidationError):
        InmuebleCreate(**(BASE | {'precio': '-2'}))


def test_tipo_no_permitido():
    with pytest.raises(ValidationError):
        InmuebleCreate(**(BASE | {'tipo': 'garaje'}))


def test_terreno_sin_habitaciones():
    obj = InmuebleCreate(**(BASE | {'tipo': 'terreno', 'm2_parcela': '300'}))
    assert obj.habitaciones is None
    assert obj.m2_parcela == Decimal('300')


def test_moneda_no_soportada():
    with pytest.raises(ValidationError):
        InmuebleCreate(**(BASE | {'moneda': 'EUR'}))


def test_quinta_con_ubicacion_venezolana():
    obj = InmuebleCreate(**(BASE | {
        'tipo': 'quinta', 'estado_ve': 'Carabobo', 'municipio': 'Valencia',
        'urbanizacion': 'Sector de prueba', 'codigo_referencia': 'DEMO-004'
    }))
    assert obj.tipo == 'quinta'
    assert obj.estado_ve == 'Carabobo'
    assert obj.moneda == 'USD'
